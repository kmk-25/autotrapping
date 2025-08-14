import asyncio
from valvecommands import valvecontroller
import struct
from nifpga import Session
from time import sleep
import numpy as np

HOST = '171.64.56.233'
PORT = 6340

BITFILEPATH = 'C:/Users/gravity/Desktop/levitation_code_20241127/FPGA Bitfiles/myDemod_FPGATarget_feedbackv10(FPGA_917M9JBMis0.lvbitx'
RESOURCE = 'PXI1Slot3'

READDELAY = 0.1

reader = None
writer = None
vc = valvecontroller()

def getlaserpower():
    pow_set = 0
    Iz_bitshift = -3

    with Session(bitfile=BITFILEPATH, resource=RESOURCE) as sess:
        lp = sess.registers["Iz_shifted"].read()
        lp = (lp + pow_set) * (2**(-Iz_bitshift)*3.15e-6)

    return lp

async def connect_to_server():
    global reader
    global writer
    reader, writer = await asyncio.open_connection(HOST, PORT)
    print(f'Connected to {HOST}:{PORT}')
    return reader, writer

async def setlaserpower_trap(lpow):
    lpow_cur = getlaserpower()
    while abs(lpow_cur - lpow) > 1:
        writer.write('l'.encode())
        await writer.drain()

        curpow_dbm = await reader.read(8)
        curpow_dbm = struct.unpack('>d', curpow_dbm)[0]

        targpow = np.log10(lpow/lpow_cur) * 10 + curpow_dbm
        targpow_bytes = struct.pack('>d', targpow)
        targpow_bytes = bytes(targpow_bytes)
        writer.write(targpow_bytes)
        await writer.drain()

        await waitforstop()
        lpow_cur = getlaserpower()

async def setpressure(press, slowroughing=False):
    press_bytes = struct.pack('>d', press)
    press_bytes = bytes(press_bytes)

    writer.write('p'.encode())
    await writer.drain()
    writer.write('n'.encode())
    await writer.drain()
    writer.write(press_bytes)
    await writer.drain()

    command = (await reader.read(1)).decode()
    if command == 'l':
        vc['LeakValve'] = True
    if command == 'v':
        if slowroughing: vc['SlowRoughing'] = True
        else: vc['VacuumValve'] = True
    
    await waitforstop()
    
    for valve in vc.keys():
        vc[valve] = False

    await waitforstop()


async def waitforstop():
    print("Waiting for end")
    breakmess = None
    while breakmess != "s":
        breakmess = (await reader.read(1)).decode()
        print(f"Message recieved: {breakmess}")


async def mainloop():
    pass




