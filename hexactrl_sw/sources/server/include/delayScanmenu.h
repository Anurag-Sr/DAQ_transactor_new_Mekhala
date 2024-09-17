#ifndef DELAYSCANMENU
#define DELAYSCANMENU 1

#include <yaml-cpp/yaml.h>

#include "daqmenu.h"
#include "HGCROCv2RawData.h"
#include "FastControlManager.h"
#include "LinkCaptureBlockHandler.h"
#include <link_aligner_data.h>

typedef std::shared_ptr<link_aligner_data> DELAYSCAN_DATAPTR;

class delayScanmenu : public daqmenu{
public:
  delayScanmenu(std::string name) : daqmenu(name) {;}
  ~delayScanmenu(){;}

protected:
  void on_configure(const YAML::Node& config) override;
  
  void on_runthread() override;
  
  void on_sendStartRun() override;

private:
  void configurelinks();
  void configurefc();
  void acquire();
  void acquire_link(LinkCaptureBlockHandler lchandler, std::string linkname);
  
private:
  uint32_t m_maxDelay; // maximum IDELAYE3 value
  uint32_t m_delayStep; // IDELAYE3 step value
  uint32_t m_idlePattern; //Idle pattern (0XACCCCCCC by default, but can be modified with I2C) 
  uint32_t m_acquireLength; // number of (idle) words acquired 
};

#endif
