#include <calibAndL1Amenu.h>

#include <boost/timer/timer.hpp>

#ifndef DEBUG_TIMER 
#define DEBUG_TIMER 1
#endif

void calibAndL1Amenu::on_configure(const YAML::Node& config)
{
  std::cout << "***** calibAndL1A menu configuration *****\n"
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

  m_repeatOffset=0;
  if( config["repeatOffset"].IsDefined() )
    m_repeatOffset = config["repeatOffset"].as<int>();

  m_calibType=FC_channel_flavor::CALPULINT;
  if( config["calibType"].IsDefined() )
    m_calibType = config["calibType"].as<FC_channel_flavor>();

  init_containers();
  init_linkdatavec();
}

void calibAndL1Amenu::init_linkdatavec()
{
  uint32_t acquire_length = HGCROC_DATA_BUF_SIZE*m_lengthL1A;
  m_fulldaqreadoutsize = m_daq_link->getGlobalRegister("bram_size")/(3*acquire_length)*acquire_length;
  m_linksdata.clear();
  m_linksdata = std::vector< std::vector<uint32_t> >(m_daq_link->getElinks().size());
  std::fill( m_linksdata.begin(), m_linksdata.end(), std::vector<uint32_t>(m_fulldaqreadoutsize,0x0) );
}


void calibAndL1Amenu::configurelinks()
{

  m_daq_link->setGlobalRegister( "interrupt_enable", 0x0);
  std::for_each(m_daq_link->getElinks().cbegin(), m_daq_link->getElinks().cend(),
		[&](auto &elink){ m_daq_link->setGlobalRegister( "interrupt_enable." + elink.name(), 0x1); } );
  m_daq_link->setGlobalContinousAcquire(false);
  m_daq_link->setRegister("explicit_rstb_acquire", 0);
  m_daq_link->setRegister("explicit_rstb_acquire", 1);
  m_daq_link->setRegister("capture_mode_in",0x2);
  m_daq_link->setRegister("aquire_length", HGCROC_DATA_BUF_SIZE*m_lengthL1A);
  m_daq_link->setRegister("total_length", m_fulldaqreadoutsize);

  m_daq_link->setGlobalContinousAcquire(true);
}

void calibAndL1Amenu::configurefc()
{
  int enable=0x1;
  m_fcMan->set_fc_channel_A_settings(enable, m_bxCalib, m_prescale, m_calibType, m_lengthCalib, FC_channel_follow::DISABLE);
  m_fcMan->set_fc_channel_B_settings(enable, m_bxL1A,   m_prescale, FC_channel_flavor::L1A      , m_lengthL1A  , FC_channel_follow::A);
  if( m_repeatOffset ){
    m_fcMan->set_fc_channel_C_settings(enable, 1*m_repeatOffset + m_bxCalib, m_prescale, m_calibType, 0x1, FC_channel_follow::DISABLE);
    m_fcMan->set_fc_channel_D_settings(enable, 1*m_repeatOffset + m_bxL1A,   m_prescale, FC_channel_flavor::L1A      , 0x1, FC_channel_follow::C);
    m_fcMan->set_fc_channel_E_settings(enable, 2*m_repeatOffset + m_bxCalib, m_prescale, m_calibType, 0x1, FC_channel_follow::DISABLE);
    m_fcMan->set_fc_channel_F_settings(enable, 2*m_repeatOffset + m_bxL1A,   m_prescale, FC_channel_flavor::L1A      , 0x1, FC_channel_follow::E);
    m_fcMan->set_fc_channel_G_settings(enable, 3*m_repeatOffset + m_bxCalib, m_prescale, m_calibType, 0x1, FC_channel_follow::DISABLE);
    m_fcMan->set_fc_channel_H_settings(enable, 3*m_repeatOffset + m_bxL1A,   m_prescale, FC_channel_flavor::L1A      , 0x1, FC_channel_follow::G);
  }
}

void calibAndL1Amenu::on_sendStartRun()
{
  m_pusher->sendStartOfRun(DataType::HGCROC);
  std::cout << "Starting calibAndL1A menu with : \t"
           << "NEvents = " << m_nevents << std::endl;
}
