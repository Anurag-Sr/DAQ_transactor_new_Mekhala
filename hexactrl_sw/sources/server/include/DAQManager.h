#ifndef DAQMANAGER
#define DAQMANAGER 1

#include <iostream>
#include <memory>
#include <yaml-cpp/yaml.h>

#include <daqfsm.h>
#include <daqmenufactory.h>
#include <zmq-helper.h>

#include <LinkCaptureBlockHandler.h>
#include <FastControlManager.h>

enum class LinkStatusFlag{ NOT_READY, ALIGNED, READY };

class DAQManager{

 public:
  /**
     Create the DAQManager object, initialize zmq context and REP socket and then start the listen thread
     \param port is used to initialize the ZMQ REP socket
     \param connectionfile points to connection xml file used to initialize uhal::ConnectionManager instance
  */
  DAQManager(int port, std::string connectionfile);

  /**
     Close zmq socket and context
  */
  ~DAQManager();

  /**
     Initialize the zmq pusher object, the uhal device, the LinkCaptureHandler, FastControl objects
     \param config contains configurations for LinkCaptureHandler + configurations for DAQ menus 
  */
  void initialize( YAML::Node& config );
  
  /**
     \param config contains configurations to decide which DAQ menu will be used + configuration params for the active menu (if needed)
  */
  void configure( YAML::Node& config );

  /**
     Start the active DAQ menu
  */
  void start();

  /**
     Stop the active DAQ menu
  */
  void stop();
 
  /**
     Stop the menu, close the zmq pusher, destroy uhal, LinkCaptureHandler, FastControler objects  .
  */
  void destroy();

  /**
     launch destroy method and switch m_quit to true
  */
  void quit();

 private:
  /**
     Start infinite loop, listening to command through zmq socket
  */
  void listen();
  
  /**
     send the FSM status as string with the zmq socket
  */
  void sendStatus();

  /**
     zmq socket receives command as str
  */
  std::string receiveCommand();

  /**
     zmq socket receives configuration as YAML::Node 
  */
  YAML::Node receiveConfig();

  /**
     init LinkCaptureBlockHandler instance (daq,trg,trg_phase) and fill the linkmap
  */
  void fillLinkHandlerMap(std::vector<link_description>& linkdesc, std::string name , std::string linkname, std::string bramname);

  /**
     perform link alignment and find and set BXoffset for DAQ links  
  */
  void prepareLinks();

private:
  std::unique_ptr<daqFSM> m_fsm;

  zmq_pusher* m_pusher;
  uhal::HwInterface* m_uhalHW;
  FastControlManager* m_fcMan;

  std::string m_connectionfile;
  YAML::Node m_config;
  // SelfCaptureHandler* m_self;
  // MarsHandler* m_mars;
  
  zmq::context_t m_context;
  zmq::socket_t m_socket;
  boost::thread m_listenthread;
  bool m_quit;
  LinkStatusFlag m_linkFlag;
  
  std::map<std::string,MENU> m_menus;
  MENU m_active_menu;

  std::map<std::string,LinkHandlerPTR> m_linkmap;
};

#endif
