import uhal
import yaml

class trigSource:
    def __init__(self, ipbushw, idx):
        self.node = ipbushw.getNode("input"+str(idx))
        
    def force_enable(self, setting):
        self.node.getNode("force_enable").write(setting)
        self.node.getClient().dispatch()

    def force_value(self, value):
        self.node.getNode("force_value").write(value)
        self.node.getClient().dispatch()

    def read_value(self):
        value = self.node.getNode("value").read()
        self.node.getClient().dispatch()
        return value.value()
    

class trigDestination:
    def __init__(self, ipbushw, idx):
        self.node = ipbushw.getNode("output"+str(idx))

    def select_source(self, s_idx):
        self.node.getNode("input_select").write(s_idx)
        self.node.getClient().dispatch()

    def read_source(self):
        s_idx = self.node.getNode("input_select").read()
        self.node.getClient().dispatch()
        return s_idx.value()
        
    def set_direction(self, value):
        self.node.getNode("direction").write(value)
        self.node.getClient().dispatch()
    
    def read_direction(self):
        value = self.node.getNode("direction").read()
        self.node.getClient().dispatch()
        return value.value()
    
    def force_enable(self, setting):
        self.node.getNode("force_enable").write(setting)
        self.node.getClient().dispatch()

    def force_value(self, value):
        self.node.getNode("force_value").write(value)
        self.node.getClient().dispatch()

    def read_value(self):
        value = self.node.getNode("value").read()
        self.node.getClient().dispatch()
        return value.value()
    


#=====================================test========================
class test_n_input:
    def __init__(self, ipbushw):
        self.node = ipbushw.getNode("N_INPUTS")

    def read_N_input(self):
        N_inputs = self.node.read()
        self.node.getClient().dispatch()
        return N_inputs.value()

class test_n_output:
    def __init__(self, ipbushw):
        self.node = ipbushw.getNode("N_OUTPUTS")

    def read_N_output(self):
        N_outputs = self.node.read()
        self.node.getClient().dispatch()
        return N_outputs.value()
#=============================================================

class trigger_xbar:
    def __init__(self, hwInterface=None, conFile=None):

        if hwInterface is None:
            uhal.setLogLevelTo(uhal.LogLevel.WARNING)
            self.manager = uhal.ConnectionManager()
            self.ipbushw = uhal.HwInterface(self.manager.getDevice("TOP"))
            self.baseNode = self.ipbushw.getNode("trigger_xbar")
        else:
            self.ipbushw = hwInterface
            self.baseNode = self.ipbushw.getNode("trigger_xbar")

        self.trigSources = []
        NInputs = 7
        for trigInput in range(NInputs):
            self.trigSources.append(trigSource(self.baseNode, trigInput))

        self.trigDestinations = []
        NOutputs = 9
        for trigOutput in range(NOutputs):
            self.trigDestinations.append(trigDestination(self.baseNode, trigOutput))

        #================set trigger_xbar.output_enable_bar===================
        self.baseNode.getNode("output_enable_bar").write(0)
        print("The value of output_enable_bar is now: ", self.baseNode.getNode("output_enable_bar").read())

        #=====================================================================


        if conFile is not None:
            self.config(conFile)
        

        #==========================test====================
        self.Ninputs = []
        self.Ninputs.append(test_n_input(self.baseNode))

        self.Noutputs = []
        self.Noutputs.append(test_n_output(self.baseNode))
         
        #=================================================




    def config(self, conFile):
        try:
            with open(conFile) as fin:
                cfgs = yaml.safe_load(fin)
        except FileNotFoundError:
            print("%s not found"%conFile)
        for lbl, cfg in cfgs.items():
            if "trigger_xbar" in lbl:
                for trigType in cfg:
                    for channel in cfg[trigType]:
                        #print("trigType:", trigType, "   ", channel)#===for debugging
                        if "destinations" in trigType:
                            for param, val in cfg[trigType][channel].items():
                                if "source" in param:
                                    #print("source: ", trigType, "  ", channel, " val: ", val, " param: ", param)#======for debugging
                                    self.trigDestinations[channel].select_source(val)
                                    #print("read source: ", self.trigDestinations[channel].read_source())#======for debugging
                                if "direction" in param:
                                    #print("direction: ", trigType, "  ", channel, " val: ", val, " param: ", param)#======for debugging
                                    self.trigDestinations[channel].set_direction(val)
                                    #print("read direction: ", self.trigDestinations[channel].read_direction())#======for debugging
                                if "force_enable" in param:
                                   self.trigDestinations[channel].force_enable(val)
                                elif "force_value" in param:
                                   self.trigDestinations[channel].force_value(val)
                        elif "sources" in trigType:
                            for param, val in cfg[trigType][channel].items():
                                if "force_enable" in param:
                                   self.trigSources[channel].force_enable(val)
                                elif "force_value" in param:
                                   self.trigSources[channel].force_value(val)

if __name__ == "__main__":
   from optparse import OptionParser
   parser = OptionParser()

   parser.add_option("-f", "--configFile", default="config/tbtesterv2_trigger_xbar.yaml",
                     action="store", dest="configFile",
                     help="Default yaml configuration file")
   parser.add_option("-t", "--test", default=False,
                     action="store", dest="runTest",
                     help="Write and read some registers as a test")
   (options, args) = parser.parse_args()

   uhal.setLogLevelTo(uhal.LogLevel.WARNING)
   manager = uhal.ConnectionManager("file:///opt/cms-hgcal-firmware/hgc-test-systems/active/uHAL_xml/connections.xml")
   ipbushw = uhal.HwInterface(manager.getDevice("TOP"))
   xbar = trigger_xbar(hwInterface=ipbushw,conFile=options.configFile)

   if options.runTest:
        #print("The source for trig dest. 4 is: "+str(xbar.trigDestinations[4].read_source()))
        #print("Now setting it to 5")
        print("=====================================================================")
        print("The source for trig dest. 0 is: "+str(xbar.trigDestinations[0].read_source()))
        print("The source for trig dest. 1 is: "+str(xbar.trigDestinations[1].read_source()))
        print("The source for trig dest. 2 is: "+str(xbar.trigDestinations[2].read_source()))
        print("The source for trig dest. 3 is: "+str(xbar.trigDestinations[3].read_source()))
        print("The source for trig dest. 4 is: "+str(xbar.trigDestinations[4].read_source()))
        print("The source for trig dest. 5 is: "+str(xbar.trigDestinations[5].read_source()))
        print("The source for trig dest. 6 is: "+str(xbar.trigDestinations[6].read_source()))
        print("The source for trig dest. 7 is: "+str(xbar.trigDestinations[7].read_source()))
        print("The source for trig dest. 8 is: "+str(xbar.trigDestinations[8].read_source()))        
       

        print("=====================================================================")
        print("The direction at trig dest. 0 is: "+str(xbar.trigDestinations[0].read_direction()))
        print("The direction at trig dest. 1 is: "+str(xbar.trigDestinations[1].read_direction()))
        print("The direction at trig dest. 2 is: "+str(xbar.trigDestinations[2].read_direction()))
        print("The direction at trig dest. 3 is: "+str(xbar.trigDestinations[3].read_direction()))
        print("The direction at trig dest. 4 is: "+str(xbar.trigDestinations[4].read_direction()))
        print("The direction at trig dest. 5 is: "+str(xbar.trigDestinations[5].read_direction()))
        print("The direction at trig dest. 6 is: "+str(xbar.trigDestinations[6].read_direction()))
        print("The direction at trig dest. 7 is: "+str(xbar.trigDestinations[7].read_direction()))
        print("The direction at trig dest. 8 is: "+str(xbar.trigDestinations[8].read_direction()))


        print("=====================================================================")
        print("The value at trig dest. 0 is: "+str(xbar.trigDestinations[0].read_value()))
        print("The value at trig dest. 1 is: "+str(xbar.trigDestinations[1].read_value()))
        print("The value at trig dest. 2 is: "+str(xbar.trigDestinations[2].read_value()))
        print("The value at trig dest. 3 is: "+str(xbar.trigDestinations[3].read_value()))
        print("The value at trig dest. 4 is: "+str(xbar.trigDestinations[4].read_value()))
        print("The value at trig dest. 5 is: "+str(xbar.trigDestinations[5].read_value()))
        print("The value at trig dest. 6 is: "+str(xbar.trigDestinations[6].read_value()))
        print("The value at trig dest. 7 is: "+str(xbar.trigDestinations[7].read_value()))
        print("The value at trig dest. 8 is: "+str(xbar.trigDestinations[8].read_value())) 


        print("=====================================================================")
        print("The value at trig source 0 is: "+str(xbar.trigSources[0].read_value()))
        print("The value at trig source 1 is: "+str(xbar.trigSources[1].read_value()))
        print("The value at trig source 2 is: "+str(xbar.trigSources[2].read_value()))
        print("The value at trig source 3 is: "+str(xbar.trigSources[3].read_value()))
        print("The value at trig source 4 is: "+str(xbar.trigSources[4].read_value()))
        print("The value at trig source 5 is: "+str(xbar.trigSources[5].read_value()))
        print("The value at trig source 6 is: "+str(xbar.trigSources[6].read_value()))


        print("=====================================================================")
        print("Number of inputs: "+str(xbar.Ninputs[0].read_N_input()))
        print("Number of outputs: "+str(xbar.Noutputs[0].read_N_output()))
        print("=====================================================================")       
       #===================Change the path of trigger(where go to where)================
       #===================The defalut is: source->destination(0->4, 1->5, 2->6, 3->7)=====
       #print("Change the source of trigger destination 4 to #(any number bwtween 0~3): ")
       #xbar.trigDestinations[4].select_source(0)
       #print("Change the source of trigger destination 4 to #(any number bwtween 0~3): ")
       #xbar.trigDestinations[5].select_source(1)
       #print("Change the source of trigger destination 4 to #(any number bwtween 0~3): ")
       #xbar.trigDestinations[6].select_source(2)
       #print("Change the source of trigger destination 4 to #(any number bwtween 0~3): ")
       #xbar.trigDestinations[7].select_source(3)
       #================================================================================


       #print("The source for trig dest. 0 is now: "+str(xbar.trigDestinations[0].read_source()))
       #print("The source for trig dest. 1 is now: "+str(xbar.trigDestinations[1].read_source()))
       #print("The source for trig dest. 2 is now: "+str(xbar.trigDestinations[2].read_source()))
       #print("The source for trig dest. 3 is now: "+str(xbar.trigDestinations[3].read_source()))
       #print("The source for trig dest. 4 is now: "+str(xbar.trigDestinations[4].read_source()))
       #print("The source for trig dest. 5 is now: "+str(xbar.trigDestinations[5].read_source()))
       #print("The source for trig dest. 6 is now: "+str(xbar.trigDestinations[6].read_source()))
       #print("The source for trig dest. 7 is now: "+str(xbar.trigDestinations[7].read_source()))
       #print("The source for trig dest. 8 is now: "+str(xbar.trigDestinations[8].read_source()))

       
