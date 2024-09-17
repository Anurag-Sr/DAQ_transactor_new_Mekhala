#ifndef DAQ_MENU_FACTORY
#define DAQ_MENU_FACTORY 1

#include <boost/function.hpp>
#include <boost/functional/factory.hpp>
#include <boost/bind.hpp>
#include <memory>

#include "daqmenu.h"
#include "dummymenu.h"
#include "delayScanmenu.h"
#include "randomL1Amenu.h"
#include "externalL1Amenu.h"
#include "calibAndL1Amenu.h"
#include "randomL1AplusTPGmenu.h"
#include "calibAndL1AplusTPGmenu.h"
#include "marsRndL1Amenu.h"
#include "marsCalibAndL1Amenu.h"

typedef std::shared_ptr<daqmenu> MENU;

class daqmenufactory
{
 public:
  daqmenufactory(){
    factoryDaqMap["dummy"]       = boost::bind( boost::factory<dummymenu*>(), _1 );
    factoryDaqMap["delayScan"]   = boost::bind( boost::factory<delayScanmenu*>(), _1 );
    factoryDaqMap["randomL1A"]   = boost::bind( boost::factory<randomL1Amenu*>(), _1 );
    factoryDaqMap["externalL1A"] = boost::bind( boost::factory<externalL1Amenu*>(), _1 );
    factoryDaqMap["calibAndL1A"] = boost::bind( boost::factory<calibAndL1Amenu*>(), _1 );
    factoryDaqMap["randomL1AplusTPG"] = boost::bind( boost::factory<randomL1AplusTPGmenu*>(), _1 );
    factoryDaqMap["calibAndL1AplusTPG"] = boost::bind( boost::factory<calibAndL1AplusTPGmenu*>(), _1 );
    factoryDaqMap["marsRndL1A"] = boost::bind( boost::factory<marsRndL1Amenu*>(), _1 );
    factoryDaqMap["marsCalibAndL1A"] = boost::bind( boost::factory<marsCalibAndL1Amenu*>(), _1 );
  }
  ~daqmenufactory(){;}
  
  MENU Create(const std::string& key ) const
  {
    MENU ptr{factoryDaqMap.at(key)(key)};
    return ptr;
  }

 private:
  std::map<std::string, boost::function<daqmenu* (const std::string&)>>  factoryDaqMap;
};

#endif
