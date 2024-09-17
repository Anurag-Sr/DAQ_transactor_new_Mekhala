#ifndef RUNSUMMARY
#define RUNSUMMARY 1

#include <iostream>
#include <TFile.h>
#include <TTree.h>

#include <yaml-cpp/yaml.h>

#define NCHANNELS 72
#define NCHANNELS_PER_HALF 36
#define NCALIB 2
#define NCOMMON 4
#define N_READOUT_CHANNELS 38
#define TOTAL_NCHANNEL 78

class runsummary
{
 public:
  runsummary();

  // medians and iqrs //
  
  inline void set_adc_channel_median( int index, uint16_t val ){ m_adc_channel_medians[index] = val; }
  inline void set_adc_calib_median(   int index, uint16_t val ){ m_adc_calib_medians[index]   = val; }
  inline void set_adc_common_median(  int index, uint16_t val ){ m_adc_common_medians[index]  = val; }

  inline uint16_t* adc_channel_medians(){ return m_adc_channel_medians; }
  inline uint16_t* adc_calib_medians()  { return m_adc_calib_medians;   }
  inline uint16_t* adc_common_medians() { return m_adc_common_medians;  }

  inline void set_toa_channel_median( int index, uint16_t val ){ m_toa_channel_medians[index] = val; }
  inline void set_toa_calib_median(   int index, uint16_t val ){ m_toa_calib_medians[index]   = val; }
  inline void set_toa_common_median(  int index, uint16_t val ){ m_toa_common_medians[index]  = val; }

  inline uint16_t* toa_channel_medians(){ return m_toa_channel_medians; }
  inline uint16_t* toa_calib_medians()  { return m_toa_calib_medians;   }
  inline uint16_t* toa_common_medians() { return m_toa_common_medians;  }

  inline void set_tot_channel_median( int index, uint16_t val ){ m_tot_channel_medians[index] = val; }
  inline void set_tot_calib_median(   int index, uint16_t val ){ m_tot_calib_medians[index]   = val; }
  inline void set_tot_common_median(  int index, uint16_t val ){ m_tot_common_medians[index]  = val; }

  inline uint16_t* tot_channel_medians(){ return m_tot_channel_medians; }
  inline uint16_t* tot_calib_medians()  { return m_tot_calib_medians;   }
  inline uint16_t* tot_common_medians() { return m_tot_common_medians;  }

  inline void set_adc_channel_iqr( int index, uint16_t val ){ m_adc_channel_iqrs[index] = val; }
  inline void set_adc_calib_iqr(   int index, uint16_t val ){ m_adc_calib_iqrs[index]   = val; }
  inline void set_adc_common_iqr(  int index, uint16_t val ){ m_adc_common_iqrs[index]  = val; }

  inline uint16_t* adc_channel_iqrs(){ return m_adc_channel_iqrs; }
  inline uint16_t* adc_calib_iqrs()  { return m_adc_calib_iqrs;   }
  inline uint16_t* adc_common_iqrs() { return m_adc_common_iqrs;  }

  inline void set_toa_channel_iqr( int index, uint16_t val ){ m_toa_channel_iqrs[index] = val; }
  inline void set_toa_calib_iqr(   int index, uint16_t val ){ m_toa_calib_iqrs[index]   = val; }
  inline void set_toa_common_iqr(  int index, uint16_t val ){ m_toa_common_iqrs[index]  = val; }

  inline uint16_t* toa_channel_iqrs(){ return m_toa_channel_iqrs; }
  inline uint16_t* toa_calib_iqrs()  { return m_toa_calib_iqrs;   }
  inline uint16_t* toa_common_iqrs() { return m_toa_common_iqrs;  }

  inline void set_tot_channel_iqr( int index, uint16_t val ){ m_tot_channel_iqrs[index] = val; }
  inline void set_tot_calib_iqr(   int index, uint16_t val ){ m_tot_calib_iqrs[index]   = val; }
  inline void set_tot_common_iqr(  int index, uint16_t val ){ m_tot_common_iqrs[index]  = val; }

  inline uint16_t* tot_channel_iqrs(){ return m_tot_channel_iqrs; }
  inline uint16_t* tot_calib_iqrs()  { return m_tot_calib_iqrs;   }
  inline uint16_t* tot_common_iqrs() { return m_tot_common_iqrs;  }

  // means and standard deviations //

  inline void set_adc_channel_mean( int index, float val ){ m_adc_channel_means[index] = val; }
  inline void set_adc_calib_mean(   int index, float val ){ m_adc_calib_means[index]   = val; }
  inline void set_adc_common_mean(  int index, float val ){ m_adc_common_means[index]  = val; }

  inline float* adc_channel_means(){ return m_adc_channel_means; }
  inline float* adc_calib_means()  { return m_adc_calib_means;   }
  inline float* adc_common_means() { return m_adc_common_means;  }

  inline void set_toa_channel_mean( int index, float val ){ m_toa_channel_means[index] = val; }
  inline void set_toa_calib_mean(   int index, float val ){ m_toa_calib_means[index]   = val; }
  inline void set_toa_common_mean(  int index, float val ){ m_toa_common_means[index]  = val; }

  inline float* toa_channel_means(){ return m_toa_channel_means; }
  inline float* toa_calib_means()  { return m_toa_calib_means;   }
  inline float* toa_common_means() { return m_toa_common_means;  }

  inline void set_tot_channel_mean( int index, float val ){ m_tot_channel_means[index] = val; }
  inline void set_tot_calib_mean(   int index, float val ){ m_tot_calib_means[index]   = val; }
  inline void set_tot_common_mean(  int index, float val ){ m_tot_common_means[index]  = val; }

  inline float* tot_channel_means(){ return m_tot_channel_means; }
  inline float* tot_calib_means()  { return m_tot_calib_means;   }
  inline float* tot_common_means() { return m_tot_common_means;  }

  inline void set_corruption_channel_mean( int index, float val ){ m_corruption_channel[index] = val; }
  inline void set_corruption_calib_mean(   int index, float val ){ m_corruption_calib[index]   = val; }
  inline void set_corruption_common_mean(  int index, float val ){ m_corruption_common[index]  = val; }

  inline float* corruption_channel_means(){ return m_corruption_channel; }
  inline float* corruption_calib_means()  { return m_corruption_calib;   }
  inline float* corruption_common_means() { return m_corruption_common;  }

  inline void set_adc_channel_stdd( int index, float val ){ m_adc_channel_stdds[index] = val; }
  inline void set_adc_calib_stdd(   int index, float val ){ m_adc_calib_stdds[index]   = val; }
  inline void set_adc_common_stdd(  int index, float val ){ m_adc_common_stdds[index]  = val; }

  inline float* adc_channel_stdds(){ return m_adc_channel_stdds; }
  inline float* adc_calib_stdds()  { return m_adc_calib_stdds;   }
  inline float* adc_common_stdds() { return m_adc_common_stdds;  }

  inline void set_toa_channel_stdd( int index, float val ){ m_toa_channel_stdds[index] = val; }
  inline void set_toa_calib_stdd(   int index, float val ){ m_toa_calib_stdds[index]   = val; }
  inline void set_toa_common_stdd(  int index, float val ){ m_toa_common_stdds[index]  = val; }

  inline float* toa_channel_stdds(){ return m_toa_channel_stdds; }
  inline float* toa_calib_stdds()  { return m_toa_calib_stdds;   }
  inline float* toa_common_stdds() { return m_toa_common_stdds;  }

  inline void set_tot_channel_stdd( int index, float val ){ m_tot_channel_stdds[index] = val; }
  inline void set_tot_calib_stdd(   int index, float val ){ m_tot_calib_stdds[index]   = val; }
  inline void set_tot_common_stdd(  int index, float val ){ m_tot_common_stdds[index]  = val; }

  inline float* tot_channel_stdds(){ return m_tot_channel_stdds; }
  inline float* tot_calib_stdds()  { return m_tot_calib_stdds;   }
  inline float* tot_common_stdds() { return m_tot_common_stdds;  }

  inline void set_toa_channel_efficiency( int index, float val ){ m_toa_channel_efficiencies[index] = val; }
  inline void set_toa_calib_efficiency(   int index, float val ){ m_toa_calib_efficiencies[index]   = val; }
  inline void set_toa_common_efficiency(  int index, float val ){ m_toa_common_efficiencies[index]  = val; }

  inline float* toa_channel_efficiencies(){ return m_toa_channel_efficiencies; }
  inline float* toa_calib_efficiencies()  { return m_toa_calib_efficiencies;   }
  inline float* toa_common_efficiencies() { return m_toa_common_efficiencies;  }

  inline void set_tot_channel_efficiency( int index, float val ){ m_tot_channel_efficiencies[index] = val; }
  inline void set_tot_calib_efficiency(   int index, float val ){ m_tot_calib_efficiencies[index]   = val; }
  inline void set_tot_common_efficiency(  int index, float val ){ m_tot_common_efficiencies[index]  = val; }

  inline float* tot_channel_efficiencies(){ return m_tot_channel_efficiencies; }
  inline float* tot_calib_efficiencies()  { return m_tot_calib_efficiencies;   }
  inline float* tot_common_efficiencies() { return m_tot_common_efficiencies;  }

  inline void set_toa_channel_efficiency_error( int index, float val ){ m_toa_channel_efficiency_errors[index] = val; }
  inline void set_toa_calib_efficiency_error(   int index, float val ){ m_toa_calib_efficiency_errors[index]   = val; }
  inline void set_toa_common_efficiency_error(  int index, float val ){ m_toa_common_efficiency_errors[index]  = val; }

  inline float* toa_channel_efficiency_errors(){ return m_toa_channel_efficiency_errors; }
  inline float* toa_calib_efficiency_errors()  { return m_toa_calib_efficiency_errors;   }
  inline float* toa_common_efficiency_errors() { return m_toa_common_efficiency_errors;  }

  inline void set_tot_channel_efficiency_error( int index, float val ){ m_tot_channel_efficiency_errors[index] = val; }
  inline void set_tot_calib_efficiency_error(   int index, float val ){ m_tot_calib_efficiency_errors[index]   = val; }
  inline void set_tot_common_efficiency_error(  int index, float val ){ m_tot_common_efficiency_errors[index]  = val; }

  inline float* tot_channel_efficiency_errors(){ return m_tot_channel_efficiency_errors; }
  inline float* tot_calib_efficiency_errors()  { return m_tot_calib_efficiency_errors;   }
  inline float* tot_common_efficiency_errors() { return m_tot_common_efficiency_errors;  }

  friend std::ostream& operator<<(std::ostream& out,const runsummary& rs);
 private:
  uint16_t m_adc_channel_medians[ NCHANNELS ];
  uint16_t m_adc_calib_medians[ NCALIB ];
  uint16_t m_adc_common_medians[ NCOMMON ];
  uint16_t m_toa_channel_medians[ NCHANNELS ];
  uint16_t m_toa_calib_medians[ NCALIB ];
  uint16_t m_toa_common_medians[ NCOMMON ];
  uint16_t m_tot_channel_medians[ NCHANNELS ];
  uint16_t m_tot_calib_medians[ NCALIB ];
  uint16_t m_tot_common_medians[ NCOMMON ];

  uint16_t m_adc_channel_iqrs[ NCHANNELS ];
  uint16_t m_adc_calib_iqrs[ NCALIB ];
  uint16_t m_adc_common_iqrs[ NCOMMON ];
  uint16_t m_toa_channel_iqrs[ NCHANNELS ];
  uint16_t m_toa_calib_iqrs[ NCALIB ];
  uint16_t m_toa_common_iqrs[ NCOMMON ];
  uint16_t m_tot_channel_iqrs[ NCHANNELS ];
  uint16_t m_tot_calib_iqrs[ NCALIB ];
  uint16_t m_tot_common_iqrs[ NCOMMON ];

  float m_adc_channel_means[ NCHANNELS ];
  float m_adc_calib_means[ NCALIB ];
  float m_adc_common_means[ NCOMMON ];
  float m_toa_channel_means[ NCHANNELS ];
  float m_toa_calib_means[ NCALIB ];
  float m_toa_common_means[ NCOMMON ];
  float m_tot_channel_means[ NCHANNELS ];
  float m_tot_calib_means[ NCALIB ];
  float m_tot_common_means[ NCOMMON ];

  float m_corruption_channel[ NCHANNELS ];
  float m_corruption_calib[ NCALIB ];
  float m_corruption_common[ NCOMMON ];

  float m_adc_channel_stdds[ NCHANNELS ];
  float m_adc_calib_stdds[ NCALIB ];
  float m_adc_common_stdds[ NCOMMON ];
  float m_toa_channel_stdds[ NCHANNELS ];
  float m_toa_calib_stdds[ NCALIB ];
  float m_toa_common_stdds[ NCOMMON ];
  float m_tot_channel_stdds[ NCHANNELS ];
  float m_tot_calib_stdds[ NCALIB ];
  float m_tot_common_stdds[ NCOMMON ];

  float m_toa_channel_efficiencies[ NCHANNELS ];
  float m_toa_calib_efficiencies[ NCALIB ];
  float m_toa_common_efficiencies[ NCOMMON ];
  float m_tot_channel_efficiencies[ NCHANNELS ];
  float m_tot_calib_efficiencies[ NCALIB ];
  float m_tot_common_efficiencies[ NCOMMON ];

  float m_toa_channel_efficiency_errors[ NCHANNELS ];
  float m_toa_calib_efficiency_errors[ NCALIB ];
  float m_toa_common_efficiency_errors[ NCOMMON ];
  float m_tot_channel_efficiency_errors[ NCHANNELS ];
  float m_tot_calib_efficiency_errors[ NCALIB ];
  float m_tot_common_efficiency_errors[ NCOMMON ];
};

class runsummarytupler
{
 public:
  runsummarytupler();
  runsummarytupler(std::shared_ptr<TFile> afile);
  runsummarytupler(std::shared_ptr<TFile> afile, const std::map<std::string,int> params);
  runsummarytupler(std::shared_ptr<TFile> afile, const YAML::Node node);
  runsummarytupler(std::string aname);
  runsummarytupler(std::string aname, const std::map<std::string,int> params);
  runsummarytupler(std::string aname, const YAML::Node node);
  
  virtual ~runsummarytupler();
  
  virtual void init();

  virtual void buildTTree();

  void fill(std::vector<runsummary>& summary);

  /* virtual void setExtraBranch(){;} */

 protected:
  std::shared_ptr<TFile> file;
  TTree* tree;
  bool tfileowner;

  uint32_t chip;
  uint16_t channel;
  uint16_t channeltype; //0 standard channels, 1 calib channels, 100 common mode channels
  uint16_t adc_median;
  uint16_t adc_iqr;
  uint16_t tot_median;
  uint16_t tot_iqr;
  uint16_t toa_median;
  uint16_t toa_iqr;
  
  float adc_mean;
  float adc_stdd;
  float tot_mean;
  float tot_stdd;
  float tot_efficiency;
  float tot_efficiency_error;
  float toa_mean;
  float toa_stdd;
  float toa_efficiency;
  float toa_efficiency_error;

  float corruption;

  std::map<std::string,int> paramMap;
  std::map<std::string,std::vector<int> > paramVecMap;
};

#endif
