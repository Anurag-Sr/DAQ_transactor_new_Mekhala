import pandas as pd
import csv
import re
import math
import numpy as np

data = pd.read_csv("dataPd.csv")

dacbs = pd.unique(data['dacb'])
trim_invs = sorted(list(map(lambda x: int(x), filter(lambda x: re.fullmatch("[0-9]+",x), data.columns.to_list()))))
print ('dacbs',dacbs)
print ('trim_invs',trim_invs)

#for dacb in dacbs:
data['grad_trim_inv'] = 0.

for itrim in range(len(trim_invs)-1):
    trim_inv1 = trim_invs[itrim]
    trim_inv2 = trim_invs[itrim+1]
    
    if math.fabs(trim_inv1-trim_inv2)<1:
        raise Exception("Trim inv values are identical")
        
    if trim_inv1>trim_inv2:
        raise Exception("Trim inv values are not ordered properly")
    
    pedestal1 = data[str(trim_inv1)]
    pedestal2 = data[str(trim_inv2)]

    grad = (pedestal2-pedestal1)/(trim_inv2-trim_inv1)
    #data['grad_trim_inv_'+str(itrim)] = grad
    data['grad_trim_inv'] += grad
data['grad_trim_inv'] /= len(trim_invs)-1

grad_dacb = []
for idacb in range(len(dacbs)-1):
    dacb1 = dacbs[idacb]
    dacb2 = dacbs[idacb+1]
    
    if math.fabs(dacb1-dacb2)<1:
        raise Exception("Dacb values are identical")
        
    if dacb1>dacb2:
        raise Exception("Dacb values are not ordered properly")
        
        
    diff_pedestal_avg = 0.
    print (idacb,"="*50)
    for trim_inv in trim_invs:
        pedestal1 = data[data['dacb']==dacb1][str(trim_inv)].values
        pedestal2 = data[data['dacb']==dacb2][str(trim_inv)].values
    
        diff_pedestal_avg += (pedestal2-pedestal1)
    diff_pedestal_avg /= len(trim_invs)
    diff_pedestal_avg /= (dacb2-dacb1)
    
    grad_dacb.append(diff_pedestal_avg)
grad_dacb.append(grad_dacb[-1]) #copy last one for the end
grad_dacb = np.concatenate(grad_dacb,axis=0)

data['grad_dacb'] = grad_dacb


print (data)


data['good_channels'] = (data['grad_dacb']>0.1) & (data[str(trim_invs[-1])]>10.)

print (data)


print (data[data['dacb']==0]['0'])

target = 250.  
ref_dacb = 16
ref_trim_inv = 32

for half in range(2):
    for channelPerHalf in range(39):
        channel = channelPerHalf+half*39
        #ref_pedestal = 
        

