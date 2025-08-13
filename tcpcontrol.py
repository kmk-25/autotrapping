import socket
import asyncio
import struct
#from vimba import *
from time import sleep
import subprocess
import numpy as np
import cameraimaging
import time

HOST = '171.64.56.233'
PORT = 6340

sendinterval = 1
photointerval = 3
reps = int(photointerval//sendinterval)
    
mess = float('10.67')
mess_bytes = struct.pack('>d', mess)
mess_bytes = bytes(mess_bytes)
length = struct.pack('!I', len(mess_bytes))

shutdown_event = asyncio.Event()

mess = 7.5

async def updatemess(newmess):
    global mess
    mess = newmess


async def send_periodic(writer):
    global mess
    try:
        while True:
            mess_bytes = struct.pack('>d', mess)
            mess_bytes = bytes(mess_bytes)
            length = struct.pack('!I', len(mess_bytes))
            writer.write(length)
            await writer.drain()
            writer.write(mess_bytes)
            await writer.drain()
            await asyncio.sleep(sendinterval)
    except asyncio.CancelledError:
        print('Send stopped')

async def listen_for_close(reader):
    try:
        while True:
            data = await reader.readline()
            if not data:
                print("Client disconnected.")
                break
    except:
        pass

async def handle_client(reader, writer):
    print("Client connected")
    sender_task = asyncio.create_task(send_periodic(writer))
    listener_task = asyncio.create_task(listen_for_close(reader))

    await listener_task
    sender_task.cancel()
    try:
        await sender_task
    except asyncio.CancelledError:
        pass

    writer.close()
    await writer.wait_closed()
    print("Connection closed")

async def shutdown_server():
    shutdown_event.set()

async def main():
    global shutdown_event
    shutdown_event = asyncio.Event()
    shutdown_event.clear()
    server = await asyncio.start_server(handle_client, HOST, PORT)
    try:
        async with server:
            serve_task = asyncio.create_task(server.serve_forever())
            await shutdown_event.wait()
            serve_task.cancel()
            try:
                await serve_task
            except asyncio.CancelledError:
                pass
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())