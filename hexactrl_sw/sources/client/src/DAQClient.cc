#include <DAQClient.h>

DAQClient::DAQClient(int port)
{
  m_fsm = std::make_unique<daqFSM>();

  m_context = zmq::context_t(1);
  m_socket = zmq::socket_t(m_context,ZMQ_REP);
  std::ostringstream os( std::ostringstream::ate );
  os.str("");
  os << "tcp://0.0.0.0:" << port;
  m_socket.bind(os.str().c_str());
  
  m_puller = new zmq_puller( m_context );

  m_quit = false;

  m_listenthread = boost::thread( boost::bind(&DAQClient::listen,this) );
}

DAQClient::~DAQClient()
{
  delete m_puller;
  m_socket.close();
  m_context.close();
}

void DAQClient::initialize( YAML::Node& config )
{
  m_fsm->initialize();
  std::cout << "INITIALIZE:\n" << config << std::endl;
  
  uint32_t port=8888;
  if( config["zmqPushPull_port"].IsDefined() )
    port = config["zmqPushPull_port"].as<uint32_t>();

  std::string serverIP;
  try{
    serverIP = config["serverIP"].as<std::string>();
  }
  catch(std::exception& e){
    std::cout << "DAQClient initialize error " << e.what() << std::endl;
    m_fsm->error();
  }

  std::ostringstream url(std::ostringstream::ate);
  url.str();
  url << "tcp://" << serverIP << ":" << port;

  m_puller->disconnect();
  m_puller->connect(url.str());
}
  
void DAQClient::configure( YAML::Node& config )
{
  m_fsm->configure();
  std::cout << "CONFIGURE" << std::endl;

  try{
    std::ostringstream os(std::ostringstream::ate);
    os.str("");
    os << config["outputDirectory"].as<std::string>() << "/" << config["run_type"].as<std::string>() ;
    m_outputFileName = os.str();
  }
  catch(std::exception& e){
    std::cout << "DAQClient configure error " << e.what() << std::endl;
    m_fsm->error();    
  }
}

void DAQClient::start()
{
  std::cout << "START " << std::endl;
  m_fsm->start();
  m_runningthread = boost::thread( boost::bind(&DAQClient::runningThread,this) );
}

void DAQClient::stop()
{
  m_fsm->stop();
  m_runningthread.join();
  std::cout << "STOP" << std::endl;
}
 
void DAQClient::destroy()
{
  if(m_fsm->status()=="Running") stop();
  std::cout << "DESTROY" << std::endl;
  m_fsm->destroy();
}

void DAQClient::quit()
{
  destroy();
  m_quit = true;
  m_listenthread.join();
  std::cout << "QUIT" << std::endl;
}

void DAQClient::listen()
{
  const std::unordered_map<std::string,std::function<void()> > actionMap = {
    {"initialize", [&](){ auto cfg = receiveConfig(); initialize( cfg ); }},
    {"configure",  [&](){ auto cfg = receiveConfig(); configure( cfg );  }},
    {"start",      [&](){ start();      }},
    {"stop",       [&](){ stop();       }},
    {"destroy",    [&](){ destroy();    }},
    {"status",     [&](){ ; }}
  };
  while(!m_quit){
    auto cmdstr = receiveCommand();
    if( cmdstr.empty()==true ){
      // if( m_fsm->status()=="Running" && m_active_menu->is_stopped() ) stop();
      boost::this_thread::sleep( boost::posix_time::microseconds(100) );
    }
    else{
      std::transform(cmdstr.begin(), cmdstr.end(), cmdstr.begin(), 
		     [](const char& c){ return std::tolower(c);} );
      auto it = actionMap.find( cmdstr );
      if( it!=actionMap.end() )
	it->second();
      else{
	std::ostringstream os( std::ostringstream::ate );
	os.str(""); os << "Error " << cmdstr << " does not correspond to any entry in the action map";
	if( m_fsm->status()=="Running" ) stop();
	m_fsm->error();
      }
      sendStatus();
    }
  }
}
  
std::string DAQClient::receiveCommand()
{
  zmq::message_t message;
  m_socket.recv(message,zmq::recv_flags::dontwait);
  std::string cmd;
  if( message.size()>0 )
    cmd = std::string(static_cast<char*>(message.data()), message.size());
  return cmd;
}

YAML::Node DAQClient::receiveConfig()
{
  zmq::message_t message;
  m_socket.recv(message,zmq::recv_flags::none);    
  auto configstr = std::string(static_cast<char*>(message.data()), message.size());
  return YAML::Load(configstr)["client"];
}

void DAQClient::sendStatus()
{
  auto status = m_fsm->status();
  std::transform(status.begin(), status.end(), status.begin(), 
		 [](const char& c){ return std::tolower(c);} );
  uint16_t size=status.size();
  zmq::message_t message(size);
  std::memcpy(message.data(), status.c_str(), size);
  m_socket.send(message,zmq::send_flags::none);
}

void DAQClient::runningThread()
{
  m_fileID = 0;
  while( m_fsm->status()=="Running" ){
    m_puller->recvStartOfRun();
    auto dtype = m_puller->dataType();
    if( dtype==DataType::UNDEFINED )
      continue;
    initWriter();
    switch( dtype ){
    default: break;
    case DataType::HGCROC:     receiveHGCROCData();    break;
    case DataType::DELAY_SCAN: receiveDelayScanData(); break;
    case DataType::MARS:       receiveMARSData();      break;
    }
    m_writer->save();
    m_fileID++;
  }
}

void DAQClient::initWriter()
{
  m_writer.reset();
  m_writer = nullptr;

  DataWriterFactory fac;

  std::ostringstream os(std::ostringstream::ate);
  os.str("");
  os << m_outputFileName << m_fileID;
  
  auto dtype=m_puller->dataType();
  switch( dtype ){
  default:
    break;
  case DataType::HGCROC:
    os << ".raw";
    m_writer = fac.Create("raw",os.str());
    std::cout << "\t save raw data in : " << *m_writer << std::endl;
    break;
  case DataType::DELAY_SCAN:
    os << ".root";
    m_writer = fac.Create("delayscan",os.str());
    std::cout << "\t save delay scan data in : " << *m_writer << std::endl;
    break;
  case DataType::MARS:
    os << ".root";
    m_writer = fac.Create("mars",os.str());
    std::cout << "\t save mars root data in : " << *m_writer << std::endl;
    break;
  }
}

void DAQClient::receiveHGCROCData()
{
  std::vector<HGCROCv2RawData> data;
  int valid;
  while(m_fsm->status()=="Running"){
    m_puller->receiveDataVecBuffer(data,valid);
    if(valid==1)
      std::for_each(data.cbegin(),data.cend(),[&data,this](auto& d){this->m_writer->fill(d);});
    else
      break;
  }
}

void DAQClient::receiveDelayScanData()
{
  std::vector<link_aligner_data> data;
  int valid;
  while(m_fsm->status()=="Running"){
    m_puller->receiveDataVecBuffer(data,valid);
    if(valid==1)
      std::for_each(data.cbegin(),data.cend(),[&data,this](auto& d){this->m_writer->fill(d);});
    else
      break;
  }
}

void DAQClient::receiveMARSData()
{
  std::vector<MarsData> data;
  int valid(0);
  while(1){
    m_puller->receiveDataVecBuffer(data,valid);
    if(valid==1)
      std::for_each(data.cbegin(),data.cend(),[&data,this](auto& d){this->m_writer->fill(d);});
    else
      break;
  }
}
