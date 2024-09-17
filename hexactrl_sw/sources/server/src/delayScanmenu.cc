#include <delayScanmenu.h>

#include <boost/timer/timer.hpp>

#ifndef DEBUG_TIMER 
#define DEBUG_TIMER 1
#endif

void delayScanmenu::on_configure(const YAML::Node& config)
{
  std::cout << "****** delayScan menu configuration *******\n"
	    << config << "\n"
	    << "*******************************************" << std::endl;

  m_maxDelay=512;
  if( config["maxDelay"].IsDefined() )
    m_maxDelay = config["maxDelay"].as<uint32_t>();
  
  m_delayStep=1;
  if( config["delayStep"].IsDefined() )
    m_delayStep = config["delayStep"].as<uint32_t>();

  m_idlePattern = 0xACCCCCCC;
  if( config["idlePattern"].IsDefined() )
    m_idlePattern = config["idlePattern"].as<uint32_t>();

  m_acquireLength = 1000;
  if( config["acquireLength"].IsDefined() )
    m_acquireLength = config["acquireLength"].as<uint32_t>();
}

void delayScanmenu::on_runthread()
{
  configurefc();
  configurelinks();
  acquire();
}

void delayScanmenu::on_sendStartRun()
{
  m_pusher->sendStartOfRun(DataType::DELAY_SCAN);
  std::cout << "Starting delayScan menu" << std::endl;
}

void delayScanmenu::configurelinks()
{
  auto config = [&](LinkCaptureBlockHandler lchandler){
    lchandler.setRegister("explicit_rstb_acquire", 0);
    lchandler.setRegister("explicit_rstb_acquire", 1);
    lchandler.setRegister( "align_pattern", m_idlePattern);
    lchandler.setRegister( "delay.mode", 0x0 ); //i.e. use the delay set by the user (delay.in and toggle of delay.set)
    lchandler.setRegister( "capture_mode_in", 0x0 ); //i.e. immediate acquire when toggling "acquire" register
    auto length = std::min(m_acquireLength,lchandler.getGlobalRegister("bram_size"));
    lchandler.setRegister( "aquire_length", length );
    lchandler.setRegister( "total_length", length );
    lchandler.setRegister( "fifo_latency", 0x0 );
  };

  config(*m_daq_link);
  config(*m_trg_link);
  
}

void delayScanmenu::configurefc()
{
  m_fcMan->resetFC();
}

void delayScanmenu::acquire()
{
  std::for_each( m_daq_link->getElinks().cbegin(), m_daq_link->getElinks().cend(), [&](auto &elink){ acquire_link(*m_daq_link,elink.name()); } );
  std::for_each( m_trg_link->getElinks().cbegin(), m_trg_link->getElinks().cend(), [&](auto &elink){ acquire_link(*m_trg_link,elink.name()); } );
  m_stop = true; //to let DAQManager knows the delayScan is done
}

void delayScanmenu::acquire_link(LinkCaptureBlockHandler lchandler, std::string linkname)
{
  auto length = std::min(m_acquireLength,lchandler.getGlobalRegister("bram_size"));
  bool triggerLink = lchandler.name().find("trg") != std::string::npos ;
  std::vector<DELAYSCAN_DATAPTR> datavec;
  std::ostringstream os(std::ostringstream::ate); os.str("");
  os << lchandler.name() << "." << linkname; //os has the full link name. E.g.: link_capture_daq.link5
  printf("start delay scan in link : %s\n",os.str().c_str());
  std::vector<uint32_t> idledata(length,0);

  for( uint32_t idelay=0; idelay<m_maxDelay; idelay+=m_delayStep ){
    lchandler.setRegister(linkname,"explicit_resetb",0x0);
    lchandler.setRegister(linkname,"explicit_resetb",0x1);
    lchandler.setRegister(linkname,"delay.in",idelay);
    lchandler.setRegister(linkname,"delay.set",0x1);
    lchandler.setRegister(linkname,"delay.set",0x0);
    uint32_t delayout=m_maxDelay+1;
    while(delayout!=idelay){
      delayout = lchandler.getRegister(linkname,"delay_out");
      boost::this_thread::sleep( boost::posix_time::microseconds(100) );
    }
    lchandler.setRegister(linkname,"explicit_align",0x1);
    m_fcMan->request_link_reset_roct();
    m_fcMan->request_link_reset_rocd();

    int count=0;
    while(count<10){
      auto state = lchandler.getRegister(linkname,"walign_state");
      if(!state==0) {
	count++;
	boost::this_thread::sleep( boost::posix_time::microseconds(100) );
      }
      else
	break;
    }
    lchandler.setRegister(linkname,"explicit_align",0x0);

    auto is_aligned = lchandler.getRegister(linkname,"status.link_aligned");
    auto aligned    = lchandler.getRegister(linkname,"link_aligned_count");
    auto errors     = lchandler.getRegister(linkname,"link_error_count");
    
    int nIdles=0;
    if( !triggerLink ){
      lchandler.setGlobalRegister("interrupt_enable." + linkname, 0x1);
      lchandler.setRegister(linkname, "aquire",0x1);
      lchandler.getGlobalRegister("interrupt_vec");
      lchandler.setRegister(linkname, "aquire",0x0);
      lchandler.getData(linkname,idledata,length);
      nIdles = (int)std::count( idledata.begin(), idledata.end(), m_idlePattern );
      lchandler.setRegister("explicit_rstb_acquire", 0);
      lchandler.setRegister("explicit_rstb_acquire", 1);
      lchandler.setGlobalRegister("interrupt_enable", 0x0);
    }
    auto lad = std::make_shared<link_aligner_data>( os.str(), idelay, aligned, errors, is_aligned, nIdles );
    datavec.push_back(lad);
  }
  m_pusher->sendvecptr(datavec);
}
