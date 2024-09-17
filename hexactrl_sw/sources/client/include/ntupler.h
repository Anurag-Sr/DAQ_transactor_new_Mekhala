#ifndef NTUPLER
#define NTUPLER 1

#include <iostream>
#include <map>
#include <TFile.h>
#include <TDirectory.h>
#include <TTree.h>

#include "HGCROCv2RawData.h"
#include "hgcalhit.h"

#define N_READOUT_CHANNELS 38

class ntupler
{
 public:
  ntupler();

  ntupler(std::string filename,
	  std::string dirname=std::string("unpacker_data"), 
	  std::string treename=std::string("hgcroc"), 
	  std::string description=std::string("tree with hgcroc v2 raw data"),
          std::string trigtreename=std::string("triggerhgcroc"),
	  std::string trigdescription=std::string("tree with trigger link information"));

  ntupler(std::shared_ptr<TFile> afile, 
	  std::string dirname=std::string("unpacker_data"), 
	  std::string treename=std::string("hgcroc"), 
	  std::string description=std::string("tree with hgcroc v2 raw data"),
          std::string trigtreename=std::string("triggerhgcroc"),
	  std::string trigdescription=std::string("tree with trigger link information"));

  ~ntupler();
  
  void addRawInfoBranches();
  int  decode_tc_val(int value, int sumTC9 =0);

  void fill( HGCROCv2RawData rocdata );
  void fill( Hit hit );
  void setDecoderCharacMode(){ rawdatadecoder_characterisation_mode=true; }
  void setDecoderNormalMode(){ rawdatadecoder_characterisation_mode=false; }
 protected:
  std::shared_ptr<TFile> file;
  //TDirectory* dir;
  TTree* outtree;
  TTree* trigtree;

  bool fileowner;
  bool rawdatadecoder_characterisation_mode;
  
  int event;
  int corruption;
  int bxcounter;
  int eventcounter;
  int orbitcounter;
  int errorbit; // 3 bits error flags
  int chip;
  int half;
  int channel; //0-35 standard channels; 36 calib; 37-38 cm channels
  int adc;
  int adcm;
  int tot;
  int toa;
  int totflag;
  int trigtime;
  int trigwidth;
  int channelsumid;
  int rawsum;
  float decompresssum;

};

#endif
