#include "LinkCaptureBlockHandler.h"
#include <boost/regex.hpp>
#include <boost/lexical_cast.hpp>

#include <iostream>
#include <algorithm>
#include <stdio.h>

LinkCaptureBlockHandler::LinkCaptureBlockHandler(uhal::HwInterface* uhalHW,
						 std::string link_capture_block_name, 
						 std::string bram_name, 
						 std::vector< link_description> & elinks) : m_uhalHW(uhalHW),
											    m_link_capture_block_name(link_capture_block_name),
											    m_bram_name(bram_name),
											    m_elinks(elinks)
{
  for( auto elink : m_elinks ){
    if(!elink.polarity())
      setRegister(elink.name(),"delay.invert",0x1);
  }
}

void LinkCaptureBlockHandler::sortElinks()
{
  std::sort( m_elinks.begin(), m_elinks.end(), []( const link_description &lda, const link_description &ldb )->bool{ return lda.code() < ldb.code(); } );
}

void LinkCaptureBlockHandler::setRegister(std::string elink,std::string regName, uint32_t value)
{
  char buf[200];
  sprintf(buf,"%s.%s.%s",m_link_capture_block_name.c_str(),elink.c_str(),regName.c_str());
  m_uhalHW->getNode(buf).write(value);
  m_uhalHW->dispatch();
}

void LinkCaptureBlockHandler::setRegister(std::string regName, uint32_t value)
{
  char buf[200];
  for( auto elink : m_elinks ){
    sprintf(buf,"%s.%s.%s",m_link_capture_block_name.c_str(),elink.name().c_str(),regName.c_str());
    m_uhalHW->getNode(buf).write(value);
  }
  m_uhalHW->dispatch();
}

void LinkCaptureBlockHandler::setGlobalContinousAcquire(bool enable)
{
  char buf[200];
  sprintf(buf,"%s.global.continous_acquire",m_link_capture_block_name.c_str());
  uint32_t value = 0;
  if(enable) {
    boost::regex expr("(link)(\\d+)");
    boost::smatch match;
    for( const auto& elink : m_elinks) {
      if( boost::regex_search(elink.name(), match, expr) )
	value |= 1 << boost::lexical_cast<int>(match[2]);
    }
  }
  // printf("Value: %d\n", value);
  m_uhalHW->getNode(buf).write(value);
  m_uhalHW->dispatch();

}

void LinkCaptureBlockHandler::setGlobalRegister(std::string regName, uint32_t value)
{
  char buf[200];
  sprintf(buf,"%s.%s.%s",m_link_capture_block_name.c_str(),"global",regName.c_str());
  m_uhalHW->getNode(buf).write(value);
  m_uhalHW->dispatch();
}

const uint32_t LinkCaptureBlockHandler::getRegister(std::string elink, std::string regName)
{
  char buf[200];
  sprintf(buf,"%s.%s.%s",m_link_capture_block_name.c_str(),elink.c_str(),regName.c_str());
  uhal::ValWord<uint32_t> val=m_uhalHW->getNode(buf).read();
  m_uhalHW->dispatch();
  return (uint32_t)val;
}

const uint32_t LinkCaptureBlockHandler::getRegisterMask(std::string elink, std::string regName)
{
  char buf[200];
  sprintf(buf,"%s.%s.%s",m_link_capture_block_name.c_str(),elink.c_str(),regName.c_str());
  return m_uhalHW->getNode(buf).getMask();
}

const uint32_t LinkCaptureBlockHandler::getGlobalRegister(std::string regName)
{
  char buf[200];
  sprintf(buf,"%s.%s.%s",m_link_capture_block_name.c_str(),"global",regName.c_str());
  uhal::ValWord<uint32_t> val=m_uhalHW->getNode(buf).read();
  m_uhalHW->dispatch();
  return (uint32_t)val;
}

void LinkCaptureBlockHandler::getData(std::string elink, std::vector<uint32_t> &data, uint32_t size)
{
  if( data.size()!=size )
    data = std::vector<uint32_t>(size,0);

  char buf[200];
  sprintf(buf,"%s.%s",m_bram_name.c_str(),elink.c_str());
  uhal::ValVector<uint32_t> vec=m_uhalHW->getNode(buf).readBlock(size);
  m_uhalHW->dispatch();
  std::copy( vec.begin(), vec.end(), data.begin() );
  
  // auto iter = std::find_if( m_elinks.begin(), m_elinks.end(), [&elink](const link_description& ld){return ld.name()==elink;} );
  // auto polarity = (*iter).polarity();
  // if( !polarity )
  //   std::transform( data.begin(), data.end(), data.begin(),
  // 		    [](uint32_t word)->uint32_t{ return word^0xFFFFFFFF; } );
  
}
