import asyncio
import json
import time
from datetime import datetime

from kivy.app import App

from smac_client import client
from smac_db import db
from smac_device import property_listener, set_property
from smac_device_keys import SMAC_PROPERTY
from smac_keys import smac_keys
from smac_platform import SMAC_PLATFORM

if SMAC_PLATFORM == "android":
    from jnius import autoclass
    PythonService = autoclass('org.kivy.android.PythonService')
    PythonService.mService.setAutoRestartService(True)
    print("SERVICE RESTART CODE RUN")

async def start():
    while True:
        #time.sleep(1)
        await asyncio.sleep(1)
        print("TIME: ", time.time())

def get_config_variable(key):
    try:
        with open('config.json', 'r') as f:
            fd = json.load(f)
            d = fd.get(key, None)
            f.close()
            return d
    except:
        return None

def trigger_context(id_context, ID_DEVICE, *args):
    print("triggering context {}".format(id_context))
    for id_topic, id_context, id_device, id_property, value, name_context in db.get_action_by_device(ID_DEVICE, id_context):
        # change property here
        print(id_device)
        print(id_property)
        print(value)
        tp = db.get_property_name_by_property(id_device, id_property)
        print("tp", tp)
        if tp != None:
            set_property(str(tp[1]), value, id_property)

async def loop1(*args):
    COUNTER = 0
    ID_DEVICE = get_config_variable(key="ID_DEVICE")
    while (ID_DEVICE == "") or (ID_DEVICE == None):
        ID_DEVICE = get_config_variable(key="ID_DEVICE")
        await asyncio.sleep(1)
    print("ID_DEV", ID_DEVICE)
    client.send_message(frm=ID_DEVICE, to="#", cmd=smac_keys["CMD_REQ_SEND_INFO"], message={}, udp=True, tcp=False)
    send_device_info(ID_DEVICE=ID_DEVICE, dest_topic="#", udp=True, tcp=False)
    while 1:
        await asyncio.sleep(0)
        # check for busy period and update the db
        id_topic = ""
        for id_device, name_device, type_device, view_device, is_busy, busy_period, pin_device, pin_device_valid, interval_online, last_updated  in db.get_device_list_by_topic(id_topic):
            if busy_period == int(time.time()):
                db.update_device_busy(id_device=id_device, is_busy=0, busy_period=0)

        if((COUNTER % 5) == 0):
            await property_listener(ID_DEVICE)

        if (COUNTER % 60) == 0:
            print("Sending CMD_ONLINE")
            client.send_message(frm=ID_DEVICE, to="#", cmd=smac_keys["CMD_ONLINE"], message={})
            await  asyncio.sleep(0)



        # check for trigger and update value
        if (COUNTER % 60) == 0:
            for id_topic, id_context, id_device, id_property, value, type_trigger in db.get_trigger_by_device(ID_DEVICE):
                if type_trigger == smac_keys["TYPE_TRIGGER_PROP"]:
                    db_value = db.get_value_by_property(id_device, id_property)
                    if str(db_value) == str(value):
                        trigger_context(id_context, id_device)
                        #self.send_trigger_context(id_context)
                elif type_trigger == smac_keys["TYPE_TRIGGER_TIME"]:
                    value_hour, value_min, DOW = value.split(":")
                    DOW = DOW.split(",")
                    time1 = datetime.now()
                    print("DOW", time1.weekday())
                    print(DOW)
                    print("is DOW ", int(DOW[time1.weekday()]))
                    if(value_hour == str(time1.hour)) and (value_min == str(time1.minute)) and ( int( DOW[time1.weekday()] ) ):
                        trigger_context(id_context, id_device)
                        #self.send_trigger_context(id_context)

        for id_property, property_name, type_property, value_min, value_max, value, value_temp, value_last_updated in db.get_property_list_by_device(ID_DEVICE):
            type_property = str(type_property)
            t_diff = time.time() - int(value_last_updated)
            DIFF = .3       # ensure property is stable for .5 secs
            if (type_property not in [SMAC_PROPERTY["BATTERY"]]) and (value != value_temp):
                print(SMAC_PROPERTY[type_property])
                print("t_diff", t_diff)
                if t_diff > DIFF:
                    # db.update_value_property_by_dev_id(id_device=id_device, id_property=id_property, value=value_temp)
                    set_property(type_property=type_property, value=int(value_temp), id_property=id_property)
                else:
                    print("Device is Busy")
                    d = {}
                    d[smac_keys["ID_DEVICE"]] = ID_DEVICE
                    d[smac_keys["VALUE"]] = 5
                    client.send_message(frm=ID_DEVICE, to="#", cmd=smac_keys["CMD_DEVICE_BUSY"], message=d )

        COUNTER += 1
        await asyncio.sleep(1)

async def start_tasks():
    task1 = asyncio.create_task( client.main() )
    task2 = asyncio.create_task( loop1() )
    await task1
    await task2

def send_device_info(ID_DEVICE, dest_topic, udp=True, tcp=True, *args):
    SENDING_INFO = 1

    if tcp:
        topics = db.get_topic_list_by_device(id_device=ID_DEVICE)
    else:
        topics = [ ("", "", "") ]
    #topics.append( ("#", "", "") )
    print("topics" ,topics)
    print("dest_topic", dest_topic)
    #client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd= smac_keys["CMD_INIT_SEND_INFO"], message={}, udp=True, tcp=False)
    for id_topic, name_home, name_topic in topics:
        print("aa", id_topic )
        if id_topic not in ["#", ID_DEVICE]:
            print("ab")
            m = {}
            m[ smac_keys["TOPIC"]] = 1
            m[ smac_keys["ID_TOPIC"] ] = id_topic if(id_topic != None) else ""
            m[ smac_keys["NAME_TOPIC"] ] = name_topic if(name_topic != None) else ""
            m[ smac_keys["NAME_HOME"] ] = name_home if(name_home != None) else ""
            m[ smac_keys["NAME_DEVICE"] ] = str( get_config_variable(key="NAME_DEVICE") )
            m[ smac_keys["TYPE_DEVICE"] ] = str( get_config_variable(key="TYPE_DEVICE") )
            #print(m)
            #time.sleep(.1)
            client.send_message(frm=ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=m, udp=udp, tcp=tcp)
            print("sent {}".format(id_topic))

            for id_topic, id_context, name_context in db.get_context_by_topic(id_topic):
                c1 = {}
                c1[ smac_keys["CONTEXT"] ] = 1
                c1[ smac_keys["ID_TOPIC"] ] = id_topic if(id_topic != None) else ""
                c1[ smac_keys["ID_CONTEXT"] ] = id_context if(id_context != None) else ""
                c1[ smac_keys["NAME_CONTEXT"] ] = name_context if(name_context != None) else ""
                client.send_message(frm=ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=c1 ,udp=udp, tcp=tcp)
    print("sent topics")

    for p in db.get_property(ID_DEVICE):
        print(p)
        p1 = {}
        p1[smac_keys["PROPERTY"]] = 1
        p1[smac_keys["ID_DEVICE"]] = ID_DEVICE
        p1[smac_keys["ID_PROPERTY"]] = p[2]
        p1[smac_keys["TYPE_PROPERTY"]] = str(p[3])
        p1[smac_keys["NAME_PROPERTY"]] = p[4]
        p1[smac_keys["VALUE"]] = p[5]
        p1[smac_keys["VALUE_MIN"]] = p[6]
        p1[smac_keys["VALUE_MAX"]] = p[7]
        client.send_message(frm=ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=p1, udp=udp,
                            tcp=tcp)
    print("send property")

    for id_topic1, id_context, id_device, id_property, value, name_context in db.get_action_by_device_only(ID_DEVICE):
        c2 = {}
        c2[ smac_keys["CONTEXT_ACTION"] ] = 1
        c2[ smac_keys["ID_TOPIC"]] = id_topic1 if (id_topic1 != None) else ""
        c2[ smac_keys["ID_CONTEXT"]] = id_context if (id_context != None) else ""
        c2[ smac_keys["ID_DEVICE"]] = id_device
        c2[ smac_keys["ID_PROPERTY"]] = id_property
        c2[ smac_keys["VALUE"] ] = value
        c2[ smac_keys["NAME_CONTEXT"] ] = name_context
        client.send_message(frm=ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=c2, udp=udp, tcp=tcp)

    for id_topic2, id_context, id_device, id_property, value, type_trigger in db.get_trigger_by_device(ID_DEVICE):
        c2 = {}
        c2[ smac_keys["CONTEXT_TRIGGER"] ] = 1
        c2[ smac_keys["ID_TOPIC"]] = id_topic2 if (id_topic2 != None) else ""
        c2[ smac_keys["ID_CONTEXT"]] = id_context if (id_context != None) else ""
        c2[ smac_keys["ID_DEVICE"]] = id_device
        c2[ smac_keys["ID_PROPERTY"]] = id_property
        c2[ smac_keys["VALUE"] ] = value
        c2[ smac_keys["TYPE_TRIGGER"]] = type_trigger
        #c2[ smac_keys["NAME_CONTEXT"] ] = name_context
        client.send_message(frm=ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=c2, udp=udp, tcp=tcp)
    SENDING_INFO = 0

def on_client_start(ID_DEVICE, *args):
    print(args)
    #Clock.schedule_once(partial(client.send_message, self.ID_DEVICE, "#", smac_keys["CMD_REQ_SEND_INFO"] , {}, False, None, True, False), 5)
    client.send_message(frm=ID_DEVICE, to="#", cmd=smac_keys["CMD_REQ_SEND_INFO"], message={}, udp=False, tcp=True)
    send_device_info(ID_DEVICE=ID_DEVICE, dest_topic="#", udp=False, tcp=True)

#t1 = asyncio.create_task(loop1())
client.on_start = on_client_start
asyncio.run( start_tasks() )