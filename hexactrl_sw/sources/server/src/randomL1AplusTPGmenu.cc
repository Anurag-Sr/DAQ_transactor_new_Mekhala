#include <randomL1AplusTPGmenu.h>

#include <boost/timer/timer.hpp>

#ifndef DEBUG_TIMER 
#define DEBUG_TIMER 1
#endif

void randomL1AplusTPGmenu::on_configure(const YAML::Node& config)
{
  std::cout << "***** randomL1AplusTPG menu configuration *****\n"
	    << config << "\n"
	    << "******************************************"
	    << std::endl;

  m_nevents=1000;
  if( config["NEvents"].IsDefined() )
    m_nevents = config["NEvents"].as<int>();
  
  m_random_period=0;
  if( config["log2_rand_bx_period"].IsDefined() )
    m_random_period = config["log2_rand_bx_period"].as<int>();

  m_bxmin = HGCROC_DATA_BUF_SIZE+1;
  if( config["bx_min"].IsDefined() )
    m_bxmin = config["bx_min"].as<int>();

  m_trg_fifo_latency = 3;
  if( config["trg_fifo_latency"].IsDefined() )
    m_trg_fifo_latency = config["trg_fifo_latency"].as<uint32_t>();

  init_containers();
  init_linkdatavec();
}

void randomL1AplusTPGmenu::init_linkdatavec()
{
  uint32_t nmaxevent =  std::min({
				  (uint32_t)(m_daq_link->getGlobalRegister("bram_size")/HGCROC_DATA_BUF_SIZE),
				  (uint32_t)(m_trg_link->getGlobalRegister("bram_size")/TRIG_ACQUIRE_LENGTH) });

  m_fulldaqreadoutsize = nmaxevent*HGCROC_DATA_BUF_SIZE;
  m_linksdata.clear();
  m_linksdata = std::vector< std::vector<uint32_t> >(m_daq_link->getElinks().size());
  std::fill( m_linksdata.begin(), m_linksdata.end(), std::vector<uint32_t>(m_fulldaqreadoutsize,0x0) );
  
  m_fulltrgreadoutsize = nmaxevent*TRIG_ACQUIRE_LENGTH;
  m_linkstrig.clear();
  m_linkstrig = std::vector< std::vector<uint32_t> >(m_trg_link->getElinks().size());
  std::fill( m_linkstrig.begin(), m_linkstrig.end(), std::vector<uint32_t>(m_fulltrgreadoutsize,0x0) );
}

void randomL1AplusTPGmenu::on_runthread()
{
  m_fcMan->resetFC();
  m_event=0;

  configurelinks();
  configurefc();
  
  boost::thread sender( boost::bind(&randomL1AplusTPGmenu::package_and_send,this) );
  boost::thread acquirer( boost::bind(&randomL1AplusTPGmenu::acquire,this) );

  sender.join();
  acquirer.join();
  m_fcMan->resetFC();

  int id=0;
  for(auto container : m_roceventcontainers){
    std::cout << "remaining events in chip " << id << ":\t" << std::dec << container->getDequeEvents().size() << std::endl;
    container->getDequeEvents().clear();
    id++;
  }
}

void randomL1AplusTPGmenu::on_sendStartRun()
{
  m_pusher->sendStartOfRun(DataType::HGCROC);
  std::cout << "Starting randomL1AplusTPG menu with : \t"
	    << "NEvents = " << m_nevents << std::endl;
}

void randomL1AplusTPGmenu::configurelinks()
{
  
  // DAQ links
  {    
    m_daq_link->setGlobalRegister( "interrupt_enable", 0x0);//to be sure all bits are '0'
    std::for_each(m_daq_link->getElinks().cbegin(), m_daq_link->getElinks().cend(),
		  [&](auto &elink){ m_daq_link->setGlobalRegister( "interrupt_enable." + elink.name(), 0x1); } );
    m_daq_link->setGlobalContinousAcquire(false);
    m_daq_link->setRegister("explicit_rstb_acquire", 0);
    m_daq_link->setRegister("explicit_rstb_acquire", 1);
    m_daq_link->setRegister("capture_mode_in",0x2);
    m_daq_link->setRegister("aquire_length", HGCROC_DATA_BUF_SIZE);
    m_daq_link->setRegister("total_length", m_fulldaqreadoutsize);
    m_daq_link->setGlobalContinousAcquire(true);
  }

  // TRG links
  {
    m_trg_link->setGlobalRegister( "interrupt_enable", 0x0);//to be sure all bits are '0'
    std::for_each(m_trg_link->getElinks().cbegin(), m_trg_link->getElinks().cend(),
		  [&](auto &elink){ m_trg_link->setGlobalRegister( "interrupt_enable." + elink.name(), 0x1); } );
    m_trg_link->setGlobalContinousAcquire(false);
    m_trg_link->setRegister("explicit_rstb_acquire", 0);
    m_trg_link->setRegister("explicit_rstb_acquire", 1);
    m_trg_link->setRegister("capture_mode_in",0x2);
    m_trg_link->setRegister("aquire_length", TRIG_ACQUIRE_LENGTH);
    m_trg_link->setRegister("total_length", m_fulltrgreadoutsize);
    m_trg_link->setRegister("fifo_latency",m_trg_fifo_latency);
    m_trg_link->setGlobalContinousAcquire(true);
  }

}

void randomL1AplusTPGmenu::configurefc()
{
  m_fcMan->minimum_trigger_period(m_bxmin);
  m_fcMan->enable_random_l1a(0x1);
  m_fcMan->random_trigger_log2_period(m_random_period);
}

void randomL1AplusTPGmenu::acquire()
{
  boost::thread threads[ m_daq_link->getElinks().size() ];
  
  m_fcMan->request_orbit_rst();
  m_fcMan->request_ecr();
  
  while(!m_stop){
    m_fcMan->enable_global_l1a(0x1);
    m_daq_link->getGlobalRegister("interrupt_vec");
    m_trg_link->getGlobalRegister("interrupt_vec");
    m_fcMan->enable_global_l1a(0x0);//disable L1As to be sure we don't fill FIFO of some link type while the other type are not yet ready (i.e. their FIFOs are not empty)

    // //DEBUG
    // std::cout << "Before FIFO readout" << std::endl;
    // std::for_each( m_daq_link->getElinks().cbegin(), m_daq_link->getElinks().cend(), [&](auto &elink){
    //     std::cout << "\t\t Fifo occupancy of DAQ links = " << m_daq_link->getRegister( elink.name(), "fifo_occupancy" ) << std::endl;
    //   } );
    // std::for_each( m_trg_link->getElinks().cbegin(), m_trg_link->getElinks().cend(), [&](auto &elink){
    //     std::cout << "\t\t Fifo occupancy of TRG links = " << m_trg_link->getRegister( elink.name(), "fifo_occupancy" ) << std::endl;
    //   } );
    // 
    // //
    
    int id=0;
    //put DAQ link data in m_linksdata
    std::for_each( m_daq_link->getElinks().cbegin(), m_daq_link->getElinks().cend(), [&](auto &elink){
       m_daq_link->getData( elink.name(), m_linksdata[id], m_fulldaqreadoutsize );
       id++;
     } );
    id=0;
    //put TRG link data in m_linkstrig
    std::for_each( m_trg_link->getElinks().cbegin(), m_trg_link->getElinks().cend(), [&](auto &elink){
       m_trg_link->getData( elink.name(), m_linkstrig[id], m_fulltrgreadoutsize );
       id++;
     } );
    
    //emptying the FIFO
    std::for_each( m_daq_link->getElinks().cbegin(), m_daq_link->getElinks().cend(), [&](auto &elink){
	auto occupancy = m_daq_link->getRegister( elink.name(), "fifo_occupancy" );
	if( occupancy ) {
	  std::vector<uint32_t> vec; vec.resize(occupancy);
	  m_daq_link->getData( elink.name(), vec, occupancy );
	}
      } );
    std::for_each( m_trg_link->getElinks().cbegin(), m_trg_link->getElinks().cend(), [&](auto &elink){
	auto occupancy = m_trg_link->getRegister( elink.name(), "fifo_occupancy" );
	if( occupancy ){
	  std::vector<uint32_t> vec; vec.resize(occupancy);
	  m_trg_link->getData( elink.name(), vec, occupancy );
	}
      } );
      
    // //DEBUG
    // std::cout << "After FIFO readout" << std::endl;
    // std::for_each( m_daq_link->getElinks().cbegin(), m_daq_link->getElinks().cend(), [&](auto &elink){
    //     std::cout << "\t\t Fifo occupancy of DAQ links = " << m_daq_link->getRegister( elink.name(), "fifo_occupancy" ) << std::endl;
    //   } );
    // std::for_each( m_trg_link->getElinks().cbegin(), m_trg_link->getElinks().cend(), [&](auto &elink){
    //     std::cout << "\t\t Fifo occupancy of TRG links = " << m_trg_link->getRegister( elink.name(), "fifo_occupancy" ) << std::endl;
    //   } );

    id=0;
    for(auto container : m_roceventcontainers ){
      threads[id] = boost::thread( boost::bind(&HGCROCEventContainer::fillContainer,
					       container,
					       m_event,
					       boost::ref(m_linksdata[2*id]),
					       boost::ref(m_linksdata[2*id+1]),
					       boost::ref(m_linkstrig[4*id]),
					       boost::ref(m_linkstrig[4*id+1]),
					       boost::ref(m_linkstrig[4*id+2]),
					       boost::ref(m_linkstrig[4*id+3]) ) );
      id++;
    }
    for(auto i=0; i<id; i++ )
      threads[i].join();
    m_event += m_fulldaqreadoutsize/HGCROC_DATA_BUF_SIZE;
  }
  m_daq_link->setGlobalContinousAcquire(false);
  m_daq_link->setRegister("explicit_rstb_acquire", 0);
  m_daq_link->setRegister("explicit_rstb_acquire", 1);
  m_daq_link->setGlobalRegister( "interrupt_enable", 0x0);

  m_trg_link->setGlobalContinousAcquire(false);
  m_trg_link->setRegister("explicit_rstb_acquire", 0);
  m_trg_link->setRegister("explicit_rstb_acquire", 1);
  m_trg_link->setGlobalRegister( "interrupt_enable", 0x0);
}
