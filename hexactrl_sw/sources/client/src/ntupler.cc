
#include <sstream>
#include <cstring>
#include "ntupler.h"
#include <boost/crc.hpp>
#include <iomanip>
#include <numeric>

// #include <boost/endian/conversion.hpp> does not work with boost 1.53

ntupler::ntupler()
{
  file=NULL;
  //dir=NULL;
  outtree=NULL;
  fileowner=false;
  rawdatadecoder_characterisation_mode=false;
}

ntupler::ntupler(std::string filename, std::string dirname, std::string treename, std::string description, std::string trigtreename, std::string trigdescription)
{
  fileowner=true;
  file=std::make_shared<TFile>(filename.c_str(),"RECREATE");
  try{
    file->rmdir(dirname.c_str());
  }
  catch( std::exception& e ){
    std::cerr << "Exception : " 
   	      << e.what() << " trying to rmdir a dir which does not exist" << std::endl; 
  }
  auto dir = file->mkdir(dirname.c_str());
  if( NULL==dir ){
    dir = file->mkdir(dirname.c_str());
  }
  dir->cd();
  outtree=new TTree(treename.c_str(),description.c_str());
  outtree->Branch("event", &event);
  outtree->Branch("chip", &chip);
  outtree->Branch("half", &half);
  outtree->Branch("channel", &channel);
  outtree->Branch("adc",  &adc);
  outtree->Branch("adcm", &adcm);
  outtree->Branch("toa",  &toa);
  outtree->Branch("tot",  &tot);
  outtree->Branch("totflag",  &totflag);
  outtree->Branch("trigtime",  &trigtime);
  outtree->Branch("trigwidth",  &trigwidth);

  rawdatadecoder_characterisation_mode=false;

  trigtree=new TTree(trigtreename.c_str(), trigdescription.c_str());
  trigtree->Branch("event", &event);
  trigtree->Branch("chip", &chip);
  trigtree->Branch("trigtime",  &trigtime);
  trigtree->Branch("channelsumid", &channelsumid);
  trigtree->Branch("rawsum", &rawsum);
  trigtree->Branch("decompresssum", &decompresssum);
}

ntupler::ntupler(std::shared_ptr<TFile> afile, std::string dirname, std::string treename, std::string description, std::string trigtreename, std::string trigdescription)
{
  fileowner=false;
  file=afile;
    file->rmdir(dirname.c_str());
  try{
    file->rmdir(dirname.c_str());
  }
  catch( std::exception& e ){
    std::cerr << "Exception : " 
   	      << e.what() << " trying to rmdir a dir which does not exist" << std::endl; 
  }
  auto dir = file->mkdir(dirname.c_str());
  dir->cd();
  outtree=new TTree(treename.c_str(),description.c_str());
  outtree->Branch("event", &event);
  outtree->Branch("chip", &chip);
  outtree->Branch("half", &half);
  outtree->Branch("channel", &channel);
  outtree->Branch("adc",  &adc);
  outtree->Branch("adcm", &adcm);
  outtree->Branch("toa",  &toa);
  outtree->Branch("tot",  &tot);  
  outtree->Branch("totflag",  &totflag);
  outtree->Branch("trigtime",  &trigtime);
  outtree->Branch("trigwidth",  &trigwidth);

  rawdatadecoder_characterisation_mode=false;

  trigtree=new TTree(trigtreename.c_str(), trigdescription.c_str());
  trigtree->Branch("event", &event);
  trigtree->Branch("chip", &chip);
  trigtree->Branch("trigtime",  &trigtime);
  trigtree->Branch("channelsumid", &channelsumid);
  trigtree->Branch("rawsum", &rawsum);
  trigtree->Branch("decompresssum", &decompresssum);
}

ntupler::~ntupler()
{
  if( NULL!=file && fileowner ){
    file->Write();
    file->Close();
  }
}

void ntupler::addRawInfoBranches()
{
  outtree->Branch("corruption", &corruption);
  outtree->Branch("bxcounter", &bxcounter);
  outtree->Branch("eventcounter", &eventcounter);
  outtree->Branch("orbitcounter", &orbitcounter);
}

int ntupler::decode_tc_val(int value, int sumTC9)
{
  int mant = value & 0x7;
  int pos  = (value >> 3) & 0xf;

  if(pos==0) return mant << (1 + sumTC9*2) ;

  pos += 2;

  int decompsum = 1 << pos;
  decompsum |= mant << (pos-3);
  return decompsum << (1 + sumTC9*2);
}

void ntupler::fill( HGCROCv2RawData rocdata )
{
  //for( auto roc : rocdata ){
  event = rocdata.event();      
  chip = rocdata.chip();

  int offset=-1;
  int index=0;
  for(auto latency : rocdata.triglatency()){
    if(latency!=0){
      for(auto i=0; i<32; i++){
        if( ( (latency>>(31-i))&0x1 ) == 1 ){
          offset = 32*index + i;
          break;
        }
      }
      if(offset>=0) break;
    }
    else {
      index++;
    }
  }
  trigtime = offset;// * 25.0 / 32 ;
  std::bitset<TRIG_LATENCY_ACQUIRE_LENGTH*32> bits;
  trigwidth = std::accumulate(rocdata.triglatency().begin(), rocdata.triglatency().end(), 0, [&](uint32_t width,const uint32_t val){ return width + std::bitset<32>(val).count(); });

  std::vector<uint32_t> data(HGCROC_DATA_BUF_SIZE);
  for( half=0; half<2; half++ ){
    // header = 0x5BXCECOCHb5 : BXC 12 bit bunch crossing counter; EC : 6 bit event counter, 0C : 3 bit orbit counter; Hb: 3 bit intergrity
    std::copy(rocdata.data().begin()+HGCROC_DATA_BUF_SIZE*half,
	      rocdata.data().begin()+HGCROC_DATA_BUF_SIZE*(half+1),
	      data.begin()
	      );
    uint32_t header = data[0];
    uint32_t head = ( header >> 28) & 0xf;
    uint32_t tail = header & 0xf;
    corruption = head == 0x5 && tail == 0x5 ? 0 : 1;


    // unsigned char *bytes=new unsigned char(data.size()*4);
    // std::copy(data.begin()+1,data.end(),bytes); // +1 to avoid the daq header
    
    bxcounter = ( header >> 16 ) & 0xfff ;
    eventcounter = ( header & 0xffff ) >> 10 ;
    orbitcounter = ( header & 0x3ff ) >> 7 ;

    auto target = data[39];
    std::vector<uint32_t>crcvec(data.begin(),data.end());
    // std::transform(crcvec.begin(),crcvec.end(),crcvec.begin(),[](uint32_t w){return boost::endian::endian_reverse(w);}); //does not work with boost 1.53
    std::transform( crcvec.begin(),
    		    crcvec.end(),
    		    crcvec.begin(),
    		    [](uint32_t w){ return
    			((w<<24)& 0xFF000000) |
    			((w<<8) & 0x00FF0000) |
    			((w>>8) & 0x0000FF00) |
    			((w>>24)& 0x000000FF) ; }
		    );
    auto array = &(crcvec[0]);
    auto bytes = reinterpret_cast<const unsigned char*>(array);
    auto crc32 = boost::crc<32, 0x4c11db7, 0x0, 0x0, false, false>(bytes,39*4);

    if( crc32!=target ){
      corruption+=2;
      // std::cout << rocdata << std::endl;
      // std::cout << "CRC : " << crc32 << "\t" << target << " in half " << half << std::endl;
    }

    if( (header>>4)&0x1 ) corruption+=4;
    if( (header>>5)&0x1 ) corruption+=8;
    if( (header>>6)&0x1 ) corruption+=16;
    
    //common mode channels, but we keep same channel numbering as in ROCv2    
    {
      channel = 37;
      adc = ( data[1] >> 10 ) & 0x3ff;
      tot = 0;
      toa = 0;
      totflag=0;
      adcm = 0;
      outtree->Fill();
      channel = 38;
      adc = data[1] & 0x3ff;
      tot = 0;
      toa = 0;
      totflag=0;
      adcm = 0;
      outtree->Fill();
    }
    for( int ichan=1; ichan<N_READOUT_CHANNELS; ichan++ ){
      auto dataword = data[ichan+1];
      if( ichan<=18 ) channel = ichan-1;
      else if( ichan>19 ) channel = ichan - 2;
      else if( ichan==19 ) channel = 36; // calibration channel
      adc = adcm = tot = toa = -1;
      if( rawdatadecoder_characterisation_mode==false and channel!=36){
	totflag = dataword>>30;
	if( totflag<=1 ){
	  adcm = (dataword >> 20) & 0x3ff;
	  adc  = (dataword >>10 ) & 0x3ff;
	  toa  = dataword & 0x3ff;
	}
	else if( totflag==2 ){ //should not appear but as if totflag=3 (i.e. there is tot)
	  adcm = (dataword >> 20) & 0x3ff;
	  tot  = (dataword >>10 ) & 0x3ff;
	  toa  = dataword & 0x3ff;
	}
	else if( totflag==3 ){
	  adcm = (dataword >> 20) & 0x3ff;
	  tot  = (dataword >>10 ) & 0x3ff;
	  toa  = dataword & 0x3ff;
	}
	else{
	  std::cout << "something weird happens in tot flags :" << totflag << std::endl;
	}
      }
      else{ // characterisation format
	adc  = (dataword >> 20) & 0x3ff;
	tot  = (dataword >>10 ) & 0x3ff;
	toa  = dataword & 0x3ff;
      }
      // decompress TOT : MSB is not data but a flag to know which of the 12 bits of ToT was sent
      if( tot>>0x9==1 )
	tot = (tot & 0x1ff) << 0x3 ;
      outtree->Fill();
    }
  }
  // trigger info
  int sumTC9 = 0;
  std::vector<int> trig_links = {0,1,2,3};
  
  for(auto trig_link:trig_links){
    uint32_t tp = rocdata.trigger(trig_link);
    if(tp!=0XABADCAFE){
      for(int i=0; i<4; i++){
	channelsumid  = i + (4 * trig_link);
	rawsum        = (tp >> (7*(3-i)))&0x7f;
	// if(rawsum<0)
	//   std::cout << rawsum << "\t" << tp << "\t" << i << "\t" << (7*(3-i)) << std::endl;
	decompresssum = decode_tc_val(rawsum, sumTC9);
	trigtree->Fill();
      }
    }//  else{
    // 	std::cout << " trigger links data not ok "<<std::endl;
    // }
  }
}

void ntupler::fill( Hit hit )
{
  //for( auto roc : rocdata ){
  event = hit.event();
  chip = hit.detid().chip();
  half = hit.detid().half();
  channel = hit.detid().channel();
  adc = hit.adc();
  toa = hit.toa();
  tot = hit.tot();
  trigtime = hit.triglatency();
  outtree->Fill();
}
