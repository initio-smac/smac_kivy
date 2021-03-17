import os

from kivy import platform
from kivy.app import App

from smac_client import client
from smac_db import db
from smac_device_keys import SMAC_DEVICES, SMAC_PROPERTY
from smac_keys import smac_keys
from smac_platform import SMAC_PLATFORM

from plyer import battery, brightness, flash
from plyer import bluetooth

if platform == "android":
    from android.permissions import check_permission, Permission
    from jnius import autoclass

    bt = autoclass('android.bluetooth.BluetoothAdapter')
    mBluetoothAdapter = bt.getDefaultAdapter();


def get_device_name():
    if platform == "android":
        from jnius import autoclass
        BUILD = autoclass('android.os.Build')
        return BUILD.MODEL
    else:
        import socket
        return socket.gethostname()

def get_device_type():
    if SMAC_PLATFORM == "ESP":
        return SMAC_DEVICES["ESP"]
    else:
        if platform == "android":
            return SMAC_DEVICES["SMART_PHONE"]
        elif (platform == "linux") or (platform == "win"):
            return SMAC_DEVICES["COMPUTER"]

def get_property_min_max(prop):
    if prop in [  SMAC_PROPERTY["BLUETOOTH"], SMAC_PROPERTY["FLASH"], SMAC_PROPERTY["SWITCH"], SMAC_PROPERTY["LIGHT"], SMAC_PROPERTY["GEYSER"] ]:
        return (0, 1, 0)
    elif prop in [ SMAC_PROPERTY["BATTERY"], SMAC_PROPERTY["BRIGHTNESS"] ]:
        return (0, 100, 0)
    elif prop in [ SMAC_PROPERTY["FAN"] ]:
        return  (0, 4, 0)
    elif prop in [ SMAC_PROPERTY["SHUTDOWN"], SMAC_PROPERTY["RESTART"] ]:
        return (0, 0, 0)
    else:
        return (0,0,0)



def get_device_property(id_device):
    props = []
    arr = []
    if platform == "android":
        arr = [ SMAC_PROPERTY["BLUETOOTH"], SMAC_PROPERTY["BATTERY"], SMAC_PROPERTY["FLASH"], SMAC_PROPERTY["BRIGHTNESS"] ]
        #arr = [ SMAC_PROPERTY["BLUETOOTH"], SMAC_PROPERTY["BATTERY"], SMAC_PROPERTY["FLASH"] ]
    elif ( platform == "linux") or (platform == "win"):
        arr =  [ SMAC_PROPERTY["SHUTDOWN"], SMAC_PROPERTY["RESTART"] ]
    for num, p in enumerate(arr):
        p1 = {}
        min, max, val = get_property_min_max(p)
        p1["value_min"] = min
        p1["value_max"] = max
        p1["value"] = val
        p1["type_property"] = p
        p1["name_property"] = SMAC_PROPERTY[p]
        p1["id_property"] = "P{}".format( num)
        props.append(p1)
    return props

def get_property_value(type_property, id_property=None):
    if type_property == SMAC_PROPERTY["BATTERY"]:
        return str(battery.status['percentage'])
    elif type_property == SMAC_PROPERTY["BLUETOOTH"]:
        #return  1 if(bluetooth.info=="on") else 0
        try:
            return 1 if mBluetoothAdapter.isEnabled() else 0
        except:
            return 0
    elif type_property == SMAC_PROPERTY["BRIGHTNESS"]:
        #if check_permission(Permission.WRITE_SETTINGS):
        return brightness.current_level()
        #return 0
    elif type_property == SMAC_PROPERTY["FLASH"]:
        return 0
    else:
        return 0

def set_property(type_property, value, id_property=None):
    if type_property == SMAC_PROPERTY["BLUETOOTH"]:
        try:
            if value == 0:
                mBluetoothAdapter.disable()
            elif value == 1:
                mBluetoothAdapter.enable()
            send_status(id_property, value)
            return True
        except Exception as e:
            print("Bluetooth control err: {}".format(e))
            return False
    elif type_property == SMAC_PROPERTY["BRIGHTNESS"]:
        if platform == "android":
            #print(check_permission(Permission.WRITE_SETTINGS))
            #if check_permission(Permission.WRITE_SETTINGS):
            try:
                brightness.set_level(value)
                send_status(id_property, value)
                return True
            except Exception as e:
                print("Brightness control err: {}".format(e))
                return False
    elif type_property == SMAC_PROPERTY["FLASH"]:
        try:
            if value: flash.on()
            else: flash.off()
            send_status(id_property, value)
            return True
        except Exception as e:
            print("Flash control err; {}".format(e))
            return False
    elif type_property == SMAC_PROPERTY["SHUTDOWN"]:
        if (platform == "linux") or (platform == "win"):
            print("shutting down system")
            os.system("sudo shutdown")
    elif type_property == SMAC_PROPERTY["RESTART"]:
        if (platform == "linux") or (platform == "win"):
            print("rebooting system")
            os.system("sudo reboot")


def send_status(id_property, value, update_ui=True):
    app = App.get_running_app()
    d = {}
    d[ smac_keys["ID_DEVICE"] ] = app.ID_DEVICE
    d[ smac_keys["ID_PROPERTY"] ] = id_property
    d[ smac_keys["VALUE"]] = value
    db.update_value_property_by_dev_id(id_device=app.ID_DEVICE, id_property=id_property, value=value)
    db.update_value_temp_by_dev_id(id_device=app.ID_DEVICE, id_property=id_property, value=value)

    #if update_ui:
    app.update_slider_ui_val(app.ID_DEVICE, id_property, value)

    #for id_topic in app.SUB_TOPIC:
    client.send_message(frm=app.ID_DEVICE, to="#", cmd=smac_keys["CMD_STATUS_SET_PROPERTY"], message=d, udp=True, tcp=False)


