#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <memory>
#include <algorithm>
#include <uhal/uhal.hpp>
#include <iomanip>
#include <signal.h>
#include <boost/cstdint.hpp>
#include <boost/program_options.hpp>

#include "MongooseServer.h"

volatile static bool running = true;

void handle_signal(int sig)
{
  if (running) {
    std::cout << "Exiting..." << std::endl;
    running = false;
  }
}

int main(int argc,char** argv)
{
  std::string m_connectionfile, m_devicename;
  int m_mongooseport;
  int m_uhalLogLevel;
  try { 
    /** Define and parse the program options 
     */ 
    namespace po = boost::program_options; 
    po::options_description generic_options("Generic options"); 
    generic_options.add_options()
      ("help,h", "Print help messages")
      ("connectionfile,f", po::value<std::string>(&m_connectionfile)->default_value("etc/connection.xml"), "name of ipbus connection file")
      ("devicename,d", po::value<std::string>(&m_devicename)->default_value("mylittleboard"), "name of ipbus connection file")
      ("mongooseport,p", po::value<int>(&m_mongooseport)->default_value(9999), "port for the mongoose web server")
      ("uhalLogLevel,L", po::value<int>(&m_uhalLogLevel)->default_value(4), "uhal log level : 0-Disable; 1-Fatal; 2-Error; 3-Warning; 4-Notice; 5-Info; 6-Debug");

    po::options_description cmdline_options;
    cmdline_options.add(generic_options);

    po::variables_map vm; 
    try { 
      po::store(po::parse_command_line(argc, argv, cmdline_options),  vm); 
      if ( vm.count("help")  ) { 
        std::cout << generic_options   << std::endl; 
        return 0; 
      } 
      po::notify(vm);
    }
    catch(po::error& e) { 
      std::cerr << "ERROR: " << e.what() << std::endl << std::endl; 
      std::cerr << generic_options << std::endl; 
      return 1; 
    }
    
    if( vm.count("connectionfile") ) std::cout << "connectionfile = " << m_connectionfile << std::endl;
    if( vm.count("devicename") )     std::cout << "devicename = "     << m_devicename     << std::endl;
    if( vm.count("mongooseport")  )  std::cout << "m_mongooseport = " << m_mongooseport   << std::endl;
    if( vm.count("uhalLogLevel")  )  std::cout << "m_uhalLogLevel = " << m_uhalLogLevel   << std::endl;
    std::cout << std::endl;
  }
  catch(std::exception& e) { 
    std::cerr << "Unhandled Exception reached the top of main: " 
              << e.what() << ", application will now exit" << std::endl; 
    return 2; 
  }   

  switch(m_uhalLogLevel){
  case 0:
    uhal::disableLogging();
    break;
  case 1:
    uhal::setLogLevelTo(uhal::Fatal());
    break;
  case 2:
    uhal::setLogLevelTo(uhal::Error());
    break;
  case 3:
    uhal::setLogLevelTo(uhal::Warning());
    break;
  case 4:
    uhal::setLogLevelTo(uhal::Notice());
    break;
  case 5:
    uhal::setLogLevelTo(uhal::Info());
    break;
  case 6:
    uhal::setLogLevelTo(uhal::Debug());
    break;
  }
  
  signal(SIGINT, handle_signal);
  uhal::ConnectionManager manager( "file://" + m_connectionfile );
  uhal::HwInterface m_ipbushw = manager.getDevice(m_devicename);
  uhal::HwInterface *m_ipbushwptr = &m_ipbushw;
  
  MongooseServer server(m_ipbushwptr,m_mongooseport);
  while (running) {
    sleep(1);
  }
  server.stop();
  return EXIT_SUCCESS;
}

