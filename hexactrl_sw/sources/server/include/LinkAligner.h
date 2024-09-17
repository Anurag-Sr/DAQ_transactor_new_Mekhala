#ifndef LINK_ALIGNER
#define LINK_ALIGNER 1

#include <uhal/uhal.hpp>
#include <yaml-cpp/yaml.h>
#include <FastControlManager.h>
#include <LinkCaptureBlockHandler.h>
#include <link_aligner_data.h>
#include <zmq-helper.h>

#define MAX_DELAY 512
#define LINK_ALIGNED_COUNT_TGT 128
#define LINK_ERROR_COUNT_TGT 0
#define ALIGN_PATTERN 0xACCCCCCC

class LinkAligner
{
 public:
  LinkAligner(uhal::HwInterface* uhalHWInterface, FastControlManager* fc, int nchip=1);
  ~LinkAligner(){;}

  bool configure(const YAML::Node& config, std::shared_ptr<zmq_pusher>& pusher);
  void align();
  void delayScan(std::string fname);
  void delayScan();
  bool checkLinks();
  void setLinkHandlers(std::vector<LinkCaptureBlockHandler> linkvec){m_link_capture_block_handlers = linkvec;}
 private:
  void alignLinks( LinkCaptureBlockHandler lchandler );
  bool testDelay(LinkCaptureBlockHandler lchanlder, std::string elink_name, int delay);
 protected:
  uhal::HwInterface* m_uhalHW;
  FastControlManager* m_fcMan;
  int m_idelaystep;
  std::shared_ptr<zmq_pusher> m_pusher;

  std::vector<LinkCaptureBlockHandler> m_link_capture_block_handlers;

};

#endif
