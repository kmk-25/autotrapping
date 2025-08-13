import asyncio
from valvecommands import valvecontroller
import struct
from nifpga import Session

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
        lp = sess.registers["Iz_shifted"]
        lp = (lp + pow_set) * (2**(-Iz_bitshift)*3.15e-6)

    return lp

async def connect_to_server():
    reader, writer = await asyncio.open_connection(HOST, PORT)
    print(f'Connected to {HOST}:{PORT}')
    return reader, writer

async def setlaserpower_trap(lpow):
    lpow_bytes = struct.pack('>d', lpow)
    lpow_bytes = bytes(lpow_bytes)

    writer.write('l'.encode())
    await writer.drain()
    writer.write(lpow_bytes)
    await writer.drain()

async def setpressure(press, slowroughing=False):
    press_bytes = struct.pack('>d', press)
    press_bytes = bytes(press_bytes)

    writer.write('l'.encode())
    await writer.drain()
    writer.write(press_bytes)
    await writer.drain()

    command = (await reader.read(1)).decode()
    if command == 'l':
        vc['LeakValve'] = True
    if command == 'v':
        vc['VacuumValve'] = True
    
    breakmess = None
    while breakmess != "s":
        breakmess = (await reader.read(1)).decode()
    
    for valve in vc.keys():
        vc[valve] = False



async def mainloop():




    breakmess = None
    while breakmess != "s":
        breakmess = (await reader.read(1)).decode()