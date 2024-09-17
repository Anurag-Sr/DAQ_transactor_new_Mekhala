#include <marsRndL1Amenu.h>

void marsRndL1Amenu::on_configure(const YAML::Node& config)
{
  std::cout << "***** marsRndL1A menu configuration *****\n"
	    << config << "\n"
	    << "****************************************"
	    << std::endl;
  
  m_random_period=0;
  if( config["log2_rand_bx_period"].IsDefined() )
    m_random_period = config["log2_rand_bx_period"].as<int>();

  m_bxmin = HGCROC_DATA_BUF_SIZE+1;
  if( config["bx_min"].IsDefined() )
    m_bxmin = config["bx_min"].as<int>();

  configureMarsTypes(config);
  
  m_marsptr = std::make_shared<MarsAccumulatorInterface>(m_uhalHW);
}

void marsRndL1Amenu::configureMarsTypes(const YAML::Node& config)
{
  m_marsTypes = {MARS_DATA_TYPE::ADC, MARS_DATA_TYPE::TOA, MARS_DATA_TYPE::TOT, MARS_DATA_TYPE::TDC };
  if( config["marsTypes"].IsDefined() ){
    m_marsTypes = config["marsTypes"].as< MARS_DATA_TYPE_VEC >();
  }
}

void marsRndL1Amenu::on_runthread()
{
  m_fcMan->resetFC();

  configurelinks();
  configurefc();
  
  acquire();

  m_fcMan->resetFC();
  m_stop=true;
}

void marsRndL1Amenu::on_sendStartRun()
{
  m_pusher->sendStartOfRun(DataType::MARS);
  std::cout << "Starting marsRndL1A menu " << std::endl;
}

void marsRndL1Amenu::configurelinks()
{  
  m_marsptr->setMarsTriggerLink( (*m_daq_link->getElinks().cbegin()).name() );

  m_daq_link->setGlobalRegister( "interrupt_enable", 0x0);
  std::for_each(m_daq_link->getElinks().cbegin(), m_daq_link->getElinks().cend(),
		[&](auto &elink){ m_daq_link->setGlobalRegister( "interrupt_enable." + elink.name(), 0x1); } );
  m_daq_link->setGlobalContinousAcquire(false);
  m_daq_link->setRegister("explicit_rstb_acquire", 0);
  m_daq_link->setRegister("explicit_rstb_acquire", 1);
  m_daq_link->setRegister("capture_mode_in",0x2);
  m_daq_link->setRegister("aquire_length", HGCROC_DATA_BUF_SIZE);
  m_daq_link->setRegister("total_length", HGCROC_DATA_BUF_SIZE);
  m_daq_link->setGlobalContinousAcquire(true);

  m_marsdata = std::vector<MarsData>(m_daq_link->getElinks().size());
}

void marsRndL1Amenu::configurefc()
{
  m_fcMan->minimum_trigger_period(m_bxmin);
  m_fcMan->enable_random_l1a(0x1);
  m_fcMan->random_trigger_log2_period(m_random_period);
}

void marsRndL1Amenu::acquire()
{
  m_fcMan->request_orbit_rst();
  m_fcMan->request_ecr();
  m_fcMan->enable_global_l1a(0x1);

  for(auto dtype: m_marsTypes){
    m_marsptr->resetMars();
    m_marsptr->setDataType(dtype);
    m_marsptr->startMars();
    m_marsptr->waitUntilDone();
    int linkid=0;
    std::for_each(m_marsdata.begin(), m_marsdata.end(), [&](auto &md){
							  link_description linkdesc = m_daq_link->getElinks()[linkid];
							  md=m_marsptr->readMars(linkdesc);
							  linkid++;
							} );
    m_pusher->sendvec(m_marsdata);
  }

  m_marsptr->resetMars();
  m_daq_link->setGlobalContinousAcquire(false);
  m_daq_link->setRegister("explicit_rstb_acquire", 0);
  m_daq_link->setRegister("explicit_rstb_acquire", 1);
  m_daq_link->setGlobalRegister( "interrupt_enable", 0x0);
}

