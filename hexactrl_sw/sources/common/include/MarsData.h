#ifndef MARSDATA
#define MARSDATA 1

#include <iostream>
#include <deque>
#include <cmath>
#include <unordered_map>

#include <boost/archive/binary_oarchive.hpp>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/serialization/vector.hpp>

#include <yaml-cpp/yaml.h>

#define MARS_NUMBER_OF_EVENTS 1024
#define SUMSQUARE_MSB_MASK 0xC0000000
#define SUM_MASK 0x3FFFF
#define NUMBER_OF_MARS_CHANNELS 39

enum class ChannelType{CH,CM,CALIB};
enum class MARS_DATA_TYPE{ ADC, TOT, TOA, TDC };
// In case the TDC mode is used, m_mean contains efficiency vector for ToA and m_std the efficiency vector for ToT

typedef std::vector<MARS_DATA_TYPE> MARS_DATA_TYPE_VEC;

struct EnumClassHash
{
    template <typename T>
    std::size_t operator()(T t) const
    {
        return static_cast<std::size_t>(t);
    }
};

struct mars_type_helper{

  std::unordered_map<MARS_DATA_TYPE, std::string> marstype2str = {
								  {MARS_DATA_TYPE::ADC, "ADC"},
								  {MARS_DATA_TYPE::TOA, "TOA"},
								  {MARS_DATA_TYPE::TOT, "TOT"},
								  {MARS_DATA_TYPE::TDC, "TDC"}
  };
  std::unordered_map< std::string, MARS_DATA_TYPE> str2marstype = {
								   {"ADC", MARS_DATA_TYPE::ADC},
								   {"TOA", MARS_DATA_TYPE::TOA},
								   {"TOT", MARS_DATA_TYPE::TOT},
								   {"TDC", MARS_DATA_TYPE::TDC}
  };
};

namespace YAML {
  template<>
  struct convert<MARS_DATA_TYPE> {

    static Node encode(const MARS_DATA_TYPE& mtype) {
      mars_type_helper mth;
      Node node;
      node["marsTypes"] = mth.marstype2str[mtype];
      return node;
    }
    
    static bool decode(const Node& node, MARS_DATA_TYPE& mtype) {
      mars_type_helper mth;
      if(!node.IsScalar()) {
      	return false;
      }
      auto str = node.as<std::string>();
      mtype = mth.str2marstype[str];
      return true;
    }
  };
}

class MarsData
{
 public:
  MarsData(){;}

  MarsData( uint16_t chip, uint16_t half,
	    MARS_DATA_TYPE dtype,
	    std::vector<float>::const_iterator mean_begin, std::vector<float>::const_iterator mean_end,
	    std::vector<float>::const_iterator std_begin, std::vector<float>::const_iterator std_end );
  
  inline int chip() const { return m_chip; }
  inline int half() const { return m_half; }
  inline MARS_DATA_TYPE dataType() const { return m_dtype; }
  const std::vector<float>& means() { return m_mean; }
  const std::vector<float>& stds() { return m_std; }

  friend std::ostream& operator<<(std::ostream& out,const MarsData& data);

 private:
  friend class boost::serialization::access;
  template<class Archive>
    void serialize(Archive & ar, const unsigned int version)
    {
      ar & m_chip;
      ar & m_half;
      ar & m_dtype;
      ar & m_mean;
      ar & m_std;
    }

 private:
  MARS_DATA_TYPE m_dtype;
  std::vector<float> m_mean;
  std::vector<float> m_std;
  uint16_t m_chip;
  uint16_t m_half;
};

#endif
