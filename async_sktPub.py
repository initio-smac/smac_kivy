#!/usr/bin/python
"""
    ZMQ PUB simulation with pure Python sockets
"""
import json
import socket
import time
import asyncio
import binascii
#--------------------------------------------------------------------------------
# Cast bytes to bytearray     0   1   2   3   4   5   6   7   8   9   
zGreetingSig = bytearray(b'\xFF\x00\x00\x00\x00\x00\x00\x00\x01\x7F')
zGreetingVerMajor= bytearray(b'\x03')    
zGreetingVerMinor= bytearray(b'\x00')    
zGreetingMech= bytearray(b"NULL")
zGreetingEnd = bytearray(48) 
#                                        R   E   A   D   Y       S
zHandshake1  = bytearray(b'\x04\x19\x05\x52\x45\x41\x44\x59\x0B\x53')
#                            o   c   k   e   t   -   T   y   p   e     
zHandshake2  = bytearray(b'\x6F\x63\x6B\x65\x74\x2D\x54\x79\x70\x65\x00\x00\x00')
#                                P   U   B
zHandshake3  = bytearray(b'\x03\x50\x55\x42')
#
zSubStart = bytearray(b'\x00\x01\x01')
#---------------------------------------------------------------------------------
# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


SERVER = "127.0.0.1"
#SERVER = "smacsystem.com"

import struct
async def test2(long_frame=True):
    try:
        reader, writer = await asyncio.open_connection(SERVER, 5556)
        writer.write(zGreetingSig)
        await writer.drain()
        #await writer.drain()
        #while True:
        
        while 1:
            data = await reader.read(16)
            #print("data", data)
            if (data.startswith(zGreetingSig)) :
                print("Got ZMQ Greeting!")
                writer.write(zGreetingVerMajor+zGreetingVerMinor)
                await writer.drain()
                print("ZMQ Ver/Mech")  
                writer.write(zGreetingMech+zGreetingEnd)  
                await writer.drain()
                print("a1")
                writer.write(zHandshake1+zHandshake2+zHandshake3)
                await writer.drain()
                print("a2")
            if (b"READY" in data):
                print("READY")
                while 1:
                    d = {}
                    d["name"]= "sfasdfasfdssdffffffffffffffvvfffffffffffddfffvvvvvvvvvvvvvvvvvvvvvvvvffffffggggggggfffffffffffffffffffd"
                    d["age"] = " fsadfdsadfsd dfdfdgdtedgdgdfgdrtsdfrfvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvfrfrvffffffffffffffffrgrgrfrfrfrgf222"
                    d["test"] = "asfwefsfksjfnsdfjsogosjlklsdkosdjfojjsofsmofjsdojlsnfklndkgnslogldnvkdnrfgoerogsodngsldglsdgln"
                    d["E"] = "D_cf"
                    d["e"]= 0
                    msg = json.dumps(d)
                    #msg = '{"F": "Dcf", "K": "P0", "L": 8, "M": "SHUTDOWN_1", "N": 0, "O": 0, "P": 0, "5": "D_cf", "6": "T1", "7": "4", "9": 91}'
                    # refer encoding section
                    # https://stackoverflow.com/questions/7585435/best-way-to-convert-string-to-bytes-in-python-3
                    print(len(msg))
                    print( chr(len(msg)) )
                    if long_frame:
                        l = str(hex(len(msg) + 1))[2:]
                        l = l.zfill(16)
                        N = 2
                        l = "".join([chr(int(l[i:i + N], 16)) for i in range(0, len(l), N)])
                        m = bytearray("\x02{}{}\n".format(l, msg), encoding="raw_unicode_escape")
                        writer.write(  m  )
                    else:
                        writer.write( bytearray('\x00{}{}'.format(chr(len(msg)), msg), encoding="raw_unicode_escape") )

                    #writer.write(  chr(00) + chr(129) +      )
                    await writer.drain()
                    print(msg)
                    time.sleep(1)
            '''if data:
                d = ''.join(chr(i) for i in data)
                print(d)
            else:
                #print ("<END Connection>")
                #break 
                pass'''
    except Exception as e:
        print(e)
        
        
        

async def test():
    # Connect the socket to the port where the server is listening
    server_address = ('smacsystem.com', 5556)
    print ('connecting on address %s port %s' % server_address)
    sock.connect(server_address)
    #time.sleep(10)
    try:
        sock.send(zGreetingSig)
        while True:
            data = sock.recv(16)
            #print("data", data)
            if (data.startswith(zGreetingSig)) : #Found zmq Greeting
                print("Got ZMQ Greeting!")
                sock.send(zGreetingVerMajor+zGreetingVerMinor)
                print("ZMQ Ver/Mech")   
                sock.send(zGreetingMech+zGreetingEnd)   
                print("a")           
                sock.send(zHandshake1+zHandshake2+zHandshake3)
                print("b")     
            if (b"READY" in data) : #Found READY   
                ba = bytearray('\x00\x06\x30\x31\x32\x33\x34\x35', encoding="utf-8")
                sock.send(ba)   
                #ba = bytearray('\x00\x06\x30\x31\x32\x33\x34\x35', encoding="utf-8")
                msg = 'hello world : {}'.format(time.time())  
                ba1 = bytearray('\x00'+chr(len(msg)), encoding="utf-8")
                while 1: 
                    print("sending...")
                    sock.send( ba1 + bytearray(msg, encoding="utf-8")    )  
                    #time.sleep(1)
                    await asyncio.sleep(1) 
            '''if data:
                d = ''.join(chr(i) for i in data)
                print(d)
            else:
                #print ("<END Connection>")
                #break 
                pass'''
        await asyncio.sleep(0)
        #sock.close()
    except Exception as e:
        print(e)
        raise
    finally:
        #sock.close()   
        sock.close()


async def main():
    await test2()


asyncio.run(main())
