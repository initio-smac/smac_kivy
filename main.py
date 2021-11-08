import base64
import os
from datetime import datetime

import kivy.core.window
from kivy.core.window import Window
from kivy.properties import *
#from kivy.utils import get_color_from_hex, platform
#from kivy.uix.screenmanager import ScreenManager, Screen, CardTransition, NoTransition, SlideTransition, SwapTransition, FadeTransition, WipeTransition, FallOutTransition, RiseInTransition
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.utils import get_hex_from_color
from plyer import notification

from smac_device import set_property, get_device_property, get_property_value, property_listener
from smac_limits import STATE_NO_CONNECTION, STATE_CONNECTED_INTERNET, STATE_CONNECTED_NO_INTERNET
from smac_platform import SMAC_PLATFORM
from smac_requests import restapi
from smac_theme_colors import THEME_LIGHT, THEME_DARK

#Window.clearcolor = get_color_from_hex("#e0e0e0")

import json

from smac_device_keys import SMAC_DEVICES
from smac_tools import update_network_connection
from smac_widgets.smac_screens import *
from smac_widgets.smac_layouts import *
from smac_db import db


# android specific code
# update the statusbar color android
if SMAC_PLATFORM == "android":
    from android.runnable import run_on_ui_thread
    @run_on_ui_thread
    def change_statusbar_color(color):
        #print(color)
        from jnius import autoclass
        Color = autoclass("android.graphics.Color")
        WindowManager = autoclass('android.view.WindowManager$LayoutParams')
        activity = autoclass('org.kivy.android.PythonActivity').mActivity
        window = activity.getWindow()
        window.clearFlags(WindowManager.FLAG_TRANSLUCENT_STATUS)
        window.addFlags(WindowManager.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)
        #c = [ str(i) for i in Color.parseColor(color)]
        print(color[:7])
        c= get_hex_from_color(color)
        print(c[:7])
        c = Color.parseColor( c[:7] )
        window.setStatusBarColor(c)
        window.setNavigationBarColor(c)


class BoxLayout_property(BoxLayout):
    data = DictProperty({
        "min": 0,
        "max": 1,
        "value": 0,
        "instance": 0
    })


class SmacApp(App):
    text1 = StringProperty("hai")   # test variable
    image_source = ""               # 
    grid_min = dp(50)               # minimum UI unit
    screen_manager = ScreenManager(transition=NoTransition())   # Screen manager instance
    modal = ModalView_custom(size_hint_x=.9, size_hint_max_x=dp(400), size_hint_y=None, height=dp(400))    # app specific modal
    is_modal_open = False           # state of modal
    APP_DATA = DictProperty({       # used for various functions across the screens such as
        "id_topic": "",             # device_settings, contexts, current_topic, current_device etc
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
    _TASKS = []                 # ID: (task_function, args ); async tasks; alternative to the ACK
    TASKS = {}                  # task function is basically a UI response task updated when a MSG is received and UI action is needed. Ex: delete_device
    TASK_ID = 0                 # ID for each tasks
    SENDING_INFO = 0            # STATE of sending device info; 1 if if alreading sending else 0
    TEST_VAL = 0                # Test variable
    INTERVAL_ONLINE = 30        # send_online interval 
    theme = OptionProperty("", options=["", "LIGHT", "DARK"])  # theme variable
    colors = DictProperty(THEME_LIGHT)               # theme colors
    source_icon = StringProperty("icons/LIGHT/")     # set icon source based on the THEME
    DEBUG = False                                    # app DEBUG
    EMAIL = StringProperty("")
    MOBILE_NUMBER = StringProperty('')
    #OTP_API_KEY = "68a846d4-c386-11eb-8089-0200cd936042"
    _KEYBOARD = None            # app keyboard instance     
    VERSION = 0.5               # app version; SMAC SPECIFIC
    BACK_BTN_COUNTER = 0        # counter for back button press
    title="SMAC"                # app title
    icon = "smac_logo.png"      # app icon
    BROADCAST_RECEIVER = None   # app broadcast receiver; android
    STATE_CONNECTION = NumericProperty(1)    # network connection status

    # on network state change
    def on_STATE_CONNECTION(self, instance, value, *args):
        print(value)
        print(args)
        if value == STATE_NO_CONNECTION:
            #self.open_modalInfo(title="Info", text="No connection")
            notification.notify( message="No Connection", toast=True)
        elif value == STATE_CONNECTED_INTERNET:
            #self.open_modalInfo(title="Info", text="Connected to Internet")
            notification.notify(message="Connected to Internet", toast=True)
        elif value == STATE_CONNECTED_NO_INTERNET:
            #self.open_modalInfo(title="Info", text="Connected to Network. No Internet" )
            notification.notify(message="Connected to Network. No Internet", toast=True)

    # on theme change
    def on_theme(self, *args):
        print("on_theme", self.theme)
        if self.theme == "DARK":
            self.colors = THEME_DARK
            self.source_icon = "icons/DARK/"
            self.update_config_variable(key="theme", value="DARK")
        else:
            self.colors = THEME_LIGHT
            self.source_icon = "icons/LIGHT/"
            self.update_config_variable(key="theme", value="LIGHT")
        print(self.colors["COLOR_THEME"])
        if SMAC_PLATFORM == "android":
            change_statusbar_color(self.colors["COLOR_THEME"])
        Window.clearcolor = self.colors["COLOR_THEME"]


    # logout from app
    def logout(self, *args):
        self.update_config_variable(key="EMAIL_VERIFIED", value=0)
        self.change_screen(screen="Screen_register")

    # add a task
    # task is a response function to a command
    # alternative to the ACK
    def add_task(self,  func, args):
        self.TASKS[ str(self.TASK_ID) ] = (func, args)
        self.TASK_ID += 1

    # remove a task
    def remove_task(self, task_id):
        if str(task_id) in self.TASKS.keys():
            del self.TASKS[task_id]

    # app build function
    # set screen widgets
    def build(self):
        Builder.load_file('smac_widgets/smac_screens.kv')
        Builder.load_file('smac_widgets/smac_layouts.kv')
        if not self.DEBUG:
            self.screen_manager.add_widget(Screen_register(name="Screen_register"))
        self.screen_manager.add_widget(Screen_network(name='Screen_network'))
        self.screen_manager.add_widget(Screen_deviceSetting(name='Screen_deviceSetting'))
        self.screen_manager.add_widget(Screen_context(name='Screen_context'))
        self.screen_manager.add_widget(Screen_espConfig(name='Screen_espConfig'))
        #self.screen_manager.add_widget(Screen_devices(name='Screen_devices'))
        #self.screen_manager.add_widget(Screen_property(name='Screen_deviceSetting'))

        return self.screen_manager

    # change screen function
    def change_screen(self, screen, *args):
        self.screen_manager.current = screen

    # open app modal with content
    def open_modal(self, content, title="Info", auto_dismiss=True):
        if content != None:
            #print(content.height)
            print("modal content", self.modal.content)
            self.modal.content = content
            self.modal.title = title
            #self.modal.content.parent.parent.parent.height = content.height + dp(70)
            self.modal.height = content.height + dp(70)
            self.modal.open(auto_dismiss=auto_dismiss)
            self.is_modal_open = True

            scr = self.screen_manager.get_screen( self.screen_manager.current )
            #print(scr)
            scr.get_selectable_nodes(widget=self.modal)

    # close app modal
    def close_modal(self, *args):
        #self.modal.content = None
        self.modal.title = ""
        self.modal.dismiss()
        self.is_modal_open = False
        scr = self.screen_manager.get_screen(self.screen_manager.current)
        scr.get_selectable_nodes()
        print(args)
        return True

    # open modal with text
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

    # close modal
    def close_modalInfo(self, *args):
        self.close_modal()

    # Not used (OLD)
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

    # Get text based on the MSG received
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

    # add a new topic function
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

    # remove a topic widget from Screen_network
    def delete_topic_widget(self, id_topic):
        scr = self.screen_manager.get_screen(name="Screen_network")
        container = scr.ids["id_network_container"]
        print(id_topic)
        print(scr.TOPIC_IDS.get(id_topic, None))
        if scr.TOPIC_IDS.get(id_topic, None) != None:
            container.remove_widget(scr.TOPIC_IDS[id_topic])
            del scr.TOPIC_IDS[id_topic]

    # remove context action widget from Screen_context 
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

    # remove a context trigger widget from Screen_context
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

    # remove a topic and unsubscribe to that topic
    def delete_topic(self, frm, id_topic, id_device, passkey, *args):
        print(passkey)
        print(self.PIN_DEVICE)
        print(passkey == self.PIN_DEVICE)
        #print(type(passkey))
        #print(type(self.PIN_DEVICE))
        if str(passkey) == str(self.PIN_DEVICE):
            #db.add_network_entry(name_topic=id_topic, id_topic=id_topic, id_device=id_device, name_device=self.NAME_DEVICE, type_device=self.TYPE_DEVICE)
            if id_device == self.ID_DEVICE:
                db.delete_network_entry(id_topic)
            else:
                db.delete_network_entry_by_topic(id_topic, id_device)
            db.remove_action_by_topic(id_topic)
            db.remove_trigger_by_topic(id_topic)
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

    # send device information on device start
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
                m[ smac_keys["TYPE_DEVICE"] ] = str(self.TYPE_DEVICE)
                #print(m)
                #time.sleep(.1)
                client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=m, udp=udp, tcp=tcp)
                print("sent {}".format(id_topic))

                for id_topic, id_context, name_context in db.get_context_by_topic(id_topic):
                    c1 = {}
                    c1[ smac_keys["CONTEXT"] ] = 1
                    c1[ smac_keys["ID_TOPIC"] ] = id_topic
                    c1[ smac_keys["ID_CONTEXT"] ] = id_context
                    c1[ smac_keys["NAME_CONTEXT"] ] = name_context
                    client.send_message(frm=self.ID_DEVICE, to=dest_topic, cmd=smac_keys["CMD_SEND_INFO"], message=c1 ,udp=udp, tcp=tcp)
        print("sent topics")

        for p in db.get_property(self.ID_DEVICE):
            print(p)
            p1 = {}
            p1[smac_keys["PROPERTY"]] = 1
            p1[smac_keys["ID_DEVICE"]] = self.ID_DEVICE
            p1[smac_keys["ID_PROPERTY"]] = p[2]
            p1[smac_keys["TYPE_PROPERTY"]] = str(p[3])
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

        triggers = db.get_trigger_by_device(self.ID_DEVICE)
        if triggers == None:
            triggers = []
        for id_topic2, id_context, id_device, id_property, value, type_trigger in triggers:
            c2 = {}
            c2[ smac_keys["CONTEXT_TRIGGER"] ] = 1
            c2[ smac_keys["ID_TOPIC"]] = id_topic2
            c2[ smac_keys["ID_CONTEXT"]] = id_context
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

    # when a message is received either on UDP or TCP
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
            print(data)
            if frm != self.ID_DEVICE:
                # update device_busy status of the device
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

                # update device invalid PIN status
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

                # change property of this device
                # update the VALUE_TEMP of the db
                # async interval will detect the change and updates the property
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

                # cmd to request a device info
                if cmd == smac_keys["CMD_REQ_SEND_INFO"]:
                    if not self.SENDING_INFO:
                        #if protocol == "UDP":
                            self.send_device_info( dest_topic="#", udp=True)
                        #elif protocol == "ZMQ":
                        #    self.send_device_info(dest_topic="#", tcp=False)

                # when a device_info is received, 
                # process the device_info and add it to the db
                if cmd == smac_keys["CMD_SEND_INFO"]:
                    print("CMD_SEND_INFO")
                    if data.get( smac_keys["TOPIC"], None) != None:
                        id_device = data.get( smac_keys["ID_DEVICE"] )
                        id_topic = data.get( smac_keys["ID_TOPIC"] )
                        name_device = data.get(smac_keys["NAME_DEVICE"], "")
                        name_home = data.get(smac_keys["NAME_HOME"], "")
                        name_topic = data.get(smac_keys["NAME_TOPIC"], "")
                        type_device = data.get(smac_keys["TYPE_DEVICE"], "")
                        if (protocol == "UDP") or ((protocol == "ZMQ") and (id_topic != '') and  (id_topic in self.SUB_TOPIC)):
                        #if (id_topic != "") and (id_topic in self.SUB_TOPIC):
                            db.add_network_entry(name_home=name_home, name_topic=name_topic, id_topic=id_topic, id_device=frm, name_device=name_device, type_device=type_device, remove=0)
                            #db.update_delete_by_topic_id(id_device=frm, id_topic=id_topic, value=0)
                            print("new network entry added: {}, {}".format(id_topic, frm))
                        print("12")
                    if data.get(smac_keys["PROPERTY"], None) != None:
                        id_device = data.get(smac_keys["ID_DEVICE"])
                        id_prop = data.get(smac_keys["ID_PROPERTY"])
                        type_prop = data.get(smac_keys["TYPE_PROPERTY"], "")
                        type_prop = str(type_prop)
                        name_prop = data.get(smac_keys["NAME_PROPERTY"], "")
                        value = data.get(smac_keys["VALUE"], 0)
                        value_min = data.get(smac_keys["VALUE_MIN"], 0)
                        value_max = data.get(smac_keys["VALUE_MAX"], 1)
                        if (protocol == "UDP") or ((protocol == "ZMQ") and  len(db.get_topic_list_by_device(id_device)) >0):
                        #if True:
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



                # OLD
                if cmd == smac_keys["CMD_INIT_SEND_INFO"]:
                    print("updating DELETE field of entries: {}".format(frm))
                    # SET_PROPERTY field updates delte field of PROPERTY TABLE also
                    db.update_delete_by_dev_id(id_device=frm, value=1, SET_PROPERTY=True)

                # OLD
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


                # status of a device property is received, 
                # update it in db
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

                # add a new topic
                if cmd == smac_keys["CMD_ADD_TOPIC"]:
                    id_topic = data.get(smac_keys["ID_TOPIC"])
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    passkey = data.get(smac_keys["PASSKEY"])
                    name_home = data.get(smac_keys["NAME_HOME"])
                    name_topic = data.get(smac_keys["NAME_TOPIC"])
                    self.add_topic(frm, id_topic, name_home, name_topic, id_device, passkey, msg_id)
                    #self.ACKS.append( "{}:{}:{}".format(id_topic, id_device, smac_keys["CMD_ADD_TOPIC"]) )

                # remove a topic
                if cmd == smac_keys["CMD_REMOVE_TOPIC"]:
                    id_topic = data.get(smac_keys["ID_TOPIC"])
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    passkey = data.get(smac_keys["PASSKEY"])
                    self.delete_topic(frm, id_topic, id_device, passkey, msg_id)

                # status of a new topic is received
                # update it in db
                if cmd == smac_keys["CMD_STATUS_ADD_TOPIC"]:
                    id_topic = data.get(smac_keys["ID_TOPIC"])
                    name_device = data.get(smac_keys["NAME_DEVICE"], "")
                    name_topic = data.get(smac_keys["NAME_TOPIC"], "")
                    name_home = data.get(smac_keys["NAME_HOME"], "")
                    type_device = data.get(smac_keys["TYPE_DEVICE"], "")
                    if ( len(db.get_property_list_by_device(frm)) > 0):
                    #if ((protocol == "TCP") and len(db.get_property_list_by_device(frm)) > 0):
                        db.add_network_entry(name_home=name_home, name_topic=name_topic, id_topic=id_topic, id_device=frm, name_device=name_device,
                                         type_device=type_device, remove=0)
                    #self.ACKS.append( "{}:{}:{}".format(id_topic, id_device, smac_keys["CMD_STATUS_ADD_TOPIC"]) )
                    db.add_command_status(id_topic=id_topic, id_device=frm, cmd=cmd)

                # status of a topic removal is received
                # update it in db
                if cmd == smac_keys["CMD_STATUS_REMOVE_TOPIC"]:
                    id_topic = data.get(smac_keys["ID_TOPIC"])
                    if len(db.get_property_list_by_device(frm)) > 0:
                    #if ((protocol == "TCP") and len(db.get_property_list_by_device(frm)) > 0):
                        db.delete_network_entry_by_topic(id_topic=id_topic, id_device=frm)
                        db.add_command_status(id_topic=id_topic, id_device=frm, cmd=cmd)
                        scr = self.screen_manager.get_screen(name="Screen_network")
                        container = scr.ids["id_network_container"]
                        container.remove_widget(scr.TOPIC_IDS[id_topic])
                        del scr.TOPIC_IDS[id_topic]
                        #self.ACKS.append( "{}:{}:{}".format(id_topic, id_device, smac_keys["CMD_STATUS_REMOVE_TOPIC"]) )

                # update the device online time
                if cmd == smac_keys["CMD_ONLINE"]:
                    db.update_device_last_updated(id_device=frm)

                # if total no. of topics subscribed is more than the limit
                if cmd in [ smac_keys["CMD_TOPIC_LIMIT_EXCEEDED"], smac_keys["CMD_ACTION_LIMIT_EXCEEDED"], smac_keys["CMD_TRIGGER_LIMIT_EXCEEDED"] ]:
                    id_topic = data.get(smac_keys["ID_TOPIC"], "")
                    id_context = data.get(smac_keys["ID_CONTEXT"], "")
                    db.add_command_status(id_topic=id_topic, id_context=id_context, id_device=frm, cmd=cmd)

                # update device name
                if cmd == smac_keys["CMD_UPDATE_NAME_DEVICE"]:
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    name_device = data.get(smac_keys["NAME_DEVICE"])
                    passkey = data.get( smac_keys["PASSKEY"] )
                    self.update_name_device(frm, id_device, name_device, passkey)

                # status of a device name is received
                # update it in db
                if cmd == smac_keys["CMD_STATUS_UPDATE_NAME_DEVICE"]:
                    id_topic = ""
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    name_device = data.get(smac_keys["NAME_DEVICE"])
                    db.update_device_name(id_device, name_device)
                    #id_device = id_device
                    db.add_command_status(id_topic=id_topic, id_device=frm, cmd=cmd)

                # update property name of this device
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

                # status of a property name is received
                # update it in db
                if cmd == smac_keys["CMD_STATUS_UPDATE_NAME_PROPERTY"]:
                    id_topic = ""
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    id_property = data.get(smac_keys["ID_PROPERTY"])
                    name_property = data.get(smac_keys["NAME_PROPERTY"])
                    db.update_name_property(id_device, id_property, name_property)
                    db.add_command_status(id_topic=id_topic, id_device=frm, cmd=cmd, id_property=id_property)

                # update device online interval 
                if cmd == smac_keys["CMD_UPDATE_INTERVAL_ONLINE"]:
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    interval_online = data.get(smac_keys["INTERVAL"])
                    passkey = data.get( smac_keys["PASSKEY"] )
                    self.update_interval_online(frm, id_device, interval_online, passkey)

                # status of a device online interval is received
                # update it in db
                if cmd == smac_keys["CMD_STATUS_UPDATE_INTERVAL_ONLINE"]:
                    id_topic = ""
                    id_device = data.get(smac_keys["ID_DEVICE"])
                    interval_online = data.get(smac_keys["INTERVAL"])
                    db.update_device_interval_online(id_device, interval_online)
                    db.add_command_status(id_topic=id_topic, id_device=frm, cmd=cmd)

                # status of a device wifi config is received
                # update it in db
                if cmd == smac_keys["CMD_STATUS_UPDATE_WIFI_CONFIG"]:
                    id_topic = ""
                    db.add_command_status(id_topic=id_topic, id_device=frm, cmd=cmd)

                # status of a software update is received
                # update it in db
                if cmd == smac_keys["CMD_STATUS_UPDATE_SOFTWARE"]:
                    m = data.get(smac_keys["MESSAGE"], "")
                    if m != "":
                        self.open_modalInfo(text=m , title="Info")

                # status of a new context is received
                # update it in db
                if cmd == smac_keys["CMD_STATUS_ADD_CONTEXT"]:
                    id_context = data.get( smac_keys["ID_CONTEXT"] )
                    #id_device = smac_keys["ID_DEVICE"]
                    name_context = data.get( smac_keys["NAME_CONTEXT"] )
                    id_topic = data.get( smac_keys["ID_TOPIC"] )
                    db.add_context(id_context=id_context, name_context=name_context, id_topic=id_topic)

                # status of a context removal is received
                # update it in db
                if cmd == smac_keys["CMD_STATUS_REMOVE_CONTEXT"]:
                    id_context = data.get( smac_keys["ID_CONTEXT"] )
                    id_topic = data.get( smac_keys["ID_TOPIC"] )
                    db.remove_context(id_context=id_context, id_topic=id_topic)
                    scr = self.screen_manager.get_screen(name="Screen_context")
                    container = scr.ids["id_context_container"]
                    container.remove_widget(container.ids[id_context])
                    #del scr.TOPIC_IDS[id_topic]

                # status of a context action is received
                # update it in db
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

                # status of a context trigger is received
                # update it in db
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

                # status of a action/trigger removal is received
                # update it in db
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

                # trigger context
                if cmd == smac_keys["CMD_TRIGGER_CONTEXT"]:
                    id_context = data.get(smac_keys["ID_CONTEXT"])
                    self.trigger_context(id_context)

    #except Exception as e:
        #    print("Exception while decoding message: {}".format(e) )

    # check of actions or triggers meet the condition
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

    # send a message to trigger a context
    def send_trigger_context(self, id_context, *args):
        print("sending trigger context request", id_context)
        d = {}
        d[ smac_keys["ID_CONTEXT"]] = id_context
        client.send_message(frm=self.ID_DEVICE, to="#", message=d,
                            cmd=smac_keys["CMD_TRIGGER_CONTEXT"], udp=True, tcp=True)

    # trigger a context
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

    # add context action
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
                client.send_message(frm=self.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_STATUS_ADD_ACTION"], message=d1)
            else:
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Context Action Not Added. Passkey Error"
                d1[smac_keys["ID_DEVICE"]] = id_device
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)

    # remove a context action
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
                client.send_message(frm=self.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_STATUS_REMOVE_ACTION"],message=d1)
            else:
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Context Action Not Removed. Passkey Error"
                d1[smac_keys["ID_DEVICE"]] = id_device
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)

    # removea a context trigger
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
                client.send_message(frm=self.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_STATUS_REMOVE_TRIGGER"],message=d1)
            else:
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Context Trigger Not Removed. Passkey Error"
                d1[smac_keys["ID_DEVICE"]] = id_device
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)

    # add a context trigger
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
                d1[smac_keys["TYPE_TRIGGER"]] = type_trigger
                #d1[smac_keys["NAME_CONTEXT"]] = name_context
                d1[smac_keys["VALUE"]] = value
                # id_topic, id_context, id_device, id_property, value, name_context
                client.send_message(frm=self.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_STATUS_ADD_TRIGGER"], message=d1)
            else:
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Context Trigger Not Added. Passkey Error"
                d1[smac_keys["ID_DEVICE"]] = id_device
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)

    # update device online interval
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


    # update property name
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

    # update device name
    def update_name_device(self, frm, id_device, name_device, passkey):
        if id_device == self.ID_DEVICE:
            passkey = str(passkey)
            if passkey == self.PIN_DEVICE:
                db.update_device_name(id_device, name_device)
                self.update_config_variable(key="NAME_DEVICE", value=name_device)
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Device Name updated"
                d1[smac_keys["ID_DEVICE"]] = id_device
                d1[smac_keys["NAME_DEVICE"]] = name_device
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_STATUS_UPDATE_NAME_DEVICE"], message=d1)
                req = "request_update_name_device"
                url = SMAC_SERVER + req
                restapi.rest_call(url, method="POST", request=req, data={"id_device": self.ID_DEVICE , "name_device": name_device})
            else:
                d1 = {}
                d1[smac_keys["MESSAGE"]] = "Device Name not updated. Passkey Error"
                d1[smac_keys["ID_DEVICE"]] = id_device
                print(d1[smac_keys["MESSAGE"]])
                client.send_message(frm=self.ID_DEVICE, to=frm, cmd=smac_keys["CMD_INVALID_PIN"], message=d1)


    # update property value in the slider
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

    # async send message function
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

    # set async tasks
    # task1 --> smac_client
    # task2 --> UI_loop() interval .1 sec
    # task3 --> UI_loop() interval 1 sec
    def t(self, *args):
        async def start_app():
            print("starting app")
            await self.async_run(async_lib="asyncio")

        #task1 = asyncio.ensure_future( self.async_test() )
        task2 = asyncio.ensure_future( client.main() )
        task3 = asyncio.ensure_future( self.UI_loop() )  
        task4 = asyncio.ensure_future( self.UI_loop2() )
        #if SMAC_PLATFORM != "android":
        self._TASKS = [ task2, task3, task4 ]
        #self._TASKS = [task3, task4]
        #task3 = asyncio.ensure_future( self.send_test() )

        #return asyncio.gather( start_app(),zmq_sub_start, zmq_pub_start, task1, zmq_t1, zmq_t2, udp_t1, udp_t2, test1 )
        return asyncio.gather( start_app(), task2, task3, task4)

    # test function to send status 
    def test_send_status(self, *args):
        self.TEST_VAL = 1 - self.TEST_VAL
        m = {}
        m[ smac_keys["ID_PROPERTY"] ] = "0"
        m[ smac_keys["ID_DEVICE"] ] = self.ID_DEVICE
        m[ smac_keys["VALUE"] ] =  self.TEST_VAL
        print("m", m)
        client.send_message(frm=self.ID_DEVICE, to="#", cmd=smac_keys["CMD_STATUS"] , message=m, udp=True, tcp=False)


    # request device info and send device info
    def send_info(self, udp=True, tcp=True, *args):
        #Clock.schedule_once(partial(client.send_message, self.ID_DEVICE, "#", smac_keys["CMD_REQ_SEND_INFO"] , {}, False, None, True, False), 5)
        client.send_message(frm=self.ID_DEVICE, to="#", cmd=smac_keys["CMD_REQ_SEND_INFO"], message={}, udp=udp, tcp=tcp)
        self.send_device_info(dest_topic="#", udp=udp, tcp=tcp)
        #Clock.schedule_interval(self.test_send_status, 0)
        #Clock.schedule_interval(self.check_for_new_value, 0)

    # async UI loop to process (.1 sec)
    # 1. property change in VALUE_TEMP and send SET_PROPERTY
    # 2. Define device busy
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

    # async UI loop 1 sec
    # update device busy
    # send ONLINE msg every INTERVAL seconds
    # update Network status
    # check property values and trigger a context
    #
    # process tasks
    # task is a UI response system
    # when an Information is to be shown to the user on message arrival such as a device deletion etc
    # a task is added to command status table
    # a task is removed if it is older than 15 seconds
    async def UI_loop2(self, *args):
        TASK_COUNT = {}
        #interval_online = db.get_device_interval_online(id_device=self.ID_DEVICE)
        COUNTER = 0
        while 1:
            #self.send_info()

            # check for busy period and update the db
            id_topic = ""
            #print("busy_devs", db.get_busy_devices(is_busy=1))
            for id_device, is_busy, busy_period  in db.get_busy_devices(is_busy=1):
                #print("BUSY_DEV", id_device, is_busy, busy_period, int(time.time()))
                if int(busy_period) == int(time.time()):
                    db.update_device_busy(id_device=id_device, is_busy=0, busy_period=0)

            if(SMAC_PLATFORM == "android") and ((COUNTER % 5) == 0):
                await property_listener(self.ID_DEVICE)
            #print("interval", interval_online)
            #print("COUNTER", COUNTER)
            if (COUNTER % self.INTERVAL_ONLINE) == 0:
                #COUNTER = 0
                print("Sending CMD_ONLINE")
                #print("Sending CMD_ONLINE")
                client.send_message(frm=self.ID_DEVICE, to="#", cmd=smac_keys["CMD_ONLINE"], message={})
                await  asyncio.sleep(0)


            if (COUNTER % 10) == 0:
                print("updating state_connection")
                self.STATE_CONNECTION = update_network_connection()
                print(self.STATE_CONNECTION)

            # check for trigger and update value
            if (COUNTER % 60) == 0:
                triggers = db.get_triggers_all()
                if triggers == None:
                    triggers = []
                for id_topic, id_context, id_device, id_property, value, type_trigger in triggers:
                    if type_trigger == smac_keys["TYPE_TRIGGER_PROP"]:
                        db_value = db.get_value_by_property(id_device, id_property)
                        print(str(db_value))
                        print(str(value))
                        print( str(db_value) == str(value) )
                        if str(db_value) == str(value):
                            self.trigger_context(id_context)
                            #self.send_trigger_context(id_context)
                    elif type_trigger == smac_keys["TYPE_TRIGGER_TIME"]:
                        value_hour, value_min, DOW = value.split(":")
                        DOW = DOW.split(",")
                        time1 = datetime.now()
                        print("DOW", time1.weekday())
                        print(DOW)
                        print("is DOW ", int(DOW[time1.weekday()]))
                        if(value_hour == str(time1.hour)) and (value_min == str(time1.minute)) and ( int( DOW[time1.weekday()] ) ):
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

    # OLD
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

    # get local ip address
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

    # get config variable from config.json
    def get_config_variable(self, key):
        try:
            with open('config.json', 'r') as f:
                fd = json.load(f)
                d = fd.get(key, None)
                if (d != None) and ( key in ["LIMIT_DEVICE", "LIMIT_TOPIC", "LIMIT_CONTEXT"] ):
                    d = self.decode_word(d)
                f.close()
                return d
        except:
            return None

    # delete a aconfig variable in config.json
    def delete_config_variable(self, key):
        with open('config.json', 'r') as f:
            fd = json.load(f)
            d = fd.get(key, None)
            f.close()
        if d != None:
            with open('config.json', 'w') as f1:
                fd = json.load(f1)
                del fd[key]
                f1.write( json.dumps(fd) )
                f1.close()


    # update a config variable in config.json
    def update_config_variable(self, key, value, arr_op="ADD"):
        with open('config.json', 'r') as f:
            fd = json.load(f)
            if key == "SUB_TOPIC":
                if arr_op == "ADD":
                    fd[key] += [ value ]
                elif arr_op == "REM":
                    if value in fd[key]:
                        fd[key].remove(value)
                self.SUB_TOPIC = fd[key]
            elif key in ["LIMIT_DEVICE", "LIMIT_TOPIC", "LIMIT_CONTEXT"]:
                fd[key] = self.encode_word( value)
            else:
                fd[key] = value
                if key == "ID_DEVICE":
                    self.ID_DEVICE = value
                elif key == "theme":
                    self.theme = value
            f.close()
        with open('config.json', 'w') as f:
            f.write(json.dumps(fd))
            f.close()

    # set config.json default values
    # used to reset a device
    def set_default_config(self):
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
        #d["EMAIL"] = "manjunathls13@gmail.com"
        d["EMAIL"] = ""
        d["MOBILE_NUMBER"] = ""
        d["LOGIN_PIN"] = "1234"
        d["EMAIL_VERIFIED"] = False
        d["VERSION"] = 0.5
        d['theme'] = "LIGHT"
        #d["PLATFORM"] = SMAC_PLATFORM
        f.write(json.dumps(d))
        f.close()

        self.ID_DEVICE = ""

    # on device start, load config.json variables and update to APP varibles for faster processing
    def load_config_variables(self, *args):
        from smac_device import get_device_name, get_device_type
        changed = False
        if not os.path.isfile('config.json'):
            self.set_default_config()

        f = open('config.json', 'r')
        if len(f.read()) == 0:
            self.set_default_config()

        with open('config.json', 'r') as f:
            fd = json.load(f)
            print("fd", fd)
            if fd["ID_DEVICE"] == "":
                #d_id = self.get_local_ip()
                d_id = restapi.req_get_device_id()
                #while self.get_config_variable("ID_DEVICE") == "":
                #    pass
                #from smac_device import get_id_device
                #d_id = get_id_device()
                #print("d_id", d_id)
                #if (d_id != "") and (d_id != None):
                #    fd["ID_DEVICE"] = d_id
                #    changed = True
                #else:
                #    self.open_modalInfo(title="Info", text="Could not get the Device Id.\nCheck the Network Connection.")
            else:
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
            if fd.get("EMAIL", None) != None:
                self.EMAIL = fd.get("EMAIL")
            if fd.get("MOBILE_NUMBER", None) != None:
                self.MOBILE_NUMBER = fd.get("MOBILE_NUMBER")
            print(self.theme)
            self.theme = fd.get("theme", "LIGHT")
            #if fd.get("PLATFORM", None) != None:
             #   self.PLATFORM = fd.get("PLATFORM")
            f.close()

        print("fd", fd)
        print(self.theme)
        if changed:
            with open('config.json', 'w') as f:
                f.write( json.dumps(fd) )
                f.close()



    # when ZMQ is initialized, send device_info 
    def on_tcp_start(self, *args):
        print("TCP services started")
        print(args)
        self.send_info(tcp=True, udp=False)

    # set a keyboard 
    def initialise_keyboard(self, *args):
        #self._KEYBOARD = EventLoop.window.request_keyboard(
        #    self._keyboard_released,
        #    self.screen_manager
        #)
        self._KEYBOARD = kivy.core.window.Keyboard

    # bind keydown events to the app window
    def _bind_keyboard(self):
        self.initialise_keyboard()
        Window.bind(on_key_down=self._on_keyboard_down)

    # unbind keydown events to the app window
    def _unbind_keyboard(self):
        Window.unbind(on_key_down=self._on_keyboard_down)
        #self._KEYBOARD.release()

    # on keybaord key press
    # ESC     --> close app
    # TOP     --> navigate top
    # BOTTOM  --> navigate bottom
    # ENTER   --> press, focus etc
    def _on_keyboard_down(self, window, keycode, *args):
        #print(args)
        #print(keycode)
        key = self._KEYBOARD.keycode_to_string(self._KEYBOARD, keycode)
        #print(k)
        scr = self.screen_manager.get_screen(name=self.screen_manager.current)
        if key == "escape":
            print(scr.back_screen)
            if scr.back_screen != None:
                self.BACK_BTN_COUNTER = 0
                self.change_screen(scr.back_screen)
            elif self.BACK_BTN_COUNTER == 1:
                self.stop()
            else:
                self.BACK_BTN_COUNTER += 1
                notification.notify(message="Press Again to Close.", toast=True)
            return True
        if len(scr.nodes) > scr.index:
            if key  == "down":
                print(scr.index)
                print(scr.nodes)
                print(scr.nodes[scr.index])
                scr.nodes[scr.index].select = False
                if (scr.index+1) <= scr.max_index:
                    scr.index += 1
                else:
                    scr.index = 0
                scr.nodes[scr.index].select = True
                wid = scr.nodes[scr.index]
                #if wid.y >= Window.size[1]:
                #print("hasattr", hasattr(wid, "scroll_container") )
                print("wid pos", self.screen_manager.collide_point(*wid.pos))

                if hasattr(wid, "scroll_container"):
                    print(wid.scroll_container.scroll_y)
                    wid.scroll_container.scroll_to(wid)
                #self.nodes[self.index-1].select = False
            elif key  == "up":
                scr.nodes[scr.index].select = False
                if (scr.index-1) >= 0:
                    scr.index -= 1
                else:
                    scr.index = scr.max_index
                #self.index -= 1
                scr.nodes[scr.index].select = True
                #self.nodes[self.index + 1].select = False
                #self.nodes[self.index - 1].select = False
                wid = scr.nodes[scr.index]
                if hasattr(wid, "scroll_container"):
                    wid.scroll_container.scroll_to(wid)
            elif key == 'enter':
                wid = scr.nodes[scr.index]
                if wid.__class__.__name__ == "Widget_switch":
                    wid.dispatch("on_press")
                if Button in wid.__class__.__bases__:
                    wid.dispatch("on_release")
                elif CheckBox in wid.__class__.__bases__:
                    wid.active = not wid.active
                elif ButtonBehavior in wid.__class__.__bases__:
                    wid.dispatch("on_release")
                elif TextInput in wid.__class__.__bases__:
                    wid.focus = not wid.focus


    # when a keyboard is unbinded and released
    def _keyboard_released(self, *args):
        print("keyboard_released", args)

    # encode word
    # used to encode DEVICE_PIN
    def encode_word(self, string):
        try:
            t = base64.b64encode( str(string).encode(encoding="utf-8") ).decode("utf-8")
            #print("BASE64", t)
            return str(t)
        except:
            return None

    # decode a code
    def decode_word(self, code):
        try:
            #print(code)
            #print(type(code))
            t = base64.b64decode( str(code).encode(encoding="utf-8") ).decode(encoding="utf-8")
            #print(type(t))
            #print("BASE64a", t)
            return t
        except:
            return None

    # load limits from SMAC server
    def load_device_data(self, *args):
        #self.decode_word( b'NQ=')
        req = "request_device_data"
        url = SMAC_SERVER + req
        print("ID_DEV", self.ID_DEVICE)
        r = restapi.rest_call(url, method="GET", data={"id_device": self.ID_DEVICE}, request=req, on_success=self.on_req_device_data)
        if SMAC_PLATFORM == "android":
            #time.sleep(5)
            #check_update_url = "https://api.github.com/repos/initio-smac/smac_kivy/contents/download.json"
            check_update_url = "https://raw.githubusercontent.com/initio-smac/smac_kivy/main/download.json"
            restapi.rest_call(check_update_url, method="GET", request="check_for_update", on_success=self.on_update_available)

    # if software updates are available, popup the info
    def on_update_available(self, req, data):
        try:
            print("NEw update available")
            print(data)
            data = json.loads(data)
            NEW_VERSION = data.get("VERSION", None)
            if (NEW_VERSION != None) and (NEW_VERSION > self.VERSION):
                content = BoxLayout_downloadUpdateContent()
                self.open_modal(title="Updates", content=content)

        except Exception as e:
            print("update app err", e)

    # download the app and show the progress 
    def download_app(self):
        #self.close_modal()
        notification.notify(message="Downloading Smac App.", toast=True)
        url = "https://raw.githubusercontent.com/initio-smac/smac_kivy/main/bin/smacapp-0.1-armeabi-v7a-debug.apk"
        download_path =  '/sdcard/Download/smac.apk'
        th = UrlRequest(url=url, method="GET", chunk_size=8192, on_progress=self.on_download_progress, on_success=self.install_app_success, on_failure=self.install_app_failure)
        print("downloading app...")
        loader = BoxLayout_loader()
        self.open_modal(content=loader)
        self.modal.ids["id_loader"] = loader

    # update the widget value on download progress
    def on_download_progress(self,*args):
        print(args)
        progress = int(args[1]/args[2]*100)
        self.modal.ids["id_loader"].text = "Downloading ({}%)".format(progress)
        print("Download IP: {}%".format(progress))
        notification.notify(title="SMAC", message="Downloading ({}%)".format(progress))
        #print(cur_size/total_size)

    # once the app is downloaded, install it
    # android only
    def install_app_success(self, req, data):
        self.modal.ids["id_loader"].text = "App Downloaded."
        notification.notify(message="Downloaded.", toast=True)
        filename = '/sdcard/Download/smac.apk'
        with open(filename, 'wb') as f:
            f.write(data)
            f.close()
            print("File content written")
        print("app downloades")
        from jnius import autoclass, cast
        Intent = autoclass("android.content.Intent")
        Uri = autoclass('android.net.Uri')
        File = autoclass('java.io.File')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')

        intent = Intent(Intent.ACTION_VIEW);
        intent.setDataAndType(Uri.fromFile( File(filename)), "application/vnd.android.package-archive");
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        currentActivity = PythonActivity.mActivity
        currentActivity.getApplicationContext().startActivity(intent)
        #startActivity(intent);

    # install app failure callback
    def install_app_failure(self, req, data):
        print("install app failure")
        print(data)

    # on REQ_GET_DEVICE_DATA from SMAC server success
    # get and update limits on current device from smac server
    def on_req_device_data(self, res, data):
        try:
            if data.get("limit_topic", None) != None:
                self.update_config_variable(key="LIMIT_TOPIC", value=data.get("limit_topic"))
            if data.get("limit_device", None) != None:
                self.update_config_variable(key="LIMIT_DEVICE", value=data.get("limit_device"))
        except Exception as e:
            print("on_req_err", e)

    # on app stop
    def on_stop(self, *args):
        print("APP stopped")
        if self.BROADCAST_RECEIVER != None:
            self.BROADCAST_RECEIVER.stop()
        for task in self._TASKS:
            task.cancel()

    # on app pause
    def on_pause(self):
        print("APP pause")
        return True

    # on app resume
    def on_resume(self):
        print("APP resume")
        return True

    # get the ZMQ server address from SMAC, if success
    def on_server_address_success(self, req, data):
        print("on server address success")
        print(req)
        print(data)
        print(client.ZMQ_PUB_PORT)
        print(client.ZMQ_SUB_PORT)
        client.ZMQ_SERVER = data.get("server",  client.ZMQ_SERVER)
        client.ZMQ_PUB_PORT = data.get("port_pub", client.ZMQ_PUB_PORT)
        client.ZMQ_SUB_PORT = data.get("port_sub", client.ZMQ_SUB_PORT)
        print(client.ZMQ_PUB_PORT)
        print(client.ZMQ_SUB_PORT)

    # get the ZMQ server address from SMAC, if failure
    def on_server_address_failure(self, req, err, *args):
        print("on server address failure")
        print(err)

    # on app start
    # get the ZMQ server address from SMAC
    # bind keyboard functions
    # load app_data
    # get DEVICE limits and update locally
    def on_start(self):
        print("kivy started")
        print("starting smac_client...")
        restapi.rest_call(url="https://www.smacsystem.com/smacapi/request_server_address", request="request_server_address",
                          method="GET", on_success=self.on_server_address_success, on_failure=self.on_server_address_failure)
        Window.softinput_mode = "below_target"
        self._bind_keyboard()
        self.load_app_data()
        self.load_device_data()
        #self.open_modal(content=BoxLayout_loader())
        #print(self.modal.content.ids["id_loader_icon"].source)
        #print("modal opened")
        #print(self.modal.content)
        #print([i for i in self.modal.content.walk()])

    # on android broadcast
    def on_broadcast(self, context, intent):
        print("on broadcast main")
        from jnius import autoclass
        ConnectivityManager = autoclass('android.net.ConnectivityManager')
        if intent.getAction() == ConnectivityManager.CONNECTIVITY_ACTION:
            extras = intent.getExtras()
            ni = extras.get( ConnectivityManager.EXTRA_NETWORK_INFO )
            if (ni != None) and (ni.isConnectedOrConnecting() ):
                print("extra network info", ni)
            else:
                print("extra no network", extras.get( ConnectivityManager.EXTRA_NO_CONNECTIVITY ))



    # load config.json variables to APP variables
    # subscribe to the topics in db
    # bind event for app-modal/context-modal close button
    # delete all local network entries
    # remove all command status
    # remove all device data except THIS device
    # if no devices, add this device
    # if no property, add this device property
    # get the property value and send updates
    # send device data on_start
    #
    # android
    # check property permissions, and askif necessary
    def load_app_data(self):
        self.load_config_variables()
        if self.get_config_variable(key="EMAIL_VERIFIED"):
            self.change_screen(screen="Screen_network")
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
        if SMAC_PLATFORM == "android":
            from jnius import autoclass, cast
            from android.broadcast import BroadcastReceiver
            #service = autoclass('com.smacsystem.smacapp.ServiceMyservice')
            #mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
            #argument = ''
            #service.start(mActivity, argument)

            from android.permissions import request_permissions, check_permission, Permission
            print("permision", check_permission(Permission.CAMERA))
            if not check_permission(Permission.CAMERA):
                request_permissions([Permission.CAMERA])
            if not check_permission(Permission.WRITE_EXTERNAL_STORAGE):
                request_permissions( [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE] )

            ConnectivityManager = autoclass('android.net.ConnectivityManager')
            self.BROADCAST_RECEIVER =  BroadcastReceiver( self.on_broadcast, actions=[ConnectivityManager.CONNECTIVITY_ACTION] )
            self.BROADCAST_RECEIVER.start()


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