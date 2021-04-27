import os
from datetime import datetime
#import time

from kivy.properties import *
#from kivy.utils import get_color_from_hex, platform
#from kivy.uix.screenmanager import ScreenManager, Screen, CardTransition, NoTransition, SlideTransition, SwapTransition, FadeTransition, WipeTransition, FallOutTransition, RiseInTransition
from kivy.uix.screenmanager import ScreenManager, NoTransition
#from kivy.core.window import Window

from smac_device import set_property, get_device_property, get_property_value, property_listener
from smac_theme_colors import THEME_LIGHT, THEME_DARK

#Window.clearcolor = get_color_from_hex("#e0e0e0")

import json

from smac_device_keys import SMAC_DEVICES
from smac_widgets.smac_screens import *
from smac_widgets.smac_layouts import *
from smac_db import db


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
    modal = ModalView_custom(size_hint_x=.9, size_hint_max_x=dp(400), size_hint_y=None, height=dp(400))
    is_modal_open = False
    APP_DATA = DictProperty({
        "id_topic": "",
        "name_topic": "",
        "name_home": "Local",
        "id_device": "",
        "name_device": "",
        "type_device": "",
        "id_context": ""
    })
    ID_DEVICE = ""
    NAME_DEVICE = ""
    TYPE_DEVICE = "0"
    PIN_DEVICE = "1234"
    SUB_TOPIC = ["#"]
    ACKS = [] # ACK format = [ <id_topic>:<id_device>:<smac_id> ]
    LIMITS = {
        "LIMIT_DEVICE": 10,
        "LIMIT_TOPIC": 10
    }
    _TASKS = [] # ID: (task_function, args )
    TASKS = {}
    TASK_ID = 0
    SENDING_INFO = 0
    TEST_VAL = 0
    INTERVAL_ONLINE = 30
    theme = OptionProperty("LIGHT", options=["LIGHT", "DARK"])
    colors = DictProperty(THEME_LIGHT)
    source_icon = StringProperty("icons/LIGHT/")

    def on_theme(self, *args):
        if self.theme == "DARK":
            self.colors = THEME_DARK
            self.source_icon = "icons/DARK/"
            self.update_config_variable(key="theme", value="DARK")
        else:
            self.colors = THEME_LIGHT
            self.source_icon = "icons/LIGHT/"
            self.update_config_variable(key="theme", value="LIGHT")

    def add_task(self,  func, args):
        self.TASKS[ str(self.TASK_ID) ] = (func, args)
        self.TASK_ID += 1

    def remove_task(self, task_id):
        if str(task_id) in self.TASKS.keys():
            del self.TASKS[task_id]

    def build(self):
        Builder.load_file('smac_widgets/smac_screens.kv')
        Builder.load_file('smac_widgets/smac_layouts.kv')
        self.screen_manager.add_widget(Screen_network(name='Screen_network'))
        self.screen_manager.add_widget(Screen_deviceSetting(name='Screen_deviceSetting'))
        self.screen_manager.add_widget(Screen_context(name='Screen_context'))
        #self.screen_manager.add_widget(Screen_devices(name='Screen_devices'))
        #self.screen_manager.add_widget(Screen_property(name='Screen_deviceSetting'))
        return self.screen_manager

    def change_screen(self, screen, *args):
        self.screen_manager.current = screen

    def open_modal(self, content, title="Info", auto_dismiss=True):
        if content != None:
            #print(content.height)
            self.modal.content = content
            self.modal.title = title
            #self.modal.content.parent.parent.parent.height = content.height + dp(70)
            self.modal.height = content.height + dp(70)
            self.modal.open(auto_dismiss=auto_dismiss)
            self.is_modal_open = True

            scr = self.screen_manager.get_screen( self.screen_manager.current )
            #print(scr)
            scr.get_selectable_nodes(widget=self.modal)


    def close_modal(self, *args):
        #self.modal.content = None
        self.modal.title = ""
        self.modal.dismiss()
        self.is_modal_open = False
        scr = self.screen_manager.get_screen(self.screen_manager.current)
        scr.get_selectable_nodes()

    def open_modalInfo(self, title="Info", text="", auto_dismiss=True):
        print("text", text)
        label = Label(text=text, color=[1, 1, 1, 1])
        label.text = text
        # self.modal.clear_widgets()
        self.modal.title = title
        self.modal.content = label
        self.modal.height = dp(400)
        self.modal.open(auto_dismiss=auto_dismiss)
        self.is_modal_open = True

    def close_modalInfo(self, *args):
        self.close_modal()

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

    def get_command_status_text(self, cmd):
        if cmd == smac_keys["CMD_STATUS_ADD_TOPIC"]:
            return "Subscribed to Home."
        elif cmd == smac_keys["CMD_STATUS_REMOVE_TOPIC"]:
            return "Unsubscribed to Home."
        elif cmd == smac_keys["CMD_INVALID_PIN"]:
            return "Invalid PIN. Update the PIN."
        elif cmd == smac_keys["CMD_STATUS_UPDATE_NAME_PROPERTY"]:
            return "Property Name Updated"
        elif cmd == smac_keys["CMD_STATUS_UPDATE_NAME_DEVICE"]:
            return "Device Name Updated"
        elif cmd == smac_keys["CMD_STATUS_UPDATE_INTERVAL_ONLINE"]:
            return "Device Online Interval Updated"
        elif cmd == smac_keys["CMD_TOPIC_LIMIT_EXCEEDED"]:
            return "Home Limit for the Device is Exceeded"
        elif cmd == smac_keys["CMD_ACTION_LIMIT_EXCEEDED"]:
            return "Context Action Limit for the Device is Exceeded"
        elif cmd == smac_keys["CMD_TRIGGER_LIMIT_EXCEEDED"]:
            return "Context Trigger Limit for the Device is Exceeded"
        elif cmd == smac_keys["CMD_STATUS_UPDATE_WIFI_CONFIG"]:
            return "Wifi Config Updated"
        elif cmd == smac_keys["CMD_STATUS_ADD_ACTION"]:
            return "Context Action Added"
        elif cmd == smac_keys["CMD_STATUS_REMOVE_ACTION"]:
            return "Context Action Removed"
        elif cmd == smac_keys["CMD_STATUS_ADD_TRIGGER"]:
            return "Context Trigger Added"
        elif cmd == smac_keys["CMD_STATUS_REMOVE_TRIGGER"]:
            return "Context Trigger Removed"
        else:
            return smac_keys[cmd]


    def add_topic(self, frm, id_topic, name_home, name_topic, id_device, passkey, *args):
        #topics = self.SUB_TOPIC
        #topics.remove("#")
        #topics.remove(self.ID_DEVICE)
        # self.SUB_TOPIC - 2 is because the device is subscribed to "#" and itself ie self.ID_DEVICE
        print("len SUB_TOPIC", len(self.SUB_TOPIC))
        print("limit topic", self.LIMITS["LIMIT_TOPIC"])
        if len(self.SUB_TOPIC) <= self.LIMITS["LIMIT_TOPIC"]:

            if str(passkey) == str(self.PIN_DEVICE):
                db.add_network_entry(name_home=name_home,name_topic=name_topic, id_topic=id_topic, id_device=id_device, name_device=self.NAME_DEVICE, type_device=self.TYPE_DEVICE)
                self.update_config_variable(key='SUB_TOPIC', value=id_topic, arr_op="ADD")
                client.subscribe(id_topic)
                d = {}
                d[ smac_keys["ID_TOPIC"] ] = id_topic
                d[ smac_keys["NAME_DEVICE"]] = self.NAME_DEVICE
                d[ smac_keys["TYPE_DEVICE"]] = self.TYPE_DEVICE
                d[ smac_keys["NAME_HOME"]] = name_home
                d[ smac_keys["NAME_TOPIC"]] = name_topic
                client.send_message(frm=self.ID_DEVICE, to="#", cmd=smac_keys["CMD_STATUS_ADD_TOPIC"], message=d)
                # sending ACK
                d1 = {}
                d1[ smac_keys["MESSAGE"] ] = "Topic subscribed successfylly"
                print("subscribed topic: {}".format(id_topic))
            else:
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Topic '{}' not subscribed".format(id_topic)
                d1[smac_keys["ID_DEVICE"]] = id_device
                d1[smac_keys["ID_TOPIC"]] = id_topic
                print("Cannot subscribe to {}. Passkey error.".format(id_topic))
                if self.ID_DEVICE == frm:
                    print("same device")
                else:
                    client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)
                    #client.send_message(frm=self.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)

        else:
            d1 = {}
            d1[smac_keys["MESSAGE"]] = "Topic '{}/{}' not subscribed. Topic Limit Reached.".format(name_home, name_topic)
            d1[smac_keys["ID_DEVICE"]] = id_device
            d1[smac_keys["ID_TOPIC"]] = id_topic
            print("Cannot subscribe to {}. Topic Limit Reached.".format(id_topic))
            if self.ID_DEVICE == frm:
                print("same device")
            else:
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_TOPIC_LIMIT_EXCEEDED"], message=d1)
                # client.send_message(frm=self.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_INVALID_PIN"], messa

    '''def send_req_delete_topic(self, id_topic, id_device, passkey, *args):
        if id_device == self.ID_DEVICE:
            self.delete_topic(frm=id_device, id_topic=id_topic, id_device=id_device, passkey=passkey, id_msg=None)
        else:
            d = {}
            d[smac_keys["ID_TOPIC"]] = id_topic
            d[smac_keys["ID_DEVICE"]] = id_device
            d[smac_keys["PASSKEY"]] = passkey
            MSG_ID = (client.MSG_ID +1)
            client.send_message(frm=self.ID_DEVICE, to=id_device, cmd=smac_keys["CMD_REMOVE_TOPIC"], message=d, udp=True, tcp=False)'''

    def delete_topic_widget(self, id_topic):
        scr = self.screen_manager.get_screen(name="Screen_network")
        container = scr.ids["id_network_container"]
        print(id_topic)
        print(scr.TOPIC_IDS.get(id_topic, None))
        if scr.TOPIC_IDS.get(id_topic, None) != None:
            container.remove_widget(scr.TOPIC_IDS[id_topic])
            del scr.TOPIC_IDS[id_topic]

    def remove_action_widget(self, id_context, id_device, id_property):
        app = App.get_running_app()
        scr = app.screen_manager.get_screen(name="Screen_context")
        container = scr.ids["id_context_container"]
        if container.ids.get(id_context, None) != None:
            cxt = container.ids[id_context]
            act_id = "act_{}:{}".format(id_device, id_property)
            if cxt.ids.get(act_id, None) != None:
                cxt.ids["id_action_container"].remove_widget( cxt.ids[act_id] )
                del cxt.ids[act_id]

    def remove_trigger_widget(self, id_context, id_device, id_property):
        app = App.get_running_app()
        scr = app.screen_manager.get_screen(name="Screen_context")
        container = scr.ids["id_context_container"]
        if container.ids.get(id_context, None) != None:
            cxt = container.ids[id_context]
            trig_id = "trig_{}:{}".format(id_device, id_property)
            if cxt.ids.get(trig_id, None) != None:
                cxt.ids["id_trigger_container"].remove_widget( cxt.ids[trig_id] )
                del cxt.ids[trig_id]

    def delete_topic(self, frm, id_topic, id_device, passkey, *args):
        print(passkey)
        print(self.PIN_DEVICE)
        print(passkey == self.PIN_DEVICE)
        #print(type(passkey))
        #print(type(self.PIN_DEVICE))
        if str(passkey) == str(self.PIN_DEVICE):
            #db.add_network_entry(name_topic=id_topic, id_topic=id_topic, id_device=id_device, name_device=self.NAME_DEVICE, type_device=self.TYPE_DEVICE)
            db.delete_network_entry_by_topic(id_topic, id_device)
            self.update_config_variable(key='SUB_TOPIC', value=id_topic, arr_op="REM")
            client.unsubscribe(id_topic)
            self.delete_topic_widget(id_topic)
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
            d1[smac_keys["ID_DEVICE"]] = id_device
            d1[smac_keys["ID_TOPIC"]] = id_topic
            print("Cannot unsubscribe to {}. Passkey error.".format(id_topic))
            if self.ID_DEVICE == frm:
                print("same device")
            else:
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)
                #client.send_message(frm=self.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)

        # if sent from the same device
        #if self.ID_DEVICE != frm:
        #    client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["ACK"], message=d1, msg_id=id_msg, udp=True, tcp=False)
        #else:
        #    print( d1[smac_keys["MESSAGE"]] )

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

    def send_device_info(self, dest_topic, udp=True, tcp=True, *args):
        self.SENDING_INFO = 1
        #topics = client.SUB_TOPIC
        #print(topics)
        #print(client.SUB_TOPIC)
        #topics.remove( "#" )
        #topics.remove( self.ID_DEVICE)
        if tcp:
            topics = db.get_topic_list_by_device(id_device=self.ID_DEVICE)
        else:
            topics = [ ("", "", "") ]
        #topics.append( ("#", "", "") )
        print("topics" ,topics)
        print("dest_topic", dest_topic)
        #client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd= smac_keys["CMD_INIT_SEND_INFO"], message={}, udp=True, tcp=False)
        for id_topic, name_home, name_topic in topics:
            print("aa", id_topic )
            if id_topic not in ["#", self.ID_DEVICE]:
                print("ab")
                m = {}
                m[ smac_keys["TOPIC"]] = 1
                m[ smac_keys["ID_TOPIC"] ] = id_topic if(id_topic != None) else ""
                m[ smac_keys["NAME_TOPIC"] ] = name_topic if(name_topic != None) else ""
                m[ smac_keys["NAME_HOME"] ] = name_home if(name_home != None) else ""
                m[ smac_keys["NAME_DEVICE"] ] = self.NAME_DEVICE
                m[ smac_keys["TYPE_DEVICE"] ] = self.TYPE_DEVICE
                #print(m)
                #time.sleep(.1)
                client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=m, udp=udp, tcp=tcp)
                print("sent {}".format(id_topic))

                for id_topic, id_context, name_context in db.get_context_by_topic(id_topic):
                    c1 = {}
                    c1[ smac_keys["CONTEXT"] ] = 1
                    c1[ smac_keys["ID_TOPIC"] ] = id_topic if(id_topic != None) else ""
                    c1[ smac_keys["ID_CONTEXT"] ] = id_context if(id_context != None) else ""
                    c1[ smac_keys["NAME_CONTEXT"] ] = name_context if(name_context != None) else ""
                    client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=c1 ,udp=udp, tcp=tcp)
        print("sent topics")

        for p in db.get_property(self.ID_DEVICE):
            print(p)
            p1 = {}
            p1[smac_keys["PROPERTY"]] = 1
            p1[smac_keys["ID_DEVICE"]] = self.ID_DEVICE
            p1[smac_keys["ID_PROPERTY"]] = p[2]
            p1[smac_keys["TYPE_PROPERTY"]] = p[3]
            p1[smac_keys["NAME_PROPERTY"]] = p[4]
            p1[smac_keys["VALUE"]] = p[5]
            p1[smac_keys["VALUE_MIN"]] = p[6]
            p1[smac_keys["VALUE_MAX"]] = p[7]
            client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=p1, udp=udp,
                                tcp=tcp)
        print("send property")

        for id_topic1, id_context, id_device, id_property, value, name_context in db.get_action_by_device_only(self.ID_DEVICE):
            c2 = {}
            c2[ smac_keys["CONTEXT_ACTION"] ] = 1
            c2[ smac_keys["ID_TOPIC"]] = id_topic1 if (id_topic1 != None) else ""
            c2[ smac_keys["ID_CONTEXT"]] = id_context if (id_context != None) else ""
            c2[ smac_keys["ID_DEVICE"]] = id_device
            c2[ smac_keys["ID_PROPERTY"]] = id_property
            c2[ smac_keys["VALUE"] ] = value
            c2[ smac_keys["NAME_CONTEXT"] ] = name_context
            client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=c2, udp=udp, tcp=tcp)

        for id_topic2, id_context, id_device, id_property, value, type_trigger in db.get_trigger_by_device(self.ID_DEVICE):
            c2 = {}
            c2[ smac_keys["CONTEXT_TRIGGER"] ] = 1
            c2[ smac_keys["ID_TOPIC"]] = id_topic2 if (id_topic2 != None) else ""
            c2[ smac_keys["ID_CONTEXT"]] = id_context if (id_context != None) else ""
            c2[ smac_keys["ID_DEVICE"]] = id_device
            c2[ smac_keys["ID_PROPERTY"]] = id_property
            c2[ smac_keys["VALUE"] ] = value
            c2[ smac_keys["TYPE_TRIGGER"]] = type_trigger
            #c2[ smac_keys["NAME_CONTEXT"] ] = name_context
            client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=c2, udp=udp, tcp=tcp)




        #client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_END_SEND_INFO"], message={},
        #                    udp=True, tcp=False)
        self.SENDING_INFO = 0

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
                client.send_message(frm=self.ID_DEVICE, to=id_topic, message=d, cmd=smac_keys["CMD_STATUS_SET_PROPERTY"], udp=True, tcp=True)

    def on_message(self, topic, message, protocol,  *args):
            print( "{}, {}, {}".format(topic, message, protocol) )
        #try:
            msg = json.loads(message)
            #print("1")
            frm = msg.get( smac_keys["FROM"] , None)
            to = msg.get( smac_keys["TO"], None)
            cmd = msg.get( smac_keys["COMMAND"], None )
            ack = msg.get( smac_keys["ACK"], None )
            msg_id = msg.get( smac_keys["ID_MESSAGE"], None )
            #print(cmd == smac_keys["CMD_UPDATE_NAME_PROPERTY"])
            #print(frm)
            #print(self.ID_DEVICE)
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
                    value = value if type(value) == int else int(value)
                    print("2a")
                    busy_period = int(time.time()) + value
                    db.update_device_busy(id_device=id_device, is_busy=1, busy_period=busy_period )
                    #db.update_device_busy_period(id_device=id_device, busy_period=busy_period)
                    #Clock.schedule_once(partial(db.update_device_busy, id_device, 0), value)
                    print("id_device: {} is busy".format(id_device))
                    #self.ACKS.append("{}:{}:{}".format(topic, id_device, smac_keys["CMD_INVALID_PIN"]))

                if cmd == smac_keys["CMD_INVALID_PIN"]:
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    id_topic = data.get(smac_keys["ID_TOPIC"], "")
                    id_property = data.get(smac_keys["ID_PROPERTY"], "")
                    #value = data.get(smac_keys["VALUE"])
                    db.update_pin_valid(id_device=id_device, pin_device_valid=0 )
                    ##Clock.schedule_once(partial(db.update_device_busy, id_device, 0), 5)
                    print("id_device: {} pin is invalid".format(id_device))
                    #self.ACKS.append("{}:{}:{}".format(topic, id_device, smac_keys["CMD_INVALID_PIN"]))
                    db.add_command_status(id_topic=id_topic, id_device=id_device, cmd=cmd, id_property=id_property)

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
                        #if protocol == "UDP":
                            self.send_device_info( dest_topic="#", udp=True)
                        #elif protocol == "ZMQ":
                        #    self.send_device_info(dest_topic="#", tcp=False)


                if cmd == smac_keys["CMD_SEND_INFO"]:
                    print("CMD_SEND_INFO")
                    if data.get( smac_keys["TOPIC"], None) != None:
                        id_device = data.get( smac_keys["ID_DEVICE"] )
                        id_topic = data.get( smac_keys["ID_TOPIC"] )
                        name_device = data.get(smac_keys["NAME_DEVICE"], "")
                        name_home = data.get(smac_keys["NAME_HOME"], "")
                        name_topic = data.get(smac_keys["NAME_TOPIC"], "")
                        type_device = data.get(smac_keys["TYPE_DEVICE"], "")
                        if (protocol == "UDP") or ((protocol == "TCP") and (id_topic != '') and  (id_topic in self.SUB_TOPIC)):
                            db.add_network_entry(name_home=name_home, name_topic=name_topic, id_topic=id_topic, id_device=frm, name_device=name_device, type_device=type_device, remove=0)
                            #db.update_delete_by_topic_id(id_device=frm, id_topic=id_topic, value=0)
                            print("new network entry added: {}, {}".format(id_topic, frm))
                        print("12")
                    if data.get(smac_keys["PROPERTY"], None) != None:
                        id_device = data.get(smac_keys["ID_DEVICE"])
                        id_prop = data.get(smac_keys["ID_PROPERTY"])
                        type_prop = data.get(smac_keys["TYPE_PROPERTY"], "")
                        name_prop = data.get(smac_keys["NAME_PROPERTY"], "")
                        value = data.get(smac_keys["VALUE"], 0)
                        value_min = data.get(smac_keys["VALUE_MIN"], 0)
                        value_max = data.get(smac_keys["VALUE_MAX"], 1)
                        if (protocol == "UDP") or ((protocol == "TCP") and  len(db.get_property_list_by_device(id_device)) >0):
                            db.add_property(id_device=id_device, id_property=id_prop, type_property=type_prop, name_property=name_prop, value=value, value_min=value_min, value_max=value_max, remove=0)
                            #db.update_delete_by_prop_id(id_device=frm, id_property=id_prop, value=0)
                            print("new property entry added: {}".format(name_prop) )
                        #print("13")

                    if data.get(smac_keys["CONTEXT"], None) != None:
                        id_topic = data.get(smac_keys["ID_TOPIC"])
                        id_context = data.get( smac_keys["ID_CONTEXT"] )
                        name_context = data.get( smac_keys["NAME_CONTEXT"] )
                        db.add_context(id_context=id_context, id_topic=id_topic, name_context=name_context)
                        #print("14")

                    if data.get(smac_keys["CONTEXT_ACTION"], None) != None:
                        id_topic = data.get(smac_keys["ID_TOPIC"])
                        id_context = data.get( smac_keys["ID_CONTEXT"] )
                        id_device = data.get( smac_keys["ID_DEVICE"] )
                        id_property = data.get( smac_keys["ID_PROPERTY"] )
                        value = data.get( smac_keys["VALUE"] )
                        name_context = data.get( smac_keys["NAME_CONTEXT"] )
                        db.add_context_action(id_context, id_topic, id_device, id_property, name_context, value)

                    if data.get(smac_keys["CONTEXT_TRIGGER"], None) != None:
                        id_topic = data.get(smac_keys["ID_TOPIC"])
                        id_context = data.get(smac_keys["ID_CONTEXT"])
                        id_device = data.get(smac_keys["ID_DEVICE"])
                        id_property = data.get(smac_keys["ID_PROPERTY"])
                        value = data.get(smac_keys["VALUE"])
                        #name_context = data.get(smac_keys["NAME_CONTEXT"])
                        db.add_context_trigger(id_context, id_topic, id_device, id_property, value)




                if cmd == smac_keys["CMD_INIT_SEND_INFO"]:
                    print("updating DELETE field of entries: {}".format(frm))
                    # SET_PROPERTY field updates delte field of PROPERTY TABLE also
                    db.update_delete_by_dev_id(id_device=frm, value=1, SET_PROPERTY=True)


                if cmd == smac_keys["CMD_END_SEND_INFO"]:
                    print("deleting all entries of: {}".format(frm))
                    scr = self.screen_manager.get_screen(name="Screen_network")
                    devs = db.get_device_by_delete_field(id_device=frm, value=1)
                    for id_topic in devs:
                        #id_topic = id_topic[0]
                        self.delete_topic_widget(id_topic[0])
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
                    id_property = str( msg.get( smac_keys["ID_PROPERTY"] ) )
                    #id_device = frm
                    id_device=  str( msg.get( smac_keys["ID_DEVICE"] ) )
                    value = msg.get( smac_keys["VALUE"])

                    '''db_value = db.get_value_by_property(id_device, id_property)
                    #print("db_value", db_value)
                    if db_value != None:
                        if value !=  (db_value[0]+1):
                            #self.open_modal(text="Value missed: {}".format(value))
                            print("Value missed: {}".format(value))'''

                    #print(type(value))
                    #print(id_device)
                    #print(type(id_device))
                    #print(id_property)
                    #print(type(id_property))
                    db.update_value_property_by_dev_id(id_property=id_property, id_device=frm, value=value)
                    self.update_slider_ui_val(id_device, id_property, value)
                    self.check_for_action_trigger_status(id_device, id_property, value)

                if cmd == smac_keys["CMD_ADD_TOPIC"]:
                    id_topic = data.get(smac_keys["ID_TOPIC"])
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    passkey = data.get(smac_keys["PASSKEY"])
                    name_home = data.get(smac_keys["NAME_HOME"])
                    name_topic = data.get(smac_keys["NAME_TOPIC"])
                    self.add_topic(frm, id_topic, name_home, name_topic, id_device, passkey, msg_id)
                    #self.ACKS.append( "{}:{}:{}".format(id_topic, id_device, smac_keys["CMD_ADD_TOPIC"]) )

                if cmd == smac_keys["CMD_REMOVE_TOPIC"]:
                    id_topic = data.get(smac_keys["ID_TOPIC"])
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    passkey = data.get(smac_keys["PASSKEY"])
                    self.delete_topic(frm, id_topic, id_device, passkey, msg_id)

                if cmd == smac_keys["CMD_STATUS_ADD_TOPIC"]:
                    id_topic = data.get(smac_keys["ID_TOPIC"])
                    name_device = data.get(smac_keys["NAME_DEVICE"], "")
                    name_topic = data.get(smac_keys["NAME_TOPIC"], "")
                    name_home = data.get(smac_keys["NAME_HOME"], "")
                    type_device = data.get(smac_keys["TYPE_DEVICE"], "")
                    if ((protocol == "TCP") and len(db.get_property_list_by_device(frm)) > 0):
                        db.add_network_entry(name_home=name_home, name_topic=name_topic, id_topic=id_topic, id_device=frm, name_device=name_device,
                                         type_device=type_device, remove=0)
                    #self.ACKS.append( "{}:{}:{}".format(id_topic, id_device, smac_keys["CMD_STATUS_ADD_TOPIC"]) )
                    db.add_command_status(id_topic=id_topic, id_device=frm, cmd=cmd)


                if cmd == smac_keys["CMD_STATUS_REMOVE_TOPIC"]:
                    id_topic = data.get(smac_keys["ID_TOPIC"])
                    if ((protocol == "TCP") and len(db.get_property_list_by_device(frm)) > 0):
                        db.delete_network_entry_by_topic(id_topic=id_topic, id_device=frm)
                        db.add_command_status(id_topic=id_topic, id_device=frm, cmd=cmd)
                        scr = self.screen_manager.get_screen(name="Screen_network")
                        container = scr.ids["id_network_container"]
                        container.remove_widget(scr.TOPIC_IDS[id_topic])
                        del scr.TOPIC_IDS[id_topic]
                        #self.ACKS.append( "{}:{}:{}".format(id_topic, id_device, smac_keys["CMD_STATUS_REMOVE_TOPIC"]) )

                if cmd == smac_keys["CMD_ONLINE"]:
                    db.update_device_last_updated(id_device=frm)

                if cmd in [ smac_keys["CMD_TOPIC_LIMIT_EXCEEDED"], smac_keys["CMD_ACTION_LIMIT_EXCEEDED"], smac_keys["CMD_TRIGGER_LIMIT_EXCEEDED"] ]:
                    id_topic = data.get(smac_keys["ID_TOPIC"], "")
                    id_context = data.get(smac_keys["ID_CONTEXT"], "")
                    db.add_command_status(id_topic=id_topic, id_context=id_context, id_device=frm, cmd=cmd)

                if cmd == smac_keys["CMD_UPDATE_NAME_DEVICE"]:
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    name_device = data.get(smac_keys["NAME_DEVICE"])
                    passkey = data.get( smac_keys["PASSKEY"] )
                    self.update_name_device(frm, id_device, name_device, passkey)

                if cmd == smac_keys["CMD_STATUS_UPDATE_NAME_DEVICE"]:
                    id_topic = ""
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    name_device = data.get(smac_keys["NAME_DEVICE"])
                    db.update_device_name(id_device, name_device)
                    #id_device = id_device
                    db.add_command_status(id_topic=id_topic, id_device=frm, cmd=cmd)

                if cmd == smac_keys["CMD_UPDATE_NAME_PROPERTY"]:
                    #print("111")
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    #print("112")
                    id_property = data.get(smac_keys["ID_PROPERTY"])
                    #print("113")
                    name_property = data.get(smac_keys["NAME_PROPERTY"])
                    #print("114")
                    passkey = data.get( smac_keys["PASSKEY"] )
                    #print("id_prop", id_property)
                    #print("id_device", id_device)
                    #print("name_prop", name_property)
                    self.update_name_property(frm, id_device, name_property, id_property, passkey)


                if cmd == smac_keys["CMD_STATUS_UPDATE_NAME_PROPERTY"]:
                    id_topic = ""
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    id_property = data.get(smac_keys["ID_PROPERTY"])
                    name_property = data.get(smac_keys["NAME_PROPERTY"])
                    db.update_name_property(id_device, id_property, name_property)
                    db.add_command_status(id_topic=id_topic, id_device=frm, cmd=cmd, id_property=id_property)

                if cmd == smac_keys["CMD_UPDATE_INTERVAL_ONLINE"]:
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    interval_online = data.get(smac_keys["INTERVAL"])
                    passkey = data.get( smac_keys["PASSKEY"] )
                    self.update_interval_online(frm, id_device, interval_online, passkey)

                if cmd == smac_keys["CMD_STATUS_UPDATE_INTERVAL_ONLINE"]:
                    id_topic = ""
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    interval_online = data.get(smac_keys["INTERVAL"])
                    db.update_device_interval_online(id_device, interval_online)
                    db.add_command_status(id_topic=id_topic, id_device=frm, cmd=cmd)

                if cmd == smac_keys["CMD_STATUS_UPDATE_WIFI_CONFIG"]:
                    id_topic = ""
                    db.add_command_status(id_topic=id_topic, id_device=frm, cmd=cmd)

                if cmd == smac_keys["CMD_STATUS_UPDATE_SOFTWARE"]:
                    m = data.get(smac_keys["MESSAGE"], "")
                    if m != "":
                        self.open_modalInfo(text=m , title="Info")

                if cmd == smac_keys["CMD_STATUS_ADD_CONTEXT"]:
                    id_context = data.get( smac_keys["ID_CONTEXT"] )
                    #id_device = smac_keys["ID_DEVICE"]
                    name_context = data.get( smac_keys["NAME_CONTEXT"] )
                    id_topic = data.get( smac_keys["ID_TOPIC"] )
                    db.add_context(id_context=id_context, name_context=name_context, id_topic=id_topic)

                if cmd == smac_keys["CMD_STATUS_REMOVE_CONTEXT"]:
                    id_context = data.get( smac_keys["ID_CONTEXT"] )
                    id_topic = data.get( smac_keys["ID_TOPIC"] )
                    db.remove_context(id_context=id_context, id_topic=id_topic)

                if cmd in  [ smac_keys["CMD_ADD_ACTION"], smac_keys["CMD_STATUS_ADD_ACTION"] ]:
                    print("cmd in CMD_ACTION")
                    id_context = data.get( smac_keys["ID_CONTEXT"] )
                    id_topic =  data.get( smac_keys["ID_TOPIC"] )
                    id_device=  data.get( smac_keys["ID_DEVICE"] )
                    id_property =  data.get( smac_keys["ID_PROPERTY"] )
                    name_context =  data.get( smac_keys["NAME_CONTEXT"] )
                    value =  data.get( smac_keys["VALUE"] )
                    passkey =  data.get( smac_keys["PASSKEY"] )
                    if cmd == smac_keys["CMD_ADD_ACTION"]:
                        print("act")
                        self.add_action(frm, id_context, id_topic, id_device, id_property, name_context, value, passkey)
                    elif cmd == smac_keys["CMD_STATUS_ADD_ACTION"]:
                        print("b1")
                        db.add_context_action(id_context=id_context, id_topic=id_topic,id_device=id_device, id_property=id_property,name_context=name_context, value=value)
                        db.add_command_status(id_topic=id_topic, id_device=id_device, cmd=cmd, id_context=id_context)
                        print("b2")

                if cmd in [smac_keys["CMD_ADD_TRIGGER"], smac_keys["CMD_STATUS_ADD_TRIGGER"]]:
                    id_context =  data.get(  smac_keys["ID_CONTEXT"] )
                    id_topic =  data.get( smac_keys["ID_TOPIC"] )
                    id_device=  data.get( smac_keys["ID_DEVICE"] )
                    id_property =  data.get( smac_keys["ID_PROPERTY"] )
                    type_trigger = data.get( smac_keys["TYPE_TRIGGER"])
                    #name_context = smac_keys["NAME_CONTEXT"]
                    value =  data.get( smac_keys["VALUE"] )
                    passkey =  data.get( smac_keys["PASSKEY"] )
                    if cmd == smac_keys["CMD_ADD_TRIGGER"]:
                        self.add_trigger(frm, id_context, id_topic, id_device, id_property, value, type_trigger, passkey)
                    elif cmd == smac_keys["CMD_STATUS_ADD_TRIGGER"]:
                        db.add_context_trigger(id_context=id_context, id_topic=id_topic,id_device=id_device, id_property=id_property,value=value, type_trigger=type_trigger)
                        db.add_command_status(id_topic=id_topic, id_device=id_device, cmd=cmd, id_context=id_context)

                if cmd in [smac_keys["CMD_REMOVE_ACTION"], smac_keys["CMD_REMOVE_TRIGGER"], smac_keys["CMD_STATUS_REMOVE_ACTION"], smac_keys["CMD_STATUS_REMOVE_TRIGGER"]]:
                    #id_topic, id_context, id_device, id_property, passkey
                    id_context =  data.get( smac_keys["ID_CONTEXT"] )
                    id_topic =  data.get( smac_keys["ID_TOPIC"] )
                    id_device =  data.get( smac_keys["ID_DEVICE"] )
                    id_property =  data.get( smac_keys["ID_PROPERTY"] )
                    passkey =  data.get( smac_keys["PASSKEY"] )
                    if cmd == smac_keys["CMD_REMOVE_ACTION"]:
                        self.remove_action(frm, id_topic, id_context, id_device, id_property, passkey)
                    elif cmd == smac_keys["CMD_REMOVE_TRIGGER"]:
                        self.remove_trigger(frm, id_topic, id_context, id_device, id_property, passkey)
                    elif cmd == smac_keys["CMD_STATUS_REMOVE_ACTION"]:
                        db.remove_action_by_property(id_topic=id_topic, id_context=id_context, id_device=id_device, id_property=id_property)
                        db.add_command_status(id_topic=id_topic, id_device=id_device, cmd=cmd, id_context=id_context)
                        self.remove_action_widget(id_context, id_device, id_property)
                    elif cmd == smac_keys["CMD_STATUS_REMOVE_TRIGGER"]:
                        db.remove_trigger_by_property(id_topic=id_topic, id_context=id_context, id_device=id_device, id_property=id_property)
                        self.remove_trigger_widget(id_context, id_device, id_property)
                        db.add_command_status(id_topic=id_topic, id_device=id_device, cmd=cmd, id_context=id_context)

                if cmd == smac_keys["CMD_TRIGGER_CONTEXT"]:
                    id_context = data.get(smac_keys["ID_CONTEXT"])
                    self.trigger_context(id_context)

    #except Exception as e:
        #    print("Exception while decoding message: {}".format(e) )

    def check_for_action_trigger_status(self, id_device, id_property, value, *args):
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


    def send_trigger_context(self, id_context, *args):
        print("sending trigger context request", id_context)
        d = {}
        d[ smac_keys["ID_CONTEXT"]] = id_context
        client.send_message(frm=self.ID_DEVICE, to="#", message=d,
                            cmd=smac_keys["CMD_TRIGGER_CONTEXT"], udp=True, tcp=True)

    def trigger_context(self, id_context, *args):
        print("triggering context {}".format(id_context))
        for id_topic, id_context, id_device, id_property, value, name_context in db.get_action_by_device(self.ID_DEVICE,id_context):
            # change property here
            print(id_device)
            print(id_property)
            print(value)
            tp = db.get_property_name_by_property(id_device, id_property)
            print("tp", tp)
            if tp != None:
                set_property(str(tp[1]), value, id_property)
            #db.update_value_property_by_dev_id(id_device=self.ID_DEVICE, id_property=id_property, value=value)
            #d = {}
            #d[smac_keys["ID_PROPERTY"]] = id_property
            #d[smac_keys["ID_DEVICE"]] = id_device
            #d[smac_keys["VALUE"]] = value
            # topics = db.get_topic_list_by_device(id_device=id_device)
            #client.send_message(frm=self.ID_DEVICE, to="#", message=d,
            #                    cmd=smac_keys["CMD_STATUS_SET_PROPERTY"], udp=True, tcp=True)

    def add_action(self, frm, id_context, id_topic, id_device, id_property, name_context, value, passkey ):
        passkey = str(passkey)
        print(id_device)
        print(self.ID_DEVICE)
        if id_device == self.ID_DEVICE:
            print("act 0")
            if passkey == self.PIN_DEVICE:
                print("act 1")
                db.add_context_action(id_context=id_context, id_topic=id_topic, id_device=id_device, id_property=id_property, name_context=name_context,value=value)
                print("act 2")
                d1 = {}
                d1[smac_keys["ID_DEVICE"]] = id_device
                d1[smac_keys["ID_TOPIC"]] = id_topic
                d1[smac_keys["ID_CONTEXT"]] = id_context
                d1[smac_keys["ID_PROPERTY"]] = id_property
                d1[smac_keys["NAME_CONTEXT"]] = name_context
                d1[smac_keys["VALUE"]] = value
                # id_topic, id_context, id_device, id_property, value, name_context
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_STATUS_ADD_ACTION"], message=d1)
            else:
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Context Action Not Added. Passkey Error"
                d1[smac_keys["ID_DEVICE"]] = id_device
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)

    def remove_action(self, frm, id_topic, id_context, id_device, id_property, passkey):
        passkey = str(passkey)
        if id_device == self.ID_DEVICE:
            if passkey == self.PIN_DEVICE:
                db.remove_action_by_property(id_context=id_context, id_topic=id_topic, id_device=id_device, id_property=id_property)
                d1 = {}
                d1[smac_keys["ID_DEVICE"]] = id_device
                d1[smac_keys["ID_TOPIC"]] = id_topic
                d1[smac_keys["ID_CONTEXT"]] = id_context
                d1[smac_keys["ID_PROPERTY"]] = id_property
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_STATUS_REMOVE_ACTION"],message=d1)
            else:
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Context Action Not Removed. Passkey Error"
                d1[smac_keys["ID_DEVICE"]] = id_device
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)

    def remove_trigger(self, frm, id_topic, id_context, id_device, id_property, passkey):
        passkey = str(passkey)
        if id_device == self.ID_DEVICE:
            if passkey == self.PIN_DEVICE:
                db.remove_trigger_by_property(id_context=id_context, id_topic=id_topic, id_device=id_device, id_property=id_property)
                d1 = {}
                d1[smac_keys["ID_DEVICE"]] = id_device
                d1[smac_keys["ID_TOPIC"]] = id_topic
                d1[smac_keys["ID_CONTEXT"]] = id_context
                d1[smac_keys["ID_PROPERTY"]] = id_property
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_STATUS_REMOVE_TRIGGER"],message=d1)
            else:
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Context Trigger Not Removed. Passkey Error"
                d1[smac_keys["ID_DEVICE"]] = id_device
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)

    def add_trigger(self, frm, id_context, id_topic, id_device, id_property, value, type_trigger, passkey ):
        passkey = str(passkey)
        if id_device == self.ID_DEVICE:
            if passkey == self.PIN_DEVICE:
                db.add_context_trigger(id_context=id_context, id_topic=id_topic, id_device=id_device,id_property=id_property,value=value, type_trigger=type_trigger)
                d1 = {}
                d1[smac_keys["ID_DEVICE"]] = id_device
                d1[smac_keys["ID_TOPIC"]] = id_topic
                d1[smac_keys["ID_CONTEXT"]] = id_context
                d1[smac_keys["ID_PROPERTY"]] = id_property
                d1[ smac_keys["TYPE_TRIGGER"]] = type_trigger
                #d1[smac_keys["NAME_CONTEXT"]] = name_context
                d1[smac_keys["VALUE"]] = value
                # id_topic, id_context, id_device, id_property, value, name_context
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_STATUS_ADD_TRIGGER"], message=d1)
            else:
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Context Trigger Not Added. Passkey Error"
                d1[smac_keys["ID_DEVICE"]] = id_device
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)

    def update_interval_online(self, frm, id_device, interval_online, passkey):
        if id_device == self.ID_DEVICE:
            passkey = str(passkey)
            if passkey == self.PIN_DEVICE:
                db.update_device_interval_online(id_device, interval_online)
                self.update_config_variable(key="INTERVAL_ONLINE", value=interval_online)
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Device Online Interval updated"
                d1[smac_keys["ID_DEVICE"]] = id_device
                d1[smac_keys["INTERVAL"]] = interval_online
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_STATUS_UPDATE_INTERVAL_ONLINE"], message=d1)
            else:
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Device Online Interval not updated. Passkey Error"
                d1[smac_keys["ID_DEVICE"]] = id_device
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)



    def update_name_property(self, frm, id_device, name_property, id_property, passkey):
        print(id_device)
        print(self.ID_DEVICE)
        if id_device == self.ID_DEVICE:
            passkey = str(passkey)
            if passkey == self.PIN_DEVICE:
                db.update_name_property(id_device, id_property, name_property)
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Property Name updated"
                d1[smac_keys["ID_DEVICE"]] = id_device
                d1[smac_keys["ID_PROPERTY"]] = id_property
                d1[smac_keys["NAME_PROPERTY"]] = name_property
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_STATUS_UPDATE_NAME_PROPERTY"], message=d1)
            else:
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "PROPERTY Name not updated. Passkey Error"
                d1[smac_keys["ID_DEVICE"]] = id_device
                d1[smac_keys["ID_PROPERTY"]] = id_property
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)


    def update_name_device(self, frm, id_device, name_device, passkey):
        if id_device == self.ID_DEVICE:
            passkey = str(passkey)
            if passkey == self.PIN_DEVICE:
                db.update_device_name(id_device, name_device)
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Device Name updated"
                d1[smac_keys["ID_DEVICE"]] = id_device
                d1[smac_keys["NAME_DEVICE"]] = name_device
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_STATUS_UPDATE_NAME_DEVICE"], message=d1)
            else:
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Device Name not updated. Passkey Error"
                d1[smac_keys["ID_DEVICE"]] = id_device
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)


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
        task3 = asyncio.ensure_future( self.UI_loop() )
        task4 = asyncio.ensure_future( self.UI_loop2() )
        self._TASKS = [ task2, task3, task4 ]
        #task3 = asyncio.ensure_future( self.send_test() )

        #return asyncio.gather( start_app(),zmq_sub_start, zmq_pub_start, task1, zmq_t1, zmq_t2, udp_t1, udp_t2, test1 )
        return asyncio.gather( start_app(), task2, task3, task4)

    def test_send_status(self, *args):
        self.TEST_VAL = 1 - self.TEST_VAL
        m = {}
        m[ smac_keys["ID_PROPERTY"] ] = "0"
        m[ smac_keys["ID_DEVICE"] ] = self.ID_DEVICE
        m[ smac_keys["VALUE"] ] =  self.TEST_VAL
        print("m", m)
        client.send_message(frm=self.ID_DEVICE, to="#", cmd=smac_keys["CMD_STATUS"] , message=m, udp=True, tcp=False)


    def send_info(self, udp=True, tcp=True, *args):
        #Clock.schedule_once(partial(client.send_message, self.ID_DEVICE, "#", smac_keys["CMD_REQ_SEND_INFO"] , {}, False, None, True, False), 5)
        client.send_message(frm=self.ID_DEVICE, to="#", cmd=smac_keys["CMD_REQ_SEND_INFO"], message={}, udp=udp, tcp=tcp)
        self.send_device_info(dest_topic="#", udp=udp, tcp=tcp)
        #Clock.schedule_interval(self.test_send_status, 0)
        #Clock.schedule_interval(self.check_for_new_value, 0)


    async def UI_loop(self, *args):
        while 1:
            # check for value_temp and update the value of property according to that
            # set_property_of_current_device
            for id_property, property_name, type_property, value_min, value_max, value, value_temp, value_last_updated in db.get_property_list_by_device(self.ID_DEVICE):
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
                        d[smac_keys["ID_DEVICE"]] = self.ID_DEVICE
                        d[smac_keys["VALUE"]] = 5
                        client.send_message(frm=self.ID_DEVICE, to="#", cmd=smac_keys["CMD_DEVICE_BUSY"], message=d )
                    #else:
                        #self.open_modal(text=)
            await asyncio.sleep(.1)

    async def UI_loop2(self, *args):
        TASK_COUNT = {}
        #interval_online = db.get_device_interval_online(id_device=self.ID_DEVICE)
        COUNTER = 0
        while 1:
            #self.send_info()

            # check for busy period and update the db
            id_topic = ""
            for id_device, name_device, type_device, view_device, is_busy, busy_period, pin_device, pin_device_valid, interval_online, last_updated  in db.get_device_list_by_topic(id_topic):
                if busy_period == int(time.time()):
                    db.update_device_busy(id_device=id_device, is_busy=0, busy_period=0)

            if(platform == "android") and ((COUNTER % 5) == 0):
                await property_listener(self.ID_DEVICE)
            #print("interval", interval_online)
            #print("COUNTER", COUNTER)
            if (COUNTER % self.INTERVAL_ONLINE) == 0:
                #COUNTER = 0
                print("Sending CMD_ONLINE")
                print("Sending CMD_ONLINE")
                client.send_message(frm=self.ID_DEVICE, to="#", cmd=smac_keys["CMD_ONLINE"], message={})
                await  asyncio.sleep(0)



            # check for trigger and update value
            if (COUNTER % 60) == 0:
                for id_topic, id_context, id_device, id_property, value, type_trigger in db.get_trigger_by_device(self.ID_DEVICE):
                    if type_trigger == smac_keys["TYPE_TRIGGER_PROP"]:
                        db_value = db.get_value_by_property(id_device, id_property)
                        if str(db_value) == str(value):
                            self.trigger_context(id_context)
                            #self.send_trigger_context(id_context)
                    elif type_trigger == smac_keys["TYPE_TRIGGER_TIME"]:
                        value_hour, value_min = value.split(":")
                        time1 = datetime.now()
                        if(value_hour == str(time1.hour)) and (value_min == str(time1.minute)):
                            self.trigger_context(id_context)
                            #self.send_trigger_context(id_context)





            #check for tasks and print the POPUP message
            # ex: wait for reply from device for commands like:
            # CMD_ADD_TOPIC, CMD_REMOVE_TOPIC etc
            for t_id in list(self.TASKS):
                print(t_id)
                task = self.TASKS[t_id]
                func = task[0]
                args = task[1]
                print("args", args)
                if func == db.get_command_status:
                    if TASK_COUNT.get(t_id, None) == None:
                        TASK_COUNT[t_id] = 0
                    id_topic = args[0]
                    id_device = args[1]
                    cmd = args[2]
                    id_property = args[3] if(len(args) > 3) else ""
                    id_context= args[4] if(len(args) > 4) else ""
                    st = db.get_command_status(id_topic=id_topic, id_device=id_device, id_property=id_property, id_context=id_context)
                    print("st", st)
                    if st != None:
                        tim = st[6]
                        cmd1 = st[5]
                        t_diff = int(time.time()) - tim
                        print("t_diff", t_diff)
                        if t_diff < 15:
                            if cmd1 in cmd:
                                text = self.get_command_status_text(cmd=cmd1)
                                if self.is_modal_open:
                                    self.close_modal()
                                    await asyncio.sleep(.5)
                                self.open_modalInfo(title="Info", text=text)
                                self.remove_task(t_id)
                                for c in cmd:
                                    db.remove_command_status(id_topic=id_topic, id_device=id_device, cmd=c, id_context=id_context, id_property=id_property)
                        #else:
                        #    for c in cmd:
                        #        db.remove_command_status(id_topic=id_topic, id_device=id_device, cmd=c)

                    TASK_COUNT[t_id] += 1
                    if TASK_COUNT[t_id] == 10:
                        self.remove_task(task_id=t_id)
                        for c in cmd:
                            db.remove_command_status(id_topic=id_topic, id_device=id_device, cmd=c, id_context=id_context, id_property=id_property)
                        text = "Timeout: No response from the device"
                        if self.is_modal_open:
                            self.close_modal()
                            await asyncio.sleep(.5)
                        self.open_modalInfo(title="Info", text=text)

            COUNTER += 1
            await asyncio.sleep(1) # Busy period of device should be > than this interval period

    async def check_for_command_status(self, id_topic, id_device, id_property="", cmd=[], COUNT=10):
        while COUNT:
            st = db.get_command_status(id_topic=id_topic, id_device=id_device, id_property=id_property)
            print("st", st)
            if st != None:
                tim = st[5]
                cmd1 = st[4]
                t_diff = int(time.time()) - tim
                if t_diff < 30:
                    if cmd1 in cmd:
                        text = self.get_command_status_text(cmd=cmd1)
                        if self.is_modal_open:
                            self.close_modal()
                        self.open_modalInfo(title="Info", text=text)
            COUNT -= 1
        else:
            text = "Timeout: No response from the device"
            print(text)
            if self.is_modal_open:
                self.close_modal()
            self.open_modalInfo(title="Info", text=text)

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
            d["LIMIT_TOPIC"] = 10
            d["LIMIT_DEVICE"] = 10
            d["INTERVAL_ONLINE"] = 30
            f.write(json.dumps(d))
            f.close()

        with open('config.json', 'r') as f:
            fd = json.load(f)
            print("fd", fd)
            if fd["ID_DEVICE"] == "":
                #d_id = self.get_local_ip()
                #d_id = req_get_device_id()
                from smac_device import get_id_device
                d_id = get_id_device()
                print("d_id", d_id)
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
            if fd["TYPE_DEVICE"] == "":
                fd["TYPE_DEVICE"] = get_device_type()
                changed = True
            self.TYPE_DEVICE = fd["TYPE_DEVICE"]
            if fd.get("LIMIT_DEVICE") != None:
                self.LIMITS["LIMIT_DEVICE"] = fd["LIMIT_DEVICE"]
            if fd.get("LIMIT_TOPICS") != None:
                self.LIMITS["LIMIT_TOPIC"] = fd["LIMIT_TOPIC"]
            if fd.get("INTERVAL_ONLINE", None) != None:
                self.INTERVAL_ONLINE = int(fd["INTERVAL_ONLINE"])
            self.theme = fd.get("theme", "LIGHT")
            f.close()

        print("fd", fd)
        if changed:
            with open('config.json', 'w') as f:
                f.write( json.dumps(fd) )




    def on_stop(self, *args):
        for task in self._TASKS:
            task.cancel()


    def on_resume(self):
        return True

    def on_tcp_start(self, *args):
        print("TCP services started")
        print(args)
        self.send_info(tcp=True, udp=False)

    def on_start(self):
        print("kivy started")
        print("starting smac_client...")

        self.load_config_variables()
        #topics = [ i[0] for i in  db.get_topic_list()]
        topics = self.SUB_TOPIC
        print("subscribing to: {}".format(["#", self.ID_DEVICE] + topics))
        client.subscribe( ["#", self.ID_DEVICE] + topics )
        client.process_message = self.on_message
        client.on_start = self.on_tcp_start
        self.modal.separator_color = self.colors["COLOR_THEME_HIGHLIGHT"]
        self.modal.separator_height = dp(2)
        self.modal.ids["id_btn_close"].bind(on_release=self.close_modal)
        self.screen_manager.get_screen("Screen_context").modal.ids["id_btn_close"].bind(on_release=self.close_modal)
        #c = self.modal.children[0].children[0]
        #c.add_widget(Label_custom(text="ge", size_hint=(None, None), size=(50, 50),pos=c.pos))
        db.delete_network_entry(id_topic='')
        db.remove_command_status_all()
        db.update_delete_all(this_device=self.ID_DEVICE, value=1)
        tps = db.get_device_list_by_topic(id_topic='')
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
        self.send_info(udp=True, tcp=False)
        


#SmacApp().async_run(async_lib='asyncio')
#asyncio.run(SmacApp().t())
loop = asyncio.get_event_loop()
loop.run_until_complete(SmacApp().t())
loop.close()