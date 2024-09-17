#ifndef DAQ_MENU
#define DAQ_MENU 1

#include <yaml-cpp/yaml.h>

#include <boost/thread/thread.hpp>

#include <LinkCaptureBlockHandler.h>
#include <FastControlManager.h>

#include "zmq-helper.h"

class daqmenu{
public:

  daqmenu(std::string name) : m_name(name)
  {;}

  virtual ~daqmenu(){;}
    
  virtual void configure(const YAML::Node& config, zmq_pusher* pusher=nullptr) final
  {
    if( nullptr!=pusher ) m_pusher = pusher;
    on_configure(config);
  }

  virtual void start() final
  {
    boost::lock_guard<boost::mutex> lock{m_mutex};
    m_stop = false;
    on_sendStartRun();
    m_runthread = boost::thread( boost::bind(&daqmenu::runthread,boost::ref(*this)) );
  }
  
  virtual void stop() final
  {
    boost::lock_guard<boost::mutex> lock{m_mutex};
    m_stop = true;
    m_runthread.join();
    m_pusher->sendEndOfRun();
  }

  virtual bool is_stopped() final { return m_stop; }

  virtual void setUhalInterface(uhal::HwInterface* uhalHW) final
  {
    m_uhalHW = uhalHW;
  }

  virtual void setFastControlManager(FastControlManager* fcman) final
  {
    m_fcMan = fcman;
  }

  virtual void setLinkHandlers(std::map<std::string,LinkHandlerPTR>& linkmap) final
  {
    if( linkmap.find("daq")!=linkmap.end() )
      m_daq_link = linkmap["daq"];
    if( linkmap.find("trg")!=linkmap.end() )
      m_trg_link = linkmap["trg"];
    if( linkmap.find("trg_phase")!=linkmap.end() )
      m_trgphase_link = linkmap["trg_phase"];
  }

  std::string name() const
  {
    return m_name;
  }

  friend bool operator==(const daqmenu& A, const daqmenu& B)
  {
    return A.name()==B.name();
  }

protected:

  virtual void runthread() final
  {
    on_runthread();
  }

  virtual void on_configure(const YAML::Node& config) {;}
  
  virtual void on_runthread() {;}
  
  virtual void on_sendStartRun() {;}

protected:
  std::string m_name;
  zmq_pusher* m_pusher;
  boost::mutex m_mutex;
  boost::thread m_runthread;
  bool m_stop;
  uhal::HwInterface* m_uhalHW;
  FastControlManager* m_fcMan;
  LinkHandlerPTR m_daq_link;
  LinkHandlerPTR m_trg_link;
  LinkHandlerPTR m_trgphase_link;
};

#endif
