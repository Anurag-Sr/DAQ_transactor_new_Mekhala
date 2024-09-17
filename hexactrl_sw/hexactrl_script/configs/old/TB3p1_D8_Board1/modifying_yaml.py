import yaml

with open('sipm_roc0_onbackup0_gainconv4.yaml', 'r') as file:
    input_configFile = yaml.safe_load(file)

#print(input_configFile['roc_s0']['sc']['calib'][0])

for ch_type in ['calib','cm','ch']:
    for ch in input_configFile['roc_s0']['sc'][ch_type].keys():   
        input_configFile['roc_s0']['sc'][ch_type][ch]['trim_toa'] = 31
        input_configFile['roc_s0']['sc'][ch_type][ch]['trim_tot'] = 31
        
#print(input_configFile['roc_s0']['sc']['ch'][0]) 

with open('sipm_roc0_onbackup0_gainconv4_trimtoa_trimtot_31_channelwise.yml', 'w') as outfile:
    yaml.dump(input_configFile, outfile, default_flow_style=False)      
