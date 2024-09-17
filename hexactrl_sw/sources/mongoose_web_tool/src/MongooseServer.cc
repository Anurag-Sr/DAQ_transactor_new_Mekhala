#include "MongooseServer.h"

#include <iostream>
#include <sstream>
#include <cstring>
#include <iomanip>

MgosUhalController::MgosUhalController(uhal::HwInterface* uhalHWInterface)
{
  m_uhalHW = uhalHWInterface;
}


void MgosUhalController::status(Mongoose::Request &request, Mongoose::StreamResponse &response)
{
  for( auto node : m_uhalHW->getNodes() ){
    if( m_uhalHW->getNode(node).getPermission() == 2 ) continue; //i.e. only write permission
    uhal::ValWord< uint32_t > data = m_uhalHW->getNode(node).read();
    m_uhalHW->dispatch();
    response << m_uhalHW->getNode(node).getPath() << "( mask = " << std::hex << std::setfill('0') << std::setw(8) << m_uhalHW->getNode(node).getMask() << ") = " << data << "<br/>" << std::endl;
  }
}

void MgosUhalController::setValues(Mongoose::Request &request, Mongoose::StreamResponse &response)
{
  response << "<form method=\"post\">" << endl;
  for( auto node : m_uhalHW->getNodes() ){
    if( m_uhalHW->getNode(node).getPermission() == 1 ) continue; //i.e. only read permission
    response << m_uhalHW->getNode(node).getPath() << " : <input type=\"text\" name=\"" << m_uhalHW->getNode(node).getPath() << "\" /><br >" << endl;
  }
  response << "<input type=\"submit\" value=\"Send\" />" << endl;
  response << "</form>" << endl;
}

void MgosUhalController::setValuesPost(Mongoose::Request &request, Mongoose::StreamResponse &response)
{
  for( auto node : m_uhalHW->getNodes() ){
    std::string strData = Mongoose::Utils::htmlEntities(request.get(m_uhalHW->getNode(node).getPath(),"")); //the html text is filled only if the write was set in setValues
    if( !strData.empty() ){
      response << m_uhalHW->getNode(node).getPath() << "( mask = " << std::hex << std::setfill('0') << std::setw(8) << m_uhalHW->getNode(node).getMask() << ") = " << strData << "<br/>" << std::endl;
      m_uhalHW->getNode(node).write( (uint32_t)std::stoi(strData) );
    }
  }
  m_uhalHW->dispatch();
}

void MgosUhalController::setup()
{
  using namespace Mongoose; //did not find other solutions
  addRoute("GET","/",MgosUhalController,status);
  addRoute("GET","/status",MgosUhalController,status);
  addRoute("GET","/setvalues",MgosUhalController,setValues);
  addRoute("POST","/setvalues",MgosUhalController,setValuesPost);
}


MongooseServer::MongooseServer(uhal::HwInterface* hw, int port)
{
  m_controller = std::make_shared<MgosUhalController>(hw);
  m_server = std::make_shared<Mongoose::Server>(port);
  m_server->registerController(m_controller.get());
  m_server->setOption("enable_directory_listing", "true");

  m_server->start();
  std::cout << "Started mongoose web server on port " << port 
  	    << "\nAvailable routes :";
  m_controller->dumpRoutes();
}

void MongooseServer::stop()
{
  m_server->stop();
}
