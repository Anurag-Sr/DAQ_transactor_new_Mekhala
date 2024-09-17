#include "marsntupler.h"

marsntupler::marsntupler() :   adc_mean(-1),
			       adc_stdd(-1),
			       tot_mean(-1),
			       tot_stdd(-1),
			       toa_mean(-1),
			       toa_stdd(-1),
			       toa_eff(-1),
			       tot_eff(-1)
{
  file=NULL;
  tree=NULL;
  fileowner=false;
}

marsntupler::marsntupler(std::string filename) : marsntupler()
{
  fileowner=true;
  file=std::make_shared<TFile>(filename.c_str(),"RECREATE");
}

marsntupler::marsntupler(std::shared_ptr<TFile> afile) : marsntupler()
{
  file=afile;
}

marsntupler::marsntupler(std::shared_ptr<TFile> afile, const YAML::Node node) : marsntupler(afile)
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
	  if( m_paramMap.find(key)==m_paramMap.end() )
	    m_paramMap.insert( std::pair<std::string,int>(key,val) );
	  else
	    std::cout << "\nWARNING : key " << key << " was found at least twice in " << chip_params << "\n" << "only 1st one will be used\n" << std::endl;
	  break;
	}
      case YAML::NodeType::Sequence: 
	{
	  try{
	    auto vec = it->second.as< std::vector<int> >();
	    if( m_paramVecMap.find(key)==m_paramVecMap.end() )
	      m_paramVecMap.insert( std::pair<std::string,std::vector<int> >(key,vec) );
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

marsntupler::~marsntupler()
{
  if( NULL!=file && fileowner ){
    file->Write();
    file->Close();
  }
}

void marsntupler::buildTTree()
{
  if( NULL!=file ){
    auto dir = file->mkdir("mars");
    dir->cd();
    tree=new TTree("mars","mars ntuple with adc/toa/tot mean and std for all channels");
    tree->Branch("chip",&chip);
    tree->Branch("channel",&channel);
    tree->Branch("channeltype",&channeltype);
    tree->Branch("adc_mean",&adc_mean);
    tree->Branch("adc_stdd",&adc_stdd);
    tree->Branch("tot_mean",&tot_mean);
    tree->Branch("tot_stdd",&tot_stdd);
    tree->Branch("toa_mean",&toa_mean);
    tree->Branch("toa_stdd",&toa_stdd);
    tree->Branch("tot_efficiency",&tot_eff);
    tree->Branch("toa_efficiency",&toa_eff);
    // tree->Branch("tot_efficiency_error",&tot_efferr);
    // tree->Branch("toa_efficiency_error",&toa_efferr);
    for( auto it=m_paramMap.begin(); it!=m_paramMap.end(); ++it )
      tree->Branch(it->first.c_str(),&it->second);
    for( auto it=m_paramVecMap.begin(); it!=m_paramVecMap.end(); ++it )
      tree->Branch(it->first.c_str(),&it->second);
    
  }
  else
    std::cout << "Code implementation error : tree of runsummary should not be a NULL ptr" << std::endl;
}

void marsntupler::fill( MarsData data )
{
  auto dtype = data.dataType();
  auto chip = data.chip();
  auto half = data.half();

  for( unsigned int ichan=0; ichan<NUMBER_OF_MARS_CHANNELS; ichan++){
    mars_channel_data mcd(chip,half,ichan);
    auto iter = std::find(m_datavec.begin(), m_datavec.end(),mcd);
    if( iter==m_datavec.end() ){
      m_datavec.push_back(mcd);
      iter = std::prev(m_datavec.end());
    }
    switch(dtype){
    case MARS_DATA_TYPE::ADC:
      (*iter).m_adc_mean = data.means()[ichan];
      (*iter).m_adc_std = data.stds()[ichan];
      break;
    case MARS_DATA_TYPE::TOA:
      (*iter).m_toa_mean = data.means()[ichan];
      (*iter).m_toa_std = data.stds()[ichan];
      break;
    case MARS_DATA_TYPE::TOT:
      (*iter).m_tot_mean = data.means()[ichan];
      (*iter).m_tot_std = data.stds()[ichan];
      break;
    case MARS_DATA_TYPE::TDC:
      (*iter).m_toa_eff = data.means()[ichan];
      (*iter).m_tot_eff = data.stds()[ichan];  
      break;
    }
  }
}

void marsntupler::fillTree()
{
  if( NULL!=tree ){
    std::for_each(m_datavec.begin(),m_datavec.end(),[&](auto &mcd)
						    {
						      chip = mcd.m_chip;
						      channel = mcd.m_channel;
						      channeltype = mcd.m_channeltype;
						      adc_mean = mcd.m_adc_mean;
						      adc_stdd = mcd.m_adc_std;
						      tot_mean = mcd.m_tot_mean;
						      tot_stdd = mcd.m_tot_std;
						      toa_mean = mcd.m_toa_mean;
						      toa_stdd = mcd.m_toa_std;
						      toa_eff  = mcd.m_toa_eff;
						      tot_eff  = mcd.m_tot_eff;
						      tree->Fill();
						    });

  }
}
