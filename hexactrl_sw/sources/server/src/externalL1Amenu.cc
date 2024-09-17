#include <externalL1Amenu.h>

#include <boost/timer/timer.hpp>

#ifndef DEBUG_TIMER 
#define DEBUG_TIMER 1
#endif

void externalL1Amenu::on_configure(const YAML::Node& config)
{
  std::cout << "***** externalL1A menu configuration *****\n"
	    << config << "\n"
	    << "******************************************"
	    << std::endl;

  m_nevents=1000;
  if( config["NEvents"].IsDefined() )
    m_nevents = config["NEvents"].as<int>();
  
  m_loopBack=false;
  if( config["loopBack"].IsDefined() )
    m_loopBack = config["loopBack"].as<bool>();

  m_bxExtCalib=0;
  if( config["bxCalibExt"].IsDefined() )
    m_bxExtCalib = config["bxCalibExt"].as<int>();

  m_lengthCalib=1;
  if( config["lengthCalibExt"].IsDefined() )
    m_lengthCalib = config["lengthCalibExt"].as<int>();

  m_prescale = 0;
  if( config["prescale"].IsDefined() )
    m_prescale = config["prescale"].as<int>();

  m_trg_fifo_latency = 3;
  if( config["trg_fifo_latency"].IsDefined() )
    m_trg_fifo_latency = config["trg_fifo_latency"].as<uint32_t>();

  m_trgphase_fifo_latency = 15;
  if( config["trgphase_fifo_latency"].IsDefined() )
    m_trgphase_fifo_latency = config["trgphase_fifo_latency"].as<uint32_t>();

  init_containers();
  init_linkdatavec();
  // unsigned int nChip=m_daq_link->getElinks().size()/2;
  // m_roceventcontainers.clear();
  // m_roceventcontainers = std::vector< std::shared_ptr<HGCROCEventContainer> >( nChip,nullptr );
  // auto index = std::size_t(0);
  // std::transform( m_roceventcontainers.begin(), m_roceventcontainers.end(), m_roceventcontainers.begin(),
  // 		  [&index](auto &container){return std::make_shared<HGCROCEventContainer>(index++);} );

  m_selftrig.reset();
  m_selftrig = std::make_unique<SelfTriggerBlockManager>( m_uhalHW );
}

void externalL1Amenu::init_linkdatavec()
{
  uint32_t nmaxevent =  std::min({
      (uint32_t)(m_daq_link->getGlobalRegister("bram_size")/HGCROC_DATA_BUF_SIZE),
	(uint32_t)(m_trg_link->getGlobalRegister("bram_size")/TRIG_ACQUIRE_LENGTH),
	(uint32_t)(m_trgphase_link->getGlobalRegister("bram_size")/TRIG_LATENCY_ACQUIRE_LENGTH) });
   
  m_fulldaqreadoutsize = nmaxevent*HGCROC_DATA_BUF_SIZE;
  m_linksdata.clear();
  m_linksdata = std::vector< std::vector<uint32_t> >(m_daq_link->getElinks().size());
  std::fill( m_linksdata.begin(), m_linksdata.end(), std::vector<uint32_t>(m_fulldaqreadoutsize,0x0) );
  
  m_fulltrgreadoutsize = nmaxevent*TRIG_ACQUIRE_LENGTH;
  m_linkstrig.clear();
  m_linkstrig = std::vector< std::vector<uint32_t> >(m_trg_link->getElinks().size());
  std::fill( m_linkstrig.begin(), m_linkstrig.end(), std::vector<uint32_t>(m_fulltrgreadoutsize,0x0) );

  m_fulltrgphasereadoutsize = nmaxevent*TRIG_LATENCY_ACQUIRE_LENGTH;
  m_triglatency_data.clear();
  m_triglatency_data = std::vector< uint32_t >(m_fulltrgphasereadoutsize,0x0);
}

void externalL1Amenu::on_runthread()
{
  m_fcMan->resetFC();
  m_event=0;

  configurelinks();
  configurefc();
  
  boost::thread sender( boost::bind(&externalL1Amenu::package_and_send,this) );
  boost::thread acquirer( boost::bind(&externalL1Amenu::acquire,this) );

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

void externalL1Amenu::on_sendStartRun()
{
  m_pusher->sendStartOfRun(DataType::HGCROC);
  std::cout << "Starting externalL1A menu with : \t"
	    << "NEvents = " << m_nevents << std::endl;
}

void externalL1Amenu::configurelinks()
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

  // Trigger phase link
  {
    m_trgphase_link->setGlobalRegister( "interrupt_enable", 0x0);//to be sure all bits are '0'
    m_trgphase_link->setGlobalRegister( "interrupt_enable.link0", 0x1);
    m_trgphase_link->setGlobalContinousAcquire(false);
    m_trgphase_link->setRegister("explicit_resetb",0);
    m_trgphase_link->setRegister("explicit_resetb",1);
    m_trgphase_link->setRegister("explicit_rstb_acquire", 0);
    m_trgphase_link->setRegister("explicit_rstb_acquire", 1);
    m_trgphase_link->setRegister("capture_mode_in",0x2);
    m_trgphase_link->setRegister("aquire_length", TRIG_LATENCY_ACQUIRE_LENGTH);
    m_trgphase_link->setRegister("total_length", m_fulltrgphasereadoutsize);
    m_trgphase_link->setRegister("fifo_latency",m_trgphase_fifo_latency);
    m_trgphase_link->setGlobalContinousAcquire(true);
  }

}

void externalL1Amenu::configurefc()
{
  m_selftrig->configForExternalL1A();
  m_fcMan->enable_external_l1a(0x1);

  if(m_loopBack){
    int enable=0x1;
    m_fcMan->set_fc_channel_A_settings(enable, m_bxExtCalib, m_prescale, FC_channel_flavor::EXTPULSE0, m_lengthCalib, FC_channel_follow::DISABLE);
  }
}

void externalL1Amenu::acquire()
{
  boost::thread threads[ m_daq_link->getElinks().size() ];
  
  m_fcMan->request_orbit_rst();
  m_fcMan->request_ecr();
  m_selftrig->start();

  while(!m_stop){
    m_fcMan->enable_global_l1a(0x1);
    m_daq_link->getGlobalRegister("interrupt_vec");
    m_trg_link->getGlobalRegister("interrupt_vec");
    m_trgphase_link->getGlobalRegister("interrupt_vec");
    m_fcMan->enable_global_l1a(0x0);//disable L1As to be sure we don't fill FIFO of some link type while the other type are not yet ready (i.e. their FIFOs are not empty)

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
    //put Trigger phase data in m_triglatency_data
    m_trgphase_link->getData( "link0", m_triglatency_data, m_fulltrgphasereadoutsize );
    
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
    std::for_each( m_trgphase_link->getElinks().cbegin(), m_trgphase_link->getElinks().cend(), [&](auto &elink){
	auto occupancy = m_trgphase_link->getRegister( elink.name(), "fifo_occupancy" );
	if( occupancy ){
	  std::vector<uint32_t> vec; vec.resize(occupancy);
	  m_trgphase_link->getData( elink.name(), vec, occupancy );
	}
      } );

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
					       boost::ref(m_linkstrig[4*id+3]),
					       boost::ref(m_triglatency_data) )
				   );
      id++;
    }
    for(auto i=0; i<id; i++ )
      threads[i].join();
    m_event += m_fulldaqreadoutsize/HGCROC_DATA_BUF_SIZE;
  }
  m_selftrig->stop();
  m_daq_link->setGlobalContinousAcquire(false);
  m_daq_link->setRegister("explicit_rstb_acquire", 0);
  m_daq_link->setRegister("explicit_rstb_acquire", 1);
  m_daq_link->setGlobalRegister( "interrupt_enable", 0x0);
  
  m_trg_link->setGlobalContinousAcquire(false);
  m_trg_link->setRegister("explicit_rstb_acquire", 0);
  m_trg_link->setRegister("explicit_rstb_acquire", 1);
  m_trg_link->setGlobalRegister( "interrupt_enable", 0x0);

  m_trgphase_link->setGlobalContinousAcquire(false);
  m_trgphase_link->setRegister("explicit_rstb_acquire", 0);
  m_trgphase_link->setRegister("explicit_rstb_acquire", 1);
  m_trgphase_link->setGlobalRegister( "interrupt_enable", 0x0);
}

