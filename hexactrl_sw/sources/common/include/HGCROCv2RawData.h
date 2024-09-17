#ifndef HGCROCV2RAWDATA
#define HGCROCV2RAWDATA 1

#include <iostream>
#include <deque>

#include <boost/archive/binary_oarchive.hpp>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/serialization/vector.hpp>
#include <boost/thread/thread.hpp>

#define HGCROC_DATA_BUF_SIZE 41  //36 channels + 1 common mode (with 2 channels gathered together) + 1 calib + 1 header + 1 crc, 1 idle in trailer per half
#define TRIG_LATENCY_ACQUIRE_LENGTH 20  //FIFO depth is twice smaller and DAQ elink FIFOs, so we readout half length of HGCROC data size to ease the synchronization
#define TRIG_ACQUIRE_LENGTH 1

class HGCROCv2RawData
// NEED to add some flag to handle HD hexaboard data with only 2 TRG links
// NEED to add some flag to handle partial hexaboard data with only 1 DAQ link (with 1 or 2 TRG links??) 
{
 public:
  HGCROCv2RawData(){;}

  HGCROCv2RawData(int event, int chip, 
		  std::vector<uint32_t>::const_iterator data0_begin, std::vector<uint32_t>::const_iterator data0_end, 
		  std::vector<uint32_t>::const_iterator data1_begin, std::vector<uint32_t>::const_iterator data1_end);

  HGCROCv2RawData(int event, int chip, 
		  std::vector<uint32_t>::const_iterator data0_begin, std::vector<uint32_t>::const_iterator data0_end, 
		  std::vector<uint32_t>::const_iterator data1_begin, std::vector<uint32_t>::const_iterator data1_end,
		  uint32_t trig0, uint32_t trig1, uint32_t trig2, uint32_t trig3);

  HGCROCv2RawData(int event, int chip, 
		  std::vector<uint32_t>::const_iterator data0_begin, std::vector<uint32_t>::const_iterator data0_end, 
		  std::vector<uint32_t>::const_iterator data1_begin, std::vector<uint32_t>::const_iterator data1_end,
		  uint32_t trig0, uint32_t trig1, uint32_t trig2, uint32_t trig3,
		  std::vector<uint32_t>::const_iterator triglatency__begin, std::vector<uint32_t>::const_iterator triglatency_end);
  
  int event() const { return m_event; }
  
  int chip() const { return m_chip; }
  
  const std::vector<uint32_t> &data() const { return m_data; }
  const uint32_t &trigger(int id) const {
    switch(id){
    case 0 :return m_data[HGCROC_DATA_BUF_SIZE*2] ; 
    case 1 :return m_data[HGCROC_DATA_BUF_SIZE*2+1] ; 
    case 2 :return m_data[HGCROC_DATA_BUF_SIZE*2+2] ; 
    case 3 :return m_data[HGCROC_DATA_BUF_SIZE*2+3] ;
    default: break;
    }
    return 0xDEADBEEF; 
  }
  const std::vector<uint32_t> &triglatency() const { return m_triglatency;}
  
  friend std::ostream& operator<<(std::ostream& out,const HGCROCv2RawData& h);

 private:
  friend class boost::serialization::access;
  template<class Archive>
    void serialize(Archive & ar, const unsigned int version)
    {
      ar & m_event;
      ar & m_chip;
      ar & m_data;
      // ar & m_data1;
      ar & m_triglatency;
    }

 private:
  int m_event;
  int m_chip;
  std::vector<uint32_t> m_data;
  // std::vector<uint32_t> m_data1;
  std::vector<uint32_t> m_triglatency;
  
};

class HGCROCEventContainer
{
 public:
  HGCROCEventContainer();
  HGCROCEventContainer(int chip);
  
  void fillContainer( int eventID,
		      const std::vector<uint32_t>& data0, const std::vector<uint32_t>& data1 );

  void fillContainer( int eventID,
		      const std::vector<uint32_t>& data0, const std::vector<uint32_t>& data1,
		      const std::vector<uint32_t>& trig0, const std::vector<uint32_t>& trig1,
		      const std::vector<uint32_t>& trig2, const std::vector<uint32_t>& trig3 );

  void fillContainer( int eventID,
		      const std::vector<uint32_t>& data0, const std::vector<uint32_t>& data1,
		      const std::vector<uint32_t>& trig0, const std::vector<uint32_t>& trig1,
		      const std::vector<uint32_t>& trig2, const std::vector<uint32_t>& trig3,
		      const std::vector<uint32_t>& triglatency );

  inline std::deque< std::unique_ptr<HGCROCv2RawData> >& getDequeEvents() {return m_rocdata;} 
  inline void deque_lock(){ m_mutex.lock(); }
  inline void deque_unlock(){ m_mutex.unlock(); }

  int chip() const{ return m_chip; }

  bool operator==( const HGCROCEventContainer& container ){ return container.chip()==m_chip; }
  
 private:
  std::deque< std::unique_ptr<HGCROCv2RawData> > m_rocdata;
  boost::mutex m_mutex;
  int m_chip;
};

#endif
