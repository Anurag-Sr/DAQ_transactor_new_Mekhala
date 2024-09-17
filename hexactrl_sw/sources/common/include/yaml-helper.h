#ifndef YAML_HELPER
#define YAML_HELPER 1

#include <yaml-cpp/yaml.h>

enum class L1AGen{ A, B, C, D, AB, CD, E, F, G, H, rand };

class l1a_generator_setting{
public:
  l1a_generator_setting(){;}
  l1a_generator_setting(std::string name, int enable, int BX, int length, int prescale, std::string flavor, std::string followMode ) : 
    _name(name),
    _enable(enable),
    _BX(BX),
    _length(length),
    _prescale(prescale),
    _flavor(flavor),
    _followMode(followMode)
  { ; }
  std::string name()       const { return _name; }
  int enable()             const { return _enable; }
  int BX()                 const { return _BX; }
  int length()             const { return _length; }
  int prescale()           const { return _prescale; }
  std::string flavor()     const { return _flavor; }
  std::string followMode() const { return _followMode; }

  friend struct YAML::convert<l1a_generator_setting>;

private:
  std::string _name;
  int _enable;
  int _BX;
  int _length;
  int _prescale;
  std::string _flavor;
  std::string _followMode;
};

namespace YAML {
  template<>
  struct convert<l1a_generator_setting> {
    static Node encode(const l1a_generator_setting& rhs) {
      Node node;
      node["name"]       = rhs._name;
      node["enable"]     = rhs._enable;
      node["BX"]         = rhs._BX;
      node["length"]     = rhs._length;
      node["prescale"]   = rhs._prescale;
      node["flavor"]     = rhs._flavor;
      node["followMode"] = rhs._followMode;
      return node;
    }
    
    static bool decode(const Node& node, l1a_generator_setting& rhs) {
      if(!node.IsMap() || node.size() != 7) {
      	return false;
      }
      auto amap = node.as< std::map<std::string,std::string> >();
      rhs._name       = amap["name"];
      rhs._flavor     = amap["flavor"];
      rhs._followMode = amap["followMode"];

      std::stringstream sse;
      if( amap["enable"].find("0x")==0 )
        sse << std::hex << amap["enable"];
      else
	sse << amap["enable"];
      sse >> rhs._enable;

      std::stringstream ssb;
      if( amap["BX"].find("0x")==0 )
        ssb << std::hex << amap["BX"];
      else
	ssb << amap["BX"];
      ssb >> rhs._BX;
      
      std::stringstream ssl;
      if( amap["length"].find("0x")==0 )
        ssl << std::hex << amap["length"];
      else
	ssl << amap["length"];
      ssl >> rhs._length;

      std::stringstream ssp;
      if( amap["prescale"].find("0x")==0 )
        ssp << std::hex << amap["prescale"];
      else
	ssp << amap["prescale"];
      ssp >> rhs._prescale;
      return true;
    }
  };
}

#endif
