#include <dummymenu.h>

void dummymenu::on_configure(const YAML::Node& config)
{
  std::cout << config << std::endl;
  m_nevents=1000;
  m_neventsperpush=100;
  if( config["NEvents"].IsDefined() )
    m_nevents = config["NEvents"].as<int>();
  
  if( config["NEventsPerPush"].IsDefined() )
    m_neventsperpush = config["NEventsPerPush"].as<int>();
}

void dummymenu::on_runthread()
{
  int index=0;
  while(1){
    boost::lock_guard<boost::mutex> lock{m_mutex};
    if(m_stop==true || (m_nevents>-1 && index>=m_nevents) ){
      break;
    }
    std::deque< std::shared_ptr<HGCROCv2RawData> >vec( m_neventsperpush, std::make_shared<HGCROCv2RawData>() );
    std::for_each( vec.begin(), vec.end(), [&](std::shared_ptr<HGCROCv2RawData> &roc){ roc=std::make_shared<HGCROCv2RawData>( createROCData(index,0) ); index++; } );
    m_pusher->sendvecptr(vec);
    continue;
  }
  if(m_stop!=true)
    stop();
}

void dummymenu::on_sendStartRun()
{
  m_pusher->sendStartOfRun(DataType::HGCROC);
  std::cout << "Starting dummy menu with : \n"
	    << "NEvents = " << m_nevents << "\n"
	    << "NEventsPerPush = " << m_neventsperpush << std::endl;
}
