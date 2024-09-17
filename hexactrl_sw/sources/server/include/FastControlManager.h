#ifndef FASTCONTROLMANAGER
#define FASTCONTROLMANAGER 1

#include <uhal/uhal.hpp>
#include <yaml-cpp/yaml.h>
#include <unordered_map>

// enum class FC_channel_type{ L1A, CALIBL1A, DUMP, CALIBREQ };
enum class FC_channel_follow{ DISABLE, A, B, C, D, E, F, G, H };
enum class FC_channel_flavor{ L1A, L1A_NZS, CALPULINT, CALPULEXT, EXTPULSE0, EXTPULSE1 };

struct umap_helper{

    std::unordered_map<FC_channel_flavor, std::string> flavor2str = {
      {FC_channel_flavor::CALPULINT, "CALPULINT"},
      {FC_channel_flavor::CALPULEXT, "CALPULEXT"}
    };
    std::unordered_map<std::string, FC_channel_flavor> str2flavor = {
      {"CALPULINT", FC_channel_flavor::CALPULINT},
      {"CALPULEXT", FC_channel_flavor::CALPULEXT}
    };

};

namespace YAML {
  template<>
  struct convert<FC_channel_flavor> {

    static Node encode(const FC_channel_flavor& flavor) {
      umap_helper umap;
      Node node;
      node["calibType"] = umap.flavor2str[flavor];
      return node;
    }

    static bool decode(const Node& node, FC_channel_flavor& flavor) {
      umap_helper umap;
      if(!node.IsScalar()) {
      	return false;
      }
      auto str = node.as<std::string>();
      flavor = umap.str2flavor[str];
      return true;
    }
  };
}

class FastControlManager
{
public:
  FastControlManager(uhal::HwInterface* uhalHW);
  ~FastControlManager(){;}
  void resetFC();

  //fast control commands
  void enable_FC_stream(int val);
  void force_idles(int val); //
  void enable_orbit_sync(int val);
  void enable_global_l1a(int val);
  void prel1a_offset(int val);
  void enable_external_l1a(int val);
  void enable_random_l1a(int val);
  void enable_block_sequencer(int val);
  void enable_nzs_generator(int val);
  void enable_nzs_jitter(int val);

  //fast control request, don't take any args as the related registers have an auto-clear mechanism
  void request_reset_nzs();
  void request_count_rst();
  void request_sequence();
  void request_orbit_rst();
  void request_chipsynq();
  void request_ebr();
  void request_ecr();
  void request_link_reset_roct();
  void request_link_reset_rocd();
  void request_link_reset_econt();
  void request_link_reset_econd();

  // BX for requests
  void bx_orbit_synq(int val);
  void bx_chipsynq(int val);
  void bx_ebr(int val);
  void bx_ecr(int val);
  void bx_link_reset_roct(int val);
  void bx_link_reset_rocd(int val);
  void bx_link_reset_econt(int val);
  void bx_link_reset_econd(int val);

  // Random gen and external L1A settings
  void minimum_trigger_period(int val);
  void random_trigger_log2_period(int val);
  void external_triggers_debounce(int val);
  // void set_l1a_n_consecutive(int val);

  void external_trigger_delay(int chan, int val);
  void external_trigger_delay(int val);

  // Block sequencer settings
  void command_sequence_length(int val);
  void command_sequence_bx(int val);
  void command_sequence_orbit_prescale(int val);
  void command_sequence_page(int val);
  void command_sequence_contents(const std::vector<uint32_t>& vec);

  // Periodic generator settings
  void set_fc_periodic_settings(int periodic_chan, int enable, int bx, int prescale, FC_channel_flavor flavor, int length, FC_channel_follow follow);   
  void set_fc_channel_A_settings(int enable, int bx, int prescale, FC_channel_flavor flavor, int length, FC_channel_follow follow); 
  void set_fc_channel_B_settings(int enable, int bx, int prescale, FC_channel_flavor flavor, int length, FC_channel_follow follow); 
  void set_fc_channel_C_settings(int enable, int bx, int prescale, FC_channel_flavor flavor, int length, FC_channel_follow follow); 
  void set_fc_channel_D_settings(int enable, int bx, int prescale, FC_channel_flavor flavor, int length, FC_channel_follow follow); 
  void set_fc_channel_E_settings(int enable, int bx, int prescale, FC_channel_flavor flavor, int length, FC_channel_follow follow); 
  void set_fc_channel_F_settings(int enable, int bx, int prescale, FC_channel_flavor flavor, int length, FC_channel_follow follow); 
  void set_fc_channel_G_settings(int enable, int bx, int prescale, FC_channel_flavor flavor, int length, FC_channel_follow follow); 
  void set_fc_channel_H_settings(int enable, int bx, int prescale, FC_channel_flavor flavor, int length, FC_channel_follow follow); 

  void setRegister( std::string reg, int val );
  const uint32_t getRegister( std::string reg );
  const uint32_t getRecvRegister( std::string reg );
  
 private:
  uhal::HwInterface* m_uhalHW;
};

#endif

