#ifndef ZMQ_HELPER
#define ZMQ_HELPER 1

#include <boost/archive/binary_oarchive.hpp>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/serialization/export.hpp>
#include <boost/serialization/access.hpp>
#include <boost/serialization/vector.hpp>

#include <iostream>
#include <sstream>
#include <unordered_map>
#include <memory>

#include <zmq.hpp>

enum class DataType{ UNDEFINED, HGCROC, MARS, DELAY_SCAN };

class zmq_pusher
{
 public:

  zmq_pusher(){;}

  zmq_pusher(zmq::context_t& context);
  
  ~zmq_pusher();

  bool bind(int port);
  
  void unbind();

  void sendStartOfRun(DataType t);

  void sendEndOfRun();
  
  void resetStream()
  {
    oss.str("");
  }

  template < typename container >
  void sendvec(container const &data, int maxIterator=-1)
    {
      resetStream();
      boost::archive::binary_oarchive oa(oss);
      auto cend = data.cend();
      if( maxIterator>-1 )
	cend=data.cbegin()+maxIterator;
      
      std::for_each(data.cbegin(),cend,[&oa](auto& t){oa<<t;});
      zmq::message_t message(oss.str().size());
      memcpy(message.data(), oss.str().c_str(), oss.str().size());
      m_pusher.send(message,zmq::send_flags::none);
    }
  
  template < typename container >
  void sendvecptr(container const &data, int maxIterator=-1)
    {
      resetStream();
      boost::archive::binary_oarchive oa(oss);
      auto cend = data.cend();
      if( maxIterator>-1 )
  	cend=data.cbegin()+maxIterator;
      std::for_each(data.cbegin(),cend,[&oa](auto& t){oa<<(*t);});
      zmq::message_t message(oss.str().size());
      memcpy(message.data(), oss.str().c_str(), oss.str().size());
      m_pusher.send(message,zmq::send_flags::none);
    }

  template < typename T >
    void send(const T &data)
    {
      oss.seekp(0);
      boost::archive::binary_oarchive oa(oss);
      oa << data ;
      zmq::message_t message(oss.str().size());
      memcpy(message.data(), oss.str().c_str(), oss.str().size());
      m_pusher.send(message,zmq::send_flags::none);
    }

 protected:
  zmq::socket_t m_pusher;
  std::ostringstream oss;
};

class zmq_puller
{
 public:

  zmq_puller(){;}

  zmq_puller(zmq::context_t &context);

  zmq_puller(std::string url);

  ~zmq_puller();

  void connect(std::string url);

  void disconnect();

  void closeContext();
  
  void recvStartOfRun();

  inline DataType dataType() const { return m_datatype; }

  template < typename T >
    void receiveDataBuffer(T &data,int &valid)
    {
      valid=0;
      zmq::message_t message;
      m_puller.recv(message,zmq::recv_flags::none);//maybe dontwait+check size
      std::string dataStr( static_cast<char*>(message.data()), message.size() );
      if( dataStr.compare("END_OF_RUN")==0 ){
	m_datatype = DataType::UNDEFINED;
	std::cout << dataStr << std::endl;
	return;
      }
      else{
	std::istringstream iss(dataStr);
	boost::archive::binary_iarchive ia{iss};
	try{
	  ia >> data;
	  valid=1;
	}
	catch( std::exception& e ){
	  std::cout << e.what() << std::endl;
	}
      }
    }
  
  template < typename T >
    void receiveDataVecBuffer(std::vector<T> &vec,int &valid)
    {
      valid=0;
      vec.clear();
      zmq::message_t message;
      m_puller.recv(message,zmq::recv_flags::none);//maybe dontwait+check size
      std::string dataStr( static_cast<char*>(message.data()), message.size() );
      if( dataStr.compare("END_OF_RUN")==0 ){
	m_datatype = DataType::UNDEFINED;
	std::cout << dataStr << std::endl;
	return;
      }
      else{
	std::istringstream iss(dataStr);
	boost::archive::binary_iarchive ia{iss};
	T data;
	while(1){
	  try{
	    ia >> data;
	    vec.push_back(data);
	    valid=1;
	  }
	  catch( std::exception& e ){
	    break;
	  }
	}
      }
    }

 protected:
  zmq::context_t m_context;
  zmq::socket_t m_puller;
  DataType m_datatype;
  std::unordered_map<std::string,DataType> m_datatypemap; 
};

#endif
