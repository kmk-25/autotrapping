import pyvisa

class pyvisaDevice():
    '''Parent class providing framework to connect, read, and write to a NI VISA device with pyvisa.'''
    def __init__(self, portnum):
        self.rm = pyvisa.ResourceManager()
        #Note: the number after GPIB is a counter for usb ports used for GPIB connected devices
        #This is independant from port number, and doesn't matter for our purposes

        # self.instrument = self.rm.open_resource('USB0::0xF4EC::0x1700::SNA5XCEX800090::INSTR')
        self.instrument = self.rm.open_resource(f"ASRL{portnum}::INSTR")
        
    def write(self, instruction):
        self.instrument.write(instruction)
        
    def query(self, instruction):
        return self.instrument.query(instruction)
    
    def read(self):
        return self.instrument.read_raw()
    
    def flush(self):
        self.instrument.flush(pyvisa.constants.BufferOperation.discard_read_buffer)
        
    def __del__(self):
        self.instrument.close()

class leakvalvecontroller(pyvisaDevice):
    def __init__(self, portnum=5, nom=5e-2):
        super().__init__(portnum)
        self.nom = nom

    def close(self):
        self.write(f"FLO={4.99e-6:.2E}")
        self.read()

    def open(self):
        self.write(f"FLO={self.nom:.2E}")
        self.read()

    def checkclosed(self):
        return float(self.query("FLO?")[4:12]) == 4.99e-6
    
    @property
    def pressure(self):
        return float(self.query("PRI?")[5:13])

