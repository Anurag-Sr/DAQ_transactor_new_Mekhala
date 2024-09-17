#ifndef BX_OR_L1A_OFFSETFINDER
#define BX_OR_L1A_OFFSETFINDER 1

#include <map>
#include <uhal/uhal.hpp>
#include <yaml-cpp/yaml.h>

#include <FastControlManager.h>
#include <LinkCaptureBlockHandler.h>

class BX_or_L1A_OffsetFinder
{
public:
  BX_or_L1A_OffsetFinder(uhal::HwInterface* uhalHW, FastControlManager* fcman);
  ~BX_or_L1A_OffsetFinder(){;}
  
  bool configureLatencyAndOffset(const YAML::Node& config);
  
  void setLinkHandler(LinkCaptureBlockHandler handler){m_lchandler = handler;}
private:
  bool FindAndSetOffset();
  
private:
  uhal::HwInterface* m_uhalHW;
  FastControlManager* m_fcMan;
  
  LinkCaptureBlockHandler m_lchandler;

};

#endif

