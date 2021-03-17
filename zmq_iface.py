import asyncio
import socket
import time


class SMACZMQ():
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
    #                                S   U   B
    zHandshake3_sub  = bytearray(b'\x03\x53\x55\x42')
    #                                P   U   B
    zHandshake3_pub  = bytearray(b'\x03\x50\x55\x42')
    #
    zSubStart = bytearray(b'\x00\x01\x01')
    #---------------------------------------------------------------------------------

    def __init__(self, *args):
        # create TCP/IP socket
        self.sock_sub = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.sock_sub.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sock_pub = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.sock_pub.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #self.sock_sub = self.sock_pub
        

    def connect_sub(self, server_address, port):
        self.sock_sub.connect( (server_address, port) )

    def connect_pub(self, server_address, port):
        self.sock_pub.connect( (server_address, port) )


smac_zmq = SMACZMQ()


def test_pub():
    sock = smac_zmq.sock_pub
    sock.connect( ("smacsystem.com", 5556) )
    #await asyncio.sleep(1)
    time.sleep(1)
    sock.send(smac_zmq.zGreetingSig)
    #sock.send(b"hello")
    print("Sending ZMQ Greeting")
    while True:
        data = sock.recv(16)
        if (data.startswith(bytes(smac_zmq.zGreetingSig))) : #Found zmqGreeting
            print("Got ZMQ Greeting!")
            sock.send(smac_zmq.zGreetingVerMajor+smac_zmq.zGreetingVerMinor)
            print("ZMQ Ver/Mech")   
            sock.send(smac_zmq.zGreetingMech+smac_zmq.zGreetingEnd)              
            sock.send(smac_zmq.zHandshake1+smac_zmq.zHandshake2+smac_zmq.zHandshake3_pub)
        if (b"READY" in data) : #Found READY   
            #ba = bytearray('\x00\x06\x30\x31\x32\x33\x34\x35', encoding="utf-8")
            msg = 'hello world : {}'.format(time.time())  
            ba1 = bytearray('\x00'+chr(len(msg)), encoding="utf-8")
            sock.send( ba1 + bytearray(msg, encoding="utf-8")    )  
        if data:
            d = ''.join(chr(i) for i in data)
            #print(d)
        else:
            print ("<END Connection>")
            break 

async def test_sub():
    smac_zmq.connect_sub("smacsystem.com", 5559)
    while True:
        data = smac_zmq.sock.recv(16)          
        if (data.startswith(bytes(smac_zmq.zGreetingSig))) : #Found zmq Greeting
            print("ZMQ Greeting!")
            smac_zmq.sock.send(smac_zmq.zGreetingSig+smac_zmq.zGreetingVerMajor)
        if (b"NULL" in data) : #Found zmq NULL Mechnism
            print("ZMQ Ver/Mech")   
            smac_zmq.sock.send(smac_zmq.zGreetingVerMinor+smac_zmq.zGreetingMech+smac_zmq.zGreetingEnd)              
            smac_zmq.sock.send(smac_zmq.zHandshake1+smac_zmq.zHandshake2+smac_zmq.zHandshake3_sub)
        if (b"READY" in data): #Found zmq READY, Send Subscription Start
            print("ZMQ READY Subscribe")  
            smac_zmq.sock.send(smac_zmq.zSubStart)

        if data:
            d = ''.join(chr(i) for i in data)
            print(d)
        else:
            print ("<END Connection>")
            break
        await asyncio.sleep(0)


async def main():    
    test_pub()
    await asyncio.sleep(1)


#asyncio.run(main())
#test_pub()
