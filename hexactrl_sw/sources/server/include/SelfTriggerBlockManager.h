#ifndef SELFTRIGGERBLOCKMANAGER
#define SELFTRIGGERBLOCKMANAGER 1

#include <uhal/uhal.hpp>

class SelfTriggerBlockManager
{
public:
  SelfTriggerBlockManager(uhal::HwInterface* uhalHW){m_uhalHW = uhalHW;}
  ~SelfTriggerBlockManager(){;}

  void setRegister( std::string reg, int val )
  {
    char buf[200];
    sprintf(buf,"%s.%s","self_trigger",reg.c_str());
    m_uhalHW->getNode(buf).write(val);
  }

  const uint32_t getRegister( std::string reg )
  {
    char buf[200];
    sprintf(buf,"%s.%s","self_trigger",reg.c_str());
    uhal::ValWord<uint32_t> val=m_uhalHW->getNode(buf).read();
    m_uhalHW->dispatch();
    return (uint32_t)val;
  }
  
  void configForExternalL1A(){
    setRegister("control.trg_mode",0x3);
    setRegister("control.trg_edge",0x1);
  }

  void start(){ setRegister("control.start",0x1); }

  void stop() { setRegister("control.start",0x0); }

  const uint32_t trigCount() { return getRegister("trig_count"); }

 private:
  uhal::HwInterface* m_uhalHW;
};

#endif

