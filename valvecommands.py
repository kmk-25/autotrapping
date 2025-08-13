import nidaqmx
from nidaqmx.constants import LineGrouping

bitFilePath = 'C:/Users/gravity/Desktop/levitation_code_20241127/FPGA Bitfiles/myDemod_FPGATarget_feedbackv10(FPGA_917M9JBMis0.lvbitx'
valve_dict = {'LeakValve':'PXI1Slot2/port1/line0', 'VacuumValve':'PXI1Slot2/port1/line3', 'SlowRoughing':'PXI1Slot2/port1/line4'}

class valvecontroller():
    def __init__(self, statevec=[False, False, False]):
        self.statedict = {}
        for i, valve in enumerate(valve_dict.keys()):
            self.statedict[valve] = statevec[i]
        self.set_all_valves()

    def __getitem__(self, key):
        if key not in set(valve_dict.keys()): raise ValueError(f"Invalid valve name: use one of {','.join(list(valve_dict.keys()))}")
        return self.statedict[key]
    
    def __setitem__(self, key, state):
        if key not in set(valve_dict.keys()): raise ValueError(f"Invalid valve name: use one of {','.join(list(valve_dict.keys()))}")
        self.setvalve(key, state)

    def keys(self):
        return self.statedict.keys()

    def setvalve(self, valvename, valvestate):
        if valvename not in set(valve_dict.keys()): raise ValueError(f"Invalid valve name: use one of {','.join(list(valve_dict.keys()))}")
        with nidaqmx.Task() as gascontroltask:
            gascontroltask.do_channels.add_do_chan(valve_dict[valvename], line_grouping=LineGrouping.CHAN_PER_LINE)
            gascontroltask.write(valvestate, auto_start=True)
        self.statedict[valvename] = valvestate

    def set_all_valves(self):
        for valve in self.statedict.keys():
            self.setvalve(valve, self.statedict[valve])