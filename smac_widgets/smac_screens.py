import asyncio

#from kivy import platform
#from kivy.core.window import Window
#from kivy.properties import DictProperty
import json
import random
import re
import socket
from functools import partial

from kivy.clock import Clock
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.screenmanager import Screen
#from kivy.app import App
#from kivy.uix.scrollview import ScrollView


from smac_device import set_property, generate_id_topic, generate_id_context
from smac_device_keys import SMAC_PROPERTY, SMAC_DEVICES
from smac_keys import smac_keys
from smac_platform import SMAC_PLATFORM
from smac_requests import SMAC_SERVER, restapi
from smac_widgets.smac_layouts import *
from smac_tools import network_scanner
from webrepl.webrepl_client import webrepl_client



from smac_client import client


from smac_db import db
import time

class SelectClass(Screen):
    nodes = []
    index = 0
    max_index = 0
    #scroll_containers = []

    def get_selectable_nodes(self, widget=None, *args):
        self.nodes = []
        self.index = 0
        #self.max_index = 0
        w = widget if(widget != None) else self
        #print(widget)
        #print(w)
        scroll_container = None
        #print("wid", [ a for a in w.walk()])
        for wid in w.walk():
            #print(wid)

            if "ScrollView" == wid.__class__.__name__:
                scroll_container = wid
            #print("scroll_con", scroll_container)
            try:
                #print(wid.__class__.__bases__)
                #print(SelectBehavior in wid.__class__.__bases__)
                #print(wid.width)
                #if(not wid.disabled) and (wid.width > 0) and (wid.height >= 0):
                if(not wid.disabled):
                    if SelectBehavior in wid.__class__.__bases__:
                        self.nodes.append(wid)
                        if scroll_container != None:
                            wid.scroll_container = scroll_container
                        wid.select = False
            except Exception as e:
                print(e)
            self.max_index = len(self.nodes) - 1

    async def get_nodes(self, *args):
        await asyncio.sleep(1)
        self.get_selectable_nodes()

    def on_enter(self, *args):
        #if platform != "android":
        #self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        #self._keyboard.bind(on_key_down=self._on_keyboard_down)
        #self._keyboard.release()
        #self.get_selectable_nodes()
        asyncio.gather(self.get_nodes())


    def on_leave(self, *args):
        self.nodes = []

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        _, key = keycode
        print(key)
        if len(self.nodes) > self.index:
            if key  == "down":
                print(self.index)
                print(self.nodes)
                print(self.nodes[self.index])
                self.nodes[self.index].select = False
                if (self.index+1) <= self.max_index:
                    self.index += 1
                else:
                    self.index = 0
                self.nodes[self.index].select = True
                #self.nodes[self.index-1].select = False
            elif key  == "up":
                self.nodes[self.index].select = False
                if (self.index-1) >= 0:
                    self.index -= 1
                else:
                    self.index = self.max_index
                #self.index -= 1
                self.nodes[self.index].select = True
                #self.nodes[self.index + 1].select = False
                #self.nodes[self.index - 1].select = False
            elif key == 'enter':
                wid = self.nodes[self.index]
                #print(wid)
                if Button in wid.__class__.__bases__:
                    wid.dispatch("on_release")
                elif ButtonBehavior in wid.__class__.__bases__:
                    wid.dispatch("on_release")
                elif TextInput in wid.__class__.__bases__:
                    wid.focus = True

class Screen_espConfig(SelectClass):
    CONNECTED = BooleanProperty(False)
    ADDR = ""
    scan_task = None
    DATA = DictProperty({})
    modal = None
    UPDATE_FILE = None

    def on_enter(self, *args):
        #self.scan_task = asyncio.create_task(network_scanner.scan_network(port=8266) )
        #asyncio.gather( self.scan_task )
        #asyncio.run( self.scan_task )
        #network_scanner.scan_network(port=8266)
        pass

    def on_CONNECTED(self, wid, value, *args):
        app = App.get_running_app()
        if value:
            app.open_modalInfo(text="Connected to {}".format(self.ADDR))
            #self.ids["id_config_state_text"].text = "Connected to {} ({})".format( network_scanner.get_hostname(self.ADDR), self.ADDR )
            f = webrepl_client.get_file("config_esp.json", "config.json")
            self.DATA = json.loads(f)
            print("F", self.DATA)
            self.add_config_widgets()
        else:
            self.clear_config_widgets()

    def add_config_widgets(self):
        app = App.get_running_app()
        container = self.ids["id_esp_config_container"]

        wa1 = Widget_block()
        wa1.text = "Update Device Name"
        w1 = BoxLayout(size_hint=(1, None))
        w1.height = app.grid_min
        txt1 = TextInput_custom(hint_text="Device Name")
        txt1.text = self.DATA.get("name_device", "")
        self.ids["id_name_device"] = txt1
        btn1 = Button_custom1(text="Update")
        btn1.bind(on_release=self.update_device_name)
        w1.add_widget(txt1)
        w1.add_widget(btn1)
        wa1.add_widget(w1)

        wa2 = Widget_block()
        wa2.height = app.grid_min*4
        wa2.text = "Update Wifi Config"
        wifi_con = self.DATA.get("wifi_config_1", {"ssid": "", "password": ""})
        txt2 = TextInput_custom(hint_text="SSID", size_hint_y=None, height=app.grid_min)
        txt2.text = wifi_con["ssid"]
        #txt2.height = app.grid_min
        self.ids["id_ssid"] = txt2
        txt3 = TextInput_custom(hint_text="Password",size_hint_y=None,  height=app.grid_min)
        txt3.text = wifi_con["password"]
        #txt3.height = app.grid_min
        self.ids["id_password"] = txt3
        btn2 = Button_custom1(text="Update")
        btn2.bind(on_release=self.update_wifi_config)
        wa2.add_widget(txt2)
        wa2.add_widget(txt3)
        wa2.add_widget(btn2)

        wa3 = Widget_block()
        wa3.text = "Software Update"
        btn3 = Button_link(text="Select .Zip File")
        btn3.bind(on_release=self.select_zip_file)
        self.ids["id_btn_sel_file"] = btn3
        btn4 = Button_custom1(text="Update")
        btn4.bind(on_release=self.update_software)
        wa3.add_widget(btn3)
        wa3.add_widget(btn4)

        container.add_widget(wa1)
        container.add_widget(wa2)
        container.add_widget(wa3)

    def update_device_name(self, btn):
        app = App.get_running_app()
        text = self.ids["id_name_device"].text
        res = webrepl_client.update_config_variable(key="name_device", value=text)
        if res:
            app.open_modalInfo(title="Info", text="Device Name Updated")
        else:
            app.open_modalInfo(title="Info", text="Device Name Not Updated")

    def update_wifi_config(self, btn):
        app = App.get_running_app()
        ssid = self.ids["id_ssid"].text
        password = self.ids["id_password"].text
        res = webrepl_client.update_config_variable(key="wifi_config_1", value={"ssid": ssid, "password": password} )
        if res:
            app.open_modalInfo(title="Info", text="Wifi Config Updated")
        else:
            app.open_modalInfo(title="Info", text="Wifi Config Not Updated")

    def select_zip_file(self, btn):
        #app = App.get_running_app()
        fc = FileChooserListView(on_submit=self.on_file_selection, filters=["*.zip"])
        self.modal = Popup(title="Select A .zip Update File", content=fc)
        self.modal.open()

    def on_file_selection(self, filechooser, files,  *args):
        print("file selection")
        print(args)
        self.UPDATE_FILE = files[0]
        self.ids["id_btn_sel_file"].text += "({})".format(self.UPDATE_FILE)
        if self.modal != None:
            self.modal.dismiss()

    def update_software(self, btn):
        app = App.get_running_app()
        app.open_modal(content=BoxLayout_loader(text="Updating Software..."))
        if self.UPDATE_FILE != None:

            res = webrepl_client.send_files(zip_file=self.UPDATE_FILE)
            if res:
                app.open_modalInfo(title="Info", text="Software Updated.")
            else:
                app.open_modalInfo(title="Info", text="Software Not Updated.")
        else:
            app.open_modalInfo(title="Info", text="Select A Valid File to Continue.")

    def clear_config_widgets(self):
        container = self.ids["id_esp_config_container"]
        container.clear_widgets()

    def on_leave(self, *args):
        self.CONNECTED = False
        if self.scan_task != None:
            #self.scan_task.cancel()
            self.scan_task = None

    def connect_esp(self, addr):
        self.ADDR = addr
        self.CONNECTED = webrepl_client.connect_ws(host=addr, port=8266, passwd=1234)
        if self.CONNECTED:
            text = "Connected to Address: {}".format(addr)
        else:
            text = "Couldn't connect to the Address: {}".format(addr)
        #app = App.get_running_app()
        #app.open_modalInfo(title="Info", text=text)
        print(self.CONNECTED)


class Screen_context(SelectClass):
    modal = ModalView_custom(size_hint_x=.9, size_hint_max_x=dp(400), size_hint_y=None, height=dp(400))
    is_modal_open = False
    _interval = None
    add_action_content = None
    add_trig_content = None
    data = DictProperty({
        "id_topic": "",
        "id_context": '',
        'name_context': '',
        "id_device": "",
        "name_device": "Device",
        "id_property": "",
        "name_property": "Prop",
        "type_property": "",
        "value": "0",
        "value_min": "0",
        "value_max": "1",
        "value_hour": "0",
        "value_minute": "0"
    })

    def open_modal(self, content, title="Info", auto_dismiss=True):
        print(self.modal.children)
        if content != None:
            print(content)
            print(content.height)
            self.modal.content = content
            self.modal.title = title
            self.modal.height = content.height + dp(70)
            self.modal.open(auto_dismiss=auto_dismiss)
            self.is_modal_open = True
            # clear old selectable widgets and replace with current modal widgets
            app = App.get_running_app()
            scr = app.screen_manager.get_screen(app.screen_manager.current)
            scr.get_selectable_nodes(widget=self.modal)

    def close_modal(self, *args):
        self.modal.dismiss()
        self.modal.title = ""
        self.is_modal_open = False

        # clear current modal selectable widgets and
        # replace with old modal selectable widgets if that modal is open else
        # replace with old screen selectable widgets
        app = App.get_running_app()
        scr = app.screen_manager.get_screen(app.screen_manager.current)
        wid = app.modal if app.is_modal_open else self
        scr.get_selectable_nodes(widget=wid)

    def on_release_add_btn(self, wid, *args):
        app = App.get_running_app()
        #content = BoxLayout(size_hint_y=None, orientation="vertical")
        #content.height = content.minimum_height
        #for w in ["Add Action", "Add Trigger"]:
        #    btn =  Button_custom1(text=w, size_hint_x=1)
        #    btn.bind(on_release=self.open_add_action_trigger_modal)
        #    content.add_widget(btn)
        cxt_obj = wid.parent.parent
        self.data["id_context"] = cxt_obj.id_context
        self.data["name_context"] = cxt_obj.name_context

        content = BoxLayout_btnActionTriggerContent()
        for child in content.children:
            child.bind(on_release=self.open_add_action_trigger_modal)
        app.open_modal(content)

    def on_data(self, *args):
        if self.add_action_content != None:
            self.add_action_content.data = self.data
        if self.add_trig_content != None:
            self.add_trig_content.data = self.data

    def open_add_action_trigger_modal(self, wid, *args):
        app = App.get_running_app()
        #app.close_modal()
        if wid.text == "Add Action":
            self.add_action_content = BoxLayout_addActionContent()
            self.add_action_content.data = self.data
            self.add_action_content.ids["id_btn_sel_device"].bind(on_release=self.open_device_selection)
            self.add_action_content.ids["id_btn_sel_property"].bind(on_release=self.open_property_selection)
            self.add_action_content.ids["id_btn_sel_value"].bind(on_release=self.open_value_selection)
            self.add_action_content.ids["id_btn_add_action"].bind(on_release=self.add_action)
            app.open_modal(content=self.add_action_content, title='Add Action')
        if wid.text == "Add Trigger":
            self.add_trig_content = BoxLayout_addTriggerContent()
            self.add_trig_content.data = self.data
            self.add_trig_content.ids["id_btn_sel_device"].bind(on_release=self.open_device_selection)
            #self.add_trig_content.ids["id_btn_sel_device1"].bind(on_release=self.open_device_selection)
            self.add_trig_content.ids["id_btn_sel_property"].bind(on_release=self.open_property_selection)
            self.add_trig_content.ids["id_btn_sel_value"].bind(on_release=self.open_value_selection)
            self.add_trig_content.ids["id_btn_sel_hour"].bind(on_release=self.open_value_time_selection)
            self.add_trig_content.ids["id_btn_sel_minute"].bind(on_release=self.open_value_time_selection)
            self.add_trig_content.ids["id_btn_add_trigger"].bind(on_release=self.add_trigger)
            app.open_modal(content=self.add_trig_content, title="Add Trigger")

    def add_trigger(self, wid, *args):
        add_trigger_root = wid.parent.parent
        add_trigger_container = wid.parent
        #print(wid)
        #print(add_trigger_root)
        #print(add_trigger_container)
        type_trigger = smac_keys["TYPE_TRIGGER_PROP"]
        print("child")
        for child in add_trigger_container.children:
            print(child)
            chkbox= child.ids.get("id_chkbox", None)
            if (chkbox != None) and chkbox.active:
                print("active", chkbox.active)
                type_trigger = chkbox.value
                break
        print(type_trigger)
        app = App.get_running_app()
        id_device = self.data["id_device"]
        #id_device = self.data["id_device"]
        value = self.data["value"]
        id_context = self.data['id_context']
        id_topic = app.APP_DATA["id_topic"]
        id_property = self.data["id_property"] if (type_trigger == smac_keys["TYPE_TRIGGER_PROP"]) else "TIME"
        print( type_trigger == smac_keys["TYPE_TRIGGER_TIME"] )
        print("DOW", add_trigger_root.DOW)
        if type_trigger == smac_keys["TYPE_TRIGGER_TIME"]:
            if "".join( [ str(i) for i in  add_trigger_root.DOW] ) == "0000000":
                app.open_modalInfo(title="Info", text="Select a Timer Repetition")
                return
            value = "{}:{}:{}".format(self.data["value_hour"], self.data["value_minute"], ",".join( [str(i) for i in add_trigger_root.DOW ]) )
        elif (id_device == None) or (id_device == ""):
            app.open_modalInfo(text="Select A Device to Continue")
            return
        if (id_property == None) or (id_property == ""):
            app.open_modalInfo(text="Select A Property to Continue")
            return
        if (value == None) or (value == ""):
            app.open_modalInfo(text="Select A Value to Continue")
            return
        if (id_device == app.ID_DEVICE) or (type_trigger == smac_keys["TYPE_TRIGGER_TIME"]):
            db.add_context_trigger(id_context=id_context, id_topic=id_topic, id_device=id_device, id_property=id_property,  value=value, type_trigger=type_trigger)
            d1 = {}
            d1[smac_keys["ID_DEVICE"]] = id_device
            d1[smac_keys["ID_TOPIC"]] = id_topic
            d1[smac_keys["ID_CONTEXT"]] = id_context
            d1[smac_keys["ID_PROPERTY"]] = id_property
            d1[smac_keys["TYPE_TRIGGER"]] = type_trigger
            #d1[smac_keys["NAME_CONTEXT"]] = name_context
            d1[smac_keys["VALUE"]] = value
            # id_topic, id_context, id_device, id_property, value, name_context
            client.send_message(frm=app.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_STATUS_ADD_TRIGGER"], message=d1)
            app.open_modalInfo(text="Context Trigger added")
        else:
            d = {}
            d[smac_keys["ID_TOPIC"]] = id_topic
            d[smac_keys["ID_DEVICE"]] = id_device
            d[smac_keys["ID_CONTEXT"]] = self.data["id_context"]
            d[smac_keys["ID_PROPERTY"]] = id_property
            d[smac_keys["TYPE_TRIGGER"]] = type_trigger
            #d[smac_keys["NAME_CONTEXT"]] = self.data["name_context"]
            d[smac_keys["VALUE"]] = value
            d[smac_keys["PASSKEY"]] = db.get_pin_device(id_device)
            #id_topic, id_context, id_device, id_property, value
            client.send_message(frm=app.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_ADD_TRIGGER"], message=d, udp=True,
                                tcp=True)
            #app.add_task(db.get_command_status, (self.data["id_topic"], id_device, [smac_keys["CMD_STATUS_ADD_TRIGGER"], smac_keys["CMD_INVALID_PIN"], smac_keys["CMD_TRIGGER_LIMIT_EXCEEDED"]]))
            app.add_task(db.get_command_status, (id_topic, id_device, [smac_keys["CMD_STATUS_ADD_TRIGGER"], smac_keys["CMD_INVALID_PIN"], smac_keys["CMD_ACTION_LIMIT_EXCEEDED"]], "", self.data["id_context"]))
            app.open_modal(content=BoxLayout_loader(), auto_dismiss=False)
        self.set_context_data_default_values()

    def add_action(self, wid, *args):
        app = App.get_running_app()
        print("self.data", self.data)
        id_device = self.data["id_device"]
        id_property = self.data["id_property"]
        id_topic = app.APP_DATA["id_topic"]
        value = self.data["value"]
        if(id_device == None) or (id_device == ""):
            app.open_modalInfo(text="Select A Device to Continue")
            return
        if (id_property == None) or (id_property == ""):
            app.open_modalInfo(text="Select A Property to Continue")
            return
        if (value == None) or (value == ""):
            app.open_modalInfo(text="Select A Value to Continue")
            return
        if  id_device == app.ID_DEVICE:
            #id_context = generate_id_context(id_device)
            id_context = self.data["id_context"]
            db.add_context_action(id_context=id_context, id_topic=id_topic, id_device=id_device, id_property=id_property, name_context=self.data["name_context"], value=value)
            d1 = {}
            d1[smac_keys["ID_DEVICE"]] = id_device
            d1[smac_keys["ID_TOPIC"]] = id_topic
            d1[smac_keys["ID_CONTEXT"]] = self.data["id_context"]
            d1[smac_keys["ID_PROPERTY"]] = id_property
            d1[smac_keys["NAME_CONTEXT"]] = self.data["name_context"]
            d1[smac_keys["VALUE"]] = value
            # id_topic, id_context, id_device, id_property, value, name_context
            client.send_message(frm=app.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_STATUS_ADD_ACTION"], message=d1)
            app.open_modalInfo(text="Context Action added")
        else:
            d = {}
            d[smac_keys["ID_TOPIC"]] = id_topic
            d[smac_keys["ID_DEVICE"]] = id_device
            d[smac_keys["ID_CONTEXT"]] = self.data["id_context"]
            d[smac_keys["ID_PROPERTY"]] = id_property
            d[smac_keys["NAME_CONTEXT"]] = self.data["name_context"]
            d[smac_keys["VALUE"]] = value
            d[smac_keys["PASSKEY"]] = db.get_pin_device(id_device)
            #id_topic, id_context, id_device, id_property, value, name_context
            client.send_message(frm=app.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_ADD_ACTION"], message=d, udp=True,
                                tcp=True)
            app.add_task(db.get_command_status, (id_topic, id_device, [smac_keys["CMD_STATUS_ADD_ACTION"], smac_keys["CMD_INVALID_PIN"], smac_keys["CMD_ACTION_LIMIT_EXCEEDED"]], "", self.data["id_context"]))
            app.open_modal(content=BoxLayout_loader(), auto_dismiss=False)
        self.set_context_data_default_values()

    def set_context_data_default_values(self, *args):
        self.data = {
            #"id_topic": "",
            "id_context": '',
            'name_context': '',
            "id_device": "",
            "name_device": "Device",
            "id_property": "",
            "name_property": "Prop",
            "type_property": "",
            "value": "0",
            "value_min": "0",
            "value_max": "1",
            "value_hour": "0",
            "value_minute": "0"
        }

    def remove_action(self, wid, *args):
        app = App.get_running_app()
        parent = wid.parent.parent
        # id_topic, id_context, id_device, id_property
        id_device = parent.id_device
        id_context = parent.id_context
        id_topic = app.APP_DATA["id_topic"]
        id_property = parent.id_property
        if id_device == app.ID_DEVICE:
            db.remove_action_by_property(id_context=id_context, id_topic=id_topic, id_device=id_device, id_property=id_property)
            app.remove_action_widget(id_context, id_device, id_property)
            d1 = {}
            d1[smac_keys["ID_DEVICE"]] = id_device
            d1[smac_keys["ID_TOPIC"]] = id_topic
            d1[smac_keys["ID_CONTEXT"]] = id_context
            d1[smac_keys["ID_PROPERTY"]] = id_property
            client.send_message(frm=app.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_STATUS_REMOVE_ACTION"],message=d1)
            app.open_modalInfo(text="Context Action Removed")
        else:
            d = {}
            d[smac_keys["ID_TOPIC"]] = id_topic
            d[smac_keys["ID_DEVICE"]] = id_device
            d[smac_keys["ID_CONTEXT"]] = id_context
            d[smac_keys["ID_PROPERTY"]] = id_property
            d[smac_keys["PASSKEY"]] = db.get_pin_device(id_device)
            # id_topic, id_context, id_device, id_property, value, name_context
            client.send_message(frm=app.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_REMOVE_ACTION"], message=d, udp=True,
                                tcp=True)
            app.add_task(db.get_command_status, (id_topic, id_device,[smac_keys["CMD_STATUS_REMOVE_ACTION"], smac_keys["CMD_INVALID_PIN"]], "", id_context))
            app.open_modal(content=BoxLayout_loader(), auto_dismiss=False)

    def remove_trigger(self, wid, *args):
        app = App.get_running_app()
        parent = wid.parent.parent
        # id_topic, id_context, id_device, id_property
        id_device = parent.id_device
        id_context = parent.id_context
        id_topic = app.APP_DATA["id_topic"]
        id_property = parent.id_property
        type_trigger = parent.type_trigger
        print("type_trig", type_trigger)
        if id_device == app.ID_DEVICE:
            db.remove_trigger_by_property(id_context=id_context, id_topic=id_topic, id_device=id_device, id_property=id_property)
            app.remove_trigger_widget(id_context, id_device, id_property)
            d1 = {}
            d1[smac_keys["ID_DEVICE"]] = id_device
            d1[smac_keys["ID_TOPIC"]] = id_topic
            d1[smac_keys["ID_CONTEXT"]] = id_context
            d1[smac_keys["ID_PROPERTY"]] = id_property
            client.send_message(frm=app.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_STATUS_REMOVE_TRIGGER"],message=d1)
            app.open_modalInfo(text="Context Trigger Removed")
        else:
            d = {}
            d[smac_keys["ID_TOPIC"]] = id_topic
            d[smac_keys["ID_DEVICE"]] = id_device
            d[smac_keys["ID_CONTEXT"]] = id_context
            d[smac_keys["ID_PROPERTY"]] = id_property
            d[smac_keys["TYPE_TRIGGER"]] = type_trigger
            d[smac_keys["PASSKEY"]] = db.get_pin_device(id_device)
            # id_topic, id_context, id_device, id_property, value, name_context
            client.send_message(frm=app.ID_DEVICE, to=id_topic, cmd=smac_keys["CMD_REMOVE_TRIGGER"], message=d, udp=True,
                                tcp=True)
            app.add_task(db.get_command_status, (id_topic, id_device,[smac_keys["CMD_STATUS_REMOVE_TRIGGER"], smac_keys["CMD_INVALID_PIN"]], "", id_context))
            app.open_modal(content=BoxLayout_loader(), auto_dismiss=False)

    def open_device_selection(self, *args):
        app = App.get_running_app()
        scroll = ScrollView(size_hint_y=None)
        scroll.height = app.grid_min * 4
        content = BoxLayout_container(spacing=0)
        content.height = content.minimum_height
        for dev in db.get_device_list_by_topic(id_topic=app.APP_DATA["id_topic"]):
            btn = Button_custom1(size_hint=(1,None), height=app.grid_min, text=dev[1])
            btn.id_device = dev[0]
            btn.name_device = dev[1]
            btn.type_device = dev[2]
            btn.bind(on_release=self.select_device)
            content.add_widget(btn)
        scroll.add_widget(content)
        self.open_modal(content=scroll, title="Select A Device")

    def select_device(self, wid,  *args):
        self.data["id_device"] = wid.id_device
        self.data["name_device"] = wid.name_device
        self.data["type_device"] = wid.type_device
        self.close_modal()

    def open_property_selection(self, *args):
        app = App.get_running_app()
        scroll = ScrollView(size_hint_y=None)
        scroll.height = app.grid_min * 4
        content = BoxLayout_container(spacing=0)
        content.height = content.minimum_height
        print(self.data)
        if self.data["id_device"] != "":
            for prop in db.get_property_list_by_device(id_device=self.data["id_device"]):
                btn = Button_custom1(size_hint=(1,None), height=app.grid_min, text=prop[1])
                btn.id_property =prop[0]
                btn.name_property = prop[1]
                btn.type_property = prop[2]
                btn.value_min = prop[3]
                btn.value_max = prop[4]
                btn.bind(on_release=self.select_property)
                content.add_widget(btn)
            scroll.add_widget(content)
            self.open_modal(content=scroll, title="Select A Property")
        else:
            app.open_modalInfo(text="Select A Device To Continue")

    def select_property(self, wid, *args):
        self.data["id_property"] = wid.id_property
        self.data["name_property"] = wid.name_property
        self.data["type_property"] = wid.type_property
        self.data["value_min"] = wid.value_min
        self.data["value_max"] = wid.value_max
        self.close_modal()

    def open_value_time_selection(self, wid, *args):
        app = App.get_running_app()
        scroll = ScrollView(size_hint_y=None)
        scroll.height = app.grid_min * 4
        content = BoxLayout_container(spacing=0)
        content.height = content.minimum_height
        #content.size_hint_y = None
        value_max = 60 if(wid.time_selection == "minute") else 24
        for val in range(0, value_max, 1):
            btn = Button_custom1(size_hint=(1,None), height=app.grid_min, text=str(val) )
            btn.value = str(val)
            btn.time_selection = wid.time_selection
            btn.bind(on_release=self.select_value_time)
            content.add_widget(btn)
        scroll.add_widget(content)
        self.open_modal(content=scroll, title="Select A Value")

    def select_value_time(self, wid, *args):
        if wid.time_selection == "hour":
            self.data["value_hour"] = wid.value
        elif wid.time_selection == "minute":
            self.data["value_minute"] = wid.value
        self.close_modal()

    def open_value_selection(self, *args):
        app = App.get_running_app()
        if self.data["id_property"] != "":
            scroll = ScrollView(size_hint_y=None)
            scroll.height = app.grid_min * 4
            content = BoxLayout_container(spacing=0)
            content.height = content.minimum_height
            print(self.data)
            value_max = int(self.data["value_max"])
            step = 10 if(value_max >= 100) else 1
            for val in range(int(self.data["value_min"]), value_max+1, step):
                btn = Button_custom1(size_hint=(1,None), height=app.grid_min, text=str(val) )
                btn.value = str(val)
                btn.bind(on_release=self.select_value)
                content.add_widget(btn)
            scroll.add_widget(content)
            self.open_modal(content=scroll, title="Select A Value")
        else:
            app.open_modalInfo(text="Select A Property To Continue")

    def select_value(self, wid, *args):
        self.data["value"] = wid.value
        self.close_modal()

    async def interval(self, timeout=5):
        await asyncio.sleep(.5)
        while 1:
            await self.load_widgets()
            await asyncio.sleep(timeout)

    def on_enter(self, *args):
        app = App.get_running_app()
        #c = self.modal.children[0].children[0]
        #c.add_widget(Label_custom(text="ge", size_hint=(None, None), size=(50, 50), pos=(c.right, c.y)))
        #print(c.children)
        #print(c.pos)
        #print(c.children[0].pos)
        print("id_topic", app.APP_DATA["id_topic"])
        self._interval = asyncio.gather(self.interval(1))
        super().on_enter()
        self.modal.ids["id_btn_close"].bind(on_release=self.close_modal)

    def on_leave(self, *args):
        #container = self.ids["id_context_container"]
        #container.clear_widgets()
        #if self._interval != None:
        #    self._interval.cancel()
        super().on_leave()
        self.modal.ids["id_btn_close"].unbind(on_release=self.close_modal)
        pass

    async def load_widgets(self, *args):
        await asyncio.sleep(0)
        app = App.get_running_app()
        id_topic = app.APP_DATA["id_topic"]
        container = self.ids["id_context_container"]
        for id_topic, id_context, name_context in db.get_context_by_topic(id_topic):
            if container.ids.get(id_context, None) == None:
                c = Widget_context(text=name_context)
                c.id_topic = id_topic
                c.id_context = id_context
                container.ids[id_context] = c
                container.add_widget(c)
                c.ids["id_icon1"].bind(on_release=self.on_release_remove_context)
                c.ids["id_icon2"].bind(on_release=self.on_release_add_btn)
                c.ids["id_icon3"].bind(on_release=self.on_release_trigger_context)
            else:
                c = container.ids[id_context]
            c.name_context = name_context
            actions = db.get_action_by_context(id_context)
            c.ids["id_label_act"].text = "Actions" if(len(actions) > 0) else ''
            #label_act = Label_title(text="Actions")
            #if (c.ids.get("label_act", None) == None) and (len(actions) > 0):
            #    c.ids["label_act"] = label_act
            #    c.add_widget(label_act)
            #else:
            #    if label_act in c.children:
            #        c.remove_widget(label_act)
            for id_device, id_property, value, comparator, status, last_updated in actions:
                #try:
                if (id_device != None) and (id_device != ''):
                    id = "act_{}:{}".format(id_device, id_property)
                    name_device = db.get_device_name(id_device)
                    if c.ids.get(id, None) == None:
                        a = BoxLayout_action()
                        np = db.get_property_name_by_property(id_device, id_property)
                        a.name_property = ""
                        if np != None:
                            a.name_property = np[0]
                            a.type_property = np[1]
                        a.id_context = id_context
                        a.id_device = id_device
                        a.id_property = id_property
                        a.ids["id_btn_remove_action"].bind(on_release=self.remove_action)
                        c.ids[id] = a
                        c.ids["id_action_container"].add_widget(a)
                    else:
                        a = c.ids[id]
                    a.text = "When device: {} property: {} value is {}".format(name_device, a.name_property, value)
                    a.status = int(status)

                #except Exception as e:
                #    print("exception while adding action: {}".format(e))
            triggers = db.get_trigger_by_context(id_context)
            c.ids["id_label_trig"].text = "Triggers" if(len(triggers) > 0) else ''
            #print(triggers)
            #label_trig = Label_title(text="Triggers")
            #if (c.ids.get("label_trig", None) == None) and (len(triggers) > 0):
            #    c.ids["label_trig"] = label_trig
            #    c.add_widget(label_trig)
            #else:
            #    if label_trig in c.children:
            #        c.remove_widget(label_trig)
            for id_device, id_property, value,  status, last_updated, type_trigger in triggers:
                #try:
                #if(id_device != None) and (id_device != ''):
                if (id_device != None):
                    id_trig = "trig_{}:{}".format(id_device, id_property)
                    name_device = db.get_device_name(id_device)
                    if c.ids.get(id_trig, None) == None:
                        t = BoxLayout_trigger()
                        t.name_property = ""
                        if type_trigger == smac_keys["TYPE_TRIGGER_PROP"]:
                            np = db.get_property_name_by_property(id_device, id_property)
                            #print(id_device, id_property)
                            #print("np", np)
                            if np != None:
                                t.name_property = np[0]
                                t.type_property = np[1]
                        elif type_trigger == smac_keys["TYPE_TRIGGER_TIME"]:
                            t.name_property = "time"
                            t.type_property = ""
                        t.id_context = id_context
                        t.id_device = id_device
                        t.id_property = id_property
                        t.type_trigger = type_trigger
                        #t.text = "When device: {} property: {} value is {}".format(name_device, t.name_property, value)
                        t.ids["id_btn_remove_trigger"].bind(on_release=self.remove_trigger)
                        c.ids[id_trig] = t
                        c.ids["id_trigger_container"].add_widget(t)
                    else:
                        t = c.ids[id_trig]
                    t.text = "When device: {} property: {} value is {}".format(name_device, t.name_property, value)
                    #print(type_trigger)
                    #print(smac_keys["TYPE_TRIGGER_TIME"])
                    #print(type_trigger == smac_keys["TYPE_TRIGGER_TIME"])
                    if type_trigger == smac_keys["TYPE_TRIGGER_TIME"]:
                        hh, mm, DOW = value.split(":")
                        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                        #print(DOW)
                        DOW = [ days[num] for num, i in enumerate(DOW.split(",")) if(int(i)) ]
                        #print(DOW)
                        t.text = "When Time is {}:{} {}".format( hh, mm, DOW)
                    t.status = int(status)
                #except Exception as e:
                #    print("exception while adding trigger: {}".format(e))

    def on_release_remove_context(self, wid,  *args):
        cxt_obj = wid.parent.parent
        app = App.get_running_app()
        print(cxt_obj)
        db.remove_context(cxt_obj.id_context, cxt_obj.id_topic)
        container = self.ids["id_context_container"]
        container.remove_widget(container.ids[cxt_obj.id_context])
        d1 = {}
        d1[smac_keys["ID_CONTEXT"]] = cxt_obj.id_context
        d1[smac_keys["ID_TOPIC"]] = cxt_obj.id_topic
        client.send_message(frm=app.ID_DEVICE, to=cxt_obj.id_topic, cmd=smac_keys["CMD_STATUS_REMOVE_CONTEXT"], message=d1)

    def open_add_context(self, *args):
        app = App.get_running_app()
        content = BoxLayout_addContextContent()
        content.id_topic = app.APP_DATA["id_topic"]
        content.ids["id_btn"].bind(on_release=self.add_context)
        #content.ids["id_name_context"].text = ""
        app = App.get_running_app()
        app.open_modal(content=content, title="Add Context")

    def on_release_trigger_context(self, wid, *args):
        app = App.get_running_app()
        cxt_obj = wid.parent.parent
        app.open_modalInfo(text="Triggering context: {}".format(cxt_obj.name_context))
        d1 = {}
        d1[smac_keys["ID_CONTEXT"]] = cxt_obj.id_context
        #d1[smac_keys["NAME_CONTEXT"]] = cxt_obj.name_context
        #d1[smac_keys["ID_TOPIC"]] = app.APP_DATA["id_topic"]
        client.send_message(frm=app.ID_DEVICE, to="#", cmd=smac_keys["CMD_TRIGGER_CONTEXT"], message=d1)
        app.trigger_context(cxt_obj.id_context)

    def add_context(self, wid, *args):
        content = wid.parent
        print(content)
        app = App.get_running_app()
        id_context = generate_id_context( app.ID_DEVICE )
        name_context = content.ids["id_name_context"].text
        if name_context == "":
            app.open_modalInfo(title="Info", text="Context Name Cannot Be empty.")
            return
        db.add_context(id_context=id_context, name_context=name_context, id_topic=app.APP_DATA["id_topic"])
        app.open_modalInfo(text="Context added")
        d1 = {}
        d1[smac_keys["ID_CONTEXT"]] = id_context
        #d1[smac_keys["ID_DEVICE"]] = app.ID_DEVICE
        d1[smac_keys["NAME_CONTEXT"]] = name_context
        d1[smac_keys["ID_TOPIC"]] = app.APP_DATA["id_topic"]
        client.send_message(frm=app.ID_DEVICE, to=app.APP_DATA["id_topic"], cmd=smac_keys["CMD_STATUS_ADD_CONTEXT"], message=d1)

    def remove_context(self, wid, *args):
        content = wid.parent
        app = App.get_running_app()
        id_topic = app.APP_DATA["id_topic"]
        id_context = content.id_context
        db.remove_context(id_context, id_topic)
        d1 = {}
        d1[smac_keys["ID_CONTEXT"]] = id_context
        d1[smac_keys["ID_TOPIC"]] = app.APP_DATA["id_topic"]
        client.send_message(frm=app.ID_DEVICE, to="#", cmd=smac_keys["CMD_STATUS_REMOVE_CONTEXT"], message=d1)



class Screen_network(SelectClass):
    TOPIC_IDS = {}
    RENDERING = False
    RENDERING_COUNT = 0
    CLEAR_WIDGETS = 0
    _interval = None

    async def add_widgets(self, clear_widgets=False, *args):
        #print("RENDERING", self.RENDERING)
        app = App.get_running_app()
        if not self.RENDERING:
            self.RENDERING = True
            self.RENDERING_COUNT += 1
            container = self.ids["id_network_container"]
            #self.ids["id_btn"].text = str(self.RENDERING_COUNT)
            if clear_widgets or self.CLEAR_WIDGETS:
                self.TOPIC_IDS = {}
                container.clear_widgets()
                self.CLEAR_WIDGETS = 0
            name_topic = "" if(app.APP_DATA["name_home"]=="Local") else app.APP_DATA["name_home"]
            for id_topic, name_home, name_topic, view_topic  in db.get_topic_list_by_name_home(name_topic):
                #print("id_topic: {}".format(id_topic))
                if self.TOPIC_IDS.get(id_topic, None) == None:
                    w = Widget_network(text=name_topic)
                    w.disable_icon2 = True
                    w.disable_icon1 = True if(id_topic == "") else False
                    w.DEVICE_IDS = {}
                    w.id_topic = id_topic
                    w.bind(on_release=self.on_topic_release)
                    w.ids["id_icon1"].bind(on_release=self.change_topic_view)
                    self.TOPIC_IDS[id_topic] = w
                    self.ids[id_topic] = w
                    container.add_widget( w )
                    #testing only
                else:
                    w = self.TOPIC_IDS[id_topic]
                w.name_topic= name_topic
                w.view_topic = view_topic
                w.icon1 = 'BOTTOM.png' if view_topic else  'TOP.png'

                #w.bind( on_release=self.goto_prop_page )
                for id_device, name_device, type_device, view_device, is_busy, busy_period, pin_device, pin_device_valid, interval_online, last_updated in db.get_device_list_by_topic(id_topic):
                    #print("id_device: {}".format(id_device))

                    if id_device == app.ID_DEVICE:
                        online = True
                    else:
                        t_diff = int(time.time()) - last_updated
                        online =  True if(t_diff <= interval_online+20) else False
                    if online:
                        if( w.DEVICE_IDS.get(id_device, None) == None):
                            w1 = Widget_device(text=name_device)
                            w1.disable_icon2 = True if (id_topic == None) else False
                            w1.PROP_IDS = {}
                            w1.id_device = id_device
                            w1.name_device = name_device
                            w1.type_device = type_device
                            w1.ids["id_icon1"].bind(on_release=self.change_device_view)
                            w1.icon2 = 'SETTING.png'
                            w1.ids["id_icon2"].bind(on_release=self.goto_setting_page)
                            w.DEVICE_IDS[id_device] = w1
                            w.add_widget(w1)

                            '''if id_device == app.ID_DEVICE:
                                img = Image_iconButton(source=app.source_icon + 'FAN.png')
                                w1.add_widget(img)
                                sp = random.randint(1, 3)
                                sp = 5
                                print(sp)
                                self.start_animation(img, duration=sp)'''
                        else:
                            w1 = w.DEVICE_IDS[id_device]

                        w1.name_device= name_device
                        w1.text = name_device
                        w1.id_topic = id_topic
                        w1.view_device = view_device
                        w1.icon1 =  'BOTTOM.png' if view_device else 'TOP.png'
                        w1.hide = view_topic
                        w1.pin_device_valid = pin_device_valid
                        w1.interval_online = interval_online

                        #print("is_busy", is_busy)
                        for id_property, property_name, type_property, value_min, value_max, value, value_temp, value_last_updated in db.get_property_list_by_device(id_device):
                            #print("id_property: {}".format(id_property))
                            #print("value", value)
                            #print(type(value))
                            type_property = str(type_property)
                            if w1.PROP_IDS.get(id_property, None) == None:
                                w2 = Widget_property(text="{}:{}".format(property_name, value) )
                                w2.id_property = id_property
                                w2.id_device = id_device
                                w2.value = 0 if(value == None) else int(value)
                                w2.value_max = value_max
                                w2.value_min = value_min
                                w2.type_property = str(type_property)
                                w2.source = self.get_icon(type_property=w2.type_property)
                                w1.PROP_IDS[id_property] = w2
                                w1.add_widget(w2)
                                slider_container = w2.ids["id_slider_container"]
                                if value_max == 1:
                                    slider = Widget_switch()
                                    w2.ids["id_slider"] = slider
                                    slider.value = w2.value
                                    slider.bind(on_release=self.change_value)
                                    slider_container.add_widget(slider)
                                elif value_max > 1:
                                    slider = Widget_slider(value=w2.value, value_max=value_max, value_min=value_min, step=1)
                                    w2.ids["id_slider"] = slider
                                    slider.bind(value_copy=self.change_value)
                                    if w2.type_property in [ SMAC_PROPERTY["BATTERY"] ]:
                                        slider.disabled = True
                                        slider.cursor_image = app.source_icon + 'TRANSPARENT.png'
                                    slider_container.add_widget(slider)
                            else:
                                w2 = w1.PROP_IDS[id_property]

                            #if property_name == "BRIGHTNESS":
                            #	print("is_busy", is_busy)
                            w2.text = property_name
                            if value != None:
                                w2.value = int(value)
                            w2.ids["id_property_name"].bind(on_release=self.on_prop_name_release)
                            w2.is_busy = is_busy
                            w1.text1 = " ( DEVICE BUSY ) " if is_busy else ""
                            # hide for hiding the widget based on the Expand or Collapse icon on the Parent Widget
                            w2.hide = view_device
                    else:
                        if w.DEVICE_IDS.get(id_device, None) != None:
                            w.remove_widget( w.DEVICE_IDS.get(id_device) )
                            del w.DEVICE_IDS[id_device]

                #print("\n")
            self.RENDERING = False
            #super().get_selectable_nodes()
        else:
            print("ALREADY RENDERING")

    def on_prop_name_release(self, wid, *args):
        wid_prop = wid.parent
        prop_name = wid.text
        content = BoxLayout_updatePropNameContent()
        content.id_device = wid_prop.id_device
        content.id_property = wid_prop.id_property
        content.ids["id_btn"].bind(on_release=self.update_property_name)
        content.ids["id_name_property"].text = prop_name
        app = App.get_running_app()
        app.open_modal(content=content, title="Update Property Name")

    def update_property_name(self, wid, *args):
        w = wid.parent
        name_property = w.name_property
        id_property = w.id_property
        id_device = w.id_device
        app = App.get_running_app()
        if (name_property == "") or (name_property == None):
            app.open_modalInfo(title="Info", text="Property Name cannot be empty.")
            return
        if id_device == app.ID_DEVICE:
            db.update_name_property(id_device, id_property, name_property)
            print("Property Name updated")
            app.open_modalInfo(text="Property Name Updated")
        else:
            passkey = db.get_pin_device(id_device=id_device)
            d = {}
            d[smac_keys["ID_DEVICE"]] = id_device
            d[smac_keys["PASSKEY"]] = passkey
            d[smac_keys["NAME_PROPERTY"]] = name_property
            d[smac_keys["ID_PROPERTY"]] = id_property
            client.send_message(frm=app.ID_DEVICE, to=id_device, cmd=smac_keys["CMD_UPDATE_NAME_PROPERTY"], message=d,
                                udp=True,
                                tcp=True)
            app.add_task(db.get_command_status, (
            "", id_device, [smac_keys["CMD_STATUS_UPDATE_NAME_PROPERTY"], smac_keys["CMD_INVALID_PIN"]], id_property))
            app.open_modal(content=BoxLayout_loader(), auto_dismiss=False)

    def goto_setting_page(self, wid, *args):
        w = wid.parent.parent
        app = App.get_running_app()
        app.APP_DATA["id_device"] = w.id_device
        app.APP_DATA["name_device"] = w.name_device
        app.APP_DATA["type_device"] = w.type_device
        app.change_screen(screen="Screen_deviceSetting")

    def change_value(self, wid, *args):
        wid_prop = wid.parent.parent.parent
        app = App.get_running_app()
        print("ID_TOPIC", app.APP_DATA["id_topic"])
        value = int(wid.value)
        app = App.get_running_app()
        if wid_prop.id_device == app.ID_DEVICE:
            set_property(type_property=wid_prop.type_property, id_property=wid_prop.id_property, value=value)
        else:
            d = {}
            d[ smac_keys["ID_PROPERTY"] ] = wid_prop.id_property
            d[ smac_keys["TYPE_PROPERTY"] ] = wid_prop.type_property
            d[ smac_keys["ID_DEVICE"]] = wid_prop.id_device
            d[ smac_keys["VALUE"]] = value
            MSG_ID = (client.MSG_ID + 1)
            #asyncio.gather(app.check_for_ack(MSG_ID, 10))
            #app.open_modal(text="Sending message to the device...", auto_close=True, timeout=10)
            #client.send_message(frm=app.ID_DEVICE, to=wid_prop.id_device, cmd=smac_keys["CMD_SET_PROPERTY"], message=d, udp=True, tcp=True)
            client.send_message(frm=app.ID_DEVICE, to=wid_prop.id_device, cmd=smac_keys["CMD_SET_PROPERTY"], message=d, udp=True, tcp=True)
            wid_prop.MSG_COUNTER = MSG_ID

    def get_icon(self, type_property, *args):
        app = App.get_running_app()
        if type_property == SMAC_PROPERTY["BATTERY"]:
            return 'BATTERY.png'
        elif type_property == SMAC_PROPERTY["BLUETOOTH"]:
            return  'BLUETOOTH.png'
        elif type_property == SMAC_PROPERTY["FLASH"]:
            return 'FLASH.png'
        elif type_property == SMAC_PROPERTY["BRIGHTNESS"]:
            return 'BRIGHTNESS.png'
        elif type_property == SMAC_PROPERTY["SHUTDOWN"]:
            return 'SHUTDOWN.png'
        elif type_property == SMAC_PROPERTY["RESTART"]:
            return 'RESTART.png'
        else:
            return ''


    def change_topic_view(self, icon, *args):
        app = App.get_running_app()
        wid = icon.parent.parent
        wid.view_topic = (1-wid.view_topic)
        view = wid.view_topic
        wid.icon1 = 'BOTTOM.png' if view else 'TOP.png'
        for i in wid.children:
            i.hide = view
        #print( type(wid.view_topic) )
        db.set_topic_view(id_topic=wid.id_topic, view_topic=view)

    def change_device_view(self, icon, *args):
        app = App.get_running_app()
        wid = icon.parent.parent
        wid.view_device = (1 - wid.view_device)
        view = wid.view_device
        wid.icon1 = 'BOTTOM.png' if view else  'TOP.png'
        #print( type(wid.view_device) )
        for i in wid.children:
            i.hide = view
        db.set_device_view(id_topic=wid.id_topic, id_device=wid.id_device, view_device=view)

    def on_topic_release(self, wid, *args):
        #anim = Animation(size=self.size, duration=1)
        #anim.repeat = True
        #anim.start(wid)
        pass

    def start_animation(self, img, duration=1, *args):
        #anim = Animation(size=[dp(60), dp(60)], duration=.1)
        #anim += Animation(size=[dp(50), dp(50)], duration=.5)\
        anim = Animation(angle=-360, duration=duration)
        anim += Animation(angle=-360, duration=duration)
        anim.repeat = True
        anim.start(img)
        anim.on_start = self.on_anim_start

    def on_anim_start(self, wid, *args):
        #wid.rot.origin = wid.center
        pass

    async def interval(self, timeout=5):
        await asyncio.sleep(.5)
        while 1:
            await self.add_widgets()
            await asyncio.sleep(timeout)

    def add_menu_widgets(self, *args):
        #app = App.get_running_app()
        menu = self.ids["id_menu_home_container"]
        menu.clear_widgets()
        menu.ids ={}
        for name_home, id_topic in db.get_home_list():
            if (name_home not in menu.ids.keys()):
                if (name_home != "") and (name_home != None):
                    # name_home = "Local"
                    print("name_home", name_home)
                    wid = Label_menuItem(text=name_home)
                    wid.id_topic = id_topic
                    wid.padding = ( dp(10), dp(15))
                    #wid.bg_color = app.colors["COLOR_THEME"]
                    wid.bind(on_release=self.on_menu_item_release)
                    menu.ids[name_home] = wid
                    menu.add_widget(wid)

    def clear_menu_widgets(self, *args):
        menu = self.ids["id_menu_home_container"]
        menu.clear_widgets()
        menu.ids = {}

    def on_enter(self, *args):

        #self.add_widgets()
        #Clock.schedule_interval(self.add_widgets, 1)
        #print(self.ids)
        #db.delete_network_entry(id_topic='')
        #app = App.get_running_app()
        #self.center_x = app.screen_manager.center_x


        self._interval = asyncio.gather(self.interval(1))
        super().on_enter()

    def on_leave(self, *args):
        #container = self.ids["id_network_container"]
        #container.clear_widgets()
        super().on_leave()
        #if self._interval != None:
        #    self._interval.cancel()

    def open_close_menu(self,  *args):
        app = App.get_running_app()
        menu_container = self.ids["id_menu_container"]
        menu_bg = self.ids["id_menu_bg"]
        #print("menu pos", menu_container.pos)
        #print(app.screen_manager.collide_point(*menu_container.pos))
        width = 0 if(menu_container.width > 0) else app.grid_min * 6
        #menu_bg.disabled = 0 if(width > 0) else 1
        #menu_bg.opacity = 0.5 if(width > 0) else 0
        menu_bg.size_hint_x = 1 if(width >0) else 0
        anim = Animation(width=width, duration=.1)
        anim.start(menu_container)
        #self.get_selectable_nodes(widget=self.modal)
        print(width)
        if width > 0:
            #self.get_selectable_nodes(widget=menu_container)
            self.add_menu_widgets()
            self.get_selectable_nodes(widget=self.ids["id_menu_container"])
        else:
            self.clear_menu_widgets()
            self.get_selectable_nodes()



    def on_menu_item_release(self, wid, *args):
        app = App.get_running_app()
        app.APP_DATA["name_home"] = wid.text
        app.APP_DATA["id_topic"] = wid.id_topic
        self.open_close_menu()
        self.CLEAR_WIDGETS = 1

    def goto_prop_page(self, wid,  *args):
        app = App.get_running_app()
        app.app_data["id_device"] = wid.id_device
        app.app_data["name_device"] = wid.name_device
        app.change_screen("Screen_property")

    def add_widgets_old(self, *args):
        container = self.ids["id_network_container"]
        container.clear_widgets()
        for id_topic, name_topic in db.get_topic_list():
            # print("id_topic: {}".format(id_topic))
            w = Widget_network(text=id_topic)
            w.id_topic = id_topic
            w.name_topic = name_topic
            container.add_widget(w)
            # testing only
            button = Button(text="delete", size_hint=(None, None), size=(dp(100), dp(50)))
            app = App.get_running_app()
            button.bind(on_release=app.delete_topic)
            button.id_topic = id_topic
            w.add_widget(button)

            # w.bind( on_release=self.goto_prop_page )
            for id_device, name_device in db.get_device_list_by_topic(id_topic):
                # print("id_device: {}".format(id_device))
                w1 = Widget_device(text=name_device)
                # w1.color = [  ]
                w1.id_device = id_device
                w1.name_device = name_device
                w1.type_device = ty
                w.add_widget(w1)

                for id_property, property_name, value in db.get_property_list_by_device(id_device):
                    # print("id_property: {}".format(id_property))
                    w2 = Widget_property(text="{}:{}".format(property_name, value))
                    w2.id_property = id_property
                    w2.property_name = "{}:{}".format(property_name, value)
                    w2.value = value
                    w1.add_widget(w2)

class Screen_deviceSetting(SelectClass):

    data = DictProperty({
        'interval_online': 10
    })

    #modal.content = None

    def load_widgets(self, clear=True, *args):
        '''dd_home_container = self.ids["id_dropdown_home_container"]
        dd_home = dd_home_container.ids["id_dropdown"]
        dd_room_container = self.ids["id_dropdown_room_container"]
        dd_room = dd_room_container.ids["id_dropdown"]
        if clear:
            dd_home.clear_widgets()
            dd_room.clear_widgets()'''
            #for child in dd_home.children:
            #	dd_home.remove(child)
            #for child in dd_room.children:
            #	dd_room.remove(child)
        app = App.get_running_app()
        id_device = app.APP_DATA["id_device"]
        # get the topic list which are not subscribed and append to the
        # dropdown list
        print("ID_DEV", id_device)
        print("DEVS", db.get_topic_list_not_by_device(id_device=id_device))
        btn = Button_custom1(text="Add Home/Room")
        btn.size_hint_x=1
        #btn.background_color = app.colors["COLOR_THEME_BASIC"]
        btn.bind(on_release=self.create_topic)
        self.ids["id_topic_container"].clear_widgets()
        self.ids["id_topic_container"].add_widget(btn)
        DEVS = db.get_topic_list_not_by_device(id_device=id_device)
        for id_topic, name_home, name_topic in DEVS:
            print(id_topic)
            #if (id_topic != None) and (id_topic != "") and (id_topic not in app.SUB_TOPIC):
            print(app.SUB_TOPIC)
            if (id_topic != None) and (id_topic != ""):
                '''label = Label_dropDown(text=name_home)
                label.id_topic = id_topic
                label.bind(on_release=self.on_dropdown_homeitem_release)
                dd_home.add_widget(label)

                label = Label_dropDown(text=name_topic)
                label.id_topic = id_topic
                label.bind(on_release=self.on_dropdown_roomitem_release)
                dd_room.add_widget(label)'''

                label = Widget_block(text=name_home+"/"+name_topic)
                label.orientation = "horizontal"
                label.bg_color = app.colors["COLOR_THEME_BASIC"]
                label.id_topic = id_topic
                label.name_home= name_home
                label.name_room = name_topic
                self.ids["id_topic_container"].add_widget(label)
                btn = Image_iconButton(source=app.source_icon + 'CHECK.png')
                btn.bind(on_release=partial(self.subscribe_topic, name_home, name_topic, id_topic) )
                btn.pos = label.pos
                label.add_widget(btn)
        if len(DEVS) == 0:
            label = Label_custom(text="No Homes", size_hint_y=None, height=app.grid_min)
            self.ids["id_topic_container"].add_widget(label)

        #if (len(devs) == 1) and ( ('','','') in devs ):
        #    label = Label_custom(text="No Homes", size_hint_y=None, height=app.grid_min)
        #    self.ids["id_topic_container"].add_widget(label)


        #label = Label_dropDown(text="Add Home")
        #label.bind(on_release=self.create_home)
        #dd_home.add_widget(label)

        #label = Label_dropDown(text="Add Room")
        #label.bind(on_release=self.create_room)
        #dd_room.add_widget(label)

        # get the topic list which are subscribed by the device
        # and add it to a list
        device_container = self.ids["id_device_container"]
        if clear:
            device_container.clear_widgets()
        devs = db.get_topic_list_by_device(id_device=id_device)
        print("devs", devs)
        if len(devs) > 0:
            for id_topic, name_home, name_topic in devs:
                if (id_topic != None) and (id_topic != ""):
                    label = Widget_block(text=name_home + "/" + name_topic, orientation="horizontal",
                                         height=app.grid_min)
                    label.bg_color = app.colors["COLOR_THEME_BASIC"]
                    label.id_topic = id_topic
                    btn = Image_iconButton(source=app.source_icon + 'CLOSE.png')
                    btn.bind(on_release=self.unsunbscribe_topic)
                    # btn.pos = 0,0
                    label.add_widget(btn)
                    # label.bind(on_release=self.on_dropdown_item_release)
                    device_container.add_widget(label)
        else:
            label = Label_custom(text="No Homes", size_hint_y=None, height=app.grid_min)
            device_container.add_widget(label)

        if (len(devs) == 1) and ( ('','','') in devs ):
            label = Label_custom(text="No Homes", size_hint_y=None, height=app.grid_min)
            device_container.add_widget(label)

    def get_device_interval(self, id_device):
        interval = db.get_device_interval_online(id_device)
        if interval != None:
            return str(interval)
        else:
            return str(30)

    def create_topic(self, *args):
        content = BoxLayout_addTopicContent(spacing='2dp')
        content.ids["id_btn"].bind(on_release=self.add_topic_widget)
        app = App.get_running_app()
        app.open_modal(content=content, title="Add Home")

    def add_topic_widget(self, wid, *args):
        print(args)
        print(wid.parent)
        app = App.get_running_app()
        name_home = wid.parent.name_home
        if(name_home == "") or (name_home == None):
            app.open_modalInfo(title="Info", text="Home Name Should Not Be Empty.")
            return
        name_room = wid.parent.name_room
        if (name_room == "") or (name_room == None):
            app.open_modalInfo(title="Info", text="Room Name Should Not Be Empty.")
            return
        id_topic = generate_id_topic(app.ID_DEVICE)
        self.subscribe_topic(name_home, name_room, id_topic)


    def create_home(self, *args):
        content = BoxLayout_addHomeContent()
        content.ids["id_btn"].bind(on_release=self.add_home_widget)
        app = App.get_running_app()
        app.open_modal(content=content, title="Add home")

    def create_room(self, *args):
        content = BoxLayout_addRoomContent()
        content.ids["id_btn"].bind(on_release=self.add_room_widget)
        app = App.get_running_app()
        app.open_modal(content=content, title="Add room")

    def add_home_widget(self, wid, *args):
        name_home = wid.parent.name_home
        dd_home_container = self.ids["id_dropdown_home_container"]
        dd_home = dd_home_container.ids["id_dropdown"]
        label = Label_button(text=name_home)
        label.id_topic = None
        label.bind(on_release=self.on_dropdown_homeitem_release)
        dd_home.add_widget(label)
        dd_home.select(name_home)
        app = App.get_running_app()
        app.close_modal()

    def add_room_widget(self, wid, *args):
        app = App.get_running_app()
        #dd_home_container = self.ids["id_dropdown_home_container"]
        dd_room_container = self.ids["id_dropdown_room_container"]
        dd_room = dd_room_container.ids["id_dropdown"]
        #dd_home = dd_home_container.ids["id_dropdown"]
        id_topic = generate_id_topic(app.ID_DEVICE)
        name_topic=wid.parent.name_topic
        #name_home = dd_home_container.text

        label = Label_button(text=name_topic)
        label.id_topic = id_topic
        label.bind(on_release=self.on_dropdown_roomitem_release)
        dd_room.add_widget(label)
        dd_room.select(name_topic)
        dd_room.id_topic = id_topic
        app.close_modal()
        #self.add_home(name_home, name_topic, show_popup=True)

    def add_device_specific_widgets(self):
        container = self.ids["id_container"]
        app = App.get_running_app()
        if app.ID_DEVICE == app.APP_DATA["id_device"]:
            wid = Widget_block()
            wid.text = "Reconfigure Device"
            btn = Button_custom1(text="Reconfigure")
            btn.bind( on_release=self.reconfigure_device )
            wid.add_widget( btn)
            container.ids["id_reconfigure_device"] = wid
            container.add_widget(wid)

        if str( app.APP_DATA["type_device"] ) == SMAC_DEVICES["ESP"]:
            w1 = Widget_block()
            w1.text = "Update Wifi Config"
            w1.height = w1.minimum_height
            b1 = BoxLayout_updateWifiContent()
            #b1.ids["id_btn_wifi_config"].bind(on_release=self.update_device_wifi_config )
            b1.ids["id_btn_update_wifi"].bind(on_release=self.update_device_wifi_config )
            w1.add_widget( b1)
            container.ids["id_wifi_config"] = w1
            container.add_widget(w1)

            w2 = Widget_block()
            w2.text = "Device Updates and Downloads"
            b2 = Button_custom1(text="Check for Updates")
            b2.width = app.grid_min*4
            b2.bind(on_release=self.update_software)
            w2.add_widget(b2)
            container.ids["id_device_updates"] = w2
            container.add_widget(w2)

    def remove_device_specific_widgets(self):
        container = self.ids["id_container"]
        if container.ids.get("id_reconfigure_device", None) != None:
            container.remove_widget(container.ids["id_reconfigure_device"])
        if container.ids.get("id_wifi_config", None) != None:
            container.remove_widget(container.ids["id_wifi_config"])
        if container.ids.get("id_device_updates", None) != None:
            container.remove_widget(container.ids["id_device_updates"])

        
    def reconfigure_device(self, *args):
        app = App.get_running_app()
        db.remove_all_entries()
        app.set_default_config()
        app.load_config_variables()
        app.open_modalInfo(text="Device Reconfigured.")

    def on_enter(self, *args):
        super().on_enter()
        self.load_widgets()
        app = App.get_running_app()
        interval = db.get_device_interval_online(id_device=app.APP_DATA["id_device"])
        self.data["interval_online"] = interval
        self.add_device_specific_widgets()

        print(self.data)
        print(app.APP_DATA["type_device"])
        print( type(app.APP_DATA["type_device"]) )
        print(SMAC_DEVICES["ESP"])
        print( type(SMAC_DEVICES["ESP"]))
        print(app.APP_DATA["type_device"] == SMAC_DEVICES["ESP"])

    def on_leave(self, *args):
        super().on_leave()
        self.remove_device_specific_widgets()

    def unsunbscribe_topic(self, wid, *args):
        app = App.get_running_app()
        id_device = app.APP_DATA["id_device"]
        id_topic = wid.parent.id_topic
        passkey = db.get_pin_device(id_device=id_device)
        if id_device == app.ID_DEVICE:
            app.delete_topic(frm=app.ID_DEVICE, id_topic=id_topic, id_device=id_device, passkey=passkey)
        else:
            d = {}
            d[smac_keys["ID_TOPIC"]] = id_topic
            d[smac_keys["ID_DEVICE"]] = id_device
            d[smac_keys["PASSKEY"]] = passkey
            client.send_message(frm=app.ID_DEVICE, to=id_device, cmd=smac_keys["CMD_REMOVE_TOPIC"], message=d,
                                udp=True, tcp=True)
            app.add_task(db.get_command_status,
                         (id_topic, id_device, [smac_keys["CMD_STATUS_REMOVE_TOPIC"], smac_keys["CMD_INVALID_PIN"]]))
            app.open_modal(content=BoxLayout_loader(), auto_dismiss=False)
        self.load_widgets()

    def subscribe_topic(self, name_home, name_room, id_topic,*args):
        #name_home, name_room, id_topic = wid.parent.name_home, wid.parent.name_room, wid.parent.id_topic
        app = App.get_running_app()
        id_device = app.APP_DATA["id_device"]
        passkey = db.get_pin_device(id_device=id_device)
        if id_device == app.ID_DEVICE:
            app.add_topic(frm=app.ID_DEVICE, id_topic=id_topic, name_home=name_home, name_topic=name_room, id_device=id_device, passkey=passkey)
            app.open_modalInfo(text="New Home added")
        else:
            d = {}
            d[smac_keys["ID_TOPIC"]] = id_topic
            d[smac_keys["ID_DEVICE"]] = id_device
            d[smac_keys["PASSKEY"]] = passkey
            d[smac_keys["NAME_HOME"]] = name_home
            d[smac_keys["NAME_TOPIC"]] = name_room
            client.send_message(frm=app.ID_DEVICE, to=id_device, cmd=smac_keys["CMD_ADD_TOPIC"], message=d, udp=True,
                                tcp=True)
            app.add_task(db.get_command_status, (id_topic, id_device, [ smac_keys["CMD_STATUS_ADD_TOPIC"], smac_keys["CMD_INVALID_PIN"], smac_keys["CMD_TOPIC_LIMIT_EXCEEDED"] ]) )
            app.open_modal(content=BoxLayout_loader(), auto_dismiss=False)
            # if this device is not added then add it to the Topic
            topics = [ i[0] for i in db.get_device_list_by_topic(id_topic=id_topic) ]
            if app.ID_DEVICE not in topics:
                db.add_network_entry(name_home=name_home, name_topic=name_room, id_topic=id_topic, id_device=app.ID_DEVICE,
                                 name_device=app.NAME_DEVICE, type_device=app.TYPE_DEVICE)
        self.load_widgets()

    '''def subscribe_topic(self, home_dropdown_container, topic_dropdown_container, *args):
        app = App.get_running_app()
        id_device = app.APP_DATA["id_device"]
        try:
            id_topic = topic_dropdown_container.ids["id_dropdown"].id_topic
        except Exception as e:
            print(e)
            app.open_modalInfo(title="Info", text="Please Select a Home to continue.")
            return
        name_home = home_dropdown_container.text
        name_topic = topic_dropdown_container.text
        passkey = db.get_pin_device(id_device=id_device)
        if id_device == app.ID_DEVICE:
            app.add_topic(frm=app.ID_DEVICE, id_topic=id_topic, name_home=name_home, name_topic=name_topic, id_device=id_device, passkey=passkey)
            app.open_modalInfo(text="New Home added")
        else:
            d = {}
            d[smac_keys["ID_TOPIC"]] = id_topic
            d[smac_keys["ID_DEVICE"]] = id_device
            d[smac_keys["PASSKEY"]] = passkey
            d[smac_keys["NAME_HOME"]] = name_home
            d[smac_keys["NAME_TOPIC"]] = name_topic
            client.send_message(frm=app.ID_DEVICE, to=id_device, cmd=smac_keys["CMD_ADD_TOPIC"], message=d, udp=True,
                                tcp=True)
            app.add_task(db.get_command_status, (id_topic, id_device, [ smac_keys["CMD_STATUS_ADD_TOPIC"], smac_keys["CMD_INVALID_PIN"], smac_keys["CMD_TOPIC_LIMIT_EXCEEDED"] ]) )
            app.open_modal(content=BoxLayout_loader(), auto_dismiss=False)
            # if this device is not added then add it to the Topic
            topics = [ i[0] for i in db.get_device_list_by_topic(id_topic=id_topic) ]
            if app.ID_DEVICE not in topics:
                db.add_network_entry(name_home=name_home, name_topic=name_topic, id_topic=id_topic, id_device=app.ID_DEVICE,
                                 name_device=app.NAME_DEVICE, type_device=app.TYPE_DEVICE)
        self.load_widgets()'''


    def on_dropdown_homeitem_release(self, wid, *args):
        print(wid.parent.parent)
        dropdown = wid.parent.parent
        dropdown.select(wid.text)
        dropdown.id_topic = wid.id_topic

    def on_dropdown_roomitem_release(self, wid, *args):
        print(wid.parent.parent)
        dropdown = wid.parent.parent
        dropdown.select(wid.text)
        dropdown.id_topic = wid.id_topic

    '''def add_home(self, name_home, name_topic, show_popup=False, *args):
        app = App.get_running_app()
        id_topic = generate_id_topic(app.ID_DEVICE)
        app.add_topic(frm=app.ID_DEVICE, id_topic=id_topic, name_home=name_home, name_topic=name_topic, id_device=app.ID_DEVICE, passkey=app.PIN_DEVICE)
        #db.add_network_entry(id_topic=id_topic, name_home=name_home, name_topic=name_topic, id_device=app.ID_DEVICE, type_device=app.TYPE_DEVICE, name_device=app.NAME_DEVICE, pin_device=app.PIN_DEVICE)
        #app.update_config_variable(key="SUB_TOPIC", value=id_topic, arr_op="ADD")
        print("New Home added")
        if show_popup:
            app.open_modalInfo(text="New Home added")

        self.load_widgets()'''

    def update_device_pin(self, id_device, passkey):
        app = App.get_running_app()
        if (passkey == "") or (passkey == None):
            app.open_modalInfo(title="Info", text="PIN cannot be empty.")
            return
        db.update_device_pin(id_device, passkey)
        if app.APP_DATA["id_device"] == app.ID_DEVICE:
            app.update_config_variable(key="pin_device", value=passkey)
            app.PIN_DEVICE = passkey
        print("Pin updated")
        app.open_modalInfo(text="PIN updated")

    def update_device_name(self, id_device, name_device):
        app = App.get_running_app()
        if (name_device == "") or (name_device == None):
            app.open_modalInfo(title="Info", text="Device Name cannot be empty.")
            return
        if id_device == app.ID_DEVICE:
            db.update_device_name(id_device, name_device)
            app.update_config_variable(key="NAME_DEVICE", value=name_device)
            req = "request_update_name_device"
            url = SMAC_SERVER + req
            restapi.rest_call(url, method="POST", request=req, data={"id_device": app.ID_DEVICE, "name_device": name_device})
            print("Device Name updated")
            app.open_modalInfo(text="Device Name Updated")
        else:
            passkey = db.get_pin_device(id_device=id_device)
            d = {}
            d[smac_keys["ID_DEVICE"]] = id_device
            d[smac_keys["PASSKEY"]] = passkey
            d[smac_keys["NAME_DEVICE"]] = name_device
            client.send_message(frm=app.ID_DEVICE, to=id_device, cmd=smac_keys["CMD_UPDATE_NAME_DEVICE"], message=d, udp=True,
                                tcp=True)
            app.add_task(db.get_command_status, ("", id_device,[smac_keys["CMD_STATUS_UPDATE_NAME_DEVICE"], smac_keys["CMD_INVALID_PIN"]]))
            app.open_modal(content=BoxLayout_loader(), auto_dismiss=False)

    def update_device_interval_online(self, id_device, interval_online):
        app = App.get_running_app()
        if (interval_online == "") or (interval_online == None):
            app.open_modalInfo(title="Info", text="Online Interval cannot be empty.")
            return
        if id_device == app.ID_DEVICE:
            db.update_device_interval_online(id_device, interval_online)
            print("Device Online Interval updated")
            app.open_modalInfo(text="Device Online Interval Updated")
        else:
            passkey = db.get_pin_device(id_device=id_device)
            d = {}
            d[smac_keys["ID_DEVICE"]] = id_device
            d[smac_keys["PASSKEY"]] = passkey
            d[smac_keys["INTERVAL"]] = interval_online
            client.send_message(frm=app.ID_DEVICE, to=id_device, cmd=smac_keys["CMD_UPDATE_INTERVAL_ONLINE"], message=d, udp=True,
                                tcp=True)
            app.add_task(db.get_command_status, ("", id_device,[smac_keys["CMD_STATUS_UPDATE_INTERVAL_ONLINE"], smac_keys["CMD_INVALID_PIN"]]))
            app.open_modal(content=BoxLayout_loader(), auto_dismiss=False)


    def update_device_wifi_config(self, wid, *args):
        app = App.get_running_app()
        id_device = app.APP_DATA["id_device"]
        ssid = wid.parent.ids["id_ssid"].text
        password = wid.parent.ids["id_password"].text
        if (ssid == "") or (ssid == None):
            app.open_modalInfo(title="Info", text="SSID cannot be empty.")
            return
        if (password == "") or (password == None):
            app.open_modalInfo(title="Info", text="Password cannot be empty.")
            return
        passkey = db.get_pin_device(id_device=id_device)
        d = {}
        d[smac_keys["ID_DEVICE"]] = id_device
        d[smac_keys["PASSKEY"]] = passkey
        d[smac_keys["SSID"]] = ssid
        d[smac_keys["PASSWORD"]] = password
        client.send_message(frm=app.ID_DEVICE, to=id_device, cmd=smac_keys["CMD_UPDATE_WIFI_CONFIG"], message=d, udp=True,
                            tcp=True)
        app.add_task(db.get_command_status, ("", id_device,[smac_keys["CMD_STATUS_UPDATE_WIFI_CONFIG"], smac_keys["CMD_INVALID_PIN"]]))
        app.open_modal(content=BoxLayout_loader(), auto_dismiss=False)

    def update_software(self, wid, *args):
        app = App.get_running_app()
        id_device = app.APP_DATA["id_device"]
        passkey = db.get_pin_device(id_device=id_device)
        d = {}
        d[smac_keys["ID_DEVICE"]] = id_device
        d[smac_keys["PASSKEY"]] = passkey
        client.send_message(frm=app.ID_DEVICE, to=id_device, cmd=smac_keys["CMD_UPDATE_SOFTWARE"], message=d, udp=True,
                            tcp=True)
        #app.add_task(db.get_command_status, ("", id_device,[smac_keys["CMD_STATUS_UPDATE_WIFI_CONFIG"], smac_keys["CMD_INVALID_PIN"]]))
        #app.open_modal(content=BoxLayout_loader(), auto_dismiss=False)
        app.open_modalInfo(text="Request sending to check for Updates...")


class Screen_register(SelectClass):
    REQ_USER_CONSENT =  200
    br = None
    CLK = None
    OTP_REQ_COUNT = 0
    OTP_REQ_MAX_COUNT = 30
    content_register = None
    LOGIN_BLOCKED = BooleanProperty(False)
    LOGIN_ATTEMPT_FAIL_COUNT = 0
    LOGIN_ATTEMPT_FAIL_COUNT_MAX = 3
    STATE = OptionProperty("", options=["", "SEND_PIN", "SEND_PIN_SUCCESS", "SEND_PIN_FAILURE", \
                                        "VERIFY_PIN", "VERIFY_PIN_SUCCESS", "VERIFY_PIN_FAILURE"])

    def on_STATE(self, val, *args):
        if (self.STATE == "SEND_PIN") or (self.STATE == "VERIFY_PIN_FAILURE") or (self.STATE == "SEND_PIN_SUCCESS"):
            self.content_register.ids["id_btn_send_pin"].disabled = True
            self.content_register.ids["id_btn_verify_pin"].disabled = False
            self.content_register.ids["id_text_email"].disabled = True
            self.content_register.ids["id_text_mobile_number"].disabled = True
            self.content_register.ids["id_text_email_pin"].disabled = False
        elif (self.STATE == "VERIFY_PIN") :
            self.content_register.ids["id_btn_send_pin"].disabled = True
            self.content_register.ids["id_btn_verify_pin"].disabled = True
            self.content_register.ids["id_text_email"].disabled = True
            self.content_register.ids["id_text_mobile_number"].disabled = True
            self.content_register.ids["id_text_email_pin"].disabled = True
        elif (self.STATE == "VERIFY_PIN_SUCCESS") or (self.STATE == ""):
            if self.content_register != None:
                self.content_register.ids["id_btn_send_pin"].disabled = False
                self.content_register.ids["id_btn_verify_pin"].disabled = False
                self.content_register.ids["id_text_email"].disabled = False
                self.content_register.ids["id_text_mobile_number"].disabled = False
                self.content_register.ids["id_text_email_pin"].disabled = False
        elif (self.STATE == "SEND_PIN_FAILURE"):
            self.content_register.ids["id_btn_send_pin"].disabled = False
            self.content_register.ids["id_btn_verify_pin"].disabled = True
            self.content_register.ids["id_text_email"].disabled = False
            self.content_register.ids["id_text_mobile_number"].disabled = False
            self.content_register.ids["id_text_email_pin"].disabled = True
        self.stop_otp_timer()

    # timer to enable req_OTP_pin after 30 seconds
    def start_otp_timer(self):
        self.CLK = Clock.schedule_interval(self.update_OTP_count, 1)

    def stop_otp_timer(self, *args):
        if self.CLK != None:
            self.CLK.cancel()
            self.CLK = None
        if self.content_register != None:
            self.content_register.ids["id_label_info2"].text = ""
            self.content_register.ids["id_label_info"].text = ""
        self.OTP_REQ_COUNT = 0
        self.STATE = "SEND_PIN_FAILURE"

    def update_OTP_count(self, *args):
        if self.OTP_REQ_COUNT >= self.OTP_REQ_MAX_COUNT:
            self.content_register.ids["id_btn_send_pin"].disabled = False
            self.content_register.ids["id_btn_verify_pin"].disabled = True
            self.content_register.ids["id_text_email"].disabled = False
            self.content_register.ids["id_text_mobile_number"].disabled = False
            self.content_register.ids["id_text_email_pin"].disabled = False
            self.stop_otp_timer()
        else:
            self.OTP_REQ_COUNT += 1
            self.content_register.ids["id_label_info2"].text = "Send OTP Again in {} sec.".format(self.OTP_REQ_MAX_COUNT-self.OTP_REQ_COUNT)

    def on_enter(self, *args):
        #app = App.get_running_app()
        #self.ids["id_text_email"].text = app.EMAIL
        #print("app.EMAIL", app.EMAIL)
        #EMAIL_VERIFIED = app.get_config_variable(key="EMAIL_VERIFIED")
        #if EMAIL_VERIFIED:
        #    app.change_screen(screen="Screen_network")
        #else:
        app = App.get_running_app()
        LOGIN_BLOCKED = app.get_config_variable(key="LOGIN_BLOCKED")
        if LOGIN_BLOCKED != None:
            self.LOGIN_BLOCKED = True
        self.content_register = BoxLayout_register()
        print("on_enter", self.content_register.children)
        if self.content_register.ids.get("id_btn_send_pin", None) != None:
            self.content_register.ids["id_btn_send_pin"].bind(on_release=self.request_login_pin)
            self.content_register.ids["id_btn_verify_pin"].bind(on_release=self.verify_login_pin_server)

        '''if SMAC_PLATFORM == "android":
            from android import activity
            activity.bind(on_activity_result=self.on_activity_result)
            self.start_msg_listener()
            self.startSmsUserConsent()'''

    def start_msg_listener(self):
        if SMAC_PLATFORM == "android":
            from android.broadcast import BroadcastReceiver
            from jnius import autoclass
            SmsRetriever = autoclass("com.google.android.gms.auth.api.phone.SmsRetriever")
            self.br = BroadcastReceiver( self.on_broadcast, actions=[SmsRetriever.SMS_RETRIEVED_ACTION, 'headset_plug'] )
            self.br.start()
            print("BR started")

    def stop_msg_listener(self):
        if SMAC_PLATFORM == "android":
            if self.br != None:
                self.br.stop()


    def on_leave(self, *args):
        if self.content_register.ids.get("id_btn_send_pin", None) != None:
            self.content_register.ids["id_btn_send_pin"].unbind(on_release=self.request_login_pin)
            self.content_register.ids["id_btn_verify_pin"].unbind(on_release=self.verify_login_pin_server)
        self.content_register = None
        self.STATE = ""
        self.stop_msg_listener()

    def open_register_modal(self, *args):
        print(self.content_register.children)
        self.content_register.ids["id_label_info"].text = ""
        app = App.get_running_app()
        app.open_modal(title="Register/Forgot Password", content=self.content_register, auto_dismiss=False)

    def startSmsUserConsent(self):
        from jnius import autoclass
        from android import activity
        activity.bind(on_activity_result=self.on_activity_result)
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        SmsRetriever = autoclass("com.google.android.gms.auth.api.phone.SmsRetriever")
        cli = SmsRetriever.getClient(PythonActivity.mActivity.getApplicationContext())
        print(cli)
        c = cli.startSmsUserConsent(None)
        print(c)
        #c.addOnSuccessListener = self.on_ss
        #c.addOnFailureListener = self.on_st
        #c.add_on_success_listener = self.on_ss
        #c.add_on_failure_listener = self.on_st
        #cli.startSmsUserConsent(None).addOnFailureListener = self.on_msg_failure

    def on_ss(self, *args):
        print("SMS start", args)

    def on_st(self, *args):
        print("SMS stop", args)

    def on_broadcast(self, context, intent):
        print("on-broadcast")
        print(context)
        print(intent)
        from jnius import autoclass, cast
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        CommonStatusCodes = autoclass("com.google.android.gms.common.api.CommonStatusCodes")
        SmsRetriever = autoclass("com.google.android.gms.auth.api.phone.SmsRetriever")
        print("GET ACTION", intent.getAction() )
        print( SmsRetriever.SMS_RETRIEVED_ACTION )
        if intent.getAction() == SmsRetriever.SMS_RETRIEVED_ACTION:
            extras = intent.getExtras()
            smsRetrieverStatus = extras.get(SmsRetriever.EXTRA_STATUS);
            print(smsRetrieverStatus.getStatusCode())
            print(CommonStatusCodes.SUCCESS)
            print(CommonStatusCodes.TIMEOUT)
            code = smsRetrieverStatus.getStatusCode()
            if code == CommonStatusCodes.SUCCESS:
                consentIntent = extras.getParcelable(SmsRetriever.EXTRA_CONSENT_INTENT)
                consentIntent = cast('android.content.Intent', consentIntent)
                currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
                currentActivity.startActivityForResult(consentIntent, self.REQ_USER_CONSENT);
            elif code == CommonStatusCodes.TIMEOUT:
                self.on_msg_failure()

    def on_activity_result(self,req_code, res_code, intent, *args):
        print(args)
        if req_code == self.REQ_USER_CONSENT:
            from jnius import autoclass
            SmsRetriever = autoclass("com.google.android.gms.auth.api.phone.SmsRetriever")
            Activity = autoclass('android.app.Activity')
            print(Activity.RESULT_OK)
            if (res_code == Activity.RESULT_OK) and ( intent != None):
                message = intent.getStringExtra(SmsRetriever.EXTRA_SMS_MESSAGE)
                oneTimeCode = self.parseOneTimeCode(message)
                if oneTimeCode != None:
                    self.content_register.ids["id_text_email_pin"].text = str(oneTimeCode)
                else:
                    print("Cannot parse OTP from message")

    def parseOneTimeCode(self, message):
        print(message)
        matches = re.findall(r"[0-9]{4}", message)
        if len(matches) > 0:
            return matches[0]
        return None


    def on_msg_success(self, *args):
        print("ON_MSG_SUCCESS")
        print(args)

    def on_msg_failure(self, *args):
        print("ON_MSG_FAIL")
        print(args)

    def request_login_pin(self, *args):
        app = App.get_running_app()
        email = self.content_register.ids["id_text_email"].text
        mobile_number = self.content_register.ids["id_text_mobile_number"].text
        if email == "":
            app.open_modalInfo(title="Info", text="Enter Email Address")
            return
        if (mobile_number == "") or (len(mobile_number) < 10):
            app.open_modalInfo(title="Info", text="Enter Valid Mobile Number")
            return
        self.STATE = "SEND_PIN"
        label = self.content_register.ids["id_label_info"]
        label.text = "Sending Email..."
        request = "request_send_pin"
        url = SMAC_SERVER + request
        data = {}
        data["email"] = email
        #data["pin"] = pin
        data["mobile_number"] = mobile_number
        data["id_device"] = app.ID_DEVICE
        OTP = str( random.randint(1000, 9999) )
        data["pin"] = OTP
        data["name_device"] = app.NAME_DEVICE
        #otp_url = "https://2factor.in/API/V1/{api_key}/SMS/{phone_number}/{otp}".format(api_key=app.OTP_API_KEY, phone_number=mobile_number, otp=OTP)
        r = restapi.rest_call(url=url, method="POST", request=request, data=data, on_success=self.on_req_otp_success, on_failure=self.on_req_otp_failure)
        self.start_otp_timer()
        #if SMAC_PLATFORM == "android":
        #    self.startSmsUserConsent()

        if SMAC_PLATFORM == "android":
            from android import activity
            activity.bind(on_activity_result=self.on_activity_result)
            self.start_msg_listener()
            self.startSmsUserConsent()

        '''if r != None:
            status_code = r[0]
            res = r[1]
            if status_code == 200:
                label.text = "PIN sent to Email and Mobile Number"
                self.STATE = "SEND_PIN_SUCCESS"
            else:
                label.text = res
                self.STATE = "SEND_PIN_FAILURE"'''

    def on_req_otp_success(self, *args):
        print(args)
        label = self.content_register.ids["id_label_info"]
        label.text = "PIN sent to Email and Mobile Number"
        self.STATE = "SEND_PIN_SUCCESS"

    def on_req_otp_failure(self, res, data, *args):
        print("OTP_FAIL", res)
        print(data)
        print(type(data))
        try:
            label = self.content_register.ids["id_label_info"]
            if type(data) == dict:
                label.text = data["error"]
            elif type(data) == socket.gaierror:
                label.text = "Network Error."
                self.stop_otp_timer()
            else:
                label.text=  data
            self.STATE = "SEND_PIN_FAILURE"
        except Exception as e:
            print(e)

    def check_syntax_email(self, email):
        app = App.get_running_app()
        if len(email.split("@")) < 2:
            app.open_modalInfo(title="Info", text="Enter Valid Email Address.")
            return False
        return True

    #def _verify_pin_local(self, entered_pin, saved_pin):


    def verify_login_pin(self, *args):
        app = App.get_running_app()
        if not self.LOGIN_BLOCKED:
            email = self.ids["id_text_email"].text
            if email == "":
                app.open_modalInfo(title="Info", text="Enter Email Address")
                return
            pin = self.ids["id_text_email_pin"].text
            if pin == "":
                app.open_modalInfo(title="Info", text="Enter PIN")
                return

            saved_pin = app.get_config_variable(key="LOGIN_PIN")
            #if (email == app.EMAIL) and (str(saved_pin) == str(pin) ):
            if str(saved_pin) == str(pin):
                app.change_screen(screen="Screen_network")
                app.update_config_variable(key="EMAIL_VERIFIED", value=1)
            else:
                app.open_modalInfo(title="Info", text="Incorrect PIN (or) Email Is Not Valid")
                app.update_config_variable(key="EMAIL_VERIFIED", value=0)
                self.LOGIN_ATTEMPT_FAIL_COUNT += 1
                if self.LOGIN_ATTEMPT_FAIL_COUNT >= self.LOGIN_ATTEMPT_FAIL_COUNT_MAX:
                    self.LOGIN_BLOCKED = True
                    app.update_config_variable(key="LOGIN_BLOCKED", value=time.time())
        else:
            app.open_modalInfo(title="Info", text="Login Blocked. Try After Some Time.")


    def verify_login_pin_server(self, *args):
        app = App.get_running_app()
        email = self.content_register.ids["id_text_email"].text
        mobile_number = self.content_register.ids["id_text_mobile_number"].text
        label = self.content_register.ids["id_label_info"]
        label.text = ""
        if not self.check_syntax_email(email=email):
            return
        if email == "":
            #app.open_modalInfo(title="Info", text="Enter Email Address")
            label.text = "Enter Email Address"
            return
        pin = self.content_register.ids["id_text_email_pin"].text
        if pin == "":
            #app.open_modalInfo(title="Info", text="Enter PIN")
            label.text = "Enter PIN"
            return
        self.STATE = "VERIFY_PIN"
        label.text = "Verifying PIN..."
        request = "request_verify_pin"
        url = SMAC_SERVER + request
        data = {}
        data["email"] = email
        data["mobile_number"] = mobile_number
        data["pin"] = pin
        data["id_device"] = app.ID_DEVICE
        #app.open_modal(content=BoxLayout_loader())
        r = restapi.rest_call(url=url, method="POST", request=request, data=data, on_success=self.on_verify_otp_succeed, on_failure=self.on_verify_otp_failure)

    def on_verify_otp_succeed(self, res, data):
        print(res)
        print(data)
        app = App.get_running_app()
        email = self.content_register.ids["id_text_email"].text
        mobile_number = self.content_register.ids["id_text_mobile_number"].text
        pin = self.content_register.ids["id_text_email_pin"].text
        app.open_modalInfo(title="Info", text="PIN verified.\nLogin to Continue")
        app.update_config_variable(key="EMAIL", value=email)
        app.update_config_variable(key="MOBILE_NUMBER", value=mobile_number)
        app.update_config_variable(key="LOGIN_PIN", value=pin)
        self.STATE = "VERIFY_PIN_SUCCESS"
        app.delete_config_variable(key="LOGIN_BLOCKED")

    def on_verify_otp_failure(self, res, data):
        print(res)
        label = self.content_register.ids["id_label_info"]
        label.text = data["error"]
        self.STATE = "VERIFY_PIN_FAILURE"

