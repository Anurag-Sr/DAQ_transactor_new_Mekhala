#ifndef DAQMANAGER
#define DAQMANAGER 1

#include <iostream>
#include <memory>
#include <yaml-cpp/yaml.h>

#include <daqfsm.h>
#include <zmq-helper.h>
#include <datawriter.h>

class DAQClient{

 public:
  /**
     Create the DAQClient object, initialize zmq context and REP socket and then start the listen thread
     \param port is used to initialize the ZMQ REP socket
     \param connectionfile points to connection xml file used to initialize uhal::ConnectionClient instance
  */
  DAQClient(int port);

  /**
     Close zmq socket and context
  */
  ~DAQClient();

  /**
     Initialize the zmq puller object
  */
  void initialize( YAML::Node& config );
  
  /**
     Configure the name of output files 
  */
  void configure( YAML::Node& config );

  /**
     Set m_fileID to 0 and start the running thread
  */
  void start();

  /**
     Stop the running thread
  */
  void stop();
 
  /**
     Stop the running thread (if needed), close the zmq puller
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
     Running thread (launched by start): infinite loop (until m_stop it set to true) which: 
     - wait for START_RUN flag
     - receive data until END_OF_RUN flag is received; go to 1st bullet after END_OF_RUN flag is received
  */
  void runningThread();

  /**
     initialize the datawriter instance (using m_outputFileName, m_fileID, and data type flag identified in the receiveStartOfRun() method
  */
  void initWriter();

  /**
     receive data from the daq-server and write them to the output data file
  */
  void receiveHGCROCData();
  void receiveDelayScanData();
  void receiveMARSData();
  
private:
  std::unique_ptr<daqFSM> m_fsm;

  zmq_puller* m_puller;
  
  zmq::context_t m_context;
  zmq::socket_t m_socket;
  boost::thread m_listenthread;
  boost::thread m_runningthread;
  bool m_quit;
  std::string m_outputFileName;
  uint32_t m_fileID;
  std::unique_ptr<Writer> m_writer;
};

#endif
