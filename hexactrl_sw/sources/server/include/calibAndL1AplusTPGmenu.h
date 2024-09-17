#ifndef CALIBANDL1APLUSTPGMENU
#define CALIBANDL1APLUSTPGMENU 1

#include <yaml-cpp/yaml.h>

#include "randomL1AplusTPGmenu.h"
#include "HGCROCv2RawData.h"
#include "FastControlManager.h"
#include "LinkCaptureBlockHandler.h"


/*DAQ menu to use when running with internal injection and when reading out trigger sums*/
class calibAndL1AplusTPGmenu : public randomL1AplusTPGmenu{
public:
  calibAndL1AplusTPGmenu(std::string name) : randomL1AplusTPGmenu(name) {;}
  ~calibAndL1AplusTPGmenu(){;}

protected:
  void on_configure(const YAML::Node& config) override;
  
  void on_sendStartRun() override;
  
  void configurefc() override;
  
private:
  int m_bxCalib; // bx of calib pulse
  int m_bxL1A; // bx of L1A
  int m_lengthCalib; // length (in BX unit) of calib pulse
  int m_lengthL1A; // length (int BX unit) of L1A signal
  int m_prescale; // prescale to slow down the daq (only one param as 2nd periodic gen will follow the 1st gen)
};

#endif
