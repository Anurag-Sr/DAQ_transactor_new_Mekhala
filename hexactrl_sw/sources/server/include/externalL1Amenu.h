#ifndef EXTERNALL1AMENU
#define EXTERNALL1AMENU 1

#include <yaml-cpp/yaml.h>

#include "randomL1AplusTPGmenu.h"
#include "HGCROCv2RawData.h"
#include "FastControlManager.h"
#include "SelfTriggerBlockManager.h"
#include "LinkCaptureBlockHandler.h"

/*DAQ menu with external L1A, can be used with loop back option  (using CALPULEXT of FastControl periodic generator)*/
class externalL1Amenu : public randomL1AplusTPGmenu{
public:
  externalL1Amenu(std::string name) : randomL1AplusTPGmenu(name) {;}
  ~externalL1Amenu(){;}

protected:
  void on_configure(const YAML::Node& config) override;
  
  void on_runthread() override;
  
  void on_sendStartRun() override;

  void configurelinks() override;

  void configurefc() override;

  void init_linkdatavec() override;

  void acquire() override;

private:
  bool m_loopBack;  //option to set to enable the loop back
  int m_bxExtCalib; // bx of calib pulse
  int m_lengthCalib; // length (in BX unit) of calib pulse
  int m_prescale; // prescale to slow down the daq (only one param as 2nd periodic gen will follow the 1st gen)
  uint32_t m_trgphase_fifo_latency;

  int m_fulltrgphasereadoutsize; // size of the fifo block being read at each readout 

  std::vector<uint32_t> m_triglatency_data;
  std::unique_ptr<SelfTriggerBlockManager> m_selftrig;
};

#endif
