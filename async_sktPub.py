#!/usr/bin/python
"""
    ZMQ PUB simulation with pure Python sockets
"""
import socket
import time
import asyncio
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

async def test2():
    #try:
        reader, writer = await asyncio.open_connection("smacsystem.com", 5559)
        print("writing")
        writer.write(zGreetingSig)
        await writer.drain()
        print("writing done")
        #await writer.drain()
        #while True:
        
        while 1:
            data = await reader.read(16)
            print(data)
            if (data.startswith(zGreetingSig)) :
                print("Got ZMQ Greeting!")
                writer.write(zGreetingSig)
                await writer.drain()
                print("ZMQ Ver/Mech")  
                writer.write(zGreetingMech+zGreetingEnd)  
                await writer.drain()            
                writer.write(zHandshake1+zHandshake2+zHandshake3)
                await writer.drain()
            if (b"READY" in data):
                print("READY")
                while 1: 
                    writer.write( ba1 + bytearray(msg, encoding="utf-8")    )  
                    await writer.drain()
                    time.sleep(1)
            if data:
                d = ''.join(chr(i) for i in data)
                print(d)
            else:
                #print ("<END Connection>")
                #break 
                pass
    #except Exception as e:
    #    print(e)
        
        
        

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
            print("data", data)
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


#async def main():
#    await test2()


#asyncio.run(main())
