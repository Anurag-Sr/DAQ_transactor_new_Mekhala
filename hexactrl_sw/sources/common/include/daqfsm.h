#ifndef DAQ_FSM
#define DAQ_FSM 1

#include <boost/msm/back/state_machine.hpp>
#include <boost/msm/front/state_machine_def.hpp>

#include <boost/thread/thread.hpp>

namespace msm = boost::msm;
namespace mpl = boost::mpl;

namespace daqfsm{

  struct initialize {};
  struct configure  {};
  struct start      {};
  struct stop       {};
  struct destroy    {};
  struct error      {};

  // front-end: define the FSM structure 
  struct daq_fsm : public msm::front::state_machine_def<daq_fsm>
  {

    // The list of FSM states
    struct Created : public msm::front::state<> {};

    struct Initialized : public msm::front::state<> {};

    struct Configured : public msm::front::state<> {};

    struct Running : public msm::front::state<> {};

    struct Error : public msm::front::state<> {};

    // the initial state of the player SM. Must be defined
    typedef Created initial_state;

    // transition actions
    void Initialize(initialize const&)   { }
    void Configure(configure const&)    { }
    void Start(start const&)        { }
    void Stop(stop const&)          { }
    void Destroy(destroy const&)    { }
    void GotoError(error const&)    { }

    // Transition table for daq_fsm
    struct transition_table : mpl::vector<
      //    Start     Event         Next      Action				 Guard
      //  +---------+-------------+---------+---------------------+----------------------+
      a_row < Created,      initialize, Initialized, &daq_fsm::Initialize>,
      a_row < Initialized,  initialize, Initialized, &daq_fsm::Initialize>,
      a_row < Configured,   initialize, Initialized, &daq_fsm::Initialize>,
      a_row < Initialized,  configure,  Configured,  &daq_fsm::Configure>,
      a_row < Configured,   configure,  Configured,  &daq_fsm::Configure>,
      a_row < Configured,   start,      Running,     &daq_fsm::Start>,
      a_row < Running,      stop,       Configured,  &daq_fsm::Stop>,
      a_row < Created,      destroy,    Created,     &daq_fsm::Destroy>,
      a_row < Configured,   destroy,    Created,     &daq_fsm::Destroy>,
      a_row < Initialized,  destroy,    Created,     &daq_fsm::Destroy>,
      a_row < Error,        destroy,    Created,     &daq_fsm::Destroy>,
      a_row < Created,      error,      Error,       &daq_fsm::GotoError>,
      a_row < Initialized,  error,      Error,       &daq_fsm::GotoError>,
      a_row < Configured,   error,      Error,       &daq_fsm::GotoError>,
      a_row < Running,      error,      Error,       &daq_fsm::GotoError>
      //  +---------+-------------+---------+---------------------+----------------------+
      > {};
    // Replaces the default no-transition response.
    template <class FSM,class Event>
      void no_transition(Event const& e, FSM&,int state)
    {
      return;
    }
  };
  typedef msm::back::state_machine<daq_fsm> FSM;
  static char const* const state_names[] = { "Created", "Initialized", "Configured", "Running", "Error" };
}
 
class daqFSM{
 public:
  daqFSM()
    { 
      boost::lock_guard<boost::mutex> lock{m_mutex};
      m_fsm.start(); 
    }
  ~daqFSM()
    { 
      boost::lock_guard<boost::mutex> lock{m_mutex};
      m_fsm.stop(); 
    }

  std::string status() const { return daqfsm::state_names[ m_fsm.current_state()[0] ]; }
  
  bool initialize()
  {
    boost::lock_guard<boost::mutex> lock{m_mutex};
    if( m_fsm.process_event(daqfsm::initialize())!=boost::msm::back::HANDLED_TRUE ){
      std::cout << "impossible to process initialize when state is " << status() << std::endl;
      return false;
    }
    return true;
  }

  bool configure()
  {
    boost::lock_guard<boost::mutex> lock{m_mutex};
    if( m_fsm.process_event(daqfsm::configure())!=boost::msm::back::HANDLED_TRUE ){
      std::cout << "impossible to process configure when state is " << status() << std::endl;
      return false;
    }
    return true;
  }

  bool start()
  {
    boost::lock_guard<boost::mutex> lock{m_mutex};
    if( m_fsm.process_event(daqfsm::start())!=boost::msm::back::HANDLED_TRUE ){
      std::cout << "impossible to process start when state is " << status() << std::endl;
      return false;
    }
    return true;
  }

  bool stop()
  {
    boost::lock_guard<boost::mutex> lock{m_mutex};
    if( m_fsm.process_event(daqfsm::stop())!=boost::msm::back::HANDLED_TRUE ){
      std::cout << "impossible to process stop when state is " << status() << std::endl;
      return false;
    }
    return true;
  }

  bool destroy()
  {
    if( m_fsm.process_event(daqfsm::destroy())!=boost::msm::back::HANDLED_TRUE ){
      std::cout << "impossible to process destroy when state is " << status() << std::endl;
      return false;
    }
    return true;
  }

  bool error()
  {
    if( m_fsm.process_event(daqfsm::error())!=boost::msm::back::HANDLED_TRUE ){
      std::cout << "impossible to process error when state is " << status() << std::endl;
      return false;
    }
    return true;
  }


 private:
  boost::mutex m_mutex;
  daqfsm::FSM m_fsm;
};

#endif
