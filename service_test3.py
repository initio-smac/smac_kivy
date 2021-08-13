import asyncio
import json
import time
from datetime import datetime

#from kivy.app import App

from smac_client import client
from smac_db import db
from smac_device import property_listener, set_property
from smac_device_keys import SMAC_PROPERTY
from smac_keys import smac_keys
from smac_platform import SMAC_PLATFORM

def on_task_removed(*args):
    print("APP removed")
    print(args)

if SMAC_PLATFORM == "android":
    from jnius import autoclass
    PythonService = autoclass('org.kivy.android.PythonService')
    PythonService.mService.setAutoRestartService(True)
    #PythonService.mService.onTaskRemoved = on_task_removed
    PythonService.mService.onDestroy = on_task_removed
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

def check_for_action_trigger_status(id_device, id_property, value, *args):
    print("checking for trig status")
    print(id_device)
    print(id_property)
    print(value)
    #for id_topic, id_context, id_device, id_property, value, name_context in db.get_action_by_device_only(self.ID_DEVICE):
    actions = db.get_action_by_property_value(id_device, id_property, value)
    if actions != None:
        action_status = 1 if(len(actions) > 0) else 0
        db.update_action_status(id_device, id_property, status=action_status)
    triggers = db.get_trigger_by_property_value(id_device, id_property, value)
    if triggers != None:
        trigger_status = 1 if( len(triggers)>0 ) else 0
        db.update_trigger_status(id_device, id_property, status=trigger_status)


async def loop1(*args):
    COUNTER = 0
    ID_DEVICE = get_config_variable(key="ID_DEVICE")
    while (ID_DEVICE == "") or (ID_DEVICE == None):
        ID_DEVICE = get_config_variable(key="ID_DEVICE")
        await asyncio.sleep(1)
    print("ID_DEV", ID_DEVICE)
    INTERVAL_ONLINE = get_config_variable(key="INTERVAL_ONLINE")
    while 1:
        await asyncio.sleep(0)
        # check for busy period and update the db
        id_topic = ""
        for id_device, name_device, type_device, view_device, is_busy, busy_period, pin_device, pin_device_valid, interval_online, last_updated  in db.get_device_list_by_topic(id_topic):
            if busy_period == int(time.time()):
                db.update_device_busy(id_device=id_device, is_busy=0, busy_period=0)

        if((COUNTER % 5) == 0):
            await property_listener(ID_DEVICE)

        if (COUNTER % INTERVAL_ONLINE) == 0:
            print("Sending CMD_ONLINE", INTERVAL_ONLINE)
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

def on_client_start(ID_DEVICE, *args):
    print(args)
    print("client started")


def on_message(topic, message, protocol,  *args):
    print( "{}, {}, {}".format(topic, message, protocol) )
    #try:
    msg = json.loads(message)
    frm = msg.get( smac_keys["FROM"] , None)
    to = msg.get( smac_keys["TO"], None)
    cmd = msg.get( smac_keys["COMMAND"], None )
    ack = msg.get( smac_keys["ACK"], None )
    msg_id = msg.get( smac_keys["ID_MESSAGE"], None )
    data = msg
    ID_DEVICE = get_config_variable(key="ID_DEVICE")
    if frm != ID_DEVICE:
        if cmd == smac_keys["CMD_DEVICE_BUSY"]:
            id_device = data.get(smac_keys["ID_DEVICE"])
            value = data.get(smac_keys["VALUE"])
            value = value if type(value) == int else int(value)
            busy_period = int(time.time()) + value
            db.update_device_busy(id_device=id_device, is_busy=1, busy_period=busy_period )
            print("id_device: {} is busy".format(id_device))

        if cmd == smac_keys["CMD_INVALID_PIN"]:
            id_device = data.get(smac_keys["ID_DEVICE"])
            id_topic = data.get(smac_keys["ID_TOPIC"], "")
            id_property = data.get(smac_keys["ID_PROPERTY"], "")
            db.update_pin_valid(id_device=id_device, pin_device_valid=0 )
            print("id_device: {} pin is invalid".format(id_device))
            db.add_command_status(id_topic=id_topic, id_device=id_device, cmd=cmd, id_property=id_property)

        if cmd == smac_keys["CMD_SET_PROPERTY"]:
            id_prop = data.get(smac_keys["ID_PROPERTY"])
            id_device = data.get(smac_keys["ID_DEVICE"])
            value = data.get(smac_keys["VALUE"])
            db.update_value_temp_by_dev_id(id_device=id_device, id_property=id_prop, value=value)

        if cmd == smac_keys["CMD_STATUS_SET_PROPERTY"]:
            id_property = str( msg.get( smac_keys["ID_PROPERTY"] ) )
            id_device=  str( msg.get( smac_keys["ID_DEVICE"] ) )
            value = msg.get( smac_keys["VALUE"])
            db.update_value_property_by_dev_id(id_property=id_property, id_device=frm, value=value)
            #self.update_slider_ui_val(id_device, id_property, value)
            check_for_action_trigger_status(id_device, id_property, value)

        if cmd == smac_keys["CMD_TRIGGER_CONTEXT"]:
            id_context = data.get(smac_keys["ID_CONTEXT"])
            trigger_context(id_context)

#t1 = asyncio.create_task(loop1())
client.on_start = on_client_start
client.on_message = on_message
asyncio.run( start_tasks() )