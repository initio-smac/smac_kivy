import os

from kivy.properties import *
from kivy.utils import get_color_from_hex, platform
#from kivy.uix.screenmanager import ScreenManager, Screen, CardTransition, NoTransition, SlideTransition, SwapTransition, FadeTransition, WipeTransition, FallOutTransition, RiseInTransition
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.core.window import Window
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
#Clock.max_iteration = 10

from functools import partial

from smac_device import set_property, get_device_property, get_property_value

Window.clearcolor = get_color_from_hex("#e0e0e0")

import asyncio
import json

#from smac_client import client
#from async_sktPub import test



from smac_device_keys import SMAC_DEVICES
from smac_keys import smac_keys
from smac_client import client
from smac_platform import SMAC_PLATFORM
from smac_widgets.smac_screens import *
from smac_widgets.smac_layouts import *
from smac_db import db

from kivy.lang import Builder
Builder.load_file('smac_widgets/smac_screens.kv')
Builder.load_file('smac_widgets/smac_layouts.kv')



class BoxLayout_property(BoxLayout):
    data = DictProperty({
        "min": 0,
        "max": 1,
        "value": 0,
        "instance": 0
    })


class SmacApp(App):
    text1 = StringProperty("hai")
    image_source = ""
    grid_min = dp(50)
    screen_manager = ScreenManager(transition=NoTransition())
    modal = ModalView(auto_dismiss=False)
    modal_opened = False
    app_data = DictProperty({
        "id_topic": "",
        "name_topic": "",
        "id_device": ""
    })
    ID_DEVICE = ""
    NAME_DEVICE = ""
    TYPE_DEVICE = "0"
    PIN_DEVICE = "1234"
    SUB_TOPIC = ["#"]
    ACKS ={}
    SET_PROP_COUNTER = {}

    SENDING_INFO = 0
    TEST_VAL = 0

    def build(self):
        self.screen_manager.add_widget(Screen_network(name='Screen_network'))
        #self.screen_manager.add_widget(Screen_devices(name='Screen_devices'))
        self.screen_manager.add_widget(Screen_property(name='Screen_property'))
        return self.screen_manager

    def change_screen(self, screen, *args):
        self.screen_manager.current = screen

    '''def add_topic(self, id_topic, *args):
        db.add_network_entry(name_topic=id_topic, id_topic=id_topic, id_device=self.ID_DEVICE, name_device=self.NAME_DEVICE, type_device=self.TYPE_DEVICE)
        client.subscribe(id_topic)
        d = {}
        d[ smac_keys["ID_TOPIC"] ] = id_topic
        d[ smac_keys["NAME_DEVICE"]] = self.NAME_DEVICE
        d[ smac_keys["TYPE_DEVICE"]] = self.TYPE_DEVICE
        client.send_message(frm=self.ID_DEVICE, to="#", cmd=smac_keys["CMD_STATUS_ADD_TOPIC"], message=d, udp=True, tcp=False)
        print("subscribed topic: {}".format(id_topic))'''


    async def check_for_ack(self, MSG_ID, COUNT=10, *args):
        print(args)
        print(self.ACKS)
        await asyncio.sleep(0)
        while COUNT:
            if MSG_ID in self.ACKS.keys():
                text = self.ACKS[MSG_ID]
                print(text)
                #self.open_modal(text=text, auto_close=True, timeout=2)
                del self.ACKS[MSG_ID]
                break
            COUNT -= 1
            await asyncio.sleep(1)
        else:
            text = "Timeout: No response from the device"
            print(text)
            #self.open_modal(text=text, auto_close=True, timeout=2)


    def send_req_add_topic(self, id_topic, id_device, passkey, *args):
        if id_device == self.ID_DEVICE:
            self.add_topic(frm=id_device, id_topic=id_topic, id_device=id_device, passkey=passkey, id_msg=None)
        else:
            d = {}
            d[smac_keys["ID_TOPIC"]] = id_topic
            d[smac_keys["ID_DEVICE"]] = id_device
            d[smac_keys["PASSKEY"]] = passkey
            MSG_ID = (client.MSG_ID +1)

            INTERVAL = 1
            client.send_message(frm=self.ID_DEVICE, to=id_device, cmd=smac_keys["CMD_ADD_TOPIC"], message=d, udp=True, tcp=False, msg_id=MSG_ID)
            print("waiting for ack :{}".format(MSG_ID))
            #Clock.schedule_interval( partial(check_for_ack, MSG_ID), INTERVAL )
            asyncio.gather( self.check_for_ack(MSG_ID, 10) )
            self.open_modal(text="Sending message to the device...")



    def add_topic(self, frm, id_topic, id_device, passkey, id_msg, *args):
        if passkey == self.PIN_DEVICE:
            db.add_network_entry(name_topic=id_topic, id_topic=id_topic, id_device=id_device, name_device=self.NAME_DEVICE, type_device=self.TYPE_DEVICE)
            self.update_config_variable(key='SUB_TOPIC', value=id_topic, arr_op="ADD")
            client.subscribe(id_topic)
            d = {}
            d[ smac_keys["ID_TOPIC"] ] = id_topic
            d[ smac_keys["NAME_DEVICE"]] = self.NAME_DEVICE
            d[ smac_keys["TYPE_DEVICE"]] = self.TYPE_DEVICE
            client.send_message(frm=self.ID_DEVICE, to="#", cmd=smac_keys["CMD_STATUS_ADD_TOPIC"], message=d)
            # sending ACK
            d1 = {}
            d1[ smac_keys["MESSAGE"] ] = "Topic subscribed successfylly"
            print("subscribed topic: {}".format(id_topic))
        else:
            d1 = {}
            d1[smac_keys["MESSAGE"]] = "Topic '{}' not subscribed".format(id_topic)
            print("Cannot subscribe to {}. Passkey error.".format(id_topic))
        # if sent from the same device
        if self.ID_DEVICE != frm:
            client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["ACK"], message=d1, msg_id=id_msg, udp=True, tcp=False)
        else:
            print( d1[smac_keys["MESSAGE"]] )

    def send_req_delete_topic(self, id_topic, id_device, passkey, *args):
        if id_device == self.ID_DEVICE:
            self.delete_topic(frm=id_device, id_topic=id_topic, id_device=id_device, passkey=passkey, id_msg=None)
        else:
            d = {}
            d[smac_keys["ID_TOPIC"]] = id_topic
            d[smac_keys["ID_DEVICE"]] = id_device
            d[smac_keys["PASSKEY"]] = passkey
            MSG_ID = (client.MSG_ID +1)
            client.send_message(frm=self.ID_DEVICE, to=id_device, cmd=smac_keys["CMD_REMOVE_TOPIC"], message=d, udp=True, tcp=False, msg_id=MSG_ID)
            print("waiting for ack :{}".format(MSG_ID))
            #Clock.schedule_interval( partial(check_for_ack, MSG_ID), INTERVAL )
            asyncio.gather( self.check_for_ack(MSG_ID, 10) )



    def delete_topic(self, frm, id_topic, id_device, passkey, id_msg, *args):
        if passkey == self.PIN_DEVICE:
            #db.add_network_entry(name_topic=id_topic, id_topic=id_topic, id_device=id_device, name_device=self.NAME_DEVICE, type_device=self.TYPE_DEVICE)
            db.delete_network_entry_by_topic(id_topic, id_device)
            self.update_config_variable(key='SUB_TOPIC', value=id_topic, arr_op="REM")
            client.unsubscribe(id_topic)
            d = {}
            d[ smac_keys["ID_TOPIC"] ] = id_topic
            d[ smac_keys["NAME_DEVICE"]] = self.NAME_DEVICE
            d[ smac_keys["TYPE_DEVICE"]] = self.TYPE_DEVICE
            client.send_message(frm=self.ID_DEVICE, to="#", cmd=smac_keys["CMD_STATUS_REMOVE_TOPIC"], message=d)
            # sending ACK
            d1 = {}
            d1[ smac_keys["MESSAGE"] ] = "Topic unsubscribed successfylly"
            print("unsubscribed topic: {}".format(id_topic))
        else:
            d1 = {}
            d1[smac_keys["MESSAGE"]] = "Topic '{}' not unsubscribed".format(id_topic)
            print("Cannot unsubscribe to {}. Passkey error.".format(id_topic))
        # if sent from the same device
        if self.ID_DEVICE != frm:
            client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["ACK"], message=d1, msg_id=id_msg, udp=True, tcp=False)
        else:
            print( d1[smac_keys["MESSAGE"]] )

    '''def delete_topic(self, wid, *args):
        db.delete_network_entry_by_topic(id_topic=wid.id_topic, id_device=self.ID_DEVICE)
        client.unsubscribe(wid.id_topic)
        scr = self.screen_manager.get_screen(name="Screen_network")
        container = scr.ids["id_network_container"]
        container.remove_widget(scr.TOPIC_IDS[wid.id_topic])
        del scr.TOPIC_IDS[wid.id_topic]
        d = {}
        d[smac_keys["ID_TOPIC"]] = wid.id_topic
        client.send_message(frm=self.ID_DEVICE, to="#", cmd=smac_keys["CMD_STATUS_REMOVE_TOPIC"], message=d, udp=True,tcp=False)
        print("unsubscribed topic: {}".format(wid.id_topic))'''

    def send_device_info(self, dest_topic, *args):
        self.SENDING_INFO = 1
        #topics = client.SUB_TOPIC
        #print(topics)
        #print(client.SUB_TOPIC)
        #topics.remove( "#" )
        #topics.remove( self.ID_DEVICE)
        topics = db.get_topic_list_by_device(id_device=self.ID_DEVICE)
        print("topics" ,topics)
        client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd= smac_keys["CMD_INIT_SEND_INFO"], message={}, udp=True, tcp=False)
        for id_topic, name_topic in topics:
            if id_topic not in ["#", self.ID_DEVICE]:
                m = {}
                m[ smac_keys["ID_TOPIC"] ] = id_topic if(id_topic != None) else ""
                m[ smac_keys["NAME_TOPIC"] ] = name_topic if(name_topic != None) else ""
                m[ smac_keys["NAME_DEVICE"] ] = self.NAME_DEVICE
                m[ smac_keys["TYPE_DEVICE"] ] = self.TYPE_DEVICE
                #print(m)
                client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=m, udp=True, tcp=False)
                print("sent {}".format(id_topic))
        print("send topics")

        for p in db.get_property(self.ID_DEVICE):
            print(p)
            p1 = {}
            p1[ smac_keys["ID_DEVICE"] ] = self.ID_DEVICE
            p1[ smac_keys["ID_PROPERTY"] ] = p[2]
            p1[ smac_keys["TYPE_PROPERTY"] ] = p[3]
            p1[ smac_keys["NAME_PROPERTY"] ] = p[4]
            p1[ smac_keys["VALUE"]] = p[5]
            p1[ smac_keys["VALUE_MIN"]] = p[6]
            p1[ smac_keys["VALUE_MAX"]] = p[7]
            client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=p1, udp=True, tcp=False)
        print("send property")

        self.SENDING_INFO = 0
        client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_END_SEND_INFO"], message={},
                            udp=True, tcp=False)

    def change_property(self, wid, value, *args):
        if wid.id_device == self.ID_DEVICE:
            # change property here
            db.update_value_property_by_dev_id(id_device=self.ID_DEVICE, id_property=wid.id_property, value=value)
            d = {}
            d[ smac_keys["ID_PROPERTY"] ] = wid.id_property
            d[ smac_keys["ID_DEVICE"] ] = wid.id_device
            d[ smac_keys["VALUE"] ] = value
            topics = db.get_topic_list_by_device(id_device=wid.id_device)
            for id_topic, name_topic in topics:
                client.send_message(frm=self.ID_DEVICE, to=id_topic, message=d, cmd=smac_keys["CMD_STATUS_SET_PROPERTY"])

    def on_message(self, topic, message, protocol,  *args):
            #print( "{}, {}, {}".format(topic, message, protocol) )
        #try:
            msg = json.loads(message)
            #print("1")
            frm = msg.get( smac_keys["FROM"] , None)
            to = msg.get( smac_keys["TO"], None)
            cmd = msg.get( smac_keys["COMMAND"], None )
            ack = msg.get( smac_keys["ACK"], None )
            msg_id = msg.get( smac_keys["ID_MESSAGE"], None )
            #data = msg.get( smac_keys["MESSAGE"], None )
            data = msg
            #print("2")
            #print(data)
            if frm != self.ID_DEVICE:
                if cmd == smac_keys["CMD_DEVICE_BUSY"]:
                    print("1a")
                    print(data)
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    value = data.get(smac_keys["VALUE"])
                    print("2a")
                    db.update_device_busy(id_device=id_device, is_busy=value )
                    Clock.schedule_once(partial(db.update_device_busy, id_device, 0), value)
                    print("id_device: {} is busy".format(id_device))

                if cmd == smac_keys["CMD_INVALID_PIN"]:
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    #value = data.get(smac_keys["VALUE"])
                    db.update_pin_valid_by_device(id_device=id_device, pin_device_valid=0 )
                    ##Clock.schedule_once(partial(db.update_device_busy, id_device, 0), 5)
                    print("id_device: {} pin is invalid".format(id_device))

                if cmd == smac_keys["CMD_SET_PROPERTY"]:
                    id_prop = data.get(smac_keys["ID_PROPERTY"])
                    #type_prop = data.get(smac_keys["TYPE_PROPERTY"])
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    value = data.get(smac_keys["VALUE"])
                    db.update_value_temp_by_dev_id(id_device=id_device, id_property=id_prop, value=value)
                    '''print("w")
                    FB = set_property(type_property=type_prop, id_property=id_prop, value=value)
                    print("FB", FB)
                    if FB != None:
                        d1 = {}
                        if FB:
                            d1[smac_keys["MESSAGE"]] = "Property updated."
                            try:
                                scr = self.screen_manager.get_screen(name="Screen_network")
                                for id_topic in scr.TOPIC_IDS.keys():
                                    t_obj = scr.TOPIC_IDS[id_topic]
                                    # here topic is id_device
                                    d_obj = t_obj.DEVICE_IDS[topic]
                                    p_obj = d_obj.PROP_IDS[id_prop]
                                    p_obj.ids["id_slider"].value = int(value)
                                    p_obj.MSG_COUNTER = msg_id
                            except Exception as e:
                                print("updating slider err: {}".format(e))
                        else:
                            d1[smac_keys["MESSAGE"]] = "Property not updated."
                        client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["ACK"], message=d1, msg_id=msg_id, udp=True, tcp=False)'''



                if cmd == smac_keys["ACK"]:
                    info = msg.get( smac_keys["MESSAGE"] )
                    self.ACKS[msg_id] = info
                    print(self.ACKS)

                if cmd == smac_keys["CMD_REQ_SEND_INFO"]:
                    if not self.SENDING_INFO:
                        self.send_device_info( dest_topic="#")


                if cmd == smac_keys["CMD_SEND_INFO"]:
                    print("CMD_SEND_INFO")
                    if data.get( smac_keys["ID_TOPIC"], None) != None:
                        id_topic = data.get( smac_keys["ID_TOPIC"] )
                        name_device = data.get(smac_keys["NAME_DEVICE"], "")
                        type_device = data.get(smac_keys["TYPE_DEVICE"], "")
                        db.add_network_entry(name_topic=id_topic, id_topic=id_topic, id_device=frm, name_device=name_device, type_device=type_device, remove=0)
                        #db.update_delete_by_topic_id(id_device=frm, id_topic=id_topic, value=0)
                        print("new network entry added: {}, {}".format(id_topic, frm))
                    if data.get(smac_keys["ID_PROPERTY"], None) != None:
                        id_prop = data.get(smac_keys["ID_PROPERTY"])
                        type_prop = data.get(smac_keys["TYPE_PROPERTY"], "")
                        name_prop = data.get(smac_keys["NAME_PROPERTY"], "")
                        value = data.get(smac_keys["VALUE"], 0)
                        value_min = data.get(smac_keys["VALUE_MIN"], 0)
                        value_max = data.get(smac_keys["VALUE_MAX"], 1)
                        db.add_property(id_device=frm, id_property=id_prop, type_property=type_prop, name_property=name_prop, value=value, value_min=value_min, value_max=value_max, remove=0)
                        #db.update_delete_by_prop_id(id_device=frm, id_property=id_prop, value=0)
                        print("new property entry added: {}".format(name_prop) )

                if cmd == smac_keys["CMD_INIT_SEND_INFO"]:
                    print("updating DELETE field of entries: {}".format(frm))
                    # SET_PROPERTY field updates delte field of PROPERTY TABLE also
                    db.update_delete_by_dev_id(id_device=frm, value=1, SET_PROPERTY=True)


                if cmd == smac_keys["CMD_END_SEND_INFO"]:
                    print("deleting all entries of: {}".format(self.ID_DEVICE))
                    scr = self.screen_manager.get_screen(name="Screen_network")
                    devs = db.get_device_by_delete_field(id_device=frm, value=1)
                    #print(devs)
                    container = scr.ids["id_network_container"]
                    for id_topic in devs:
                        id_topic = id_topic[0]
                        print(id_topic)
                        print( scr.TOPIC_IDS.get(id_topic, None) )
                        if scr.TOPIC_IDS.get(id_topic, None) != None:
                            container.remove_widget(scr.TOPIC_IDS[id_topic])
                            del scr.TOPIC_IDS[id_topic]
                    print("z1")

                    props = db.get_property_by_delete_field(id_device=frm, value=1)
                    id_device = frm
                    try:
                        for id_prop in props:
                            for id_topic in scr.TOPIC_IDS.keys():
                                t_obj = scr.TOPIC_IDS[id_topic]
                                d_obj = t_obj.DEVICE_IDS[id_device]
                                d_obj.remove_widget( d_obj.PROP_IDS[id_prop] )
                    except:
                        pass

                    print("z2")
                    db.delete_network_entry_by_device( id_device=frm )
                    db.delete_property_by_device( id_device=frm )
                    print("z")



                if cmd == smac_keys["CMD_STATUS_SET_PROPERTY"]:
                    id_property = msg.get( smac_keys["ID_PROPERTY"] )
                    #id_device = frm
                    id_device= msg.get( smac_keys["ID_DEVICE"] )
                    value = msg.get( smac_keys["VALUE"])

                    '''db_value = db.get_value_by_property(id_device, id_property)
                    #print("db_value", db_value)
                    if db_value != None:
                        if value !=  (db_value[0]+1):
                            #self.open_modal(text="Value missed: {}".format(value))
                            print("Value missed: {}".format(value))'''

                    db.update_value_property_by_dev_id(id_property=id_property, id_device=frm, value=value)
                    self.update_slider_ui_val(id_device, id_property, value)

                if cmd == smac_keys["CMD_ADD_TOPIC"]:
                    id_topic = data.get(smac_keys["ID_TOPIC"])
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    passkey = data.get(smac_keys["PASSKEY"])
                    self.add_topic(frm, id_topic, id_device, passkey, msg_id)

                if cmd == smac_keys["CMD_REMOVE_TOPIC"]:
                    id_topic = data.get(smac_keys["ID_TOPIC"])
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    passkey = data.get(smac_keys["PASSKEY"])
                    self.delete_topic(frm, id_topic, id_device, passkey, msg_id)


                if cmd == smac_keys["CMD_STATUS_ADD_TOPIC"]:
                    id_topic = data.get(smac_keys["ID_TOPIC"])
                    name_device = data.get(smac_keys["NAME_DEVICE"], "")
                    type_device = data.get(smac_keys["TYPE_DEVICE"], "")
                    db.add_network_entry(name_topic=id_topic, id_topic=id_topic, id_device=frm, name_device=name_device,
                                         type_device=type_device, remove=0)

                if cmd == smac_keys["CMD_STATUS_REMOVE_TOPIC"]:
                    id_topic = data.get(smac_keys["ID_TOPIC"])
                    db.delete_network_entry_by_topic(id_topic=id_topic, id_device=frm)
                    scr = self.screen_manager.get_screen(name="Screen_network")
                    container = scr.ids["id_network_container"]
                    container.remove_widget(scr.TOPIC_IDS[id_topic])
                    del scr.TOPIC_IDS[id_topic]


        #except Exception as e:
        #    print("Exception while decoding message: {}".format(e) )

    #def change_property(self, frm, to, cmd, message, *args):
    #    client.send_message(frm=frm, to=to, message=message, cmd=cmd)

    #def open_add_group_modal(self, *args):
    #    self.modal.add_widget( BoxLayout_addGroupContent() )
    #    self.modal.open()

    #def add_group(self, group_name):
    #    self.modal.dismiss()
    #    db.add_group(group_name)

    #async def async_test(self):
    #    await asyncio.sleep(1)
    #    while 1:
    #        self.text1 = "message: {}".format(int(time.time()))
    #        await asyncio.sleep(1)

    def update_slider_ui_val(self, id_device, id_property, value ):
        try:
            scr = self.screen_manager.get_screen(name="Screen_network")
            #print(scr.TOPIC_IDS)
            #print(scr.TOPIC_IDS.keys())
            for id_topic in scr.TOPIC_IDS.keys():
                t_obj = scr.TOPIC_IDS[id_topic]
                #print(t_obj.DEVICE_IDS)
                #print(t_obj.ids)
                d_obj = t_obj.DEVICE_IDS[id_device]
                p_obj = d_obj.PROP_IDS[id_property]
                p_obj.ids["id_slider"].value = int(value)
        except Exception as e:
            print("updating slider err: {}".format(e))

    async def send_test(self, *args):
        d = {}
        d[ smac_keys["PROPERTY"] ] = SMAC_DEVICES["SWITCH"]
        d[ smac_keys["INSTANCE"] ] = 0

        msg = {}
        msg[ smac_keys["FROM"] ] = "D1"
        msg[ smac_keys["TO"] ] = "D2"
        msg[ smac_keys["COMMAND"] ] = smac_keys["CMD_SET_PROPERTY"]

        i = 0
        while 1:
            d[ smac_keys["VALUE"] ] = 1 if( i%2 == 0 ) else 0
            msg[ smac_keys["MESSAGE"] ] = d
            print("sending")
            print(msg)
            client.send_message( "D2", json.dumps(msg) )
            await asyncio.sleep(1)
            #time.sleep(1)
            i += 1


    #async def check_for_prop_value_change(self, *args):
    #    props = db.get_property(id_device=self.ID_DEVICE)

    def t(self, *args):
        async def start_app():
            print("starting app")
            await self.async_run(async_lib="asyncio") 

        

        #task1 = asyncio.ensure_future( self.async_test() )
        task2 = asyncio.ensure_future( client.main() )
        task3 = asyncio.ensure_future( self.set_property_of_current_device() )
        #task3 = asyncio.ensure_future( self.send_test() )

        #return asyncio.gather( start_app(),zmq_sub_start, zmq_pub_start, task1, zmq_t1, zmq_t2, udp_t1, udp_t2, test1 )
        return asyncio.gather( start_app(), task2, task3)

    def test_send_status(self, *args):
        self.TEST_VAL = 1 - self.TEST_VAL
        m = {}
        m[ smac_keys["ID_PROPERTY"] ] = "0"
        m[ smac_keys["ID_DEVICE"] ] = self.ID_DEVICE
        m[ smac_keys["VALUE"] ] =  self.TEST_VAL
        print("m", m)
        client.send_message(frm=self.ID_DEVICE, to="T1", cmd=smac_keys["CMD_STATUS"] , message=m, udp=True, tcp=False)


    def send_info(self, *args):
        Clock.schedule_once(partial(client.send_message, self.ID_DEVICE, "#", smac_keys["CMD_REQ_SEND_INFO"] , {}, False, None, True, False), 5)
        self.send_device_info(dest_topic="#")
        #Clock.schedule_interval(self.test_send_status, 0)
        #Clock.schedule_interval(self.check_for_new_value, 0)

    # check for value_temp and update the value of property according to that
    async def set_property_of_current_device(self, *args):
        while 1:
            for id_property, property_name, type_property, value_min, value_max, value, value_temp, value_last_updated in db.get_property_list_by_device(self.ID_DEVICE):
                type_property = str(type_property)
                t_diff = time.time() - int(value_last_updated)
                DIFF = .5       # ensure property is stable for .5 secs
                if (type_property not in [SMAC_PROPERTY["BATTERY"]]) and (value != value_temp):
                    print(SMAC_PROPERTY[type_property])
                    print("t_diff", t_diff)
                    if t_diff > DIFF:
                        # db.update_value_property_by_dev_id(id_device=id_device, id_property=id_property, value=value_temp)
                        set_property(type_property=type_property, value=int(value_temp), id_property=id_property)
                    else:
                        print("Device is Busy")
                        d = {}
                        d[smac_keys["ID_DEVICE"]] = self.ID_DEVICE
                        d[smac_keys["VALUE"]] = 5
                        client.send_message(frm=self.ID_DEVICE, to="#", cmd=smac_keys["CMD_DEVICE_BUSY"], message=d, udp=True, tcp=False )
                    #else:
                        #self.open_modal(text=)
            await asyncio.sleep(.1)

    def get_local_ip(self, *args):
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip =  s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"


    def update_config_variable(self, key, value, arr_op="ADD"):
        with open('config.json', 'r') as f:
            fd = json.load(f)
            if key == "SUB_TOPIC":
                if arr_op == "ADD":
                    fd[key] += [ value ]
                elif arr_op == "REM":
                    if value in fd[key]:
                        fd[key].remove(value)
            else:
                fd[key] = value
            f.close()
        with open('config.json', 'w') as f:
            f.write(json.dumps(fd))
            f.flush()

    def load_config_variables(self, *args):
        from smac_device import get_device_name, get_device_type
        changed = False
        if not os.path.isfile('config.json'):
            f = open("config.json", "w")
            d = {}
            d["ID_DEVICE"] =""
            d["TYPE_DEVICE"] = "0"
            d["NAME_DEVICE"] = ""
            d["PIN_DEVICE"] = "1234"
            d["SUB_TOPIC"] = ["#"]
            f.write(json.dumps(d))
            f.close()

        with open('config.json', 'r') as f:
            fd = json.load(f)
            if fd["ID_DEVICE"] == "":
                d_id = self.get_local_ip()
                #d_id = req_get_device_id()
                if (d_id != "") and (d_id != None):
                    fd["ID_DEVICE"] = d_id
                changed = True
            self.ID_DEVICE = fd["ID_DEVICE"]
            if fd["NAME_DEVICE"] == "":
                fd["NAME_DEVICE"] = get_device_name()
                changed = True
            self.NAME_DEVICE = fd["NAME_DEVICE"]
            if fd["TYPE_DEVICE"] == "":
                fd["TYPE_DEVICE"] = get_device_type()
                changed = True
            self.TYPE_DEVICE = fd["TYPE_DEVICE"]
            self.PIN_DEVICE = fd["PIN_DEVICE"]
            if fd["SUB_TOPIC"] == []:
                fd["SUB_TOPIC"] = ["#", self.ID_DEVICE]
                changed = True
            self.SUB_TOPIC = fd["SUB_TOPIC"]
            f.close()

        print("fd", fd)
        if changed:
            with open('config.json', 'w') as f:
                f.write( json.dumps(fd) )

    def open_modal(self, text, auto_close=False, timeout=3, *args):
        self.modal.label.text = text
        if not self.modal_opened:
            self.modal.open()
        else:
            self.modal_opened = True
        if auto_close:
            self.modal.timer = Clock.schedule_once(self.close_modal, timeout)

    def close_modal(self, *args):
        self.modal.label.text = ""
        self.modal.dismiss()
        self.modal_opened = False
        if self.modal.timer != None:
            self.modal.timer.cancel()
            self.modal.timer = None

    def on_stop(self):
        loop.close()

    def on_resume(self):
        return True

    def on_start(self):
        print("kivy started")
        print("starting smac_client...")

        self.modal.label = Label(text='')
        self.modal.add_widget(self.modal.label)
        self.load_config_variables()
        #topics = [ i[0] for i in  db.get_topic_list()]
        topics = self.SUB_TOPIC
        client.subscribe( ["#", self.ID_DEVICE] + topics )
        client.process_message = self.on_message
        tps = db.get_topic_list()
        if len(tps) < 1:
            db.add_network_entry(name_topic="", id_topic="", id_device=self.ID_DEVICE, name_device=self.NAME_DEVICE, type_device=self.TYPE_DEVICE)

        li = db.get_property_list_by_device(self.ID_DEVICE)
        if len(li) < 1:
            for i in get_device_property(self.ID_DEVICE):
                print(i)
                db.add_property(id_device=self.ID_DEVICE, id_property=i["id_property"], type_property=i["type_property"], name_property=i["name_property"], value_min=i["value_min"], value_max=i["value_max"], value=i["value"])

        print("kivy started few seconds ago")
        if platform == "android":
            from android.permissions import request_permissions, check_permission, Permission
            print("permision", check_permission(Permission.CAMERA))
            if not check_permission(Permission.CAMERA):
                request_permissions([Permission.CAMERA])

            from jnius import autoclass, cast
            Intent = autoclass('android.content.Intent')
            System = autoclass('android.provider.Settings$System')
            Settings = autoclass('android.provider.Settings')
            BuildVERSION = autoclass('android.os.Build$VERSION')
            BuildVERSION_CODES = autoclass('android.os.Build$VERSION_CODES')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Uri = autoclass('android.net.Uri')

            # refer
            # https://stackoverflow.com/questions/41969548/having-multiple-activities-in-kivy-for-android
            # https://stackoverflow.com/questions/32083410/cant-get-write-settings-permission
            activity = PythonActivity.mActivity
            if (BuildVERSION.SDK_INT >= BuildVERSION_CODES.M) :
                if (not System.canWrite(activity.getApplicationContext())):
                    intent = Intent(Settings.ACTION_MANAGE_WRITE_SETTINGS, Uri.parse("package:" + activity.getApplicationContext().getPackageName()));
                    #activity.getApplicationContext().startActivity(intent, 200);
                    currentActivity = cast('android.app.Activity', activity)
                    currentActivity.startActivity(intent)



        for i in get_device_property(self.ID_DEVICE):
            print( SMAC_PROPERTY[i["type_property"]] )
            value =  get_property_value(type_property=i["type_property"], id_property=i["id_property"] )
            db.update_value_property_by_dev_id(id_device=self.ID_DEVICE, id_property=i["id_property"], value=str(value) )

        self.text1 = "message: {}".format("kivy started")
        self.send_info()
        


#SmacApp().async_run(async_lib='asyncio')
#asyncio.run(SmacApp().t())
loop = asyncio.get_event_loop()
loop.run_until_complete(SmacApp().t())
loop.close()