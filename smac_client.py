
import socket
import json
import time

from zmq_iface import smac_zmq
from smac_platform import SMAC_PLATFORM
from smac_device_keys import SMAC_DEVICES
from smac_keys import smac_keys

if SMAC_PLATFORM == "ESP":
    import uasyncio as asyncio
    from machine import Pin
    LED = Pin(2, Pin.OUT)
else:
    import asyncio



class SMACClient():
    SUB_TOPIC = []
    UDP_PORT = 37020
    UDP_REQ = []
    ZMQ_PUB_PORT = 5556
    ZMQ_SUB_PORT = 5559
    ZMQ_SERVER = "smacsystem.com"
    ZMQ_REQ = []
    ZMQ_PUB_CONNECTED = 0
    ZMQ_SUB_CONNECTED = 0
    ZMQ_RECONNECT_INTERVAL = 60
    #_zmq_pub_connected = 0
    #_zmq_sub_connected = 0
    MAX_BUFFER = 256
    zmq_pub_reader = None
    zmq_pub_writer = None
    zmq_sub_reader = None
    zmq_sub_writer = None
    _process_message = None
    SPD_TEST_SET = 1
    SPD_TEST_SRT_TIME = None
    SPD_TEST_END_TIME = None
    SPD_TEST_PKT_ID = 0
    SPD_TEST = None
    SPD_TEST_INTERVAL = 60
    _on_start = None
    _on_speed_test = None
    MSG_ID = 0
    PENDING_ACKS = []

    # on start callback
    @property
    def on_start(self, *args):
        return self._on_start
    
    # on_start callback setter
    @on_start.setter
    def on_start(self, func,*args):
        self._on_start = func

    # speed_test callback
    @property
    def on_speed_test(self, *args):
        if self._on_speed_test != None:
            return self._on_speed_test


    # speed test setter
    @on_speed_test.setter
    def on_speed_test(self, func, *args):
        self._on_speed_test = func

    # process message callback
    @property
    def process_message(self, *args):
        #print(self._process_message)
        if self._process_message != None:
            return self._process_message

    # process message setter        
    @process_message.setter   
    def process_message(self, func):
        self._process_message = func


    # consturctor
    # set udp socket
    def __init__(self, *args):
        #self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.udp_sock.setblocking(False)
        try:
            self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except:
            pass
        #self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        #self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_sock.bind(("",self.UDP_PORT))

    # subscribe to a topic
    def subscribe(self, topic):
        if type(topic) == list:
            self.SUB_TOPIC += [ i for i in topic if i not in self.SUB_TOPIC ]
        else:
            if topic not in self.SUB_TOPIC:
                self.SUB_TOPIC.append(topic)

    # unsubscribe to a topic
    def unsubscribe(self, topic):
        if topic in self.SUB_TOPIC:
            self.SUB_TOPIC.remove(topic)

    # send through UDP socket
    def send_udp(self, topic, message, addr="255.255.255.255", broadcast=False ):
        addr = "255.255.255.255" if broadcast else addr
        msg = "{} {}".format(topic, message)
        msg = msg.encode("utf-8")
        self.udp_sock.sendto(msg, (addr, self.UDP_PORT))

    def send_message(self, frm, to, cmd, message={}, ack=False, msg_id=None, udp=True, tcp=True, *args):
        topic = to
        #msg = str(message)
        
        msg = message
        #for i in message.keys():
        #    msg[ smac_keys[i] ] = message[i]
        #d[ smac_keys["PROPERTY"] ] = SMAC_DEVICES[  message["property"].upper() ]
        #d[ smac_keys["INSTANCE"] ] = message["instance"]
        #d[ smac_keys["VALUE"] ] = message["value"]

        #msg = {}
        msg[ smac_keys["FROM"] ] = frm
        msg[ smac_keys["TO"] ] = to
        msg[ smac_keys["COMMAND"] ] = cmd
        if ack:
            msg[ smac_keys["ACK"] ] = 1
        #msg[ smac_keys["ID_MESSAGE"] ] = msg_id if(msg_id != None) else self.MSG_ID
        msg[ smac_keys["ID_MESSAGE"] ] = self.MSG_ID
        #msg[ smac_keys["MESSAGE"] ] = d
        msg = json.dumps(msg)
        if udp:
            self.send_udp(topic, msg)
        if tcp:
            if SMAC_PLATFORM == "ESP":
                asyncio.run( self.send_zmq(topic, msg)   )
            else:
                asyncio.gather( self.send_zmq(topic, msg)   )
        self.MSG_ID += 1
        #await self.send_zmq(topic, msg)

    # send through ZMQ socket
    async def send_zmq(self, topic, message):
        #await asyncio.sleep(0)
        if (self.zmq_pub_writer != None) and (self.ZMQ_PUB_CONNECTED):
            msg = "{} {}".format(topic, message)
            # encoding keyword is not supported in micropython
            ba1 = self.smac_bytearray('\x00'+chr(len(msg)))
            try:
                self.zmq_pub_writer.write(  ba1 + self.smac_bytearray(msg) )
                await self.zmq_pub_writer.drain()
                print("message sent")
            except Exception as e:
                print("Message not sent: {}".format(e))
                self.ZMQ_PUB_CONNECTED = False
                self.ZMQ_SUB_CONNECTED = False
                #await asyncio.sleep(2)
                #await self.initialize_zmq_publish()
                #await asyncio.sleep(1)
                #await self.initialize_zmq_subscribe()
                await asyncio.sleep(2)
                await self.initialize_zmq_connections()
            
        else:
            print("ZMQ message not sent: either not connected or not initialized")
            await self.initialize_zmq_connections()
            

    # convert to bytearray
    # encoding keyword is not supported in ESP
    def smac_bytearray(self, string):
        if SMAC_PLATFORM == "ESP":
            return bytearray(string)
        else:
            return bytearray(string, encoding="utf-8")

    # initialize Handshakes between Client ans Server for Publishing
    async def _initialize_zmq_publish(self, *args):
        await asyncio.sleep(0)
        try:
            self.zmq_pub_reader, self.zmq_pub_writer = await asyncio.open_connection(self.ZMQ_SERVER, self.ZMQ_PUB_PORT)
            print('sending Greetings')
            self.zmq_pub_writer.write(smac_zmq.zGreetingSig)
            await self.zmq_pub_writer.drain()
            reader = self.zmq_pub_reader
            while 1 :
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
                if (b"READY" in data) : #Found READY   
                    print("Ready to Pub")
                    #msg = "hello :{}".format(time.time())
                    #ba1 = self.smac_bytearray('\x00'+chr(len(msg)))
                    #self.zmq_pub_writer.write(  ba1 + self.smac_bytearray(msg) )
                    self.ZMQ_PUB_CONNECTED = True
                    #break
                    return 1
                #if data:
                #    d = data.decode("utf-8")
                #    print(d)
                #else:
                #    print ("<END Connection>")
                #    break
                await asyncio.sleep(0)
                
        except Exception as e:
            print("Exception while connecting to zmq_pub: {}".format(e))
            self.ZMQ_PUB_CONNECTED = False
            return 0
            #await asyncio.sleep(5)
            #await self.initialize_zmq_publish()

    # initialize Handshakes between Client ans Server for Subscribing
    async def _initialize_zmq_subscribe(self, *args):
        await asyncio.sleep(0)
        try:
            self.zmq_sub_reader, self.zmq_sub_writer = await asyncio.open_connection(self.ZMQ_SERVER, self.ZMQ_SUB_PORT)
            writer = self.zmq_sub_writer
            while 1:
                #if (not self.zmq_sub_reader.at_eof()) and (not self.ZMQ_SUB_CONNECTED):
                if (not self.ZMQ_SUB_CONNECTED):
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
                        #break
                        return 1
        except Exception as e:
            print("Exception while connecting to zmq_sub: {}".format(e))
            self.ZMQ_SUB_CONNECTED = False
            #await asyncio.sleep(5)
            #await self.initialize_zmq_subscribe()
            return 0

    async def initialize_zmq_connections(self, *args):
        pub = await self._initialize_zmq_publish()
        print("pub", pub)
        while not pub:
            await asyncio.sleep(self.ZMQ_RECONNECT_INTERVAL)
            pub = await self._initialize_zmq_publish()  
            print("pub", pub)  

        sub = await self._initialize_zmq_subscribe()
        print("sub", sub)
        while not sub:
            await asyncio.sleep(self.ZMQ_RECONNECT_INTERVAL)
            sub = await self._initialize_zmq_subscribe()  
            print("sub", sub)     


    # handle messages appended on self.UDP_REQ
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
                    #print(topic)
                    #print(self.SUB_TOPIC)
                    #print(topic in self.SUB_TOPIC)
                    if topic in self.SUB_TOPIC:
                        try:
                            self.process_message(topic, msg, "UDP")
                        except:
                            pass
                        del self.UDP_REQ[num]
                    else:
                        self.UDP_REQ.remove(message)
                except Exception as e:
                    print(e)
                    self.UDP_REQ.remove(message)
            await asyncio.sleep(0)

    # handle messages appended on self.ZMQ_REQ
    async def on_message_zmq(self, *args):
        print("on_message_zmq")
        await asyncio.sleep(0)
        while 1:
            for num, message in enumerate(self.ZMQ_REQ):
                try:
                    print("zmq_message: [{}]".format(message))
                    d = message.split(" ", 1)
                    topic = d[0]
                    msg = d[1]
                    if topic in self.SUB_TOPIC:
                        if "SPEED_TEST" in msg:
                            text,START_TIME, PKT_ID = msg.split(":")
                            if int(PKT_ID) == self.SPD_TEST_PKT_ID:
                                self.SPD_TEST_END_TIME = time.time()
                                self.SPD_TEST_SET = 1
                                self.SPD_TEST = (self.SPD_TEST_END_TIME - float(START_TIME))
                                try:
                                    self.on_speed_test(self.SPD_TEST)
                                except:
                                    pass
                                print("SPD_DIFF:{}, PKT_ID:{}".format(self.SPD_TEST, PKT_ID))
                        else:
                            try:
                                self.process_message(topic, msg, "ZMQ")
                            except:
                                pass
                            
                        del self.ZMQ_REQ[num]
                    else:
                        self.ZMQ_REQ.remove(message)
                except Exception as e:
                    print("on_message_zmq err: {}".format(e) )
                    self.ZMQ_REQ.remove(message)
            await asyncio.sleep(0)
        

    # wait for messages on UDP port and append to self.UDP_REQ
    async def listen_udp(self, *args):
        print("listening udp port...")
        await asyncio.sleep(0)
        while True:
            try:        
                data, addr = self.udp_sock.recvfrom(self.MAX_BUFFER)
                d = data.decode("utf-8")
                self.UDP_REQ.append(d)
            except:
                pass
            await asyncio.sleep(0)

    # wait for messages on ZMQ port and append to self.ZMQ_REQ
    async def listen_zmq(self, *args):
        print("listening zmq sub...")
        try:
            while 1:
                #if self.ZMQ_SUB_CONNECTED and (not self.zmq_sub_reader.at_eof()):
                if self.ZMQ_SUB_CONNECTED:
                    data = await self.zmq_sub_reader.read(100)
                    #print("dat: {}".format(data))
                    #print("at_eof: {}".format(self.zmq_sub_reader.at_eof()) )
                    if data != b"":
                        data = data[2:]
                        d = data.decode("utf-8")
                        print("zmq_msg: {}".format(d) )
                        self.ZMQ_REQ.append(d)
                #else:
                    # if not connected
                    #await asyncio.sleep(1)
                #    pass
                await asyncio.sleep(0)
        except Exception as e:
            print("listen zmq err: {}".format(e) )

   

    async def test_pub(self, *args):
        #await asyncio.sleep(0)
        i = 0
        while 1:
            await asyncio.sleep(self.SPD_TEST_INTERVAL)
            print("sending")
            await self.check_speed_test()
            #await self.send_zmq("D1", "LED ONON")
            i += 1

    async def check_speed_test(self, *args):
        print("checking speed test")
        #print(self.SPD_TEST_SET)
        #if self.SPD_TEST_SRT_TIME != None:
        #    now = time.time()
        #    diff = now - self.SPD_TEST_SRT_TIME
        #    if int(diff) > 15:
        #        self.SPD_TEST_SET = 1
        #if self.SPD_TEST_SET == 1:
        #    self.SPD_TEST_SET = 0
        self.SPD_TEST_SRT_TIME = time.time()
        self.SPD_TEST_PKT_ID += 1
        await self.send_zmq("D1", "SPEED_TEST:{}:{}".format(time.time(), self.SPD_TEST_PKT_ID))

    # main function
    async def main(self, *args):
        print("main")
        #zmq_pub_start = asyncio.create_task( self.initialize_zmq_publish() )
        #zmq_sub_start = asyncio.create_task( self.initialize_zmq_subscribe() )
        zmq_con = asyncio.create_task( self.initialize_zmq_connections() )
        

        zmq_t1 = asyncio.create_task(self.listen_zmq())
        zmq_t2 = asyncio.create_task(self.on_message_zmq())
        udp_t1 = asyncio.create_task(self.listen_udp())
        udp_t2 = asyncio.create_task(self.on_message_udp())
        #test1 = asyncio.create_task(self.test_pub())

        await udp_t1
        await udp_t2

        await zmq_con
        #await zmq_pub_start
        #await zmq_sub_start
        #await test1
        await zmq_t1
        await zmq_t2
        
        print("task created")
    

client = SMACClient()
#print(time.time())
#asyncio.run(client.main())
#print("exited")