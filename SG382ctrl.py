from datetime import datetime
from signal import signal
import telnetlib
import sys
from time import sleep
import h5py
import datetime
import signal
import numpy as np

# ipAddr_trap = '169.254.0.2'
# ipAddr_ref = '169.254.0.3'
# port = 5024

class SG382:
    '''
    Class object for SG382 Telnet object
    '''
    def __init__(self, ip='169.254.0.2', port=5024):
        try:
            self.SG382 = telnetlib.Telnet(ip, port)
            print(f'Connection established to {ip}:{port}')
            # Do the read a couple of times...
            for ii in range(3):
                self.getAmplitude()
                self.getFrequency()
            # Finally, clear the error...
            sleep(1)
            self.clearError()
        except:
            print(f'SG382 cannot be reached at {ipAddr}:{port}')
            sys.exit(0) 

        self.ramping = False

    def getRFon(self):
        self.SG382.write(b'ENBR?\n')
        RFoutputStatus = self.SG382.read_until(b'\n').decode('utf-8').strip('\r\n')
        return RFoutputStatus

    def setAmplitude(self, amp):
        self.clearError()
        cmd = 'AMPR '+str(amp)+'\n'
        self.SG382.write(cmd.encode('utf-8'))
        sleep(1)
        self.getAmplitude()
        return()

    def getAmplitude(self,):
        self.clearError()
        self.SG382.write(b'AMPR?\n')
        retStr = self.SG382.read_until(b'\n').decode('utf-8')
        self.amp = retStr.strip('\r\n')
        print(f'Amplitude is {self.amp} dB')
        return()

    def setFrequency(self, freq):
        self.clearError()
        cmd = 'FREQ '+str(freq)+'\n'
        self.SG382.write(cmd.encode('utf-8'))
        sleep(1)
        self.getFrequency()
        return()

    def getFrequency(self,):
        self.clearError()
        self.SG382.write(b'FREQ?\n')
        retStr = self.SG382.read_until(b'\n').decode('utf-8')
        self.freq = retStr.strip('\r\n')
        print(f'Frequency is {self.freq} Hz')
        return()

    def RFon(self):
        self.getAmplitude()
        cmd = 'ENBR 1\n'
        self.SG382.write(cmd.encode('utf-8'))
        return()

    def RFoff(self):
        cmd = 'ENBR 0\n'
        self.SG382.write(cmd.encode('utf-8'))
        return()

    def clearError(self):
        cmd = '*CLS\n'
        self.SG382.write(cmd.encode('utf-8'))
        return()

    def RFramp(self, start, stop, nSteps):
        self.ramping = True
        amps = np.linspace(start, stop, int(nSteps))
        print(f'Ramping RF amplitude from {start} dB to {stop} dB in {int(nSteps)} steps')
        for aa in amps:
            cmd = 'AMPR '+str(aa)+'\n'
            self.SG382.write(cmd.encode('utf-8'))
            sleep(1)
            self.amp = str(aa) # Update the internal reference
            if not self.ramping: break
        self.ramping = False
        return()

# trap = SG382(ip=ipAddr_trap)
# ref = SG382(ip=ipAddr_ref)
    





