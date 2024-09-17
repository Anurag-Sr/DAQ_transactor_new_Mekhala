#ifndef RANDOML1AMENU
#define RANDOML1AMENU 1

#include <yaml-cpp/yaml.h>

#include "daqmenu.h"
#include "HGCROCv2RawData.h"
#include "FastControlManager.h"
#include "LinkCaptureBlockHandler.h"

class randomL1Amenu : public daqmenu{
public:
  randomL1Amenu(std::string name) : daqmenu(name) {;}
  ~randomL1Amenu(){;}

protected:

  virtual void init_containers() final;

  void on_configure(const YAML::Node& config) override;
  
  void on_runthread() override;
  
  void on_sendStartRun() override;
  
  virtual void init_linkdatavec();

  virtual void configurelinks();

  virtual void configurefc();

  virtual void acquire();

  virtual void package_and_send(); //this could be handled by another class (which would use the pusher)
  
private:
  int m_random_period; // parameter controlling the period
  int m_bxmin; // minimum number of BX between L1As

protected:
  uint32_t m_nevents; // total (minimum) number of event to acquire
  uint32_t m_event; // current number of event
  int m_fulldaqreadoutsize; // size of the fifo block being read at each readout 

  std::vector< std::vector<uint32_t> > m_linksdata;
  std::vector< std::shared_ptr<HGCROCEventContainer> > m_roceventcontainers;

};

#endif
