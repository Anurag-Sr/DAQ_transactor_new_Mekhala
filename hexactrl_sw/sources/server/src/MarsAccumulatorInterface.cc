#include <MarsAccumulatorInterface.h>

#include <iostream>
#include <sstream>
#include <cstring>
#include <boost/regex.hpp>
#include <boost/lexical_cast.hpp>

MarsAccumulatorInterface::MarsAccumulatorInterface(uhal::HwInterface* uhalHW)
{
  m_uhalHW = uhalHW;
  m_datavec = std::vector<mars_chan_data>(NUMBER_OF_MARS_CHANNELS) ;
  m_mean = std::vector<float>(NUMBER_OF_MARS_CHANNELS) ;
  m_std  = std::vector<float>(NUMBER_OF_MARS_CHANNELS) ;
}

void MarsAccumulatorInterface::resetMars()
{
  m_uhalHW->getNode("mars.control.reset").write(1);
}

void MarsAccumulatorInterface::startMars()
{
  m_uhalHW->getNode("mars.control.reset").write(0);
}

void MarsAccumulatorInterface::waitUntilDone()
{
  while(1){
    auto done = m_uhalHW->getNode("mars.control.done").read();
    m_uhalHW->dispatch();
    if( done ) break;
    else boost::this_thread::sleep( boost::posix_time::microseconds(100) );
  }
}

void MarsAccumulatorInterface::setDataType(MARS_DATA_TYPE dtype)
{
  m_uhalHW->getNode("mars.control.config.dataType").write( m_typeToInt.find(dtype)->second );
}

void MarsAccumulatorInterface::setMarsTriggerLink(std::string linkname)
{
  boost::regex expr("(link)(\\d+)");
  boost::smatch match;
  boost::regex_search(linkname, match, expr);
  m_uhalHW->getNode("mars.control.config.TriggerLink").write( boost::lexical_cast<int>(match[2]) );
}

void MarsAccumulatorInterface::read_and_fill(std::string link)
{
  int chan=0;
  char buf[200];
  auto marsread = [&](mars_chan_data &mcd){
		sprintf(buf,"%s%s%s%d%s","mars.",link.c_str(),".channel",chan,".sum");
		auto sum = m_uhalHW->getNode(buf).read();
			 
		sprintf(buf,"%s%s%s%d%s","mars.",link.c_str(),".channel",chan,".mult_msb");
		auto msb = m_uhalHW->getNode(buf).read();
		
		sprintf(buf,"%s%s%s%d%s","mars.",link.c_str(),".channel",chan,".mult_lsb");
		auto lsb = m_uhalHW->getNode(buf).read();
		
		m_uhalHW->dispatch();
  
		uint64_t sum2 = ((uint64_t)msb)<<34 | lsb;
		mcd.mean = ((float)sum)/MARS_NUMBER_OF_EVENTS;
		mcd.std  = std::sqrt( (float)(sum2)/MARS_NUMBER_OF_EVENTS-mcd.mean*mcd.mean );
		chan++;
	      };
  std::for_each( m_datavec.begin(), m_datavec.end(), [&](auto& mcd){marsread(mcd); } );
  std::transform( m_datavec.begin(), m_datavec.end(), m_mean.begin(), [&](auto &mcd){ return mcd.mean; } );
  std::transform( m_datavec.begin(), m_datavec.end(), m_std.begin(),  [&](auto &mcd){ return mcd.std;  } );
}

void MarsAccumulatorInterface::read_and_fill_tdc(std::string link)
{
  int chan=0;
  char buf[200];
  auto marsread = [&](mars_chan_data &mcd){
		sprintf(buf,"%s%s%s%d%s","mars.",link.c_str(),".channel",chan,".sum");
		auto toa = m_uhalHW->getNode(buf).read();
			 		
		sprintf(buf,"%s%s%s%d%s","mars.",link.c_str(),".channel",chan,".mult_lsb");
		auto tot = m_uhalHW->getNode(buf).read();
		
		m_uhalHW->dispatch();
  
		mcd.mean = ((float)toa)/MARS_NUMBER_OF_EVENTS;
		mcd.std  = ((float)tot)/MARS_NUMBER_OF_EVENTS;
		chan++;
	      };
  std::for_each( m_datavec.begin(), m_datavec.end(), [&](auto& mcd){marsread(mcd); } );
  std::transform( m_datavec.begin(), m_datavec.end(), m_mean.begin(), [&](auto &mcd){ return mcd.mean; } );
  std::transform( m_datavec.begin(), m_datavec.end(), m_std.begin(),  [&](auto &mcd){ return mcd.std;  } );
}

MarsData MarsAccumulatorInterface::readMars(link_description& link)
{
  auto typeval = m_uhalHW->getNode("mars.control.config.dataType").read();
  m_uhalHW->dispatch();

  if( m_intToType.find(typeval)->second != MARS_DATA_TYPE::TDC )
    read_and_fill(link.name());
  else
    read_and_fill_tdc(link.name());
    
  std::vector<float> meanvec();
  return MarsData(link.chip(), link.half(),
		  m_intToType.find(typeval)->second,
		  m_mean.begin(), m_mean.end(),
		  m_std.begin(),  m_std.end() );
}
