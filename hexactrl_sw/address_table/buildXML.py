import os
import glob
import re

class label_to_addresses:
    
    def __init__(self,aid):
        self.data = { 'id':aid,
                      'link_address':0x0,
                      'bram_address':0x0
        }

    def __eq__(self, other): 
        if(self.data['id'] == other.data['id']): 
            return True
        else: 
            return False

links_and_brams=[]
lkey = 'link_capture'
bkey = 'bram'


labels = glob.glob('/sys/class/uio/uio*/device/of_node/label')
fc_address=0
fc_recv_address=0
self_trigger_address=0
for label in labels:
    print(label)
    with open(label) as fin:
        aname = fin.read()
        if aname.find(lkey)==0:
            aid = re.search(r'daq',aname)
            if( aid ):
                aid=aid.group()
            else:
                aid = re.search(r'trg',aname).group()
            print(aid)
            lta = label_to_addresses(aid)
            if not lta in links_and_brams:
                links_and_brams.append(lta)
            
            link_address_file = glob.glob( re.split('device',label)[0] )[0]+'/maps/map0/addr'
            print(link_address_file)
            with open(link_address_file) as faddr:
                links_and_brams[links_and_brams.index(lta)].data['link_address'] = int( faddr.read(), 16 )
                

        elif aname.find(bkey)==0:
            aid = re.search(r'daq',aname)
            if( aid ):
                aid=aid.group()
            else:
                aid = re.search(r'trg',aname).group()
            # print(aid)
            # aid = re.search(r'\d',aname).group()[0]
            print(aid)
            lta = label_to_addresses(aid)
            if not lta in links_and_brams:
                links_and_brams.append(lta)
            
            bram_address_file = glob.glob( re.split('device',label)[0] )[0]+'/maps/map0/addr'
            print(bram_address_file)
            with open(bram_address_file) as faddr:
                links_and_brams[links_and_brams.index(lta)].data['bram_address'] = int( faddr.read(), 16 )

        elif aname.find("fastcontrol_recv")==0:
            fc_recv_address_file = glob.glob( re.split('device',label)[0] )[0]+'/maps/map0/addr'
            print(fc_recv_address_file)
            with open(fc_recv_address_file) as faddr:
                fc_recv_address = int( faddr.read(), 16 )

        elif aname.find("fastcontrol")==0:
            fc_address_file = glob.glob( re.split('device',label)[0] )[0]+'/maps/map0/addr'
            print(fc_address_file)
            with open(fc_address_file) as faddr:
                fc_address = int( faddr.read(), 16 )

        elif aname.find("self_trigger")==0:
            self_trigger_file = glob.glob( re.split('device',label)[0] )[0]+'/maps/map0/addr'
            print(self_trigger_file)
            with open(self_trigger_file) as faddr:
                self_trigger_address = int( faddr.read(), 16 )


for i in links_and_brams:
    print(i.data)

with open('address_table/fw_block_addresses.xml','w') as fout:
    fout.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
    fout.write('<node id="TOP">\n')
    fout.write('<node id="fastcontrol_axi"\t module="file://modules/fastcontrol_axi.xml"\t  address="'+hex(fc_address)+'"/>\n')
    fout.write('<node id="fastcontrol_recv_axi"\t\t module="file://modules/fastcontrol_recv_axi.xml"\t address="'+hex(fc_recv_address)+'"/>\n')
    fout.write('<node id="self_trigger"\t module="file://modules/self_trigger.xml" address="'+hex(self_trigger_address)+'"/>\n')
    for lab in links_and_brams:
        fout.write('<node id="link_capture_'+str(lab.data['id'])+'"\t module="file://modules/link_capture_axi.xml"\t  address="'+hex(lab.data['link_address'])+'"/>\n')
        fout.write('<node id="axi_bram_ctrl_'+str(lab.data['id'])+'"\t module="file://modules/axi_bram_ctrl.xml"\t  address="'+hex(lab.data['bram_address'])+'"/>\n')
    fout.write('</node>')
