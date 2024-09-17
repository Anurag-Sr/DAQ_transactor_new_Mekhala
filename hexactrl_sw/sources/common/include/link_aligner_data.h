#ifndef LINK_ALIGNER_DATA
#define LINK_ALIGNER_DATA 1

#include <boost/archive/binary_oarchive.hpp>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/serialization/vector.hpp>

class link_aligner_data{
 public:
  link_aligner_data(){;} 
 link_aligner_data( std::string link_name, int idelay, int aligned_count, int error_count, int is_aligned, int nIdles ) : 
  m_link_name( link_name ),
    m_idelay( idelay ),
    m_aligned_count( aligned_count ),
    m_error_count( error_count ),
    m_is_aligned(is_aligned),
    m_nIdles(nIdles)
    {;}
  ~link_aligner_data(){;}

  std::string linkName() const { return m_link_name ; }
  uint32_t delay() const { return m_idelay ; }
  uint32_t aligned_counts() const { return m_aligned_count ; }
  uint32_t error_counts() const { return m_error_count ; }
  uint32_t aligned() const { return m_is_aligned ; }
  uint32_t nIdles() const { return m_nIdles ; }

  friend std::ostream& operator<<(std::ostream& out,const link_aligner_data& d)
  {
    out << d.m_link_name << " "
	<< d.m_idelay << " "
	<< d.m_aligned_count << " "
	<< d.m_error_count << " "
	<< d.m_is_aligned << " "
	<< d.m_nIdles ;
    return out;
  }

private:
  friend class boost::serialization::access;
  template<class Archive>
    void serialize(Archive & ar, const unsigned int version)
    {
      ar & m_link_name;
      ar & m_idelay;
      ar & m_aligned_count;
      ar & m_error_count;
      ar & m_is_aligned;
      ar & m_nIdles;
    }

 private:
  std::string m_link_name;
  uint32_t m_idelay;
  uint32_t m_aligned_count;
  uint32_t m_error_count;
  uint32_t m_is_aligned;
  uint32_t m_nIdles;
};

#endif
