#ifndef RUNANALYZER
#define RUNANALYZER 1

#include <iostream>
#include <vector>

#include "HGCROCv2RawData.h"
#include "runsummary.h"

class runanalyzer{
 public:
  runanalyzer(){;}
  runanalyzer( const std::vector< HGCROCv2RawData >& rocdatavec );
  ~runanalyzer(){;}
  
  void add( HGCROCv2RawData rocdata );
  runsummary analyze();

 private:
  struct channelsummary{
    channelsummary(){
      mean_adc=0.;
      mean_toa=0.;
      mean_tot=0.;
      stdd_adc=0.;
      stdd_toa=0.;
      stdd_tot=0.;
      corruption=0.;
    }
    std::vector<uint16_t> adc;
    std::vector<uint16_t> toa;
    std::vector<uint16_t> tot;
    double mean_adc;
    double mean_toa;
    double mean_tot;
    double stdd_adc;
    double stdd_toa;
    double stdd_tot;

    double corruption;
  };

  channelsummary m_channels[TOTAL_NCHANNEL];
  /* indexing skim :                                */
  /* channel 0-35  -> standard channels of half 0   */
  /* channel 36-71 -> standard channeld of half 1   */
  /* channel 72    -> calibration channel of half 0 */
  /* channel 73    -> calibration channel of half 1 */
  /* channel 74-75 -> common mode channel of half 0 */
  /* channel 76-77 -> common mode channel of half 1 */
};

#endif
