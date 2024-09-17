#include "MarsData.h"

MarsData::MarsData( uint16_t chip, uint16_t half,
		    MARS_DATA_TYPE dtype, 
		    std::vector<float>::const_iterator mean_begin, std::vector<float>::const_iterator mean_end, 
		    std::vector<float>::const_iterator std_begin, std::vector<float>::const_iterator std_end )
{
  m_chip = chip;
  m_half = half;
  m_dtype = dtype;
  m_mean.reserve(NUMBER_OF_MARS_CHANNELS);
  m_std.reserve(NUMBER_OF_MARS_CHANNELS);
  std::copy(mean_begin, mean_end, std::back_inserter( m_mean ) );
  std::copy(std_begin, std_end, std::back_inserter( m_std ) );
}


std::ostream& operator<<(std::ostream& out,const MarsData& data)
{

  static std::unordered_map<MARS_DATA_TYPE,std::string> const table = { {MARS_DATA_TYPE::ADC,"ADC"},
									{MARS_DATA_TYPE::TOA,"TOA"},
									{MARS_DATA_TYPE::TOT,"TOT"},
									{MARS_DATA_TYPE::TDC,"TDC"} };
										      
  out << "chip = " << data.m_chip  << "\t" 
      << "half = " << data.m_half  << "\t" 
      << "type = " << table.find(data.m_dtype)->second << std::endl;

  std::string text1("Averages : \n");
  std::string text2("Standard dev : \n");
  if( data.m_dtype==MARS_DATA_TYPE::TDC ){
    text1 = std::string("ToA efficiency : \n");
    text2 = std::string("ToT efficiency : \n");
  }
  out << text1;
  std::for_each(data.m_mean.begin(), data.m_mean.end(), [&](auto &d){out << std::dec << d << "  ";} );
  out << "\n";
  out << text2;
  std::for_each(data.m_std.begin(), data.m_std.end(), [&](auto &d){out << std::dec << d << "  ";} );
  out << "\n";
  return out;
}
