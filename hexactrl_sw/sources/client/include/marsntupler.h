#ifndef MARSNTUPLER
#define MARSNTUPLER 1

#include <sstream>
#include <cstring>
#include <iostream>
#include <map>
#include <unordered_map>

#include <yaml-cpp/yaml.h>
#include <TFile.h>
#include <TDirectory.h>
#include <TTree.h>

#include "MarsData.h"

#define N_READOUT_CHANNELS 38

struct mars_channel_data{
  mars_channel_data(int chip, int half, int channel) : m_adc_mean(0),
						       m_toa_mean(0),
						       m_tot_mean(0),
						       m_adc_std(0),
						       m_toa_std(0),
						       m_tot_std(0),
						       m_toa_eff(0),
						       m_tot_eff(0)
  {
    m_chip = chip;
    if( channel==0 ) { //CM channel 0 or 2
      m_channel = half*2;
      m_channeltype = 100;
    }
    else if( channel<19 ){//first 18 normal channels -> 0-17 or 36-53
      m_channel = channel-1 + half*36;
      m_channeltype = 0;
    }
    else if( channel==19 ){//calib channel -> 0 or 1
      m_channel = half;
      m_channeltype = 1;
    }
    else if( channel<38 ){//last 18 normal channels -> 18-35 or 54-71
      m_channel = channel-2 + half*36;
      m_channeltype = 0;
    }
    else{//CM channel 1 or 3
      m_channel = 1 + half*2;
      m_channeltype = 100;
    }

    // std::cout << chip << " " << half << " " << channel << "\t"
    // 	      << m_chip << " " << m_channel << " " << m_channeltype 
    // 	      << std::endl;

  }
						       
  int m_chip;
  int m_channel;
  int m_channeltype;
  float m_adc_mean;
  float m_toa_mean;
  float m_tot_mean;
  float m_adc_std;
  float m_toa_std;
  float m_tot_std;
  float m_toa_eff;
  float m_tot_eff;
  friend bool operator==(const mars_channel_data& m0, const mars_channel_data& m1)
  {
    return m0.m_chip==m1.m_chip && m0.m_channel==m1.m_channel && m0.m_channeltype==m1.m_channeltype;
  }

};

class marsntupler
{
 public:
  marsntupler();

  marsntupler(std::string filename);

  marsntupler(std::shared_ptr<TFile> afile);

  marsntupler(std::shared_ptr<TFile> afile, const YAML::Node node);

  ~marsntupler();
  
  void buildTTree();

  void fill( MarsData data );

  void fillTree();

protected:
  std::shared_ptr<TFile> file;
  TTree* tree;
  bool fileowner;

  std::vector<mars_channel_data> m_datavec;

  std::map<std::string,int> m_paramMap;
  std::map<std::string,std::vector<int> > m_paramVecMap;

  int chip;
  int channel;
  int channeltype;
  float adc_mean;
  float adc_stdd;
  float tot_mean;
  float tot_stdd;
  float toa_mean;
  float toa_stdd;
  float toa_eff;
  // float toa_efferr;
  float tot_eff;
  // float tot_efferr;

};

#endif
