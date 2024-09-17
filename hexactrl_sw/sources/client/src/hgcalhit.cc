#include "hgcalhit.h"

bool operator==(const DetectorId& lhs, const DetectorId& rhs)
{
  return lhs.chip()==rhs.chip() && lhs.half()==rhs.half() && lhs.channel()==rhs.channel();
}

std::ostream& operator<<(std::ostream& out,const Hit& rs)
{
  out << "event = "   << rs.event() << " "
      << "chip = "    << rs.detid().chip() << " "
      << "half = "    << rs.detid().half() << " "
      << "channel = " << rs.detid().channel() << " "
      << "adc = "     << rs.adc() ;
  return out;
}

std::ostream& operator<<(std::ostream& out,const pedData& rs)
{
  out << rs.detid().chip() << " "
      << rs.detid().half() << " "
      << rs.detid().channel() << " "
      << rs.adc() ;
  return out;
}

