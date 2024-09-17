#ifndef MARSCALIBANDL1AMENU
#define MARSCALIBANDL1AMENU 1

#include "marsRndL1Amenu.h"

class marsCalibAndL1Amenu : public marsRndL1Amenu{
public:
  marsCalibAndL1Amenu(std::string name) : marsRndL1Amenu(name) {;}
  
protected:
  void on_configure(const YAML::Node& config) override;
  
  void on_sendStartRun() override;

  void configurefc() override;
  
private:
  int m_bxCalib; // bx of calib pulse
  int m_bxL1A; // bx of L1A
  int m_prescale; // prescale to slow down the daq (only one param as 2nd periodic gen will follow the 1st gen)
  int m_repeatOffset; //if set and >0; sequence of calib pulse+L1A will be repeated 4 times in total, with a BX offset of m_repeatOffset

};

#endif
