#include <calibAndL1AplusTPGmenu.h>

#include <boost/timer/timer.hpp>

#ifndef DEBUG_TIMER 
#define DEBUG_TIMER 1
#endif

void calibAndL1AplusTPGmenu::on_configure(const YAML::Node& config)
{
  std::cout << "***** calibAndL1AplusTPG menu configuration *****\n"
	    << config << "\n"
	    << "******************************************"
	    << std::endl;

  m_nevents=1000;
  if( config["NEvents"].IsDefined() )
    m_nevents = config["NEvents"].as<int>();
  
  m_bxCalib=0;
  if( config["bxCalib"].IsDefined() )
    m_bxCalib = config["bxCalib"].as<int>();

  m_bxL1A=20;
  if( config["bxL1A"].IsDefined() )
    m_bxL1A = config["bxL1A"].as<int>();

  m_lengthCalib=1;
  if( config["lengthCalib"].IsDefined() )
    m_lengthCalib = config["lengthCalib"].as<int>();

  m_lengthL1A=1;
  if( config["lengthL1A"].IsDefined() )
    m_lengthL1A = config["lengthL1A"].as<int>();

  m_prescale=0;
  if( config["prescale"].IsDefined() )
    m_prescale = config["prescale"].as<int>();

  m_trg_fifo_latency = 3;
  if( config["trg_fifo_latency"].IsDefined() )
    m_trg_fifo_latency = config["trg_fifo_latency"].as<uint32_t>();

  init_containers();
  init_linkdatavec();
}

void calibAndL1AplusTPGmenu::on_sendStartRun()
{
  m_pusher->sendStartOfRun(DataType::HGCROC);
  std::cout << "Starting calibAndL1AplusTPG menu with : \t"
	    << "NEvents = " << m_nevents << std::endl;
}

void calibAndL1AplusTPGmenu::configurefc()
{
  int enable=0x1;
  m_fcMan->set_fc_channel_A_settings(enable, m_bxCalib, m_prescale, FC_channel_flavor::CALPULINT, m_lengthCalib, FC_channel_follow::DISABLE);
  m_fcMan->set_fc_channel_B_settings(enable, m_bxL1A,   m_prescale, FC_channel_flavor::L1A      , m_lengthL1A  , FC_channel_follow::A);
}
