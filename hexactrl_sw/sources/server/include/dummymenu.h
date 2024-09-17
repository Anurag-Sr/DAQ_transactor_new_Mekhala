#ifndef DUMMYMENU
#define DUMMYMENU 1

// #include <uhal/uhal.hpp> 
#include <yaml-cpp/yaml.h>

#include "HGCROCv2RawData.h"
#include "daqmenu.h"

class dummymenu : public daqmenu{
public:
  dummymenu(std::string name) : daqmenu(name){;}
  ~dummymenu(){;}

protected:
  void on_configure(const YAML::Node& config) override;
  
  void on_runthread() override;
  
  void on_sendStartRun() override;
  
  HGCROCv2RawData createROCData(int event,int chip)
  {
    std::vector<uint32_t> data0(HGCROC_DATA_BUF_SIZE),data1(HGCROC_DATA_BUF_SIZE);
    int index=0;
    std::for_each( data0.begin(), data0.end(), [&index](uint32_t &v){ v=index; index++; } );
    std::for_each( data1.begin(), data1.end(), [&index](uint32_t &v){ v=index; index++; } );
    return HGCROCv2RawData(event,chip,
			   data0.begin(),data0.end(),
			   data1.begin(),data1.end() );
  }
private:
  int m_nevents;
  int m_neventsperpush;
};

#endif
