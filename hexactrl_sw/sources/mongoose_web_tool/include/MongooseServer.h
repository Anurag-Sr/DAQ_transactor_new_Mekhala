#include <mongoose/Server.h>
#include <mongoose/WebController.h>

#include <uhal/uhal.hpp>
//#include <boost/thread/thread.hpp>

class MgosUhalController : public Mongoose::WebController
{
 public:
  MgosUhalController(uhal::HwInterface* uhalHWInterface);
  ~MgosUhalController(){;}
  void status(Mongoose::Request &request, Mongoose::StreamResponse &response);
  void setValues(Mongoose::Request &request, Mongoose::StreamResponse &response);
  void setValuesPost(Mongoose::Request &request, Mongoose::StreamResponse &response);
  void setup();
 protected:
  uhal::HwInterface* m_uhalHW;
};

class MongooseServer{
 public:
  MongooseServer(uhal::HwInterface* hw, int port);
  ~MongooseServer(){;}
  void stop();
 private:
  std::shared_ptr<MgosUhalController> m_controller;
  std::shared_ptr<Mongoose::Server> m_server;
};
