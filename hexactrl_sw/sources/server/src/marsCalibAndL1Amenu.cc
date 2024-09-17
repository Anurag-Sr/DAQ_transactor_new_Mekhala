#include <marsCalibAndL1Amenu.h>

void marsCalibAndL1Amenu::on_configure(const YAML::Node& config)
{
  std::cout << "***** marsCalibAndL1A menu configuration *****\n"
	    << config << "\n"
	    << "****************************************"
	    << std::endl;
  
  m_bxCalib=0;
  if( config["bxCalib"].IsDefined() )
    m_bxCalib = config["bxCalib"].as<int>();

  m_bxL1A=20;
  if( config["bxL1A"].IsDefined() )
    m_bxL1A = config["bxL1A"].as<int>();

  m_prescale=0;
  if( config["prescale"].IsDefined() )
    m_prescale = config["prescale"].as<int>();

  m_repeatOffset=0;
  if( config["repeatOffset"].IsDefined() )
    m_repeatOffset = config["repeatOffset"].as<int>();

  configureMarsTypes(config);

  m_marsptr = std::make_shared<MarsAccumulatorInterface>(m_uhalHW);
}

void marsCalibAndL1Amenu::on_sendStartRun()
{
  m_pusher->sendStartOfRun(DataType::MARS);
  std::cout << "Starting marsCalibAndL1A menu " << std::endl;
}

void marsCalibAndL1Amenu::configurefc()
{
  int enable=0x1;
  m_fcMan->set_fc_channel_A_settings(enable, m_bxCalib, m_prescale, FC_channel_flavor::CALPULINT, 0x1, FC_channel_follow::DISABLE);
  m_fcMan->set_fc_channel_B_settings(enable, m_bxL1A,   m_prescale, FC_channel_flavor::L1A      , 0x1, FC_channel_follow::A);

  if( m_repeatOffset ){
    m_fcMan->set_fc_channel_C_settings(enable, 1*m_repeatOffset + m_bxCalib, m_prescale, FC_channel_flavor::CALPULINT, 0x1, FC_channel_follow::DISABLE);
    m_fcMan->set_fc_channel_D_settings(enable, 1*m_repeatOffset + m_bxL1A,   m_prescale, FC_channel_flavor::L1A      , 0x1, FC_channel_follow::C);
    m_fcMan->set_fc_channel_E_settings(enable, 2*m_repeatOffset + m_bxCalib, m_prescale, FC_channel_flavor::CALPULINT, 0x1, FC_channel_follow::DISABLE);
    m_fcMan->set_fc_channel_F_settings(enable, 2*m_repeatOffset + m_bxL1A,   m_prescale, FC_channel_flavor::L1A      , 0x1, FC_channel_follow::E);
    m_fcMan->set_fc_channel_G_settings(enable, 3*m_repeatOffset + m_bxCalib, m_prescale, FC_channel_flavor::CALPULINT, 0x1, FC_channel_follow::DISABLE);
    m_fcMan->set_fc_channel_H_settings(enable, 3*m_repeatOffset + m_bxL1A,   m_prescale, FC_channel_flavor::L1A      , 0x1, FC_channel_follow::G);
  }
}
