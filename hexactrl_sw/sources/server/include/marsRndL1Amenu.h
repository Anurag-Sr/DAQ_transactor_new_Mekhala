#ifndef MARSRNDL1AMENU
#define MARSRNDL1AMENU 1

#include <yaml-cpp/yaml.h>

#include "daqmenu.h"
#include "HGCROCv2RawData.h"
#include "FastControlManager.h"
#include "LinkCaptureBlockHandler.h"
#include "MarsAccumulatorInterface.h"

class marsRndL1Amenu : public daqmenu{
public:
  marsRndL1Amenu(std::string name) : daqmenu(name) {;}
  
protected:
  void on_configure(const YAML::Node& config) override;
  
  void on_runthread() override;
  
  void on_sendStartRun() override;

  virtual void configureMarsTypes(const YAML::Node& config) final;

private:
  virtual void configurelinks();

  virtual void configurefc();

  virtual void acquire();
  
private:
  int m_random_period; // parameter controlling the period
  int m_bxmin; // minimum number of BX between L1As

protected:
  std::shared_ptr<MarsAccumulatorInterface> m_marsptr;
  std::vector<MarsData> m_marsdata;

  MARS_DATA_TYPE_VEC m_marsTypes;
};

#endif
