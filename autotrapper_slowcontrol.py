import asyncio
import socket
from leakvalvecontrol import leakvalvecontroller
from cameraimaging import take_image_std, take_image_height
from SG382ctrl import SG382
from kasa import SmartPlug
import struct
import subprocess

HOST = '171.64.56.233'
PORT = 6340

READDELAY = 0.1

def get_pressure(lv):
    return lv.pressure

async def tcp_server(host=HOST, port=PORT):
    lv = leakvalvecontroller()
    trapbeam = SG382('169.254.0.2')

    def setlaserpower_trap(pow):
        if pow < -8 and pow > -18:
            trapbeam.setAmplitude(pow)
            if not trapbeam.getRFon():
                trapbeam.RFon()
        else:
            raise ValueError("Invalid laser power")

    def getlaserpower_trap():
        trapbeam.getAmplitude()
        return float(trapbeam.amp)

    def get_pressure():
        return lv.pressure

    async def bringindevices():
        pass

    async def bringoutdevices():
        pass

    async def takestd():
        return take_image_std()

    async def handle_client(reader, writer):
        print("Connected to client")
        sending = False
        async def leaktopressure(writer, targetpressure, nom=None, thresh=0.01):
            if nom is not None: lv.nom = nom
            press = get_pressure()
            if press < targetpressure*(1-thresh):
                writer.write('l'.encode())
                await writer.drain()
                lv.open()
                while press < targetpressure:
                    await asyncio.sleep(READDELAY)
                    press = get_pressure()
                lv.close()
            if press > targetpressure*(1+thresh):
                writer.write('v'.encode())
                await writer.drain()
                while press > targetpressure:
                    await asyncio.sleep(READDELAY)
                    press = get_pressure()

            writer.write('s'.encode())
            await writer.drain()

        async def send_std():
            while sending:
                std = await takestd()
                std_bytes = struct.pack('>d', std)
                std_bytes = bytes(std_bytes)
                writer.write(std_bytes)
                await writer.drain()
                await asyncio.sleep(READDELAY)

        try:
            while True:
                print("awaiting command")
                data = await reader.read(1)
                command = data.decode()

                print(f"Command recieved: {command}")

                # SEND CAMERA STD UNTIL TOLD STOP
                if command == "d":
                    sending = True
                    stdtask = asyncio.create_task(send_std())
                    breakmess = None
                    while breakmess != "s":
                        breakmess = (await reader.read(1)).decode()
                    sending = False
                    await stdtask

                # CHECK PRESSURE. SEND COMMANDS TO ENSURE IT REACHES A TARGET VALUE
                if command == "p":
                    setnom = (await reader.read(1)).decode()
                    targetpress = await reader.read(8)
                    targetpress = struct.unpack('>d', targetpress)[0]
                    nomval = None
                    if setnom == 'y':
                        nomval = await reader.read(8)
                        nomval = struct.unpack('>d', nomval)[0]
                    await leaktopressure(writer, targetpress, nomval)
                    
                # SET TRAP BEAM POWER. TURN ON
                if command == 'l':

                    curpow = getlaserpower_trap()
                    print(curpow)
                    curpow_bytes = struct.pack('>d', curpow)
                    curpow_bytes = bytes(curpow_bytes)
                    writer.write(curpow_bytes)
                    await writer.drain()

                    lpow = await reader.read(8)
                    lpow = struct.unpack('>d', lpow)[0]
                    setlaserpower_trap(lpow)

                # BRING IN DEVICES, TURN ON DROPPER AMPS
                if command == 'c':
                    bringindevices()

                    sp1 = SmartPlug("192.168.50.98")
                    sp1.turn_on()
                    sp2 = SmartPlug("192.168.50.99")
                    sp2.turn_on()

                # TO DO: ADD BEAD RAMPING, DEVICE RETRACTION
                if command == 'f':
                    sp1 = SmartPlug("192.168.50.98")
                    sp1.turn_off()
                    sp2 = SmartPlug("192.168.50.99")
                    sp2.turn_off()

                    bringoutdevices()



                

                writer.write('s'.encode())
                await writer.drain()
        except Exception as ex:
            print(ex)
        finally:
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(handle_client, host, port)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(tcp_server())