#include "zmq-helper.h"

zmq_pusher::zmq_pusher(  zmq::context_t& context ) : oss( std::ios::binary )
{
  m_pusher = zmq::socket_t(context,ZMQ_PUSH);
}

zmq_pusher::~zmq_pusher()
{
  unbind();
  m_pusher.close();
}

bool zmq_pusher::bind(int port)
{
  try{
    std::ostringstream os(std::ostringstream::ate);
    os.str("");
    os << "tcp://*:" << port;
    m_pusher.bind(os.str().c_str());
    sleep(0.1);
  }
  catch(...){
    return false;
  }
  return true;
}

void zmq_pusher::unbind()
{
  try{
    auto last_endpoint = m_pusher.get(zmq::sockopt::last_endpoint);
    if(!last_endpoint.empty()){
      std::cout << "pusher last_endpoint = " << std::string(last_endpoint) << "  ...  ";
      m_pusher.unbind(last_endpoint);
      std::cout << "unbind fine " << std::endl;
      sleep(0.1);
    }
  }
  catch(...)
    {}
}

void zmq_pusher::sendStartOfRun(DataType t)
{
  std::string typestr;
  switch(t){
  case DataType::UNDEFINED : typestr=std::string("UNKNOWN");    break;
  case DataType::HGCROC    : typestr=std::string("HGCROC");     break;
  case DataType::MARS      : typestr=std::string("MARS");       break;
  case DataType::DELAY_SCAN: typestr=std::string("DELAY_SCAN"); break;
  }
  std::ostringstream oss( std::ostringstream::ate );
  oss.str("");
  oss << "START_RUN_" << typestr;
  zmq::message_t message(oss.str().size());
  memcpy(message.data(), oss.str().c_str(), oss.str().size());
  m_pusher.send(message,zmq::send_flags::none);
}

void zmq_pusher::sendEndOfRun()
{
  std::string _str("END_OF_RUN");
  zmq::message_t message(_str.size());
  memcpy(message.data(), _str.c_str(), _str.size());
  m_pusher.send(message,zmq::send_flags::none);
}

zmq_puller::zmq_puller(zmq::context_t &context)
{
  m_puller = zmq::socket_t(context,ZMQ_PULL);
  m_datatype = DataType::UNDEFINED;
  m_datatypemap = std::unordered_map<std::string,DataType> {
							    {"START_RUN_HGCROC",     DataType::HGCROC },
							    {"START_RUN_MARS",       DataType::MARS   },
							    {"START_RUN_DELAY_SCAN", DataType::DELAY_SCAN } 
  };
}

zmq_puller::zmq_puller(std::string url)
{
  m_context = zmq::context_t(1);
  m_puller = zmq::socket_t(m_context,ZMQ_PULL);
  m_puller.connect(url);  
  m_datatype = DataType::UNDEFINED;

  m_datatypemap = std::unordered_map<std::string,DataType> {
							    {"START_RUN_HGCROC",     DataType::HGCROC },
							    {"START_RUN_MARS",       DataType::MARS   },
							    {"START_RUN_DELAY_SCAN", DataType::DELAY_SCAN } 
  };
}

zmq_puller::~zmq_puller()
{
  m_puller.close();
  m_context.close();
}

void zmq_puller::connect(std::string url)
{
  m_puller.connect(url);  
}

void zmq_puller::disconnect()
{
  try{
    auto last_endpoint = m_puller.get(zmq::sockopt::last_endpoint);
    if(!last_endpoint.empty()){
      std::cout << "puller last_endpoint = " << std::string(last_endpoint) << "  ...  ";
      m_puller.disconnect(last_endpoint);
      std::cout << "disconnect fine " << std::endl;
      sleep(0.1);
    }
  }
  catch(...)
    {}
}

void zmq_puller::closeContext()
{
  m_context.close();
}

void zmq_puller::recvStartOfRun()
{
  m_datatype = DataType::UNDEFINED;
  zmq::message_t message;
  m_puller.recv(message,zmq::recv_flags::dontwait);
  if( message.size()==0 ){
    sleep(0.01);
    return;
  } 
  else{
    std::string start_str( static_cast<char*>(message.data()), message.size() );
    auto it = m_datatypemap.find( start_str );
    if( it!=m_datatypemap.end() )
      m_datatype=it->second;
    else{
      std::cout << "Error : " 
		<< start_str 
		<< " not in dataTypeMap"
		<< std::endl;
    }
  }
}
