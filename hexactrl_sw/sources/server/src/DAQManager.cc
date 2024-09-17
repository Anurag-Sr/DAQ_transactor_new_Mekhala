#include <DAQManager.h>
#include <LinkAligner.h>
#include <BX_or_L1A_OffsetFinder.h>

DAQManager::DAQManager(int port, std::string connectionfile) : m_connectionfile(connectionfile)
{
  m_fsm = std::make_unique<daqFSM>();

  m_context = zmq::context_t(1);
  m_socket = zmq::socket_t(m_context,ZMQ_REP);
  std::ostringstream os( std::ostringstream::ate );
  os.str("");
  os << "tcp://0.0.0.0:" << port;
  m_socket.bind(os.str().c_str());
  
  m_pusher = new zmq_pusher( m_context );

  m_quit = false;

  m_listenthread = boost::thread( boost::bind(&DAQManager::listen,this) );
}

DAQManager::~DAQManager()
{
  // delete uhal interface
  delete m_uhalHW;  
  delete m_fcMan;  
  delete m_pusher;
  m_socket.close();
  m_context.close();
}

void DAQManager::initialize( YAML::Node& config )
{
  m_fsm->initialize();
  std::cout << "INITIALIZE:\n" << config << std::endl;

  m_config = config;
  try{
    //check if we really need ptr for uhal and fcman ??
    if( nullptr==m_uhalHW && nullptr==m_fcMan ){
      std::string devicename = "mylittlememory";
      if( config["uhal_device"].IsDefined() )
	devicename = config["uhal_device"].as< std::string >();
      uhal::ConnectionManager manager( "file://" + m_connectionfile );
      m_uhalHW = new uhal::HwInterface( manager.getDevice(devicename) );
      m_fcMan = new FastControlManager( m_uhalHW );
    }
  }
  catch(std::exception& e){
    std::cerr << e.what() << std::endl; 
    m_fsm->error();
    return;
  }
  
  uint32_t port=8888;
  if( config["zmqPushPull_port"].IsDefined() )
    port = config["zmqPushPull_port"].as<uint32_t>();
  m_pusher->unbind();
  m_pusher->bind(port);

  m_linkmap.clear();
  if( config["elinks_daq"].IsDefined() ){
    auto desc = config["elinks_daq"].as< std::vector<link_description> >();
    fillLinkHandlerMap(desc,"daq","link_capture_daq","bram_daq");
  }
  if( config["elinks_trg"].IsDefined() ){
    auto desc = config["elinks_trg"].as< std::vector<link_description> >();
    fillLinkHandlerMap(desc,"trg","link_capture_trg","bram_trg");
  }
  if( config["elinks_trg_phase"].IsDefined() ){
    auto desc = config["elinks_trg_phase"].as< std::vector<link_description> >();
    fillLinkHandlerMap(desc,"trg_phase","link_capture_selftrig","bram_selftrig");
  }
  
  m_menus.clear();
  daqmenufactory fac;
  auto daqmenus = config["menus"];
  for(auto it=daqmenus.begin(); it!=daqmenus.end(); ++it){
    auto name = it->first.as<std::string>();
    auto menu = fac.Create(name);
    menu->setUhalInterface(m_uhalHW);
    menu->setFastControlManager(m_fcMan);
    menu->setLinkHandlers(m_linkmap);
    menu->configure(it->second,m_pusher);
    m_menus.insert( std::pair<std::string,MENU>( name,menu ) );
  }

  m_linkFlag = LinkStatusFlag::NOT_READY;
}
  
void DAQManager::configure( YAML::Node& config )
{
  m_active_menu = nullptr;
  //if previous actuve_menu was a delay scan -> reset link flag to NOT_READY
  m_fsm->configure();
  std::cout << "CONFIGURE" << std::endl;
  auto active_it = m_menus.find( config["active_menu"].as<std::string>() );
  if( active_it!=m_menus.end() ){
    m_active_menu = m_menus[ active_it->first ];
    m_active_menu->configure( config["menus"][active_it->first],nullptr );
    // should update m_config with config for active menu 
  }
  //need to log that active menu does not exist
}

void DAQManager::start()
{
  //if active=nullptr -> error 
  std::cout << "START " << m_active_menu->name() << " menu" << std::endl;
  if( m_linkFlag != LinkStatusFlag::READY && m_active_menu->name()!="delayScan" )
    prepareLinks();
  else m_linkFlag = LinkStatusFlag::READY;
  if( m_linkFlag == LinkStatusFlag::READY ){
    m_active_menu->start();
    m_fsm->start();
  }
}

void DAQManager::stop()
{
  m_fsm->stop();
  std::cout << "STOP" << std::endl;
  m_active_menu->stop();
  if( m_active_menu->name()=="delayScan" ) m_linkFlag = LinkStatusFlag::NOT_READY;
}
 
void DAQManager::destroy()
{
  if(m_fsm->status()=="Running") stop();
  std::cout << "DESTROY" << std::endl;
  m_fsm->destroy();
  delete m_uhalHW; m_uhalHW = nullptr;
  delete m_fcMan; m_fcMan = nullptr;
  //need delete uhal interface here based on config

}

void DAQManager::quit()
{
  destroy();
  m_quit = true;
  m_listenthread.join();
  std::cout << "QUIT" << std::endl;
}

void DAQManager::listen()
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
      if( m_fsm->status()=="Running" && m_active_menu->is_stopped() ) stop();
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
  
std::string DAQManager::receiveCommand()
{
  zmq::message_t message;
  m_socket.recv(message,zmq::recv_flags::dontwait);
  std::string cmd;
  if( message.size()>0 )
    cmd = std::string(static_cast<char*>(message.data()), message.size());
  return cmd;
}

YAML::Node DAQManager::receiveConfig()
{
  zmq::message_t message;
  m_socket.recv(message,zmq::recv_flags::none);    
  auto configstr = std::string(static_cast<char*>(message.data()), message.size());
  return YAML::Load(configstr)["daq"];
}

void DAQManager::sendStatus()
{
  auto status = m_fsm->status();
  std::transform(status.begin(), status.end(), status.begin(), 
		 [](const char& c){ return std::tolower(c);} );
  uint16_t size=status.size();
  zmq::message_t message(size);
  std::memcpy(message.data(), status.c_str(), size);
  m_socket.send(message,zmq::send_flags::none);
}
  
void DAQManager::fillLinkHandlerMap(std::vector<link_description>& linkdesc, std::string name , std::string linkname, std::string bramname)
{
  auto handler = std::make_shared<LinkCaptureBlockHandler>( m_uhalHW, linkname, bramname, linkdesc );
  handler->sortElinks();
  m_linkmap.insert( std::pair<std::string,LinkHandlerPTR>(name,handler) );
}

void DAQManager::prepareLinks()
{
  m_linkFlag = LinkStatusFlag::NOT_READY;
  LinkAligner aligner(m_uhalHW,m_fcMan);
  /*********************************************************************/
  //to be changed for map of shared ptr (need modif in LinkAligner class)
  std::vector<LinkCaptureBlockHandler> linkvec;
  linkvec.push_back( *m_linkmap["daq"] );
  linkvec.push_back( *m_linkmap["trg"] );
  aligner.setLinkHandlers( linkvec );
  /*********************************************************************/
  aligner.align();
  if( !aligner.checkLinks() )
    return;
  else m_linkFlag = LinkStatusFlag::ALIGNED;

  BX_or_L1A_OffsetFinder finder(m_uhalHW, m_fcMan);
  finder.setLinkHandler( *m_linkmap["daq"] );
  if( !finder.configureLatencyAndOffset(m_config) )
    return;
  else m_linkFlag = LinkStatusFlag::READY;
}
