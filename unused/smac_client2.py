
import socket
import json
import math
#import smac_keys
from zmq_iface import smac_zmq

# to remove errors in android debug
#import encodings.idna

SMAC_PLATFORM = None

try:
    import uasyncio as asyncio
    from machine import Pin
    LED = Pin(2, Pin.OUT)
    SMAC_PLATFORM = "ESP"
except:
    import asyncio
    SMAC_PLATFORM = "KIVY"

import time


class SMACClient():
    SUB_TOPIC = ["D1", "D_TEST"]
    UDP_PORT = 37020
    UDP_REQ = []
    ZMQ_PUB_PORT = 5556
    ZMQ_SUB_PORT = 5559
    ZMQ_SERVER = "smacsystem.com"
    ZMQ_REQ = []
    #ZMQ_PUB_READY = False
    #ZMQ_SUB_READY = False
    ZMQ_PUB_CONNECTED = 0
    ZMQ_SUB_CONNECTED = 0
    MAX_BUFFER = 256
    zmq_pub_reader = None
    zmq_pub_writer = None
    zmq_sub_reader = None
    zmq_sub_writer = None
    _process_message = None

    #---
    SPD_TEST_SET = 1
    SPD_TEST_SRT_TIME = None
    SPD_TEST_END_TIME = None
    SPD_TEST_PKT_ID = 0
    SPD_TEST = None
    #_on_speed_test = None
    _on_start = None


    @property
    def on_start(self, *args):
        return self._on_start
    
    @on_start.setter
    def on_start(self, func,*args):
        self._on_start = func

    @property
    def on_speed_test(self, *args):
        return self._on_speed_test

    @on_speed_test.setter
    def on_speed_test(self, func, *args):
        self._on_speed_test = func

    @property
    def process_message(self, *args):
        #print("arg")
        #print(args)
        return self._process_message

    @process_message.setter   #property-name.setter decorator
    def process_message(self, func):
        print(func)
        self._process_message = func


    def __init__(self, *args):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
        self.udp_sock.setblocking(False)
        try:
            self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except:
            pass
        #self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        #self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_sock.bind(("",self.UDP_PORT))

    def subscribe(self, topic):
    	if topic not in self.SUB_TOPIC:
    	    self.SUB_TOPIC.append(topic)

    def unsubscribe(self, topic):
    	if topic in self.SUB_TOPIC:
    		self.SUB_TOPIC.remove(topic)

    def send_udp(self, topic, message, addr="255.255.255.255", broadcast=False ):
        addr = "255.255.255.255" if broadcast else addr
        msg = "{} {}".format(topic, message)
        self.udp_sock.sendto(msg, (addr, self.UDP_PORT))

    async def send_zmq(self, topic, message):
        await asyncio.sleep(0)
        #print("zmq_pub is_closed: {}".format(self.zmq_pub_writer.is_closing()))
        if (self.zmq_pub_writer != None) and (self.ZMQ_PUB_CONNECTED):
            msg = "{} {}".format(topic, message)
            # encoding keyword is not supported in micropython
            ba1 = self.smac_bytearray('\x00'+chr(len(msg)))
            self.zmq_pub_writer.write(  ba1 + self.smac_bytearray(msg) )
            await self.zmq_pub_writer.drain()
            #print("sent")
        else:
            print("not able to send")
            print(self.zmq_pub_writer)
            print(self.ZMQ_PUB_CONNECTED)
        #else:
        #    self.initialize_zmq_publish()


    '''def send_zmq(self, topic, message):
        smac_zmq.sock_pub.send(smac_zmq.zGreetingSig)
        print("Sending ZMQ Greeting")
        while True:
            data = smac_zmq.sock_pub.recv(16)
            #print(data)
            if (data.startswith(smac_zmq.zGreetingSig)) : #Found zmqGreeting
                print("Got ZMQ Greeting!")
                smac_zmq.sock_pub.send(smac_zmq.zGreetingVerMajor+smac_zmq.zGreetingVerMinor)
                print("ZMQ Ver/Mech")   
                smac_zmq.sock_pub.send(smac_zmq.zGreetingMech+smac_zmq.zGreetingEnd)              
                smac_zmq.sock_pub.send(smac_zmq.zHandshake1+smac_zmq.zHandshake2+smac_zmq.zHandshake3_pub)
            if (b"READY" in data) : #Found READY  
                print("ZMQ READY to publish") 
                #ba = bytearray('\x00\x06\x30\x31\x32\x33\x34\x35', encoding="utf-8")
                ba1 = bytearray('\x00'+chr(len(message)), encoding="utf-8")
                smac_zmq.sock_pub.send( ba1 + bytearray(message, encoding="utf-8")    )  
                print("message sent")
                #smac_zmq.sock_pub.send( ba   )  
                break

                #break
            if data:
                d = ''.join(chr(i) for i in data)
                print(d)
            #else:
            #    print ("<END Connection>")
                #break 
            #await asyncio.sleep(0)'''

    def smac_bytearray(self, string):
        if SMAC_PLATFORM == "ESP":
            return bytearray(string)
        else:
            return bytearray(string, encoding="utf-8")

    #async def initialize_zmq_connections(self, *args):
    #    await self.initialize_zmq_publish()
    #    await self.initialize_zmq_subscribe()
    #    self.on_start()

    async def initialize_zmq_publish(self, *args):
        await asyncio.sleep(0)
        try:
            self.zmq_pub_reader, self.zmq_pub_writer = await asyncio.open_connection(self.ZMQ_SERVER, self.ZMQ_PUB_PORT)
            print('sending Greetings')
            self.zmq_pub_writer.write(smac_zmq.zGreetingSig)
            await self.zmq_pub_writer.drain()
            reader = self.zmq_pub_reader
            while 1 :
                #self.zmq_pub.write(b"\x00\x04test")
                '''await self.zmq_pub_writer.drain()
                print(self.zmq_pub_writer.is_closing())
                print("writer.transport._conn_lost", self.zmq_pub.transport._conn_lost)
                if self.zmq_pub_writer.is_closing():
                #if not self.zmq_pub_writer.is_closing():
                    print("ZMQ PUB connection lost")
                    self.ZMQ_PUB_CONNECTED = False'''
                    #await asyncio.sleep(5)
                    #await self.initialize_zmq_publish()
                    

                #print(self.ZMQ_PUB_CONNECTED)
                #if (not self.ZMQ_PUB_CONNECTED):
                data = await reader.read(100)
                print(data)
                if (data.startswith( bytes(smac_zmq.zGreetingSig) )) : #Found zmq Greeting
                    print("Got ZMQ Greeting!")
                    self.zmq_pub_writer.write(smac_zmq.zGreetingVerMajor+smac_zmq.zGreetingVerMinor)
                    await self.zmq_pub_writer.drain()
                    print("ZMQ Ver/Mech")   
                    self.zmq_pub_writer.write(smac_zmq.zGreetingMech+smac_zmq.zGreetingEnd)    
                    await self.zmq_pub_writer.drain()          
                    self.zmq_pub_writer.write(smac_zmq.zHandshake1+smac_zmq.zHandshake2+smac_zmq.zHandshake3_pub)
                    await self.zmq_pub_writer.drain()
                #data = await reader.read(100)
                #print(data)
                if (b"READY" in data) : #Found READY   
                    print("Ready to Pub")
                    msg = "hello :{}".format(time.time())
                    ba1 = self.smac_bytearray('\x00'+chr(len(msg)))
                    self.zmq_pub_writer.write(  ba1 + self.smac_bytearray(msg) )
                    #await self.zmq_pub.drain()
                    #self.ZMQ_PUB_READY = True
                    self.ZMQ_PUB_CONNECTED = True
                    break
                #if data:
                #    d = ''.join(chr(i) for i in data)
                #    print(d)
                if not data:
                    print ("<END Connection>")
                    break
                await asyncio.sleep(0)
                

        except Exception as e:
            print("Exception while connecting to zmq_pub: {}".format(e))
            self.ZMQ_PUB_CONNECTED = False
            await asyncio.sleep(2)
            await self.initialize_zmq_publish()

    async def initialize_zmq_subscribe(self, *args):
        try:
            self.zmq_sub_reader, self.zmq_sub_writer = await asyncio.open_connection(self.ZMQ_SERVER, self.ZMQ_SUB_PORT)
            writer = self.zmq_sub_writer
            while 1:
                if (not self.zmq_sub_reader.at_eof()) and (not self.ZMQ_SUB_CONNECTED):
                    data = await self.zmq_sub_reader.read(100)
                    #print(data)
                    if (data.startswith(bytes(smac_zmq.zGreetingSig))): #Found zmq Greeting
                        print("ZMQ Greeting!")
                        writer.write(smac_zmq.zGreetingSig+smac_zmq.zGreetingVerMajor)
                        await writer.drain()
                    if (b"NULL" in data) : #Found zmq NULL Mechnism
                        print("ZMQ Ver/Mech")   
                        writer.write(smac_zmq.zGreetingVerMinor+smac_zmq.zGreetingMech+smac_zmq.zGreetingEnd)    
                        await writer.drain()          
                        writer.write(smac_zmq.zHandshake1+smac_zmq.zHandshake2+smac_zmq.zHandshake3_sub)
                        await writer.drain()
                    if (b"READY" in data): #Found zmq READY, Send Subscription Start
                        print("ZMQ READY Subscribe")  
                        writer.write(smac_zmq.zSubStart)
                        await writer.drain()
                        self.ZMQ_SUB_CONNECTED = True
                        break


        except Exception as e:
            print("Exception while connecting to zmq_sub: {}".format(e))
            self.ZMQ_SUB_CONNECTED = False
            await asyncio.sleep(5)
            await self.initialize_zmq_subscribe()


        

    #def process_message(self, topic, message, *args):
    #    try:
    #if "ON" in msg:
    #            LED.on()
    #        elif "OFF" in msg:
    #            LED.off()
    #        #self.UDP_REQ.remove(message)'''
    #        m = json.loads(msg)
    #        frm = m.get()
    #        
    #    except Exception as e:
    #        print("msg recv error(udp): {}".format(e) )


    async def on_message_udp(self, *args):
        print("on_message_udp")
        await asyncio.sleep(0)
        while 1:
            #print("udp_messages: {}".format(self.UDP_REQ))
            for num, message in enumerate(self.UDP_REQ):
                try:
                    print("udp_message: {}".format(message))
                    d = message.split(" ", 1)
                    #print(d)
                    topic = d[0]
                    msg = d[1]
                    if topic in self.SUB_TOPIC:
                        self.process_message(topic, msg, "UDP")
                        del self.UDP_REQ[num]
                    else:
                        self.UDP_REQ.remove(message)
                except Exception as e:
                    print(e)
                    self.UDP_REQ.remove(message)
            await asyncio.sleep(0)

    async def on_message_zmq(self, *args):
        print("on_message_zmq")
        await asyncio.sleep(0)
        while 1:
            #print("zmq_messages: {}".format(self.ZMQ_REQ))
            for num, message in enumerate(self.ZMQ_REQ):
                try:
                    #message = message[2:]
                    print("zmq_message: [{}]".format(message))
                    d = message.split(" ", 1)
                    topic = d[0]
                    msg = d[1]
                    if topic in self.SUB_TOPIC:
                        if "SPEED_TEST" in msg:
                            text,START_TIME, PKT_ID = msg.split(":")
                            #print(text)
                            #print(START_TIME)
                            #print(PKT_ID)
                            if int(PKT_ID) == self.SPD_TEST_PKT_ID:
                                self.SPD_TEST_END_TIME = time.time()
                                self.SPD_TEST_SET = 1
                                self.SPD_TEST = (self.SPD_TEST_END_TIME - float(START_TIME))
                                self.on_speed_test(self.SPD_TEST)
                                print("SPD_DIFF: {}".format(self.SPD_TEST))
                        else:
                            self.process_message(topic, msg, "ZMQ")
                        del self.ZMQ_REQ[num]
                    else:
                        self.ZMQ_REQ.remove(message)
                except Exception as e:
                    print("on_message_zmq err: {}".format(e) )
                    self.ZMQ_REQ.remove(message)
            await asyncio.sleep(0)
        

    async def listen_udp(self, *args):
        print("listening udp port...")
        #self.send_udp(topic="T1", message=TEST_DATA, broadcast=True)
        await asyncio.sleep(0)
        while True:
            try:        
                data, addr = self.udp_sock.recvfrom(self.MAX_BUFFER)
                #print("received message: %s"%data)
                d = data.decode("utf-8")
                self.UDP_REQ.append(d)
                #print(self.UDP_REQ)
            except:
                pass
            await asyncio.sleep(0)

    async def listen_zmq(self, *args):
        print("listening zmq sub...")
        try:
            while 1:
                #print("SUB_CONNECTED: {}".format(self.ZMQ_SUB_CONNECTED) )
                print("sub close: {}".format(self.zmq_sub_writer.is_closing()))
                print("pub close: {}".format(self.zmq_pub_writer.is_closing()))
                #print("sub writer pipe: {}".format(self.zmq_sub_writer.get_extra_info('pipe') ))
                #print("pub writer pipe: {}".format(self.zmq_pub_writer.get_extra_info('pipe') ))
                #print("sub writer transport: {}".format(self.zmq_sub_writer.transport ))
                #print("pub writer transport: {}".format(self.zmq_pub_writer.transport ))
                if self.ZMQ_SUB_CONNECTED:
                    # check if buffer is empty, if not read the buffer
                    #if not self.zmq_sub.at_eof():
                    data = await self.zmq_sub_reader.read(100)
                    if data == b"":
                        print("Conn Lost SUB")
                    print("dat: {}".format(data))
                    print("at_eof: {}".format(self.zmq_sub_reader.at_eof()) )
                    data = data[2:]
                    #d = ''.join(chr(i) for i in data)
                    d = data.decode("utf-8")
                    print("zmq_msg: {}".format(d) )
                    time.sleep(1)
                    self.ZMQ_REQ.append(d)
                else:
                    print("ZMQ SUB CONNECTED: 0")
                #print("writer is_closed: {}".format( self.zmq_sub.is_closing() ))

            await asyncio.sleep(0)
        except Exception as e:
            print("listen zmq err: {}".format(e) )

    '''async def listen_zmq(self, *args):
        print("listening zmq sub...")
        await asyncio.sleep(0)
        while True:
            #if not self.ZMQ_PUB_READY:
            #    await self.initialize_zmq_publish()
            data = smac_zmq.sock_sub.recv(16)          
            if (data.startswith(smac_zmq.zGreetingSig)) : #Found zmq Greeting
                print("ZMQ Greeting!")
                smac_zmq.sock_sub.send(smac_zmq.zGreetingSig+smac_zmq.zGreetingVerMajor)
            if (b"NULL" in data) : #Found zmq NULL Mechnism
                print("ZMQ Ver/Mech")   
                smac_zmq.sock_sub.send(smac_zmq.zGreetingVerMinor+smac_zmq.zGreetingMech+smac_zmq.zGreetingEnd)              
                smac_zmq.sock_sub.send(smac_zmq.zHandshake1+smac_zmq.zHandshake2+smac_zmq.zHandshake3_sub)
            if (b"READY" in data): #Found zmq READY, Send Subscription Start
                print("ZMQ READY Subscribe")  
                smac_zmq.sock_sub.send(smac_zmq.zSubStart)

            #if data and data not in [smac_zmq.zGreetingSig, smac_zmq.zGreetingVerMajor, smac_zmq.zGreetingVerMinor, smac_zmq.zGreetingMech, smac_zmq.zGreetingEnd, smac_zmq.zHandshake1, smac_zmq.zHandshake2, smac_zmq.zHandshake3, smac_zmq.zSubStart]:
            if data:
                d = ''.join(chr(i) for i in data)
                print(d)
                self.ZMQ_REQ.append(d)

            await asyncio.sleep(0)'''



    async def test_pub(self, *args):
        #await asyncio.sleep(0)
        i = 0
        while 1:
            print("sending")
            #await self.check_speed_test()
            await self.send_zmq("D1", "LED ONON")
            await asyncio.sleep(1)
            i += 1

    async def check_speed_test(self, *args):
        print("checking speed test")
        #print(self.SPD_TEST_SET)
        if self.SPD_TEST_SRT_TIME != None:
            now = time.time()
            diff = now - self.SPD_TEST_SRT_TIME
            if int(diff) > 15:
                self.SPD_TEST_SET = 1
        if self.SPD_TEST_SET == 1:
            self.SPD_TEST_SET = 0
            self.SPD_TEST_SRT_TIME = time.time()
            self.SPD_TEST_PKT_ID += 1
            await self.send_zmq("D1", "SPEED_TEST:{}:{}".format(time.time(), self.SPD_TEST_PKT_ID))




    async def main(self, *args):
        print("main")
        #self.init_zmq_sockets()
        #self.init_zmq_sockets()
        #await self.initialize_zmq_connections()

        zmq_pub_start = asyncio.create_task( self.initialize_zmq_publish() )
        zmq_sub_start = asyncio.create_task( self.initialize_zmq_subscribe() )
        await zmq_pub_start
        await zmq_sub_start
        #await self.initialize_zmq_publish()

        zmq_t1 = asyncio.create_task(self.listen_zmq())
        zmq_t2 = asyncio.create_task(self.on_message_zmq())
        udp_t1 = asyncio.create_task(self.listen_udp())
        udp_t2 = asyncio.create_task(self.on_message_udp())
        test1 = asyncio.create_task(self.test_pub())
        await test1
        #await test1
        #await self.check_speed_test()
        await zmq_t1
        await zmq_t2
        #await udp_t1
        #await udp_t2

        
        print("task created")
    


client = SMACClient()
#print(time.time())
#asyncio.run(client.main())
#print("exited")
