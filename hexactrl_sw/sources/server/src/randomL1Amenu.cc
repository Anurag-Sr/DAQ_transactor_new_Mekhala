#include <randomL1Amenu.h>

#include <boost/timer/timer.hpp>

#ifndef DEBUG_TIMER 
#define DEBUG_TIMER 1
#endif

void randomL1Amenu::on_configure(const YAML::Node& config)
{
  std::cout << "***** randomL1A menu configuration *****\n"
	    << config << "\n"
	    << "****************************************"
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

  init_containers();
  init_linkdatavec();
}
 
void randomL1Amenu::init_containers()
{
  // unsigned int nChip=m_daq_link->getElinks().size()/2;
  m_roceventcontainers.clear();
  // m_roceventcontainers = std::vector< std::shared_ptr<HGCROCEventContainer> >( nChip,nullptr );
  // auto index = std::size_t(0);
  // std::transform( m_roceventcontainers.begin(), m_roceventcontainers.end(), m_roceventcontainers.begin(),
  // 		  [&index](auto &container){return std::make_shared<HGCROCEventContainer>(index++);} );

  std::for_each( m_daq_link->getElinks().cbegin(), m_daq_link->getElinks().cend(), [&](auto &elink){
      auto chip=elink.chip();
      auto iter = std::find_if( m_roceventcontainers.begin(),
				m_roceventcontainers.end(),
				[&](auto& container){return container->chip()==chip;});
      if( iter==m_roceventcontainers.end() )
        m_roceventcontainers.push_back( std::make_shared<HGCROCEventContainer>(chip) );
    } );
}


void randomL1Amenu::init_linkdatavec()
{
  m_fulldaqreadoutsize = m_daq_link->getGlobalRegister("bram_size")/(3*HGCROC_DATA_BUF_SIZE)*HGCROC_DATA_BUF_SIZE;
  m_linksdata.clear();
  m_linksdata = std::vector< std::vector<uint32_t> >(m_daq_link->getElinks().size());
  std::fill( m_linksdata.begin(), m_linksdata.end(), std::vector<uint32_t>(m_fulldaqreadoutsize,0x0) );
}

void randomL1Amenu::on_runthread()
{
  m_fcMan->resetFC();
  m_event=0;

  configurelinks();
  configurefc();
  
  boost::thread sender( boost::bind(&randomL1Amenu::package_and_send,this) );
  boost::thread acquirer( boost::bind(&randomL1Amenu::acquire,this) );

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

void randomL1Amenu::on_sendStartRun()
{
  m_pusher->sendStartOfRun(DataType::HGCROC);
  std::cout << "Starting randomL1A menu with : \t"
	    << "NEvents = " << m_nevents << std::endl;
}

void randomL1Amenu::configurelinks()
{  
  m_daq_link->setGlobalRegister( "interrupt_enable", 0x0);
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

void randomL1Amenu::configurefc()
{
  m_fcMan->minimum_trigger_period(m_bxmin);
  m_fcMan->enable_random_l1a(0x1);
  m_fcMan->random_trigger_log2_period(m_random_period);
}

void randomL1Amenu::acquire()
{
  boost::thread threads[ m_daq_link->getElinks().size() ];
  
  m_fcMan->request_orbit_rst();
  m_fcMan->request_ecr();
  m_fcMan->enable_global_l1a(0x1);
  
  while(!m_stop){
    m_daq_link->getGlobalRegister("interrupt_vec");

    int id=0;
    std::for_each( m_daq_link->getElinks().cbegin(), m_daq_link->getElinks().cend(), [&](auto &elink){
       m_daq_link->getData( elink.name(), m_linksdata[id], m_fulldaqreadoutsize );
       id++;
     } );
    
    id=0;
    for(auto container : m_roceventcontainers ){
      threads[id] = boost::thread( boost::bind(&HGCROCEventContainer::fillContainer,
					       container,
					       m_event,
					       boost::ref(m_linksdata[2*id]),
					       boost::ref(m_linksdata[2*id+1]) ) );
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
}

void randomL1Amenu::package_and_send()
{
  boost::timer::cpu_timer timer;
  timer.start();
  uint32_t neventEventSent=0;
  uint32_t printout=0;
  while(!m_stop){

    bool oneIsEmpty=false;
    uint32_t minNEvents=0xffffffff;
    std::for_each( m_roceventcontainers.cbegin(),m_roceventcontainers.cend(),
		   [&](auto &container){
		     container->deque_lock(); //don't understand why lock and unlock are necessary here, but have experienced segmentation fault whitout them 
		     if( container->getDequeEvents().empty() )
		       oneIsEmpty=true;
		     else if( container->getDequeEvents().size()<minNEvents )
		       minNEvents = container->getDequeEvents().size();
		     container->deque_unlock();
		   } );
    if( oneIsEmpty ){
      boost::this_thread::sleep( boost::posix_time::microseconds(100) );
      continue;
    }

    std::for_each(m_roceventcontainers.cbegin(),m_roceventcontainers.cend(),
		  [&](auto &container){
		    container->deque_lock(); //need the lock as writing (and erasing) into container is not thread safe
		    m_pusher->sendvecptr(container->getDequeEvents(),minNEvents);
		    container->getDequeEvents().erase(container->getDequeEvents().begin(),container->getDequeEvents().begin()+minNEvents);
		    container->deque_unlock();
		  } );
    neventEventSent+=minNEvents;
    if(neventEventSent>printout+1000){
      printout+=1000;
      std::ostringstream out;
      out << "event = " << std::dec << printout << "  (out of " << m_nevents << ")" << std::endl;
      printf("%s",out.str().c_str());
    }
    if( neventEventSent >= m_nevents && m_nevents>0 )
      m_stop = true;
  }
  timer.stop();
#ifdef DEBUG_TIMER
  printf("%s%6.1f%s","\t\t  EVENT RATE FOR THIS RUN = ",m_nevents/(timer.elapsed().wall/1e9),"\n");
#endif
}
