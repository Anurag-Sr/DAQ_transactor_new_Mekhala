#ifndef RANDOML1APLUSTPGMENU
#define RANDOML1APLUSTPGMENU 1

#include <yaml-cpp/yaml.h>

#include "randomL1Amenu.h"
#include "HGCROCv2RawData.h"
#include "FastControlManager.h"
#include "LinkCaptureBlockHandler.h"


/*DAQ menu to use when running with internal injection*/
class randomL1AplusTPGmenu : public randomL1Amenu{
public:
  randomL1AplusTPGmenu(std::string name) : randomL1Amenu(name) {;}
  ~randomL1AplusTPGmenu(){;}

protected:
  void on_configure(const YAML::Node& config) override;
  
  void on_runthread() override;
  
  void on_sendStartRun() override;

  void configurelinks() override;

  void configurefc() override;

  virtual void init_linkdatavec() ;

  void acquire() override;
  
private:
  int m_random_period; // parameter controlling the period
  int m_bxmin; // minimum number of BX between L1As

protected:
  uint32_t m_trg_fifo_latency;
  int m_fulltrgreadoutsize; // size of the fifo block being read at each readout 
  std::vector< std::vector<uint32_t> > m_linkstrig;
};

#endif
