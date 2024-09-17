#include <HGCROCv2RawData.h>

#include <algorithm>
#include <iomanip>

#ifndef NDEBUG 
#define NDEBUG 1
#endif

HGCROCv2RawData::HGCROCv2RawData(int event, int chip,
				 std::vector<uint32_t>::const_iterator data0_begin, std::vector<uint32_t>::const_iterator data0_end,
				 std::vector<uint32_t>::const_iterator data1_begin, std::vector<uint32_t>::const_iterator data1_end)// :
  // m_data0(data0_begin, data0_end),
  // m_data1(data1_begin, data1_end),
  // m_trig0(0xABADCAFE),
  // m_trig1(0xABADCAFE),
  // m_trig2(0xABADCAFE),
  // m_trig3(0xABADCAFE)
{
  m_data.reserve(HGCROC_DATA_BUF_SIZE*2+4*TRIG_ACQUIRE_LENGTH);
  // m_data1.reserve(HGCROC_DATA_BUF_SIZE+2*TRIG_ACQUIRE_LENGTH);
  std::copy(data0_begin, data0_end, std::back_inserter( m_data ) );
  std::copy(data1_begin, data1_end, std::back_inserter( m_data ) );
  m_data.push_back(0xABADCAFE);
  m_data.push_back(0xABADCAFE);
  m_data.push_back(0xABADCAFE);
  m_data.push_back(0xABADCAFE);
  m_chip=chip;
  
  m_event=event;
}

HGCROCv2RawData::HGCROCv2RawData(int event, int chip,
				 std::vector<uint32_t>::const_iterator data0_begin, std::vector<uint32_t>::const_iterator data0_end,
				 std::vector<uint32_t>::const_iterator data1_begin, std::vector<uint32_t>::const_iterator data1_end,
				 uint32_t trig0, uint32_t trig1, uint32_t trig2, uint32_t trig3) :
  HGCROCv2RawData(event, chip, data0_begin, data0_end, data1_begin, data1_end)
{
  m_data[2*HGCROC_DATA_BUF_SIZE]   = trig0;
  m_data[2*HGCROC_DATA_BUF_SIZE+1] = trig1;
  m_data[2*HGCROC_DATA_BUF_SIZE+2] = trig2;
  m_data[2*HGCROC_DATA_BUF_SIZE+3] = trig3;
}

HGCROCv2RawData::HGCROCv2RawData(int event, int chip,
				 std::vector<uint32_t>::const_iterator data0_begin, std::vector<uint32_t>::const_iterator data0_end,
				 std::vector<uint32_t>::const_iterator data1_begin, std::vector<uint32_t>::const_iterator data1_end,
				 uint32_t trig0, uint32_t trig1, uint32_t trig2, uint32_t trig3,
  				 std::vector<uint32_t>::const_iterator triglatency_begin, std::vector<uint32_t>::const_iterator triglatency_end) :
  HGCROCv2RawData(event, chip, data0_begin, data0_end, data1_begin, data1_end, trig0, trig1, trig2, trig3)
{
  m_triglatency = std::vector<uint32_t>(triglatency_begin, triglatency_end);
}

std::ostream& operator<<(std::ostream& out,const HGCROCv2RawData& rawdata)
{
  auto print = [&out](auto& d){ out << "\t" << std::hex << std::setfill('0') << std::setw(8) << d ; };

  out << "event = " << std::dec << rawdata.m_event  << " " 
      << "chip = " << std::dec << rawdata.m_chip << std::endl;
  out << "first half : \n" ;
  std::for_each( rawdata.m_data.begin(),
		 rawdata.m_data.begin()+HGCROC_DATA_BUF_SIZE,
		 print);
  out << "\n";
  out << "second half : \n" ;
  std::for_each( rawdata.m_data.begin()+HGCROC_DATA_BUF_SIZE,
		 rawdata.m_data.begin()+2*HGCROC_DATA_BUF_SIZE,
		 print);
  out << "\n";
  out << "TPG : \n" ;
  std::for_each( rawdata.m_data.begin()+2*HGCROC_DATA_BUF_SIZE,
		 rawdata.m_data.begin()+2*HGCROC_DATA_BUF_SIZE+4,
		 print);
  out << "\n";
  
  return out;
}

HGCROCEventContainer::HGCROCEventContainer()
{
  m_chip=0;
}


HGCROCEventContainer::HGCROCEventContainer(int chip) : HGCROCEventContainer()
{
  m_chip=chip;
}


void HGCROCEventContainer::fillContainer( int eventID,
					  const std::vector<uint32_t>& data0, const std::vector<uint32_t>& data1 )
{
  m_mutex.lock();
  unsigned int len = std::min(data0.size(), data1.size())/HGCROC_DATA_BUF_SIZE;
  for( unsigned int iEvt = 0; iEvt < len; ++iEvt ){
    auto header0 = data0.begin() + iEvt * HGCROC_DATA_BUF_SIZE;
    auto header1 = data1.begin() + iEvt * HGCROC_DATA_BUF_SIZE;
    m_rocdata.emplace_back( new HGCROCv2RawData(eventID, m_chip,
						header0, header0+HGCROC_DATA_BUF_SIZE,
						header1, header1+HGCROC_DATA_BUF_SIZE) );
    eventID++;
  }
  m_mutex.unlock();
}


void HGCROCEventContainer::fillContainer( int eventID,
					  const std::vector<uint32_t>& data0, const std::vector<uint32_t>& data1,
					  const std::vector<uint32_t>& trig0, const std::vector<uint32_t>& trig1,
					  const std::vector<uint32_t>& trig2, const std::vector<uint32_t>& trig3)
{
  m_mutex.lock();
  unsigned int len = std::min(data0.size(), data1.size())/HGCROC_DATA_BUF_SIZE;
#ifdef NDEBUG
  assert(trig0.size()==len);
  assert(trig1.size()==len);
  assert(trig2.size()==len);
  assert(trig3.size()==len);
#endif
  for( unsigned int iEvt = 0; iEvt < len; ++iEvt ){
    auto header0 = data0.begin() + iEvt * HGCROC_DATA_BUF_SIZE;
    auto header1 = data1.begin() + iEvt * HGCROC_DATA_BUF_SIZE;
    m_rocdata.emplace_back( new HGCROCv2RawData(eventID, m_chip,
						header0, header0+HGCROC_DATA_BUF_SIZE,
						header1, header1+HGCROC_DATA_BUF_SIZE,
						trig0[iEvt],trig1[iEvt],
						trig2[iEvt],trig3[iEvt] ) );
    eventID++;
  }
  m_mutex.unlock();
}



void HGCROCEventContainer::fillContainer( int eventID,
					  const std::vector<uint32_t>& data0, const std::vector<uint32_t>& data1,
					  const std::vector<uint32_t>& trig0, const std::vector<uint32_t>& trig1,
					  const std::vector<uint32_t>& trig2, const std::vector<uint32_t>& trig3,
					  const std::vector<uint32_t>& triglatency )
{
  m_mutex.lock();
  unsigned int len = std::min(data0.size(), data1.size())/HGCROC_DATA_BUF_SIZE;
#ifdef NDEBUG
  assert(trig0.size()==len);
  assert(trig1.size()==len);
  assert(trig2.size()==len);
  assert(trig3.size()==len);
  assert(uint32_t(triglatency.size()/TRIG_LATENCY_ACQUIRE_LENGTH)==len);
#endif
  for( unsigned int iEvt = 0; iEvt < len; ++iEvt ){
    auto header0 = data0.begin() + iEvt * HGCROC_DATA_BUF_SIZE;
    auto header1 = data1.begin() + iEvt * HGCROC_DATA_BUF_SIZE;
    auto first_word_in_triglatency = triglatency.begin() + iEvt * TRIG_LATENCY_ACQUIRE_LENGTH;
    m_rocdata.emplace_back( new HGCROCv2RawData(eventID, m_chip,
						header0, header0+HGCROC_DATA_BUF_SIZE,
						header1, header1+HGCROC_DATA_BUF_SIZE,
						trig0[iEvt],trig1[iEvt],
						trig2[iEvt],trig3[iEvt],
						first_word_in_triglatency, first_word_in_triglatency+TRIG_LATENCY_ACQUIRE_LENGTH		
						) );
    eventID++;
  }
  m_mutex.unlock();
}
