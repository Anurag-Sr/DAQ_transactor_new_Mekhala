#include "runsummary.h"

runsummary::runsummary()
{
  memset( m_adc_channel_medians, 0, sizeof( uint16_t )*NCHANNELS );
  memset( m_adc_calib_medians,   0, sizeof( uint16_t )*NCALIB    );
  memset( m_adc_common_medians,  0, sizeof( uint16_t )*NCOMMON   );
  memset( m_toa_channel_medians, 0, sizeof( uint16_t )*NCHANNELS );
  memset( m_toa_calib_medians,   0, sizeof( uint16_t )*NCALIB    );
  memset( m_toa_common_medians,  0, sizeof( uint16_t )*NCOMMON   );
  memset( m_tot_channel_medians, 0, sizeof( uint16_t )*NCHANNELS );
  memset( m_tot_calib_medians,   0, sizeof( uint16_t )*NCALIB    );
  memset( m_tot_common_medians,  0, sizeof( uint16_t )*NCOMMON   );

  memset( m_adc_channel_iqrs, 0, sizeof( uint16_t )*NCHANNELS );
  memset( m_adc_calib_iqrs,   0, sizeof( uint16_t )*NCALIB    );
  memset( m_adc_common_iqrs,  0, sizeof( uint16_t )*NCOMMON   );
  memset( m_toa_channel_iqrs, 0, sizeof( uint16_t )*NCHANNELS );
  memset( m_toa_calib_iqrs,   0, sizeof( uint16_t )*NCALIB    );
  memset( m_toa_common_iqrs,  0, sizeof( uint16_t )*NCOMMON   );
  memset( m_tot_channel_iqrs, 0, sizeof( uint16_t )*NCHANNELS );
  memset( m_tot_calib_iqrs,   0, sizeof( uint16_t )*NCALIB    );
  memset( m_tot_common_iqrs,  0, sizeof( uint16_t )*NCOMMON   );

  memset( m_adc_channel_means,  0,  sizeof( float )*NCHANNELS );
  memset( m_adc_calib_means,    0,  sizeof( float )*NCALIB    );
  memset( m_adc_common_means,   0,  sizeof( float )*NCOMMON   );
  memset( m_toa_channel_means,  0,  sizeof( float )*NCHANNELS );
  memset( m_toa_calib_means,    0,  sizeof( float )*NCALIB    );
  memset( m_toa_common_means,   0,  sizeof( float )*NCOMMON   );
  memset( m_tot_channel_means,  0,  sizeof( float )*NCHANNELS );
  memset( m_tot_calib_means,    0,  sizeof( float )*NCALIB    );
  memset( m_tot_common_means,   0,  sizeof( float )*NCOMMON   );
  memset( m_corruption_channel, 0,  sizeof( float )*NCHANNELS );
  memset( m_corruption_calib,   0,  sizeof( float )*NCALIB    );
  memset( m_corruption_common,  0,  sizeof( float )*NCOMMON   );

  memset( m_adc_channel_stdds, 0,  sizeof( float )*NCHANNELS );
  memset( m_adc_calib_stdds,   0,  sizeof( float )*NCALIB    );
  memset( m_adc_common_stdds,  0,  sizeof( float )*NCOMMON   );
  memset( m_toa_channel_stdds, 0,  sizeof( float )*NCHANNELS );
  memset( m_toa_calib_stdds,   0,  sizeof( float )*NCALIB    );
  memset( m_toa_common_stdds,  0,  sizeof( float )*NCOMMON   );
  memset( m_tot_channel_stdds, 0,  sizeof( float )*NCHANNELS );
  memset( m_tot_calib_stdds,   0,  sizeof( float )*NCALIB    );
  memset( m_tot_common_stdds,  0,  sizeof( float )*NCOMMON   );

  memset( m_toa_channel_efficiencies, 0,  sizeof( float )*NCHANNELS );
  memset( m_toa_calib_efficiencies,   0,  sizeof( float )*NCALIB    );
  memset( m_toa_common_efficiencies,  0,  sizeof( float )*NCOMMON   );
  memset( m_tot_channel_efficiencies, 0,  sizeof( float )*NCHANNELS );
  memset( m_tot_calib_efficiencies,   0,  sizeof( float )*NCALIB    );
  memset( m_tot_common_efficiencies,  0,  sizeof( float )*NCOMMON   );

  memset( m_toa_channel_efficiency_errors, 0,  sizeof( float )*NCHANNELS );
  memset( m_toa_calib_efficiency_errors,   0,  sizeof( float )*NCALIB    );
  memset( m_toa_common_efficiency_errors,  0,  sizeof( float )*NCOMMON   );
  memset( m_tot_channel_efficiency_errors, 0,  sizeof( float )*NCHANNELS );
  memset( m_tot_calib_efficiency_errors,   0,  sizeof( float )*NCALIB    );
  memset( m_tot_common_efficiency_errors,  0,  sizeof( float )*NCOMMON   );
}

std::ostream& operator<<(std::ostream& out,const runsummary& rs)
{
  for(auto i=0; i<NCHANNELS; i++)
    out << "Channel " << i << " :  "
	<< rs.m_adc_channel_medians[i] << "  " << rs.m_adc_channel_iqrs[i] << "  "
	<< rs.m_toa_channel_medians[i] << "  " << rs.m_toa_channel_iqrs[i] << "  "
	<< rs.m_tot_channel_medians[i] << "  " << rs.m_tot_channel_iqrs[i] << std::endl;

  for(auto i=0; i<NCALIB; i++)
    out << "Calib " << i << " :  "
	<< rs.m_adc_calib_medians[i] << "  " << rs.m_adc_calib_iqrs[i] << "  "
	<< rs.m_toa_calib_medians[i] << "  " << rs.m_toa_calib_iqrs[i] << "  "
	<< rs.m_tot_calib_medians[i] << "  " << rs.m_tot_calib_iqrs[i] << std::endl;

  for(auto i=0; i<NCOMMON; i++)
    out << "Common " << i << " :  "
	<< rs.m_adc_common_medians[i] << "  " << rs.m_adc_common_iqrs[i] << "  "
	<< rs.m_toa_common_medians[i] << "  " << rs.m_toa_common_iqrs[i] << "  "
	<< rs.m_tot_common_medians[i] << "  " << rs.m_tot_common_iqrs[i] << std::endl;

  return out;
}

runsummarytupler::runsummarytupler()
{
  file=NULL;
  tree=NULL;
}

runsummarytupler::runsummarytupler(std::shared_ptr<TFile> afile)
{
  file = afile;
  tfileowner=false;
}

runsummarytupler::runsummarytupler(std::shared_ptr<TFile> afile, const std::map<std::string,int> params) : runsummarytupler(afile)
{
  paramMap = params;
}

runsummarytupler::runsummarytupler(std::shared_ptr<TFile> afile, const YAML::Node node) : runsummarytupler(afile)
{
  if( node["chip_params"].IsDefined() ){
    auto chip_params = node["chip_params"];
    for ( YAML::const_iterator it=chip_params.begin(); it!=chip_params.end(); ++it ){
      auto daughternode = chip_params[ it->first.as<std::string>() ];
      auto key = it->first.as<std::string>();
      switch( daughternode.Type() ){
      case YAML::NodeType::Null: 
	break;
      case YAML::NodeType::Scalar:
	{
	  int val = it->second.as<int>();
	  if( paramMap.find(key)==paramMap.end() )
	    paramMap.insert( std::pair<std::string,int>(key,val) );
	  else
	    std::cout << "\nWARNING : key " << key << " was found at least twice in " << chip_params << "\n" << "only 1st one will be used\n" << std::endl;
	  break;
	}
      case YAML::NodeType::Sequence: 
	{
	  try{
	    auto vec = it->second.as< std::vector<int> >();
	    if( paramVecMap.find(key)==paramVecMap.end() )
	      paramVecMap.insert( std::pair<std::string,std::vector<int> >(key,vec) );
	    else
	      std::cout << "\nWARNING : key " << key << " was found at least twice in " << chip_params << "\n" << "only 1st one will be used\n" << std::endl;
	    break;
	  }
	  catch( std::exception& e ){
	    std::cout << e.what() << " a sequence (vector) in metaData['chip_params'] can not be interpreted as vector<int> -> ok, we don't add this node sequence to the summary root file " << std::endl;
	    break;
	  }
	}			// 
      case YAML::NodeType::Map: 
	break;
      case YAML::NodeType::Undefined: 
	break;
      }
    }
  }
  else
    std::cout << "\nWARNING : incorrect yaml config : chip_params node is missing in \n" 
	      << node << "\n"
	      << "output ntuple will not contain meta data parameters\n"
	      << std::endl;
}

runsummarytupler::runsummarytupler(std::string aname)
{
  file = std::make_shared<TFile>(aname.c_str(), "RECREATE");
  tfileowner=true;
}

runsummarytupler::runsummarytupler(std::string aname, const std::map<std::string,int> params) : runsummarytupler(aname)
{
  paramMap = params;
}

runsummarytupler::runsummarytupler(std::string aname, const YAML::Node node) : runsummarytupler(aname)
{
  auto chip_params = node["chip_params"];
  if( chip_params.Type() != YAML::NodeType::Undefined ){
    for ( YAML::const_iterator it=chip_params.begin(); it!=chip_params.end(); ++it ){
      auto daughternode = chip_params[ it->first.as<std::string>() ];
      auto key = it->first.as<std::string>();
      switch( daughternode.Type() ){
      case YAML::NodeType::Null: 
	break;
      case YAML::NodeType::Scalar:
	{
	  int val = it->second.as<int>();
	  if( paramMap.find(key)==paramMap.end() )
	    paramMap.insert( std::pair<std::string,int>(key,val) );
	  else
	    std::cout << "\nWARNING : key " << key << " was found at least twice in " << chip_params << "\n" << "only 1st one will be used\n" << std::endl;
	  break;
	}
      case YAML::NodeType::Sequence: 
	{
	  auto vec = it->second.as< std::vector<int> >();
	  if( paramVecMap.find(key)==paramVecMap.end() )
	    paramVecMap.insert( std::pair<std::string,std::vector<int> >(key,vec) );
	  else
	    std::cout << "\nWARNING : key " << key << " was found at least twice in " << chip_params << "\n" << "only 1st one will be used\n" << std::endl;
	  break;
	}			// 
      case YAML::NodeType::Map: 
	break;
      case YAML::NodeType::Undefined: 
	break;
      }
    }
  }
  else
    std::cout << "\nWARNING : incorrect yaml config : chip_params node is missing in \n" 
	      << node << "\n"
	      << "output ntuple will not contain meta data parameters\n"
	      << std::endl;
}

runsummarytupler::~runsummarytupler()
{
  if( NULL!=file && tfileowner ){
    file->Write();
    file->Close();
  }
}

void runsummarytupler::init()
{
  if( NULL!=file ){
    auto dir = file->mkdir("runsummary");
    dir->cd();
    tree=new TTree("summary","default run summary ntuple with adc/toa/tot median IQR for all channels");
  }
  else
    std::cout << "ERROR file is still NULL ptr when trying to init runsummarytupler instance (please don't use default constructor or runsummarytupler class)" << std::endl;
}


void runsummarytupler::buildTTree()
{
  if( NULL!=tree ){
    tree->Branch("chip",&chip);
    tree->Branch("channel",&channel);
    tree->Branch("channeltype",&channeltype);
    tree->Branch("corruption",&corruption);
    tree->Branch("adc_median",&adc_median);
    tree->Branch("adc_iqr",&adc_iqr);
    tree->Branch("tot_median",&tot_median);
    tree->Branch("tot_iqr",&tot_iqr);
    tree->Branch("toa_median",&toa_median);
    tree->Branch("toa_iqr",&toa_iqr);
    tree->Branch("adc_mean",&adc_mean);
    tree->Branch("adc_stdd",&adc_stdd);
    tree->Branch("tot_mean",&tot_mean);
    tree->Branch("tot_stdd",&tot_stdd);
    tree->Branch("toa_mean",&toa_mean);
    tree->Branch("toa_stdd",&toa_stdd);
    tree->Branch("tot_efficiency",      &tot_efficiency);
    tree->Branch("tot_efficiency_error",&tot_efficiency_error);
    tree->Branch("toa_efficiency",      &toa_efficiency);
    tree->Branch("toa_efficiency_error",&toa_efficiency_error);
    for( auto it=paramMap.begin(); it!=paramMap.end(); ++it )
      tree->Branch(it->first.c_str(),&it->second);
    for( auto it=paramVecMap.begin(); it!=paramVecMap.end(); ++it )
      tree->Branch(it->first.c_str(),&it->second);
  }
  else
    std::cout << "Code implementation error : tree of runsummary should not be a NULL ptr" << std::endl;
}

void runsummarytupler::fill( std::vector<runsummary>& summaryvec )
{
  int rocindex=0;
  auto fillOneChip = [this,&rocindex](runsummary &summary){
    this->chip=rocindex;
    this->channeltype=0;
    for( int i=0; i<NCHANNELS; i++ ){
      this->channel = i;
      this->adc_median=summary.adc_channel_medians()[i];
      this->toa_median=summary.toa_channel_medians()[i];
      this->tot_median=summary.tot_channel_medians()[i];
      this->adc_iqr=summary.adc_channel_iqrs()[i];
      this->toa_iqr=summary.toa_channel_iqrs()[i];
      this->tot_iqr=summary.tot_channel_iqrs()[i];
      this->adc_mean=summary.adc_channel_means()[i];
      this->toa_mean=summary.toa_channel_means()[i];
      this->tot_mean=summary.tot_channel_means()[i];
      this->adc_stdd=summary.adc_channel_stdds()[i];
      this->toa_stdd=summary.toa_channel_stdds()[i];
      this->tot_stdd=summary.tot_channel_stdds()[i];
      this->toa_efficiency=summary.toa_channel_efficiencies()[i];
      this->tot_efficiency=summary.tot_channel_efficiencies()[i];
      this->toa_efficiency_error=summary.toa_channel_efficiency_errors()[i];
      this->tot_efficiency_error=summary.tot_channel_efficiency_errors()[i];
      this->corruption=summary.corruption_channel_means()[i];
      this->tree->Fill();
    }
    this->channeltype=1;
    for( int i=0; i<NCALIB; i++ ){
      this->channel = i;
      this->adc_median=summary.adc_calib_medians()[i];
      this->toa_median=summary.toa_calib_medians()[i];
      this->tot_median=summary.tot_calib_medians()[i];
      this->adc_iqr=summary.adc_calib_iqrs()[i];
      this->toa_iqr=summary.toa_calib_iqrs()[i];
      this->tot_iqr=summary.tot_calib_iqrs()[i];
      this->adc_mean=summary.adc_calib_means()[i];
      this->toa_mean=summary.toa_calib_means()[i];
      this->tot_mean=summary.tot_calib_means()[i];
      this->adc_stdd=summary.adc_calib_stdds()[i];
      this->toa_stdd=summary.toa_calib_stdds()[i];
      this->tot_stdd=summary.tot_calib_stdds()[i];
      this->toa_efficiency=summary.toa_calib_efficiencies()[i];
      this->tot_efficiency=summary.tot_calib_efficiencies()[i];
      this->toa_efficiency_error=summary.toa_calib_efficiency_errors()[i];
      this->tot_efficiency_error=summary.tot_calib_efficiency_errors()[i];
      this->corruption=summary.corruption_calib_means()[i];
      this->tree->Fill();
    }
    this->channeltype=100;
    for( int i=0; i<NCOMMON; i++ ){
      this->channel = i;
      this->adc_median=summary.adc_common_medians()[i];
      this->toa_median=summary.toa_common_medians()[i];
      this->tot_median=summary.tot_common_medians()[i];
      this->adc_iqr=summary.adc_common_iqrs()[i];
      this->toa_iqr=summary.toa_common_iqrs()[i];
      this->tot_iqr=summary.tot_common_iqrs()[i];
      this->adc_mean=summary.adc_common_means()[i];
      this->toa_mean=summary.toa_common_means()[i];
      this->tot_mean=summary.tot_common_means()[i];
      this->adc_stdd=summary.adc_common_stdds()[i];
      this->toa_stdd=summary.toa_common_stdds()[i];
      this->tot_stdd=summary.tot_common_stdds()[i];
      this->toa_efficiency=summary.toa_common_efficiencies()[i];
      this->tot_efficiency=summary.tot_common_efficiencies()[i];
      this->toa_efficiency_error=summary.toa_common_efficiency_errors()[i];
      this->tot_efficiency_error=summary.tot_common_efficiency_errors()[i];
      this->corruption=summary.corruption_common_means()[i];
      this->tree->Fill();
    }
    rocindex++;
  };

  std::for_each( summaryvec.begin(), summaryvec.end(), fillOneChip );
}
