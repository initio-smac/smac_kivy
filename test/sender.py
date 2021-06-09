import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 37020
MESSAGE = b"Hello, World!"


print("UDP target IP: %s" % UDP_IP)
print("UDP target port: %s" % UDP_PORT)
print("message: %s" % MESSAGE)

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

import asyncio

async def send():
    count = 0
    while 1:
        count += 1
        sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
        print("sent", count)
        await asyncio.sleep(1)

    
