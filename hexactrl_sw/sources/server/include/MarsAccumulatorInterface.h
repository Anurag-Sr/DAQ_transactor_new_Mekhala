#ifndef MARSACCUMULATORINTERFACE
#define MARSACCUMULATORINTERFACE 1

#include <unordered_map>

#include <boost/thread/thread.hpp>

#include <uhal/uhal.hpp>

#include "LinkCaptureBlockHandler.h"
#include "MarsData.h"

struct mars_chan_data{
  float mean;
  float std;
};

class MarsAccumulatorInterface
{
public:
  MarsAccumulatorInterface(uhal::HwInterface* uhalHW);
  ~MarsAccumulatorInterface(){;}
  void resetMars();
  void startMars();

  void setDataType(MARS_DATA_TYPE t);
  void setMarsTriggerLink(std::string linkname);
  void waitUntilDone();

  MarsData readMars(link_description& link);
private:
  void read_and_fill(std::string link);
  void read_and_fill_tdc(std::string link);

  uhal::HwInterface* m_uhalHW;
  std::vector<mars_chan_data> m_datavec;
  std::vector<float> m_mean;
  std::vector<float> m_std;

  std::unordered_map<MARS_DATA_TYPE,int> m_typeToInt = { {MARS_DATA_TYPE::ADC,0},
							 {MARS_DATA_TYPE::TOA,1},
							 {MARS_DATA_TYPE::TOT,2},
							 {MARS_DATA_TYPE::TDC,3} };

  std::unordered_map<int,MARS_DATA_TYPE> m_intToType = { {0,MARS_DATA_TYPE::ADC},
							 {1,MARS_DATA_TYPE::TOA},
							 {2,MARS_DATA_TYPE::TOT},
							 {3,MARS_DATA_TYPE::TDC} };
};

#endif

