#ifndef DATAWRITER
#define DATAWRITER 1

#include <boost/function.hpp>
#include <boost/functional/factory.hpp>
#include <boost/bind.hpp>
#include <iostream>
#include <fstream>
#include <map>

#include <yaml-cpp/yaml.h>

#include "HGCROCv2RawData.h"
#include "link_aligner_data.h"
#include "MarsData.h"
#include "ntupler.h"
#include "marsntupler.h"
#include "hgcalhit.h"
#include "runanalyzer.h"

#include <TFile.h>
#include <TTree.h>

class Writer
{
 public:
 Writer(std::string aname) : m_name(aname) {;}
  virtual ~Writer() = default;
  virtual void fill(HGCROCv2RawData rocdata){;}
  virtual void fill(link_aligner_data data) {;}
  virtual void fill(MarsData data) {;}
  virtual void fill(Hit hit) {;}
  virtual void save(){;}
  void print(){
    std::cout << "saving data to " << m_name << std::endl;
  }
  friend std::ostream& operator<<(std::ostream& out,const Writer& w){
    out << w.m_name;
    return out;
  }
 protected: 
  std::string m_name;
};

class RawDataWriter : public Writer
{
 public:
  RawDataWriter(std::string aname);
  ~RawDataWriter();
  void fill(HGCROCv2RawData rocdata) ;
  void save();
 private:
  std::ofstream ofs;
  boost::archive::binary_oarchive oaf;
};

class RootDataWriter : public Writer
{
 public:
  RootDataWriter(std::string aname);
  ~RootDataWriter();
  void fill(HGCROCv2RawData rocdata) ;
  void save();
 private:
  std::shared_ptr<ntupler> m_ntupler;
  std::shared_ptr<TFile> afile;
};

class MarsDataWriter : public Writer
{
 public:
  MarsDataWriter(std::string aname);
  ~MarsDataWriter();
  void fill(MarsData data) ;
  void save();
 private:
  std::shared_ptr<marsntupler> m_ntupler;
  std::shared_ptr<TFile> afile;
};

class HGCalHitDataWriter : public Writer
{
 public:
  HGCalHitDataWriter(std::string aname);
  ~HGCalHitDataWriter();
  void fill(Hit hit);
  void save();
 private:
  std::shared_ptr<ntupler> m_ntupler;
  std::shared_ptr<TFile> afile;
};

class SummaryRootDataWriter : public Writer
{
 public:
  SummaryRootDataWriter(std::string aname);
  ~SummaryRootDataWriter();
  void fill(HGCROCv2RawData rocdata) ;
  void save();
 private:
  std::shared_ptr<runsummarytupler> m_runsummarytupler;
  std::map<int, std::shared_ptr<runanalyzer> > m_analyzermap;
};

class SummaryRootDataWriterWithMap : public Writer
{
 public:
  SummaryRootDataWriterWithMap(std::string aname, std::map<std::string,int> paramMap);
  ~SummaryRootDataWriterWithMap();
  void fill(HGCROCv2RawData rocdata) ;
  void save();
 private:
  std::shared_ptr<runsummarytupler> m_runsummarytupler;
  std::map<int, std::shared_ptr<runanalyzer> > m_analyzermap;
};

class RootDataWriterWithNode : public Writer
{
 public:
  RootDataWriterWithNode(std::string aname, YAML::Node node);
  ~RootDataWriterWithNode();
  void fill(HGCROCv2RawData rocdata) ;
  void save();
 private:
  std::shared_ptr<TFile> m_file;
  std::shared_ptr<runsummarytupler> m_runsummarytupler;
  std::shared_ptr<ntupler> m_ntupler;
  std::map<int, std::shared_ptr<runanalyzer> > m_analyzermap;
};

class DelayScanRootDataWriter : public Writer
{
 public:
  DelayScanRootDataWriter(std::string aname );
  ~DelayScanRootDataWriter();
  void fill(link_aligner_data data) ;
  void save();
 private:
  TFile* m_file;
  TTree* m_tree;
  std::string m_link_name;
  int m_idelay;
  int m_alignedCount;
  int m_errorCount;
  int m_nIdles;
};

class TextDataWriter : public Writer
{
 public:
  TextDataWriter(std::string aname);
  ~TextDataWriter();
  void fill(HGCROCv2RawData rocdata) ;
  void save();
 private:
  std::map<int,std::shared_ptr<std::ofstream> > m_fout;
};

class DataWriterFactory
{
 public:
  DataWriterFactory(){
    factoryMapStr["raw"]       = boost::bind(boost::factory<RawDataWriter*>() , _1 );
    factoryMapStr["root"]      = boost::bind(boost::factory<RootDataWriter*>(), _1 );
    factoryMapStr["mars"]      = boost::bind(boost::factory<MarsDataWriter*>(), _1 );
    factoryMapStr["hgcalhits"] = boost::bind(boost::factory<HGCalHitDataWriter*>(), _1 );
    factoryMapStr["unpacked"]  = boost::bind(boost::factory<SummaryRootDataWriter*>(), _1 );
    factoryMapStr["delayscan"] = boost::bind(boost::factory<DelayScanRootDataWriter*>(), _1 );
    factoryMapStr["text"]      = boost::bind(boost::factory<TextDataWriter*>() , _1 );

    factoryMapStrMap["paramMap"] = boost::bind(boost::factory<SummaryRootDataWriterWithMap*>(), _1, _2 );
    factoryNode["yamlnode"]      = boost::bind(boost::factory<RootDataWriterWithNode*>(), _1, _2 );
  }
  ~DataWriterFactory(){;}
  
  std::unique_ptr<Writer> Create(const std::string& key, std::string aname ) const
  {
    std::unique_ptr<Writer> ptr{factoryMapStr.at(key)(aname)};
    return ptr;
  }

  std::unique_ptr<Writer> Create(const std::string& key, std::string aname, std::map<std::string,int> map ) const
  {
    std::unique_ptr<Writer> ptr{factoryMapStrMap.at(key)(aname,map)};
    return ptr;
  }

  std::unique_ptr<Writer> Create(const std::string& key, std::string aname, YAML::Node node ) const
  {
    std::unique_ptr<Writer> ptr{factoryNode.at(key)(aname,node)};
    return ptr;
  }
 private:
  std::map<std::string, boost::function<Writer* (const std::string&)>> factoryMapStr;
  std::map<std::string, boost::function<Writer* (const std::string&,const std::map<std::string,int>&)>> factoryMapStrMap;
  std::map<std::string, boost::function<Writer* (const std::string&,const YAML::Node&)>> factoryNode;
};

#endif
