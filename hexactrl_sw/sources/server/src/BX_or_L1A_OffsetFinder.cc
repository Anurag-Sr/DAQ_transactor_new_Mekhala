#include <BX_or_L1A_OffsetFinder.h>
#include <iostream>
#include <sstream>
#include <iomanip>
#include <boost/regex.hpp>

BX_or_L1A_OffsetFinder::BX_or_L1A_OffsetFinder(uhal::HwInterface* uhalHW, FastControlManager* fcman)
{
  m_uhalHW = uhalHW;
  m_fcMan = fcman;
}

bool BX_or_L1A_OffsetFinder::configureLatencyAndOffset(const YAML::Node& config)
{
  if( config["l1aOffsetFinder"].IsDefined()==false ||
      config["l1aOffsetFinder"]["method"].IsDefined()==false ||
      config["l1aOffsetFinder"]["fifo_latency"].IsDefined()==false ||
      config["l1aOffsetFinder"]["L1A_offset_or_BX"].IsDefined()==false )
    return FindAndSetOffset();
  else if( config["l1aOffsetFinder"]["method"].as<std::string>()!=std::string("manual") )
    return FindAndSetOffset();
  else{
    m_lchandler.setRegister("L1A_offset_or_BX",config["l1aOffsetFinder"]["L1A_offset_or_BX"].as<int>());
    m_lchandler.setRegister("fifo_latency",    config["l1aOffsetFinder"]["fifo_latency"].as<int>());
    return true;
  }
}

bool BX_or_L1A_OffsetFinder::FindAndSetOffset()
{
  std::ostringstream os( std::ostringstream::ate );
  uhal::ValWord<uint32_t> norbit;
  uint32_t bsize = m_fcMan->getRegister("bx_orbit_sync"); //i.e. it will read one complete orbit (and not more) to find the event data
  m_lchandler.setGlobalRegister( "interrupt_enable", 0x0);
  m_lchandler.setRegister("L1A_offset_or_BX",0x0);
  m_lchandler.setRegister("fifo_latency",0x0);
  m_lchandler.setRegister("capture_mode_in",0x1);
  m_lchandler.setRegister("aquire_length",bsize);
  m_lchandler.setRegister("total_length",bsize);

  std::vector<uint32_t> bramdata(bsize,0);

  m_fcMan->resetFC(); //to be sure, we will not have L1As that are not coming from channel A 

  //find latency setting 
  m_lchandler.setRegister("explicit_rstb_acquire", 0x0);
  for( auto elink : m_lchandler.getElinks() ){
    (void)elink;
    m_lchandler.setGlobalRegister( "interrupt_enable." + elink.name(), 0x1);
  }
  m_lchandler.setGlobalRegister("aquire", 0x1);
  m_lchandler.getGlobalRegister("interrupt_vec");
  std::vector<uint32_t> latency_offsets;
  for( auto elink : m_lchandler.getElinks() ){
    m_lchandler.getData(elink.name(),bramdata,bsize);
    uint32_t i;
    for(i = 0; i < bsize; ++i){
      if((bramdata[i] & 0xf0000000) == 0x90000000){
        break;
      }
    }
    if(i < bsize) latency_offsets.push_back(i);
    else          latency_offsets.push_back(-1);
  }
  uint32_t maxLatency = *std::max_element(latency_offsets.begin(), latency_offsets.end());
  for( uint32_t i = 0; i < m_lchandler.getElinks().size(); ++i ){
    auto fifo_latency = maxLatency-latency_offsets[i];
    if( fifo_latency>m_lchandler.getRegisterMask(m_lchandler.getElinks()[i].name(), "fifo_latency") ){
      return false;
    }
    else
      m_lchandler.setRegister(m_lchandler.getElinks()[i].name(), "fifo_latency", fifo_latency);
  }
  
  m_lchandler.setRegister("capture_mode_in",0x2);
  m_fcMan->set_fc_channel_A_settings(0x1, 0x10, 0x0, FC_channel_flavor::L1A, 1, FC_channel_follow::DISABLE); //could be replaced by single request here
  m_fcMan->enable_global_l1a(0x1);
  
  //find approperiate L1A offset
  for( auto elink : m_lchandler.getElinks() ){
    bool offsetFound=false;
    int ntest=0;
    while(offsetFound==false){
      if(ntest>=10) {
	std::cout << "return false on link " << m_lchandler.name() << " " << elink.name() << std::endl;
	m_fcMan->enable_global_l1a(0x0);
	return false;
      }

      m_lchandler.setRegister(elink.name(), "explicit_rstb_acquire", 0x0);
      m_lchandler.setRegister(elink.name(), "explicit_rstb_acquire", 0x1);
      m_lchandler.setGlobalRegister( "interrupt_enable." + elink.name(), 0x1);
      m_lchandler.setRegister(elink.name(), "aquire", 0x1);
      m_lchandler.getGlobalRegister("interrupt_vec");
      m_lchandler.getData(elink.name(),bramdata,bsize);
      
      auto it = std::find_if( bramdata.begin(), bramdata.end(), [](const uint32_t& d){ return ( d>>28 ) == 0x5; } );
      unsigned  count = std::distance(bramdata.begin(),it);
      if( it==bramdata.end() || count>=bsize || count>=m_lchandler.getRegisterMask(elink.name(), "L1A_offset_or_BX") ){ //might be needed to check that count is indeed lower than L1A_offset_or_BX bit mask
	ntest++;
	continue;
      }
      else{
	offsetFound=true;
	m_lchandler.setRegister(elink.name(), "L1A_offset_or_BX", count);
      }
    }
  }
  m_lchandler.setRegister("explicit_rstb_acquire", 0);  // reset the acquire state machine of all links
  m_lchandler.setRegister("explicit_rstb_acquire", 1);
  m_lchandler.setGlobalRegister( "interrupt_enable", 0x0);
  m_fcMan->enable_global_l1a(0x0);
  m_fcMan->set_fc_channel_A_settings(0x0, 0x0, 0x0, FC_channel_flavor::L1A, 1, FC_channel_follow::DISABLE); 
  return true;
}
