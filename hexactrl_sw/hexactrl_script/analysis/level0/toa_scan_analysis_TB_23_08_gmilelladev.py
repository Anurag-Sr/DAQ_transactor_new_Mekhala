from level0.analyzer import *
from scipy.optimize import curve_fit
import glob
import numpy as np
import scipy.optimize
from nested_dict import nested_dict


# tot_trim_analyzer = analyzer.tot_scan_analyzer(odir=odir)
#         folders = glob.glob(odir+"2_chan_*/")
        
#                 df_summary = uproot3.open(f)['runsummary']['summary'].pandas.df()
#                 df_raw = uproot3.open(f)['unpacker_data']['hgcroc'].pandas.df()
#                 df_raw['trim_tot'] = df_summary.trim_tot.unique()[0]
#                 df_raw['injectedChannels'] = df_summary.injectedChannels.unique()[0]
#                 chan_uniq = df_summary.injectedChannels.unique()[0]
#                 df_raw = df_raw[df_raw.channel.isin([chan_uniq,chan_uniq+36])].copy()
#                 df_.append(df_raw)
#         tot_trim_analyzer.data = pandas.concat(df_)
#         tot_trim_analyzer.makePlot_trim(preffix="2")
#         tot_trim_analyzer.determineTot_trim(correction_tottrim=0)
#         i2csocket.update_yamlConfig(fname=odir+'/trimmed_tot.yaml')
#         i2csocket.configure(fname=odir+'/trimmed_tot.yaml')

odir = '/home/hgcal/Desktop/software_test_Jia-Hao/hexactrl-sw/hexactrl-script_TB_23_08/data/TB3_D8_1/Threshold_tuning/vreftoa_scurvescan/test_20230905_115419_/injection_scan/' #"%s/%s/injection_scan/"%(options.odir, options_dut)
folders = glob.glob(odir+"run_*/")
print(folders)
df_ = []
for folder in folders:
    files = glob.glob(folder+"/*.root")
    print(files)
    for f in files[:]:
        print(f)
        df_summary = uproot3.open(f)['runsummary']['summary'].pandas.df()
        df_raw = uproot3.open(f)['unpacker_data']['hgcroc'].pandas.df()
        df_raw['trim_toa'] = df_summary.trim_toa.unique()[0]
        df_raw['injectedChannels'] = df_summary.injectedChannels.unique()[0]

        chan_uniq = df_summary.injectedChannels.unique()[0]
        df_raw = df_raw[df_raw.channel.isin([chan_uniq,chan_uniq+36])].copy()
        df_.append(df_raw)

print(df_)

#         toa_threshold_analyzer = analyzer.toa_scan_analyzer(odir=odir)
        
#         df_ = []
#         for folder in folders:
#                 files = glob.glob(folder+"/*.root")
#                 for f in files[:]:
#                         df_summary = uproot3.open(f)['runsummary']['summary'].pandas.df()
#                         df_.append(df_summary)
#         toa_threshold_analyzer.data = pandas.concat(df_)
#         toa_threshold_analyzer.makePlot_calib(config_ns_charge='pC', thres=0.95)


# class tot_scan_analyzer(analyzer):

#     def erfunc(self,z,a,b):
#     	return b*scipy.special.erfc(z-a)

#     def fit(self,x,y,p):
#         try:
#             args, cov = scipy.optimize.curve_fit(self.erfunc,x,y,p0=p)
#             return args
#         except:
#             print("Fit cannot be found")
#             return p

#     def erfunc_trim(self,z,a,b):
#         return b*scipy.special.erfc(a-z)


#     def fit_trim(self,x,y,p):
#         try:
#             args, cov = scipy.optimize.curve_fit(self.erfunc_trim,x,y,p0 = p)
#             return args
#         except:
#             print("Fit cannot be found")
#             return p

    
#     ### added May 2023, input from Jose: 
    
#     def makePlot_calib_for_MaxADC(self,adc_min=950,suffix=""):
#         nchip = len( self.data.groupby('chip').nunique() )        
#         data = self.data[['chip','channel','half','channeltype','Calib', 'gain', 'adc','injectedChannels']].copy()
#         inj_chan =data.injectedChannels.unique()

#         for chip in range(nchip):
#             # plt.figure(1)
#             fig, axs = plt.subplots(2,2,figsize=(15,10),sharey = False,constrained_layout = True)
#             min_calib = []
#             channels_tot = []
#             for chan in inj_chan:
#                 for half in range(2):
#                     ax = axs[0,0] if half == 0 else axs[0,1]
#                     # ax = axs[half]                   
#                     sel = data.chip == chip
#                     sel &= data.channel == chan
#                     sel &= data.channeltype == 0
#                     sel &= data.half == half
#                     sel &= data.injectedChannels == chan
#                     sel &= data.adc >= adc_min
#                     sel &= data.adc < 1023
#                     df_sel = data[sel]
#                     if len(df_sel.Calib) > 0:
#                         channels_tot = np.append(channels_tot,chan+(36*half))
#                         min_calib = np.append(min_calib,np.min(df_sel.Calib))
#                     prof = df_sel.groupby("Calib")["adc"].std()
#                     x_rms = prof.index
#                     y_rms = prof.values
#                     ax.plot(df_sel.Calib,df_sel.adc,".-", label = "ch%i" %(chan+(36*half)))
#                     ax.set_xlabel("Calib dac 2V5")
#                     ax.set_ylabel("ADC")
#                     ax.legend(ncol=3, loc = "lower right",fontsize=8)

#                     ax = axs[1,0] if half == 0 else axs[1,1]
#                     ax.plot(x_rms, y_rms,".")
#                     ax.set_xlabel("Calib dac 2V5")
#                     ax.set_ylabel("ADC rms")
            
#             calib_MaxADC = round(np.mean(min_calib))
#             plt.savefig("%s/0_calib2V5_%i_vs_%iadc_chip%d_%s.png"%(self.odir,calib_MaxADC,adc_min,chip,suffix))

#         return calib_MaxADC

#     def makePlot(self,suffix="",preffix="1"):
#         nchip = len( self.data.groupby('chip').nunique() )        
#         if suffix == "noise":
#             data = self.data[['chip','channel','Tot_vref','tot_efficiency','injectedChannels']].copy()
#             data['half'] = data.apply(lambda x: 0 if x.channel<36 # first half 
#                                     else 1, axis=1)
#         else:
#             data = self.data[['chip','channel','half', 'Tot_vref', 'tot','injectedChannels']].copy()
#         tot_vrefs = data.Tot_vref.unique()
#         inj_chan =data.injectedChannels.unique()
#         halves = data.half.unique()
#         for chip in range(nchip):
#             fig, axs = plt.subplots(1,2,figsize=(15,10),sharey = False,constrained_layout = True)
#             for chan in inj_chan:
#                 ch = chan
#                 for half in halves:
#                     ax = axs[0] if half == 0 else axs[1]
#                     sel = data.chip == chip
#                     if suffix == "noise":
#                         sel &= data.channel == ch+(36*half)
#                     else:
#                         sel &= data.channel == ch
#                     sel &= data.half == half
#                     sel &= data.injectedChannels == chan
#                     if suffix == "noise":
#                         sel &= data.tot_efficiency > 0
#                     else:
#                         sel &= data.tot > 0
#                     df_sel = data[sel]
#                     if suffix == "noise":
#                         prof = df_sel.groupby("Tot_vref")["tot_efficiency"].median()
#                     else:
#                         prof = df_sel.groupby("Tot_vref")["tot"].median()
#                     try:
#                         args = int(prof.index.max()) #before min
#                         # args = int(df_sel.Tot_vref.max()) #before min
#                         # args = prof.index[np.argmin(prof.values)]
#                     except:
#                         continue
#                     ax.plot(prof.index,prof.values,".-", label = "ch%i (%i)" %(ch+(36*half),args))
#                     # ax.plot(df_sel.Tot_vref,df_sel.tot_median,".-", label = "ch%i (%i)" %(ch,args))
#                     if suffix == "noise":
#                         ax.set_ylabel("tot efficiency")
#                     else:
#                         ax.set_ylabel("tot")
#                     ax.set_xlabel("Tot_vref")
#                     ax.legend(ncol=3, loc = "lower right",fontsize=8)
                            
#             plt.savefig("%s/%s_tot_thr_chip%d_%s.png"%(self.odir,preffix,chip,suffix))

#     def determineTot_vref(self,suffix="",correction_totvref=0):
#         nchip = len( self.data.groupby('chip').nunique() )
#         if suffix == "noise":
#             data = self.data[['chip','channel','Tot_vref','tot_efficiency','injectedChannels']].copy()
#             data['half'] = data.apply(lambda x: 0 if x.channel<36 # first half 
#                                     else 1, axis=1)
#         else:
#             data = self.data[['chip','channel','half', 'Tot_vref', 'tot','injectedChannels']].copy()
#         inj_chan =self.data.injectedChannels.unique()
#         halves = data.half.unique()
#         nestedConf = nested_dict()
#         yaml_dict = {}
#         rockeys = []
#         with open("%s/initial_full_config.yaml"%(self.odir)) as fin:
#             initconfig = yaml.safe_load(fin)
#             for key in initconfig.keys():
#                 if key.find('roc')==0:
#                     rockeys.append(key)
#             rockeys.sort()

#         for chip in range(nchip):
#             if chip<len(rockeys):
#                 chip_key_name = rockeys[chip]
#                 yaml_dict[chip_key_name] = {
#                 'sc' : {
#                 'ReferenceVoltage' : { 
#                 }
#                 }
#                 }
#                 mean_0 = []
#                 mean_1 = []
#                 for chan in inj_chan:
#                     for half in halves:
#                         sel = data.chip == chip
#                         if suffix == "noise":
#                             sel &= data.channel == chan + (36*half)
#                             sel &= data.tot_efficiency > 0
#                         else:
#                             sel &= data.tot > 0 # before 400
#                             sel &= data.channel == chan
#                         sel &= data.half == half
#                         sel &= data.injectedChannels == chan
#                         df_sel = data[sel]
#                         if suffix == "noise":
#                             prof = df_sel.groupby("Tot_vref")["tot_efficiency"].sum()
#                             tot_efficiency_max = prof.values.max()
#                             sel &= data.tot_efficiency == tot_efficiency_max
#                             df_sel = data[sel]
#                             prof = df_sel.groupby("Tot_vref")["tot_efficiency"].sum()
#                         else:
#                             prof = df_sel.groupby("Tot_vref")["tot"].median()
#                         try:
#                             args = int(prof.index.max()) #before min
#                             # args = prof.index[np.argmin(prof.values)]
#                         except:
#                             args = 500
#                             continue
#                         # if ch < 36:
#                         if half == 0:
#                             mean_0.append(args)
#                         else:
#                             mean_1.append(args)
#                 if len(mean_0)>0:
#                     mean = int(1.0*sum(mean_0)/len(mean_0))
#                     print("Tot_Vref for half0 is %i" %mean)
#                     yaml_dict[chip_key_name]['sc']['ReferenceVoltage'][0] = { 'Tot_vref' : mean - correction_totvref }
#                     nestedConf[chip_key_name]['sc']['ReferenceVoltage'][0] = { 'Tot_vref' : mean - correction_totvref}
#                 else:
#                     print("WARNING : optimised Tot_vref will not be saved for half 0 of ROC %d"%(chip))
#                 if len(mean_1)>0:
#                     mean = int(1.0*sum(mean_1)/len(mean_1))
#                     print("Tot_Vref for half1 is %i" %mean)
#                     yaml_dict[chip_key_name]['sc']['ReferenceVoltage'][1] = { 'Tot_vref' : mean - correction_totvref}
#                     nestedConf[chip_key_name]['sc']['ReferenceVoltage'][1] = { 'Tot_vref' : mean - correction_totvref}
#                 else:
#                     print("WARNING : optimised Tot_vref will not be saved for half 1 of ROC %d"%(chip))
#             else :
#                 print("WARNING : optimised Tot_vref will not be saved for ROC %d"%(chip))

#         if suffix == "noise":
#             with open(self.odir+'/tot_vref_noise+{}.yaml'.format(correction_totvref),'w') as fout:
#                 yaml.dump(yaml_dict,fout)
#         else:
#             with open(self.odir+'/tot_vref.yaml','w') as fout:
#                 yaml.dump(yaml_dict,fout)

#         return nestedConf

#     def makePlot_trim(self, preffix="2"):
#         nchip = len( self.data.groupby('chip').nunique() )        
#         data = self.data[['chip','channel', 'half','trim_tot','tot','injectedChannels']].copy()
#         trim_tots = data.trim_tot.unique()
#         inj_chan =data.injectedChannels.unique()
#         halves = data.half.unique()
#         for chip in range(nchip):
#             fig, axs = plt.subplots(1,2, figsize=(15,8))
#             for chan in inj_chan:
#                 for half in halves:
#                     ax = axs[0] if half == 0 else axs[1]
#                     sel = data.chip == chip
#                     sel &= data.channel == chan
#                     sel &= data.half == half
#                     sel &= data.injectedChannels == chan
#                     sel &= data.tot > 0
#                     df_sel = data[sel]
#                     prof = df_sel.groupby("trim_tot")["tot"].median()
#                     try:
#                         args = int(prof.index.min()) #before min
#                         # args = prof.index[np.max(np.where(prof.values==-1))]  ########## new unpacker !!!!!!!!!!!!
#                         success = 1
#                     except:
#                         args = 0
#                         success = 0
#                     ax.plot(prof.index,prof.values,".-",label="ch%i (%i, %i)" %(chan+(36*half),args,success))
#                     ax.set_ylabel("tot")
#                     ax.set_xlabel("trim_tot")
#                     ax.legend(ncol=3,loc="lower right",fontsize=10)
#             plt.savefig("%s/%s_trim_tot_thr_chip%d.png"%(self.odir,preffix,chip))
    
#     def determineTot_trim(self,correction_tottrim=0):
#         nchip = len( self.data.groupby('chip').nunique() )
#         data = self.data[['chip','channel', 'half', 'injectedChannels','trim_tot', 'tot']].copy()
#         inj_chan =self.data.injectedChannels.unique()
#         halves = data.half.unique()
#         yaml_dict = {}
#         rockeys = []
#         with open("%s/initial_full_config.yaml"%(self.odir)) as fin:
#             initconfig = yaml.safe_load(fin)
#             for key in initconfig.keys():
#                 if key.find('roc')==0:
#                     rockeys.append(key)
#             rockeys.sort()

#         trim_tots = data.trim_tot.unique()
#         for chip in range(nchip):
#             if chip<len(rockeys):
#                 chip_key_name = rockeys[chip]
#                 yaml_dict[chip_key_name] = {
#                 'sc' : {
#                 'ch' : { 
#                 }
#                 }
#                 }
#                 for chan in inj_chan:
#                     for half in halves:
#                         sel = data.chip == chip
#                         sel &= data.channel == chan
#                         sel &= data.half == half
#                         sel &= data.injectedChannels == chan
#                         sel &= data.tot > 0 #before min
#                         df_sel = data[sel]
#                         prof = df_sel.groupby("trim_tot")["tot"].median()
#                         try:
#                             # alpha = prof.index[np.max(np.where(prof.values==-1))] ############# new unpacker !!!!!!!!!!!
#                             alpha = int(prof.index.min()) + correction_tottrim  ###, PLUS SIMPLE !!!!!!!!!
#                         except:
#                             alpha = 0
#                         if alpha < 0:
#                             alpha = 0
#                         elif alpha > 63:
#                             alpha = 63
#                         print(chan,alpha)
#                         yaml_dict[chip_key_name]['sc']['ch'][int(chan+(36*half))] = { 'trim_tot' : int( alpha ) }
#                         # yaml_dict[chip_key_name]['sc']['ch'][int(ch)] = { 'trim_tot' : int( alpha ) }
#             else :
#                 print("WARNING : optimised trim_tot will not be saved for ROC %d"%(chip))
#         print(yaml_dict)
#         with open(self.odir+'/trimmed_tot.yaml','w') as fout:
#                 yaml.dump(yaml_dict,fout)

#         return yaml_dict

#     def makePlot_calib(self,NEvents=500,suffix="",config_ns_charge=None):
#         nchip = len( self.data.groupby('chip').nunique() )        
#         data = self.data[['chip','channel','half','Calib', 'gain', 'tot','injectedChannels']].copy()
#         Calib_dac_2V5s = data.Calib.unique()
#         halves = data.half.unique()
#         gain_val = data.gain.unique()
#         inj_chan =data.injectedChannels.unique()
#         if config_ns_charge != None:
#             if config_ns_charge == 'fC':
#                 conv_val = 1000
#             else:
#                 conv_val = 1
#             data["charge"] = conv_val * ((1.6486* data['Calib'])/4095 + 0.0189)*((3*(1 - data["gain"])) + data["gain"]*120)

#         for chip in range(nchip):
#             # plt.figure(1)
#             fig, axs = plt.subplots(2,2,figsize=(15,10),sharey = False,constrained_layout = True)
#             min_charge = []
#             channels_tot = []
#             for chan in inj_chan:
#                 ch = chan
#                 for half in halves:
#                     calib_vals = []
#                     tot_counts = []
#                     tot_std = []
#                     save_min_charge = 0
#                     ax = axs[0,0] if half==0 else axs[0,1]
#                     for calib_val in Calib_dac_2V5s:
#                         charge_val = conv_val * ((1.6486* calib_val)/4095 + 0.0189)*((3*(1 - gain_val[0])) + gain_val[0]*120)
#                         sel = data.chip == chip
#                         sel &= data.channel == ch
#                         sel &= data.half == half
#                         sel &= data.injectedChannels == chan
#                         sel &= data.Calib == calib_val
#                         sel &= data.tot > 0
#                         df_sel = data[sel]
#                         df_sel_noise = data[sel]
#                         prof = df_sel.groupby("Calib")["tot"].std()
#                         if config_ns_charge == None:
#                             calib_vals = np.append(calib_vals,calib_val)
#                         else:
#                             calib_vals = np.append(calib_vals,charge_val)
#                         if len(df_sel.tot) > 0:
#                             tot_counts = np.append(tot_counts,len(df_sel.tot))
#                         else:
#                             tot_counts = np.append(tot_counts,0)
#                         if len(df_sel_noise.tot) > 0:
#                             # tot_std = np.append(tot_std,np.mean(df_sel_noise.tot_stdd))
#                             tot_std = np.append(tot_std,np.mean(prof.values))
#                         else:
#                             tot_std = np.append(tot_std,0)
#                         if len(df_sel.tot) > NEvents and save_min_charge == 0: #Before len tot > 0 (For 1000 events)
#                             channels_tot = np.append(channels_tot,ch+(36*half))
#                             if config_ns_charge != None:
#                                 min_charge = np.append(min_charge,np.min(df_sel.charge.unique()))
#                             else:
#                                 min_charge = np.append(min_charge,np.min(df_sel.calib_val))
#                             save_min_charge = 1
#                     ax.plot(calib_vals,tot_counts,".-", label = "ch%i" %(ch+(36*half)))
#                     if config_ns_charge != None:
#                         ax.set_xlabel("charge [{}]".format(config_ns_charge))
#                     else:
#                         ax.set_xlabel("Calib dac 2V5")
#                     ax.set_ylabel("tot counts")
#                     ax.legend(ncol=3, loc = "lower right",fontsize=8)

#                     ax = axs[1,0] if half==0 else axs[1,1]
#                     ax.plot(calib_vals, tot_std,".")
#                     if config_ns_charge != None:
#                         ax.set_xlabel("charge [{}]".format(config_ns_charge))
#                     else:
#                         ax.set_xlabel("Calib dac 2V5")
#                     ax.set_ylabel("tot noise")
                    
#             plt.savefig("%s/4_tot_vs_charge_chip%d_%s.png"%(self.odir,chip,suffix))

#             # plt.figure(2)
#             plt.figure(figsize = (12,5),facecolor='white')
#             plt.plot(channels_tot,min_charge,"o")
            
#             if config_ns_charge != None:
#                 plt.ylabel("charge [{}]".format(config_ns_charge), fontsize = 30)
#             else:
#                 plt.ylabel("Calib dac 2V5", fontsize = 30)
#             plt.xlabel("Channels", fontsize = 30)
#             plt.grid()
#             plt.tick_params(axis='x', labelsize=28)
#             plt.tick_params(axis='y', labelsize=28)
                    
#             plt.savefig("%s/4_channel_vs_mintot_chip%d_%s.png"%(self.odir,chip,suffix),bbox_inches='tight')
#             calib_dac_min = np.mean(min_charge)

#         return calib_dac_min
   
#     ### end Jose's input

# if __name__ == "__main__":

#     if len(sys.argv) == 3:
#         indir = sys.argv[1]
#         odir = sys.argv[2]

#         toa_threshold_analyzer = toa_threshold_scan_analyzer(odir=odir)
#         files = glob.glob(indir+"/toa_threshold_scan*.root")
#         print(files)

#         for f in files:
#             toa_threshold_analyzer.add(f)

#         toa_threshold_analyzer.mergeData()
#         toa_threshold_analyzer.makePlots()

#     else:
#         print("No argument given")
