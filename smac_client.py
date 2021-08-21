import errno
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
    ZMQ_SUB_PORT = 5572
    ZMQ_SERVER = "smacsystem.com"
    #ZMQ_SERVER = "192.168.43.85"
    #ZMQ_SERVER = "192.168.0.178"
    ZMQ_REQ = []
    ZMQ_PUB_CONNECTED = 0
    ZMQ_SUB_CONNECTED = 0
    ZMQ_RECONNECT_INTERVAL = 10
    ZMQ_CONN_INITIALIZED = False
    ZMQ_SEND_MSG_QUEUE = []
    #ZMQ_FRAME_FLAG = b"\x00"
    ZMQ_LONG_FRAME = True
    #_zmq_pub_connected = 0
    #_zmq_sub_connected = 0
    MAX_BUFFER = 512
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
    SPD_TEST_INTERVAL = 5
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
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
        #self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.udp_sock.setblocking(False)
        try:
            self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            print("Set BROADCAST option")
        except Exception as e:
            print("cant set BROADCAST option", e)
        #self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        #self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.udp_sock.bind(("",self.UDP_PORT))
        except Exception as e:
            print(e)

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
        try:
            addr = "255.255.255.255" if broadcast else addr
            msg = "{} {}".format(topic, message)
            msg = msg.encode("utf-8")
            self.udp_sock.sendto(msg, (addr, self.UDP_PORT))
            #print("Sent UDP message", msg)
        except Exception as e:
            print("UDP message send err: {}".format(e))


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
            self.ZMQ_SEND_MSG_QUEUE.append( (topic, msg) )
        #print("msg_queue", self.ZMQ_SEND_MSG_QUEUE)
        self.MSG_ID += 1
        #await self.send_zmq(topic, msg)

    # send through ZMQ socket
    async def send_zmq(self, topic, message):
        await asyncio.sleep(0)
        if (self.zmq_pub_writer != None) and (self.ZMQ_PUB_CONNECTED):
            msg = "{} {}".format(topic, message)
            #l = len(msg)

            try:
                # encoding keyword is not supported in micropython
                #ba1 = self.smac_bytearray('\x00' + len(msg))
                #l = len(msg)
                #self.zmq_pub_writer.write(  self.smac_bytearray("\x00{}{}".format(str(hex(l))[2:], msg) ) )
                if self.ZMQ_LONG_FRAME:
                    l = str(hex(len(msg)+1))[2:]
                    l = l.zfill(16)
                    N = 2
                    l = "".join( [ chr( int(l[i:i+N], 16) )  for i in range(0, len(l), N)])
                    m = bytearray("\x02{}{}\n".format(l, msg), encoding="raw_unicode_escape")
                else:
                    m = bytearray("\x00{}{}\n".format(chr(len(msg)+1),msg), encoding="raw_unicode_escape")
                #print(m)
                self.zmq_pub_writer.write( m )
                #self.zmq_pub_writer.write(bytearray("\x00\x04\x30\x31\x32\x33", encoding="utf-8") )
                #self.zmq_pub_writer.write(bytearray("00040123", encoding="utf-8") )
                await self.zmq_pub_writer.drain()
                print(msg)
                #print(chr(len(msg)))
                #print(len(msg))
                #print(  m )
                #print(chr(len(msg)))
                #print(ba1)
                print("ZMQ message sent")
            except Exception as e:
                print("ZMQ Message not sent: {}".format(e))
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

    async def send_message_listener_zmq(self, *args):
        await asyncio.sleep(0)
        while 1:
            #print(self.ZMQ_SEND_MSG_QUEUE)
            if len(self.ZMQ_SEND_MSG_QUEUE) > 0:
                print(self.ZMQ_SEND_MSG_QUEUE)
                for num, (topic, msg) in enumerate(self.ZMQ_SEND_MSG_QUEUE):
                    await self.send_zmq(topic, msg)
                    del self.ZMQ_SEND_MSG_QUEUE[num]
            await asyncio.sleep(0)

    # convert to bytearray
    # encoding keyword is not supported in ESP
    def smac_bytearray(self, string):
        if SMAC_PLATFORM == "ESP":
            return bytearray(string)
        else:
            return bytearray(string, encoding="raw_unicode_escape")

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
                #print(data)
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
                await asyncio.sleep(0)
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
        print("initializing zmq connections")
        print("ZMQ_PUB_CONNECTED", self.ZMQ_PUB_CONNECTED)
        print("ZMQ_SUB_CONNECTED", self.ZMQ_SUB_CONNECTED)
        await  asyncio.sleep(0)
        if not self.ZMQ_CONN_INITIALIZED:
            self.ZMQ_CONN_INITIALIZED = True
            if not self.ZMQ_PUB_CONNECTED:
                pub = await self._initialize_zmq_publish()
                print("pub", pub)
                while not pub:
                    await asyncio.sleep(self.ZMQ_RECONNECT_INTERVAL)
                    pub = await self._initialize_zmq_publish()
                    print("pub", pub)

            if not self.ZMQ_SUB_CONNECTED:
                sub = await self._initialize_zmq_subscribe()
                print("sub", sub)
                while not sub:
                    await asyncio.sleep(self.ZMQ_RECONNECT_INTERVAL)
                    sub = await self._initialize_zmq_subscribe()
                    print("sub", sub)

            self.ZMQ_CONN_INITIALIZED = False
            self.on_start(self.ZMQ_PUB_CONNECTED, self.ZMQ_SUB_CONNECTED)



    # handle messages appended on self.UDP_REQ
    async def on_message_udp(self, *args):
        print("on_message_udp")
        await asyncio.sleep(0)
        while 1:
            #print("udp_messages: {}".format(self.UDP_REQ))
            await asyncio.sleep(0)
            for num, message in enumerate(self.UDP_REQ):
                try:
                    print("udp_message: {}".format(message))
                    d = message.split(" ", 1)
                    #print(d)
                    topic = d[0]
                    msg = d[1]
                    #print(topic)
                    #print(self.SUB_TOPIC)
                    print(topic in self.SUB_TOPIC)
                    if topic in self.SUB_TOPIC:
                        try:
                            self.process_message(topic, msg, "UDP")
                        except Exception as e:
                            print("Exception while processing UDP msg: ", e)
                        del self.UDP_REQ[num]
                    else:
                        self.UDP_REQ.remove(message)
                except Exception as e:
                    print(e)
                    self.UDP_REQ.remove(message)


    # handle messages appended on self.ZMQ_REQ
    async def on_message_zmq(self, *args):
        print("on_message_zmq")
        await asyncio.sleep(0)
        while 1:
            await asyncio.sleep(0)
            for num, message in enumerate(self.ZMQ_REQ):
                try:
                    print("zmq_message: [{}]".format(message))
                    d = message.split(" ", 1)
                    topic = d[0]
                    msg = d[1]
                    print("#" in self.SUB_TOPIC)
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
                            except Exception as e:
                                print("Exception process_message, zmq", e)
                            
                        del self.ZMQ_REQ[num]
                    else:
                        self.ZMQ_REQ.remove(message)
                except Exception as e:
                    print("on_message_zmq err: {}".format(e) )
                    self.ZMQ_REQ.remove(message)

        

    # wait for messages on UDP port and append to self.UDP_REQ
    async def listen_udp(self, *args):
        print("listening udp port...")
        await asyncio.sleep(0)
        while True:
            try:        
                data, addr = self.udp_sock.recvfrom(self.MAX_BUFFER)
                #print("ADATA", data)
                d = data.decode("utf-8")
                #print("DDATA", d)
                self.UDP_REQ.append(d)
            except Exception as e:
                #print("ERR while listening UDP port", e)
                if e.errno == errno.EAGAIN:
                    #print("EAGAIN")
                    pass
            #print("DA", data)
            await asyncio.sleep(0)

    # wait for messages on ZMQ port and append to self.ZMQ_REQ
    async def listen_zmq(self, *args):
        print("listening zmq sub...")
        await asyncio.sleep(0)
        while 1:
            try:
                #if self.ZMQ_SUB_CONNECTED and (not self.zmq_sub_reader.at_eof()):
                #print("self.ZMQ_SUB_CONNECTED", self.ZMQ_SUB_CONNECTED)
                #if self.ZMQ_SUB_CONNECTED:
                #print("CONN_SUB", self.ZMQ_SUB_CONNECTED)
                if self.ZMQ_SUB_CONNECTED:
                    data = await self.zmq_sub_reader.readline()
                    #print("zmq_dat: {}".format(data))
                    #print("at_eof: {}".format(self.zmq_sub_reader.at_eof()) )
                    if data != b"":
                        #data = data[2:]

                        #d = data.split(self.ZMQ_FRAME_FLAG)
                        #print(len(self.ZMQ_FRAME_FLAG))
                        #for dat in d:
                        #    if (dat != None) and (dat != ''):
                        data = data[2:-1]
                        d = data.decode("utf-8")

                        #print(d)
                        #print("zmq_msg: {}".format(d) )
                        #print("zmq_msg_len: {}".format( len(d)) )
                        self.ZMQ_REQ.append(d)
                #else:
                    # if not connected
                    #await asyncio.sleep(1)
                #    pass
                    await asyncio.sleep(0)
            except Exception as e:
                print("listen zmq err: {}".format(e) )
            await asyncio.sleep(0)

   

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
        #t = {"F": "Dcf", "K": "P0", "L": 8, "M": "SHUTDOWN_1", "N": 0, "O": 0, "P": 0, "5": "D_cf", "6": "T1", "7": "4", "9": 91}
        #await self.send_zmq("D1", json.dumps(t) )

    async def start_android_service(self, *args):
        await asyncio.sleep(1)
        if SMAC_PLATFORM == "android":
            from jnius import autoclass
            PythonService = autoclass('org.kivy.android.PythonService')
            PythonService.mService.setAutoRestartService(True)
            print("SERVICE RESTART CODE RUN")

    # main function
    async def main(self, *args):
        print("main")
        #await self.start_android_service()
        #zmq_pub_start = asyncio.create_task( self.initialize_zmq_publish() )
        #zmq_sub_start = asyncio.create_task( self.initialize_zmq_subscribe() )
        udp_t1 = asyncio.create_task(self.listen_udp())
        udp_t2 = asyncio.create_task(self.on_message_udp())

        zmq_con = asyncio.create_task( self.initialize_zmq_connections() )
        zmq_t1 = asyncio.create_task(self.listen_zmq())
        zmq_t2 = asyncio.create_task(self.on_message_zmq())
        zmq_t3 = asyncio.create_task(self.send_message_listener_zmq())
        #test1 = asyncio.create_task(self.test_pub())

        '''from test.sender import send
        t = asyncio.create_task(send())
        await t'''

        #await test1
        await udp_t1
        await udp_t2

        await zmq_con
        await zmq_t3
        await zmq_t1
        await zmq_t2

        #await asyncio.gather(self.test_pub(), self.listen_udp(), self.on_message_udp(),  self.initialize_zmq_connections(), self.send_message_listener_zmq(), self.listen_zmq(), self.on_message_zmq() )

        print("task created")

client = SMACClient()
#print(time.time())
#asyncio.run(client.main())
#print("exited")

#if SMAC_PLATFORM == "android":
#    from jnius import autoclass
#    PythonService = autoclass('org.kivy.android.PythonService')
#    PythonService.mService.setAutoRestartService(True)
#    print("SERVICE RESTART CODE RUN")
#    asyncio.run( client.main() )



