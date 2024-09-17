#include <iostream>
#include <fstream>
#include <sstream>

#include <algorithm>
#include <iomanip>

#include <boost/cstdint.hpp>
#include <boost/program_options.hpp>
#include <boost/archive/binary_iarchive.hpp>

#include <yaml-cpp/yaml.h>

#include <TFile.h>

#include "datawriter.h"

int main(int argc, char** argv)
{
  
  std::string m_input,m_output,m_pedestal;
  std::string m_metaDataYaml;
  bool m_printArgs = false;
  try { 
    /** Define and parse the program options 
     */ 
    namespace po = boost::program_options; 
    po::options_description generic_options("Generic options"); 
    generic_options.add_options()
      ("help,h", "Print help messages")
      ("input,i",        po::value<std::string>(&m_input), "input raw root file name")
      ("output,o",       po::value<std::string>(&m_output), "output file name")
      ("pedestal,p",     po::value<std::string>(&m_pedestal), "input pedestal root file name")
      ("metaDataYaml,M", po::value<std::string>(&m_metaDataYaml), "yaml (created at the same time as the raw data file) file containing meta data of the run")
      ("printArgs", po::bool_switch(&m_printArgs)->default_value(false), "turn me on to print used arguments");
    
    po::options_description cmdline_options;
    cmdline_options.add(generic_options);
    
    po::variables_map vm; 
    try { 
      po::store(po::parse_command_line(argc, argv, cmdline_options),  vm); 
      if ( vm.count("help")  ) { 
        std::cout << generic_options   << std::endl; 
        return 0; 
      } 
      po::notify(vm);
    }
    catch(po::error& e) { 
      std::cerr << "ERROR: " << e.what() << std::endl << std::endl; 
      std::cerr << generic_options << std::endl; 
      return 1; 
    }

    if( m_output.empty() )
      m_output = m_input;
    if( m_pedestal.empty() )
      m_pedestal = m_input;
    if( m_printArgs ){
      std::cout << "input = "        << m_input        << std::endl;
      std::cout << "output = "       << m_output       << std::endl;
      std::cout << "metaDataYaml = " << m_metaDataYaml << std::endl;
      std::cout << "pedestal = "     << m_pedestal   << std::endl;	
      std::cout << std::endl;
    }
  }
  catch(std::exception& e) { 
    std::cerr << "Unhandled Exception reached the top of main: " 
              << e.what() << ", application will now exit" << std::endl; 
    return 2; 
  }
  
  auto file=std::make_shared<TFile>(m_pedestal.c_str(),"READ");
  if( file->IsOpen() )
    file->Print();
  else
    std::cout << "can not open file " << m_input << std::endl;
  auto dir=(TDirectory*)file->Get("runsummary");
  auto *ped_tree = (TTree*)dir->Get("summary");
  if (!ped_tree){
    std::cout << " -- Error, tree cannot be opened. Exiting..." << std::endl;
    return 0;
  }

  uint32_t ped_chip;
  uint16_t ped_channel;
  uint16_t ped_channeltype; //0 standard channels, 1 calib channels, 100 common mode channels
  uint16_t adc_median;
  ped_tree->SetBranchAddress("chip", &ped_chip);
  ped_tree->SetBranchAddress("channel", &ped_channel);
  ped_tree->SetBranchAddress("channeltype", &ped_channeltype);
  ped_tree->SetBranchAddress("adc_median", &adc_median);

  std::vector<pedData> pedestals;
  for( unsigned int ientry(0); ientry<ped_tree->GetEntries(); ++ientry ){
    ped_tree->GetEntry(ientry);
    pedestals.push_back( pedData(ped_chip,ped_channel,ped_channeltype,adc_median) );
  }
  // for( auto ped : pedestals )
  //   std::cout << ped << std::endl;
  file->Close();
  
  //let's dump the pedestal vec into an array for better performance:
  pedData pedestalArray[ pedestals.size() ];
  std::for_each( pedestals.begin(), pedestals.end(), [&pedestalArray](pedData p){
						       int code = p.detid().chip()*78 + p.detid().half()*39 + p.detid().channel();
						       pedestalArray[code] = p;
						     } );
  
  file.reset(new TFile(m_input.c_str(),"READ"));
  if( file->IsOpen() )
    file->Print();
  else
    std::cout << "can not open file " << m_input << std::endl;
  dir=(TDirectory*)file->Get("unpacker_data");
  auto *raw_tree = (TTree*)dir->Get("hgcroc");
  if (!raw_tree){
    std::cout << " -- Error, tree cannot be opened. Exiting..." << std::endl;
    return 0;
  }
  int event,corruption;
  int chip,half,channel;
  int adc(0),toa(0),tot(0),trigtime(0);

  raw_tree->SetBranchAddress("event", &event);
  raw_tree->SetBranchAddress("corruption", &corruption);
  raw_tree->SetBranchAddress("chip", &chip);
  raw_tree->SetBranchAddress("half", &half);
  raw_tree->SetBranchAddress("channel", &channel);
  raw_tree->SetBranchAddress("adc", &adc);
  raw_tree->SetBranchAddress("toa", &toa);
  raw_tree->SetBranchAddress("tot", &tot);
  raw_tree->SetBranchAddress("trigtime", &trigtime);


  DataWriterFactory fac;
  std::unique_ptr<Writer> writer;
  writer = fac.Create("hgcalhits",m_output);


  std::vector<int> maskedChannelCodes;
  if( !m_metaDataYaml.empty() ){
    YAML::Node config = YAML::LoadFile(m_metaDataYaml.c_str())["metaData"];
    try{
      maskedChannelCodes = config["Channel_off"].as<std::vector<int>>(); // assuming this "Channel_off" node is a vector of channel codes using the same logic as we build the detid : detid = channel (from 0 to 38) + half*39 + chip*78
      // for( auto c: maskedChannelCodes )
      // 	std::cout << c << " , ";
      // std::cout << std::endl;
    }
    catch( std::exception& e ){
    }
  }

  
  int nevent = raw_tree->GetEntries()/pedestals.size();
  std::vector<Hit> hits[nevent];
  for( unsigned int ientry(0); ientry<raw_tree->GetEntries(); ++ientry ){
    raw_tree->GetEntry( ientry );
    auto detid = DetectorId( FromRawData(), chip, half, channel );
    int code = chip*78+half*39+channel;
    // if( event==0 )
    //   std::cout << detid.chip() << " " << detid.half() << " " << detid.channel() << " " << detid.id() << " " << code << " " << pedestalArray[code].adc() << std::endl;
    Hit hit( event, detid, adc-pedestalArray[code].adc(), toa, tot, trigtime );
    hits[event].push_back( hit );
  }

  int nchip = hits[0].size()/78;

  for(int ievt=0; ievt<nevent; ievt++){
    for(int iroc=0; iroc<nchip; iroc++){
      std::vector<Hit> tmp(78);
      auto it = std::copy_if( hits[ievt].begin(), hits[ievt].end(), tmp.begin(),
  			      [iroc,maskedChannelCodes](const Hit& hit){
				return ( hit.detid().chip() == iroc &&
					 hit.detid().channel() < 37 &&
					 hit.detid().channel() !=8  &&
					 hit.detid().channel() !=17 &&
					 hit.detid().channel() !=18 &&
					 hit.detid().channel() !=27 &&
					 std::find(maskedChannelCodes.begin(),maskedChannelCodes.end(),hit.detid().id())==maskedChannelCodes.end() );
			      });
      tmp.resize( std::distance(tmp.begin(),it) );
      std::sort( tmp.begin(), tmp.end(),
  		 [](const Hit& hita, const Hit& hitb)->bool{ return hita.adc() < hitb.adc(); } );
      int median = tmp[tmp.size()/2].adc();

      // auto cm00 = (*std::find_if( hits[ievt].begin(), hits[ievt].end(), [&iroc](const Hit& hit){return hit.detid().id()==iroc*78+37;} ));
      // auto cm01 = (*std::find_if( hits[ievt].begin(), hits[ievt].end(), [&iroc](const Hit& hit){return hit.detid().id()==iroc*78+38;} ));
      // auto cm10 = (*std::find_if( hits[ievt].begin(), hits[ievt].end(), [&iroc](const Hit& hit){return hit.detid().id()==iroc*78+66;} ));
      // auto cm11 = (*std::find_if( hits[ievt].begin(), hits[ievt].end(), [&iroc](const Hit& hit){return hit.detid().id()==iroc*78+67;} ));
      
      std::for_each( hits[ievt].begin(), hits[ievt].end(),
  		     [&writer,median,iroc,maskedChannelCodes/*,&cm00,&cm01,&cm10,&cm11*/](Hit& hit){
  		       if( hit.detid().chip()!=iroc || std::find(maskedChannelCodes.begin(),maskedChannelCodes.end(),hit.detid().id())!=maskedChannelCodes.end())
  			 return;
		       // float cmnoise=47/22.;
		       // if( hit.detid().half()==0 )
		       // 	 cmnoise *= (cm00.adc()+cm01.adc()) / 2;
		       // else
		       // 	 cmnoise *= (cm10.adc()+cm11.adc()) / 2;
			 
  		       hit.set_adc(hit.adc()-median);
  		       writer->fill(hit);
  		     } );
    }
  }
  
  writer->save();
  return 0;
}
