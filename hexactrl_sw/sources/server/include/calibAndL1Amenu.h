#ifndef CALIBANDL1AMENU
#define CALIBANDL1AMENU 1

#include <yaml-cpp/yaml.h>

#include "randomL1Amenu.h"
#include "HGCROCv2RawData.h"
#include "FastControlManager.h"
#include "LinkCaptureBlockHandler.h"


/*DAQ menu to use when running with internal injection*/
class calibAndL1Amenu : public randomL1Amenu{
public:
  calibAndL1Amenu(std::string name) : randomL1Amenu(name) {;}
  ~calibAndL1Amenu(){;}

protected:
  void init_linkdatavec() override;

  void on_configure(const YAML::Node& config) override;
  
  void on_sendStartRun() override;

  void configurelinks() override;

  void configurefc() override;
  
private:
  int m_bxCalib; // bx of calib pulse
  int m_bxL1A; // bx of L1A
  int m_lengthCalib; // length (in BX unit) of calib pulse
  int m_lengthL1A; // length (int BX unit) of L1A signal
  int m_prescale; // prescale to slow down the daq (only one param as 2nd periodic gen will follow the 1st gen)
  int m_repeatOffset; //if set and >0; sequence of calib pulse+L1A will be repeated 4 times in total, with a BX offset of m_repeatOffset
  FC_channel_flavor m_calibType;
};

#endif
