from level0.analyzer import *
import yaml
import glob
from scipy.optimize import curve_fit
from nested_dict import nested_dict
import more_itertools as mit

class injection_scan_analyzer(analyzer):

    def fit(self,sel):
        x0 = self.data[sel]['Calib']
        y0 = self.data[sel]['adc_mean']
        if len(x0)>2:
            popt, pcov = curve_fit(lambda x,a,b:a*x*500/4096+b, x0, y0, p0=[0.6,y0.min()])
        else:
            popt = [1,0]

        return popt[0],popt[1]
    
    def adcrange_from_residuals(self,sel,alpha,beta):
        tmp = self.data[sel].copy()
        tmp = tmp[['chip','channel','Calib','adc_mean']].copy()
        tmp.sort_values(by=['adc_mean'],ignore_index=True)
        tmp['res'] = tmp.apply(lambda x: (x.adc_mean-(x.Calib*alpha*500/4096+beta))/(x.Calib*alpha*500/4096+beta) ,axis=1)
        tmp['fC'] = tmp.apply(lambda x: x.Calib*500/4096, axis=1)
        tmp = tmp.sort_values(by=['Calib'],ignore_index=True)

        alist = list(tmp[ tmp['res']<-.02 ].index)
        alist = [list(group) for group in mit.consecutive_groups(alist)]

        first=[]
        for i in alist:
            if len(i)>2:
                first=i
                break

        adcrange = tmp.iloc[first[0]-1]
        return adcrange["Calib"]*500/4096

    def makePlots(self):
        nchip = len( self.data.groupby('chip').nunique() )        
        cmap = cm.get_cmap('viridis')

        sel_data = self.data[['chip','channel','channeltype','Calib','adc_mean','toa_mean','tot_mean','toa_efficiency','tot_efficiency','injectedChannels']].copy()
        sel_data = sel_data[ (sel_data['channel'].isin(sel_data['injectedChannels'])) & (sel_data['channeltype']==0) ]
        sel_data = sel_data.sort_values(by=['Calib'],ignore_index=True)

        
        # offenders = sel_data[ (sel_data.toa_median > 0) & (sel_data.Calib < 800) ]
        # print(
        #     offenders[ ['chip', 'channel'] ].drop_duplicates().sort_values( by=['chip', 'channel'], ignore_index=True)
        # )
        
        
        print(sel_data.describe())
        for chip in sel_data.groupby('chip')['chip'].mean():
            ###########################################################
            ## let's plot ADC vs. injection for all injected channels: 
            ###########################################################
            chip_data = sel_data[ sel_data['chip']==chip ]

            varlist ={
                'adc':'adc_mean',
                'toa':'toa_mean',
                'tot':'tot_mean',
                'eff_toa':'toa_efficiency',
                'eff_tot':'tot_efficiency'
            }
            
            for var in varlist:
                fig, axes = plt.subplots(1,2,figsize=(16,9),sharey=False)
                
                axes[0].set_ylabel(f'{var.upper()} [ADC counts]')

                for ax in axes:
                    # ax.set_yscale('log')                
                    ax.set_xlabel(r'CalibDAC')
                    ax.xaxis.grid(True)

                ax=axes[0]
                ax.set_title(f'chip{chip}, first half')
                chanColor=0
                for injectedChannel in range(0, 36):                
                    half_data = chip_data[ (chip_data['channel']==injectedChannel) ].copy()
                    if len(half_data):
                        ax.plot( half_data['Calib'], half_data[varlist[var]], color=cmap(chanColor/36.), marker='o',label="chan%d"%injectedChannel)
                        chanColor=chanColor+8
                ax.legend(loc='lower right')
                
                ax=axes[1]
                ax.set_title(f'chip{chip}, second half')
                chanColor=0
                for injectedChannel in range(36, 72):
                    half_data = chip_data[ (chip_data['channel']==injectedChannel)  ].copy()
                    if len(half_data):
                        ax.plot( half_data['Calib'], half_data[varlist[var]], color=cmap(chanColor/36.), marker='o',label="chan%d"%injectedChannel)
                        chanColor=chanColor+8
                ax.legend(loc='lower right')
                
                plt.savefig(f'{self.odir}/{var}_injection_scan_chip{chip}.png', format='png', bbox_inches='tight') 
                
                plt.close()

        return

    def adcCalib(self):
        data = self.data[['chip','channel','channeltype','Calib','adc_mean','injectedChannels']].copy()
        all_rows=[]
        for chip in data['chip'].unique():
            for channel in data['injectedChannels'].unique():
                sel = data.chip==int(chip)
                sel &= data.channeltype==0
                sel &= data.channel==int(channel)
                sel &= data.injectedChannels==int(channel)
                sel &= data.adc_mean<500
                sel &= data.Calib>0
                alpha,beta = self.fit(sel)
                adcrange = 0
                if alpha!=1 and alpha>1e-3 and beta!=0:
                    sel = data.chip==int(chip)
                    sel &= data.channeltype==0
                    sel &= data.channel==int(channel)
                    sel &= data.injectedChannels==int(channel)
                    adcrange = self.adcrange_from_residuals(sel,alpha,beta)
                    # adcrange = min(adcrange,float((1023-beta)/alpha))
                adc_to_fC = float(1/alpha)
                pedestal = float(beta)
                all_rows.append([chip,channel,0,adc_to_fC,pedestal,adcrange])
        calib = pd.DataFrame(all_rows, columns=['chip','channel','channeltype','adc_to_fC','pedestal','range'])
        # print(calib)
        calibfile = calib.to_hdf(f'{self.odir}/adc_calib.h5', key='adc_calib', mode='w')
        return

    def addSummary(self):
            
        sel_data = self.data[['chip','channel','channeltype','Calib','adc_median','toa_median','tot_median','toa_efficiency','tot_efficiency','injectedChannels']].copy()
        sel_data = sel_data[ (sel_data['channel'].isin(sel_data['injectedChannels'])) & (sel_data['channeltype']==0) ]
        sel_data = sel_data.sort_values(by=['Calib'],ignore_index=True)

        # add summary information
        self._summary['bad_channels_adc'] = {
            'rejection criteria': 'ADC curve is flat (num. points w/ (delta<1) > 12)'
        }
        self._summary['bad_channels_toa'] = {
            'rejection criteria': 'TOA curve is flat (num. points w/ (delta<1) > 12)'
        }
        self._summary['bad_channels_tot'] = {
            'rejection criteria': 'TOT curve is flat (num. points w/ (delta<1) > 12)'
        }
        self._summary['bad_channels_max_adc'] = {
            'rejection criteria': 'Max ADC < 500'
        }
        
        nchip = len( self.data.groupby('chip').nunique() )        
        for chip in range(nchip):
            df = sel_data.query('chip==%d' % chip)
            df = df.query('channeltype==0')
            ## eventhough we were injecting only in normal channels, let's keep the same format for bad channels as in other analysis script (e.g.: level0/pedestal_run_analysis.py)
            badchns_adc = { 'ch'    : [] , 
                            'cm'    : [] ,
                            'calib' : [] } 
            badchns_toa = {  'ch'    : [] , 
                             'cm'    : [] ,
                             'calib' : [] }
            badchns_tot = {  'ch'    : [] , 
                             'cm'    : [] ,
                             'calib' : [] }
            badchns_max_adc = {'ch'  : [] , 
                             'cm'    : [] ,
                             'calib' : [] }
            inj_adc_saturation = {'ch'  : [] , 
                                  'cm'    : [] ,
                                  'calib' : [] }
            toa_threshold = {
                'ch': {}
            }
            tot_threshold = {
                'ch': {}
            }

            all_channel_max_adc = []
            for ch in df.groupby('injectedChannels')['injectedChannels'].mean():
                df_chn = df.query('channel==%s & injectedChannels==%s' % (ch,ch)).sort_values('Calib')
                flat_points_adc = (df_chn[ df_chn['adc_median']<1023 ]['adc_median'].astype('float').diff().abs() < 1).sum()
                # print(ch, '\n', df_chn['adc_median'].astype('float').diff(), flat_points_adc)
                if flat_points_adc > 12:
                    badchns_adc['ch'].append(ch)

                with_toa = df_chn[ df_chn['toa_median']>0 ]
                if len(with_toa)==0:
                    badchns_toa['ch'].append(ch)
                elif int(with_toa[with_toa['Calib']==with_toa['Calib'].min()]['toa_median']) == int(with_toa[with_toa['Calib']==with_toa['Calib'].max()]['toa_median']):
                    badchns_toa['ch'].append(ch)
                # (df_chn[ df_chn['toa_median']>0 ]['toa_median'].astype('float').diff().abs() < 1).sum()
                # # print(ch, '\n', df_chn['toa_median'].astype('float').diff(), flat_points_toa)
                # if flat_points_toa > 12 or len(df_chn[ df_chn['toa_median']>0 ])<10:
                #     badchns_toa['ch'].append(ch)

                
                with_tot = df_chn[ df_chn['tot_median']>0 ]
                if len(with_tot)==0:
                    badchns_tot['ch'].append(ch)
                elif int(with_tot[with_tot['Calib']==with_tot['Calib'].min()]['tot_median']) == int(with_tot[with_tot['Calib']==with_tot['Calib'].max()]['tot_median']):
                    badchns_tot['ch'].append(ch)
                # flat_points_tot = (df_chn[ df_chn['tot_median']>0 ]['tot_median'].astype('float').diff().abs() < 1).sum()
                # # print(ch, '\n', df_chn['tot_median'].astype('float').diff(), flat_points_tot)
                # if flat_points_tot > 12 or len(df_chn[ df_chn['tot_median']>0 ])<10:
                #     badchns_tot['ch'].append(ch)

                # print(chip,ch,flat_points_adc,flat_points_toa,len(df_chn[ df_chn['toa_median']>0 ]),flat_points_tot,len(df_chn[ df_chn['tot_median']>0 ]))
                max_adc = (df_chn['adc_median']).max()
                all_channel_max_adc.append(max_adc)

                non_saturated = df_chn.query('adc_median<1023')
                if len(non_saturated)>0:
                    inj_adc_saturation['ch'].append( {ch:int(non_saturated['Calib'].max())} )
                # print (ch, '\n', max_adc)
                if max_adc < 1000:
                    badchns_max_adc['ch'].append(ch)
                    
                sel = df_chn['toa_efficiency']>0.5
                if sel.any():
                    toa_threshold['ch'][ch] = int(df_chn[sel].iloc[0]['Calib'])
                else: toa_threshold['ch'][ch] = 'nan'

                sel = df_chn['tot_efficiency']>0.5
                if sel.any():
                    tot_threshold['ch'][ch] = int(df_chn[sel].iloc[0]['Calib'])
                else: tot_threshold['ch'][ch] = 'nan'
            
            #print ("array ", all_channel_max_adc)
            #print ("lenght_array ", len(all_channel_max_adc))
            mean_max_adc = np.mean(all_channel_max_adc)
            std_max_adc = np.std(all_channel_max_adc)
            # print ("mean of max adc = ", mean_max_adc, "std of max adc = " , std_max_adc)

            self._summary['stats'] = {
                'mean and std of max adc': ''
            }
            self._summary['stats']['chip%d' % chip] = {
                'mean_max_adc': float(mean_max_adc),
                'std_max_adc': float(std_max_adc)
            }
            
            self._summary['bad_channels_adc']['chip%d' % chip] = badchns_adc
            self._summary['bad_channels_adc']['chip%d' % chip]['total'] = len(badchns_adc['ch']) + len(badchns_adc['cm']) + len(badchns_adc['calib'])

            self._summary['bad_channels_toa']['chip%d' % chip] = badchns_toa
            self._summary['bad_channels_toa']['chip%d' % chip]['total'] = len(badchns_toa['ch']) + len(badchns_toa['cm']) + len(badchns_toa['calib'])

            self._summary['bad_channels_tot']['chip%d' % chip] = badchns_tot
            self._summary['bad_channels_tot']['chip%d' % chip]['total'] = len(badchns_tot['ch']) + len(badchns_tot['cm']) + len(badchns_tot['calib'])

            self._summary['bad_channels_max_adc']['chip%d' % chip] = badchns_max_adc
            self._summary['bad_channels_max_adc']['chip%d' % chip]['total'] = len(badchns_max_adc['ch']) + len(badchns_max_adc['cm']) + len(badchns_max_adc['calib'])

            self._summary['inj_saturation_adc']['chip%d' % chip] = inj_adc_saturation

            self._summary['toa_threshold']['chip%d' % chip] = toa_threshold
            self._summary['tot_threshold']['chip%d' % chip] = tot_threshold

        return

if __name__ == "__main__":

    if len(sys.argv) == 3:
        indir = sys.argv[1]
        odir = sys.argv[2]
        
        ana = injection_scan_analyzer(odir=odir)
        files = glob.glob(indir+"/*.root")
        
        for f in files:
            ana.add(f)
        
        ana.mergeData()
        # ana.makePlots()
        # ana.addSummary()
        # ana.writeSummary()
        ana.adcCalib()

    else:
        print("No argument given")
