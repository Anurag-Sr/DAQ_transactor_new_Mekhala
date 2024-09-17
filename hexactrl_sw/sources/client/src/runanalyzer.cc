#include <algorithm>
#include <cstring>
#include <cmath>
#include <iomanip>
#include <numeric>

#include "runanalyzer.h"

runanalyzer::runanalyzer( const std::vector< HGCROCv2RawData >& rocdatavec )
{
  //std::copy( rocdata.begin(), rocdata.end(), std::back_inserter(m_rocdata) );
  for( auto rocdata : rocdatavec ){
    this->add( rocdata );
  }
}

void runanalyzer::add( HGCROCv2RawData rocdata )
{
  std::vector<uint32_t> data(HGCROC_DATA_BUF_SIZE);
  for( auto half=0; half<2; half++ ){
    std::copy(rocdata.data().begin()+HGCROC_DATA_BUF_SIZE*half,
	      rocdata.data().begin()+HGCROC_DATA_BUF_SIZE*(half+1),
	      data.begin()
	      );
    int channel_id;
    uint16_t adc;
    uint16_t toa;
    uint16_t tot;

    int corruption=0;
    uint32_t header = data[0];
    uint32_t head = ( header >> 28) & 0xf;
    uint32_t tail = header & 0xf;
    if( head != 0x5 || tail != 0x5 || (head>>4)&0x1 || (head>>5)&0x1 || (head>>6)&0x1 )
      corruption=1;
    if( head != 0x5 || tail != 0x5 ){
      std::cout << "WARNING : data corruption found in event " <<  rocdata.event() << ". " 
		<< std::hex << std::setw(2) << std::setfill('0') <<  header
		<< " => the head and/or tail of the header packet was not 0x5 -> we skip the event for this half roc" << std::endl;
      // continue;
    }
    else if( (head>>4)&0x1 || (header>>5)&0x1 || (header>>6)&0x1 ){
      std::cout << "WARNING : data corruption found in event " <<  rocdata.event() << ". " 
		<< std::hex << std::setw(2) << std::setfill('0') <<  header
		<< " => Error during hamming decoding (see ROC data sheet p30)" << std::endl;
      // continue;
    }
    for( int ichan=0; ichan<N_READOUT_CHANNELS; ichan++ ){
      int data_idx = ichan+1;
      if( ichan==0 ){
	channel_id = NCHANNELS + NCALIB + half*2 ; //i.e. channels 74 and 76
	adc = ( data[data_idx] >> 10 ) & 0x3ff;
	tot = 0;
	toa = 0;
	m_channels[channel_id].adc.push_back( adc );
	m_channels[channel_id].toa.push_back( toa );
	m_channels[channel_id].tot.push_back( tot );
	m_channels[channel_id].mean_adc += adc;
	m_channels[channel_id].stdd_adc += adc*adc;
	m_channels[channel_id].corruption += corruption;
	channel_id = NCHANNELS + NCALIB + half*2 + 1; //i.e. channels 75 and 77
	adc = data[data_idx] & 0x3ff;
	tot = 0;
	toa = 0;
	m_channels[channel_id].adc.push_back( adc );
	m_channels[channel_id].toa.push_back( toa );
	m_channels[channel_id].tot.push_back( tot );
	m_channels[channel_id].mean_adc += adc;
	m_channels[channel_id].stdd_adc += adc*adc;
	m_channels[channel_id].corruption += corruption;
      }
      else{
	if( ichan<=18 )      channel_id = ichan-1 + half*NCHANNELS_PER_HALF; //i.e. channels 0 to 17 and 36 to 53
	else if( ichan==19 ) channel_id = NCHANNELS + half; //i.e. channels 72 and 73 (calib channels)
	else if( ichan>19 )  channel_id = ichan-2 + half*NCHANNELS_PER_HALF; //i.e. channels 18 to 35 and 54 to 71

	toa = data[data_idx] & 0x3ff;
	tot = ( data[data_idx] >>10 ) & 0x3ff;
	adc = ( data[data_idx] >>20 ) & 0x3ff;
	// decompress TOT : MSB is not data but a flag to know which of the 12 bits of ToT was sent
	if( tot>>0x9==1 )
	  tot = (tot & 0x1ff) << 0x3 ;
	m_channels[channel_id].adc.push_back( adc );
 	m_channels[channel_id].toa.push_back( toa );
	m_channels[channel_id].tot.push_back( tot );
	m_channels[channel_id].corruption += corruption;
	m_channels[channel_id].mean_adc += adc;
	m_channels[channel_id].mean_toa += toa;
	m_channels[channel_id].mean_tot += tot;
	m_channels[channel_id].stdd_adc += adc*adc;
	m_channels[channel_id].stdd_toa += toa*toa;
	m_channels[channel_id].stdd_tot += tot*tot;
      }
    }
  }
}

runsummary runanalyzer::analyze()
{
  runsummary summary;
  
  for( int chan_idx=0; chan_idx<TOTAL_NCHANNEL; chan_idx++ ){
    auto nevent = m_channels[chan_idx].adc.size();
    // std::cout << nevent << std::endl;
    std::sort( m_channels[chan_idx].adc.begin(), m_channels[chan_idx].adc.end() );
    std::sort( m_channels[chan_idx].toa.begin(), m_channels[chan_idx].toa.end() );
    std::sort( m_channels[chan_idx].tot.begin(), m_channels[chan_idx].tot.end() );

    uint16_t adc_median = m_channels[chan_idx].adc[ nevent/2 ];
    uint16_t adc_iqr    = m_channels[chan_idx].adc[ 3*nevent/4 ] - m_channels[chan_idx].adc[ nevent/4 ];
    double adc_mean = double(m_channels[chan_idx].mean_adc)/nevent;
    double adc_stdd = std::sqrt( double(m_channels[chan_idx].stdd_adc)/nevent - adc_mean*adc_mean );

    uint16_t toa_median = m_channels[chan_idx].toa[ nevent/2 ];
    uint16_t toa_iqr    = m_channels[chan_idx].toa[ 3*nevent/4 ] - m_channels[chan_idx].toa[ nevent/4 ];
    double toa_mean = double(m_channels[chan_idx].mean_toa)/nevent;
    double toa_stdd = std::sqrt( double(m_channels[chan_idx].stdd_toa)/nevent - toa_mean*toa_mean );

    uint16_t tot_median = m_channels[chan_idx].tot[ nevent/2 ];
    uint16_t tot_iqr    = m_channels[chan_idx].tot[ 3*nevent/4 ] - m_channels[chan_idx].tot[ nevent/4 ];
    double tot_mean = double(m_channels[chan_idx].mean_tot)/nevent;
    double tot_stdd = std::sqrt( double(m_channels[chan_idx].stdd_tot)/nevent - tot_mean*tot_mean );
    
    auto step = [](double a){return a>0 ? 1.0 : 0.0;};
    auto efficiency_func = [&nevent, &step](double a, double b){return a + step(b)/nevent ; };
    double toa_efficiency = std::accumulate( m_channels[chan_idx].toa.begin(), m_channels[chan_idx].toa.end(), 0.0, efficiency_func);
    double tot_efficiency = std::accumulate( m_channels[chan_idx].tot.begin(), m_channels[chan_idx].tot.end(), 0.0, efficiency_func);
    double toa_efficiency_error = std::sqrt( toa_efficiency*(1-toa_efficiency)/nevent );
    double tot_efficiency_error = std::sqrt( tot_efficiency*(1-tot_efficiency)/nevent );

    double corruption = double(m_channels[chan_idx].corruption)/nevent;

    if( chan_idx<NCHANNELS ){
      summary.set_adc_channel_median( chan_idx, adc_median );
      summary.set_toa_channel_median( chan_idx, toa_median );
      summary.set_tot_channel_median( chan_idx, tot_median );
      summary.set_adc_channel_iqr( chan_idx, adc_iqr );
      summary.set_toa_channel_iqr( chan_idx, toa_iqr );
      summary.set_tot_channel_iqr( chan_idx, tot_iqr );
      summary.set_adc_channel_mean( chan_idx, adc_mean );
      summary.set_toa_channel_mean( chan_idx, toa_mean );
      summary.set_tot_channel_mean( chan_idx, tot_mean );
      summary.set_adc_channel_stdd( chan_idx, adc_stdd );
      summary.set_toa_channel_stdd( chan_idx, toa_stdd );
      summary.set_tot_channel_stdd( chan_idx, tot_stdd );
      summary.set_toa_channel_efficiency( chan_idx, toa_efficiency );
      summary.set_tot_channel_efficiency( chan_idx, tot_efficiency );
      summary.set_toa_channel_efficiency_error( chan_idx, toa_efficiency_error );
      summary.set_tot_channel_efficiency_error( chan_idx, tot_efficiency_error );
      summary.set_corruption_channel_mean( chan_idx, corruption );
    }
    else if( chan_idx<NCHANNELS+NCALIB ){
      auto idx = chan_idx-NCHANNELS; //should be 0 or 1
      summary.set_adc_calib_median( idx, adc_median );
      summary.set_toa_calib_median( idx, toa_median );
      summary.set_tot_calib_median( idx, tot_median );
      summary.set_adc_calib_iqr( idx, adc_iqr );
      summary.set_toa_calib_iqr( idx, toa_iqr );
      summary.set_tot_calib_iqr( idx, tot_iqr );
      summary.set_adc_calib_mean( idx, adc_mean );
      summary.set_toa_calib_mean( idx, toa_mean );
      summary.set_tot_calib_mean( idx, tot_mean );
      summary.set_adc_calib_stdd( idx, adc_stdd );
      summary.set_toa_calib_stdd( idx, toa_stdd );
      summary.set_tot_calib_stdd( idx, tot_stdd );
      summary.set_toa_calib_efficiency( idx, toa_efficiency );
      summary.set_tot_calib_efficiency( idx, tot_efficiency );
      summary.set_toa_calib_efficiency_error( idx, toa_efficiency_error );
      summary.set_tot_calib_efficiency_error( idx, tot_efficiency_error );
      summary.set_corruption_calib_mean( idx, corruption );
    }
    else{
      auto idx = chan_idx-NCHANNELS-NCALIB; //should go from 0 to 3
      summary.set_adc_common_median( idx, adc_median );
      summary.set_toa_common_median( idx, toa_median );
      summary.set_tot_common_median( idx, tot_median );
      summary.set_adc_common_iqr( idx, adc_iqr );
      summary.set_toa_common_iqr( idx, toa_iqr );
      summary.set_tot_common_iqr( idx, tot_iqr );
      summary.set_adc_common_mean( idx, adc_mean );
      summary.set_toa_common_mean( idx, toa_mean );
      summary.set_tot_common_mean( idx, tot_mean );
      summary.set_adc_common_stdd( idx, adc_stdd );
      summary.set_toa_common_stdd( idx, toa_stdd );
      summary.set_tot_common_stdd( idx, tot_stdd );
      summary.set_toa_common_efficiency( idx, toa_efficiency );
      summary.set_tot_common_efficiency( idx, tot_efficiency );
      summary.set_toa_common_efficiency_error( idx, toa_efficiency_error );
      summary.set_tot_common_efficiency_error( idx, tot_efficiency_error );
      summary.set_corruption_common_mean( idx, corruption );
    }
  }

  return summary;
}
