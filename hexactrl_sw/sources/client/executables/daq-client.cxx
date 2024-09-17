#include <iostream>
#include <fstream>
#include <sstream>

#include <signal.h>

#include <boost/cstdint.hpp>
#include <boost/program_options.hpp>
#include <boost/timer/timer.hpp>

#include "DAQClient.h"

namespace daqClient{
  volatile static bool InterruptSIG = false;

  void interrupt_handler(int _ignored)
  { 
    std::cout << "\nInterrupt" << std::endl;
    InterruptSIG = true; 
  }
};

int main(int argc, char** argv)
{
  int m_clientport;
  try { 
    /** Define and parse the program options 
     */ 
    namespace po = boost::program_options; 
    po::options_description client_options("ZMQ client options"); 
    client_options.add_options()
      ("help,h", "Print help messages")
      ("clientport,p", po::value<int>(&m_clientport)->default_value(6001), "port of the daq client where it listens to commands");
    //connection file as option; uhal device from configuration at initialize time
    po::options_description cmdline_options;
    cmdline_options.add(client_options);

    po::variables_map vm; 
    try { 
      po::store(po::parse_command_line(argc, argv, cmdline_options),  vm); 
      if ( vm.count("help")  ) { 
        std::cout << client_options   << std::endl; 
        return 0; 
      } 
      po::notify(vm);
    }
    catch(po::error& e) { 
      std::cerr << "ERROR: " << e.what() << std::endl << std::endl; 
      std::cerr << client_options << std::endl; 
      return 1; 
    }
  }
  catch(std::exception& e) { 
    std::cerr << "Unhandled Exception reached the top of main: " 
              << e.what() << ", application will now exit" << std::endl; 
    return 2; 
  }   
  
  signal(SIGINT, daqClient::interrupt_handler);
  DAQClient* daq = new DAQClient(m_clientport);
  while(1){
    if(daqClient::InterruptSIG==true){
      daq->quit();
      break;
    }
    boost::this_thread::sleep( boost::posix_time::milliseconds(100) );
  }
  delete daq;
  return 0;
}
