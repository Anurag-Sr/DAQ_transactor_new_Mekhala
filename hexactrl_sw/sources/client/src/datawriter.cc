#include "datawriter.h"
#include <boost/regex.hpp>
#include <boost/lexical_cast.hpp>


RawDataWriter::RawDataWriter( std::string aname ) : Writer(aname), 
						    ofs(aname,std::ios::binary),
						    oaf(ofs) 
{}

RawDataWriter::~RawDataWriter()
{}

void RawDataWriter::fill( HGCROCv2RawData rocdata )
{
  oaf << rocdata;
}

void RawDataWriter::save()
{
  ofs.close();
}

RootDataWriter::RootDataWriter( std::string aname ) : Writer(aname)
{
  afile = std::make_shared<TFile>(aname.c_str(),"RECREATE");
  m_ntupler = std::make_shared<ntupler>( afile );
  m_ntupler->addRawInfoBranches();
}

RootDataWriter::~RootDataWriter()
{}

void RootDataWriter::fill(HGCROCv2RawData rocdata)
{
  m_ntupler->fill(rocdata);
}

void RootDataWriter::save()
{
  afile->Write();
  afile->Close();
}

MarsDataWriter::MarsDataWriter( std::string aname ) : Writer(aname)
{
  afile = std::make_shared<TFile>(aname.c_str(),"RECREATE");

  try{
    std::string base=aname.substr(0,aname.find(".root"));
    std::ostringstream os(std::ostringstream::ate);
    os.str("");
    os << base << ".yaml";
    auto node = YAML::LoadFile(os.str())["metaData"];
    m_ntupler = std::make_shared<marsntupler>( afile,node );
  }
  catch(std::exception& e){
    m_ntupler = std::make_shared<marsntupler>( afile );
  }
  m_ntupler->buildTTree();
}

MarsDataWriter::~MarsDataWriter()
{}

void MarsDataWriter::fill(MarsData data)
{
  m_ntupler->fill(data);
}

void MarsDataWriter::save()
{
  m_ntupler->fillTree();
  afile->Write();
  afile->Close();
}

HGCalHitDataWriter::HGCalHitDataWriter( std::string aname ) : Writer(aname)
{
  afile = std::make_shared<TFile>(aname.c_str(),"UPDATE");
  m_ntupler = std::make_shared<ntupler>( afile ,
					 std::string("hgcalhit"),
					 std::string("hits"),
					 std::string("tree with hgcal hit data (1 hit per entry)")
					 );
}

HGCalHitDataWriter::~HGCalHitDataWriter()
{}

void HGCalHitDataWriter::fill(Hit hit)
{
  m_ntupler->fill(hit);
}

void HGCalHitDataWriter::save()
{
  afile->Write();
  afile->Close(); 
}

SummaryRootDataWriter::SummaryRootDataWriter( std::string aname ) : Writer(aname)
{
  m_runsummarytupler = std::make_shared<runsummarytupler>(aname);
  m_runsummarytupler->init();
  m_runsummarytupler->buildTTree();
}

SummaryRootDataWriter::~SummaryRootDataWriter()
{}

void SummaryRootDataWriter::fill(HGCROCv2RawData rocdata)
{
  int chip=rocdata.chip();
  if( m_analyzermap.find(chip)==m_analyzermap.end() ){
    auto ptr = std::make_shared<runanalyzer>() ;
    m_analyzermap.insert( std::pair<int, std::shared_ptr<runanalyzer> >(chip,ptr) );
  }
  m_analyzermap[chip]->add( rocdata );
}

void SummaryRootDataWriter::save()
{
  std::vector<runsummary> summaryvec;
  summaryvec.reserve( m_analyzermap.size() );
  for( auto it=m_analyzermap.begin(); it!=m_analyzermap.end(); ++it)
    summaryvec.push_back( it->second->analyze() );
  m_runsummarytupler->fill(summaryvec);
}

SummaryRootDataWriterWithMap::SummaryRootDataWriterWithMap( std::string aname,std::map<std::string,int> paramMap) : Writer(aname)
{
  m_runsummarytupler = std::make_shared<runsummarytupler>(aname,paramMap);
  m_runsummarytupler->init();
  m_runsummarytupler->buildTTree();
}

SummaryRootDataWriterWithMap::~SummaryRootDataWriterWithMap()
{}

void SummaryRootDataWriterWithMap::fill(HGCROCv2RawData rocdata)
{
  int chip=rocdata.chip();
  if( m_analyzermap.find(chip)==m_analyzermap.end() ){
    auto ptr = std::make_shared<runanalyzer>() ;
    m_analyzermap.insert( std::pair<int, std::shared_ptr<runanalyzer> >(chip,ptr) );
  }
  m_analyzermap[chip]->add( rocdata );
}

void SummaryRootDataWriterWithMap::save()
{
  std::vector<runsummary> summaryvec;
  summaryvec.reserve( m_analyzermap.size() );
  for( auto it=m_analyzermap.begin(); it!=m_analyzermap.end(); ++it)
    summaryvec.push_back( it->second->analyze() );
  m_runsummarytupler->fill(summaryvec);
}

RootDataWriterWithNode::RootDataWriterWithNode( std::string aname, YAML::Node node) : Writer(aname)
{
  m_file = std::make_shared<TFile>(aname.c_str(),"RECREATE");

  int keepRawData(1),keepSummary(1);
  if( node["keepRawData"].IsDefined() )
    keepRawData = node["keepRawData"].as<int>();
  if( node["keepSummary"].IsDefined() )
    keepSummary = node["keepSummary"].as<int>();

  if( keepRawData==0 && keepSummary==0 )
    std::cout << "**********************************************************\n" 
	      << "************************* WARNING ************************\n"
	      << "** Both params keepRawData and keepSummary are set to 0 **\n"
	      << "*********** Output root file will remain empty ***********" << std::endl;
  else{
    if( keepRawData ){
      m_ntupler = std::make_shared<ntupler>( m_file );
      m_ntupler->addRawInfoBranches();
      if( node["characMode"].IsDefined() && node["characMode"].as<int>()==1 )
	m_ntupler->setDecoderCharacMode();
      else
	m_ntupler->setDecoderNormalMode();
    }
    else
      m_ntupler=NULL;
    
    if( keepSummary ){
      m_runsummarytupler = std::make_shared<runsummarytupler>(m_file,node);
      m_runsummarytupler->init();
      m_runsummarytupler->buildTTree();
    }
    else
      m_runsummarytupler=NULL;
  }
}

RootDataWriterWithNode::~RootDataWriterWithNode()
{}

void RootDataWriterWithNode::fill(HGCROCv2RawData rocdata)
{
  if( NULL!=m_ntupler )
    m_ntupler->fill(rocdata);

  if( NULL!=m_runsummarytupler ){
    int chip=rocdata.chip();
    if( m_analyzermap.find(chip)==m_analyzermap.end() ){
      auto ptr = std::make_shared<runanalyzer>() ;
      m_analyzermap.insert( std::pair<int, std::shared_ptr<runanalyzer> >(chip,ptr) );
    }
  m_analyzermap[chip]->add( rocdata );
  }
}

void RootDataWriterWithNode::save()
{
  if( NULL!=m_runsummarytupler ){
    std::vector<runsummary> summaryvec;
    summaryvec.reserve( m_analyzermap.size() );
    for( auto it=m_analyzermap.begin(); it!=m_analyzermap.end(); ++it)
      summaryvec.push_back( it->second->analyze() );
    m_runsummarytupler->fill(summaryvec);
  }
  m_file->Write();
  m_file->Close();
}

DelayScanRootDataWriter::DelayScanRootDataWriter( std::string aname) : Writer(aname)
{
  m_file = new TFile(aname.c_str(),"RECREATE");
  m_tree = new TTree("delayScanTree","");
  m_tree->Branch("link",         &m_link_name);
  m_tree->Branch("idelay",       &m_idelay);
  m_tree->Branch("alignedCount", &m_alignedCount);
  m_tree->Branch("errorCount",   &m_errorCount);
  m_tree->Branch("nIdles",      &m_nIdles);
}

DelayScanRootDataWriter::~DelayScanRootDataWriter()
{}

void DelayScanRootDataWriter::fill(link_aligner_data data)
{
  m_link_name = data.linkName();
  m_idelay = data.delay();
  m_alignedCount = data.aligned_counts();
  m_errorCount = data.error_counts();
  m_nIdles = data.nIdles();
  m_tree->Fill();
}

void DelayScanRootDataWriter::save()
{
  m_file->Write();
  m_file->Close();
}

TextDataWriter::TextDataWriter( std::string aname ) : Writer(aname)
{}

TextDataWriter::~TextDataWriter()
{}

void TextDataWriter::fill(HGCROCv2RawData rocdata)
{
  auto chip = rocdata.chip();
  // for( int half=0; half<2; half++ ){
  if( m_fout.find( chip )==m_fout.end() ){
    std::ostringstream os;
    os.str("");
    os << std::dec << m_name << "/chip" << chip << ".txt";
    std::cout << "saving text data in " << os.str() << std::endl;
    auto out = std::make_shared<std::ofstream>( os.str().c_str() , std::ofstream::out );
    m_fout.insert( std::pair<int,std::shared_ptr<std::ofstream> >(chip,out) );
  }
    // std::vector<uint32_t> data(HGCROC_DATA_BUF_SIZE);
    // std::copy(rocdata.data().begin()+HGCROC_DATA_BUF_SIZE*half,
    // 	      rocdata.data().begin()+HGCROC_DATA_BUF_SIZE*(half+1),
    // 	      data.begin()
    // 	      );
  auto out = m_fout[ chip ];
  (*out) << rocdata;
}

void TextDataWriter::save()
{
  for( auto out: m_fout )
    (*out.second).close();
}
