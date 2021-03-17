import asyncio
import random

from kivy.animation import Animation
from kivy.graphics.context_instructions import PushMatrix, Rotate, PopMatrix
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.uix.slider import Slider

from smac_client import client
from smac_device import set_property
from smac_device_keys import SMAC_PROPERTY
from smac_keys import smac_keys
from smac_widgets.smac_layouts import *

from smac_db import db
import time


class Screen_network(Screen):
	TOPIC_IDS = {}
	RENDERING = False
	RENDERING_COUNT = 0
	IMG = None

	async def add_widgets(self, clear_widgets=False, *args):
		#print("RENDERING", self.RENDERING)
		app = App.get_running_app()
		if not self.RENDERING:
			self.RENDERING = True
			self.RENDERING_COUNT += 1
			container = self.ids["id_network_container"]
			#self.ids["id_btn"].text = str(self.RENDERING_COUNT)
			if clear_widgets:
				self.TOPIC_IDS = {}
				container.clear_widgets()
			for id_topic, name_topic, view_topic  in db.get_topic_list():
				#print("id_topic: {}".format(id_topic))
				if self.TOPIC_IDS.get(id_topic, None) == None:
					w = Widget_network(text=name_topic)
					w.disable_icon2 = True if(id_topic == "") else False
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
				w.icon1 = 'icons/BOTTOM.png' if view_topic else 'icons/TOP.png'
				#w.bind( on_release=self.goto_prop_page )
				for id_device, name_device, view_device, is_busy, pin_device, pin_device_valid in db.get_device_list_by_topic(id_topic):
					#print("id_device: {}".format(id_device))
					if w.DEVICE_IDS.get(id_device, None) == None:
						w1 = Widget_device(text=name_device)
						w1.disable_icon2 = True if (id_topic == "") else False
						w1.PROP_IDS = {}
						w1.id_device = id_device
						w1.ids["id_icon1"].bind(on_release=self.change_device_view)
						w.DEVICE_IDS[id_device] = w1
						w.add_widget(w1)

						#if id_device == app.ID_DEVICE:
						#	button = Button(text="delete", size_hint=(None, None), size=(dp(100), dp(50)))
						#	button.bind(on_release=app.delete_topic)
						#	button.id_topic = id_topic
						#	w.add_widget(button)

						'''if id_device == app.ID_DEVICE:
							img = Image_icon(source='icons/FAN.png')
							w1.add_widget(img)
							sp = random.randint(1, 3)
							sp = 5
							print(sp)
							self.start_animation(img, duration=sp)'''
					else:
						w1 = w.DEVICE_IDS[id_device]
					w1.name_device= name_device
					w1.id_topic = id_topic
					w1.view_device = view_device
					w1.icon1 =  'icons/BOTTOM.png' if view_device else 'icons/TOP.png'
					w1.hide = view_topic
					w1.pin_device_valid = pin_device_valid

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
									slider.cursor_image = 'icons/TRANSPARENT.png'
								slider_container.add_widget(slider)
						else:
							w2 = w1.PROP_IDS[id_property]

						#if property_name == "BRIGHTNESS":
						#	print("is_busy", is_busy)
						w2.text = property_name
						w2.value = int(value)
						w2.is_busy = is_busy
						# hide for hiding the widget based on the Expand or Collapse icon on the Parent Widget
						w2.hide = view_device

				#print("\n")
			self.RENDERING = False
		else:
			print("ALREADY RENDERING")

	def change_value(self, wid, *args):
		wid_prop = wid.parent.parent.parent
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
			client.send_message(frm=app.ID_DEVICE, to=wid_prop.id_device, cmd=smac_keys["CMD_SET_PROPERTY"], message=d, udp=True, tcp=False)
			wid_prop.MSG_COUNTER = MSG_ID

	def get_icon(self, type_property, *args):
		if type_property == SMAC_PROPERTY["BATTERY"]:
			return 'icons/BATTERY.png'
		elif type_property == SMAC_PROPERTY["BLUETOOTH"]:
			return 'icons/BLUETOOTH.png'
		elif type_property == SMAC_PROPERTY["FLASH"]:
			return 'icons/FLASH.png'
		elif type_property == SMAC_PROPERTY["BRIGHTNESS"]:
			return 'icons/BRIGHTNESS.png'
		elif type_property == SMAC_PROPERTY["SHUTDOWN"]:
			return 'icons/SHUTDOWN.png'
		elif type_property == SMAC_PROPERTY["RESTART"]:
			return 'icons/RESTART.png'
		else:
			return ''


	def change_topic_view(self, icon, *args):
		wid = icon.parent.parent
		wid.view_topic = (1-wid.view_topic)
		view = wid.view_topic
		wid.icon1 = 'icons/BOTTOM.png' if view else 'icons/TOP.png'
		for i in wid.children:
			i.hide = view
		#print( type(wid.view_topic) )
		db.set_topic_view(id_topic=wid.id_topic, view_topic=view)

	def change_device_view(self, icon, *args):
		wid = icon.parent.parent
		wid.view_device = (1 - wid.view_device)
		view = wid.view_device
		wid.icon1 = 'icons/BOTTOM.png' if view else 'icons/TOP.png'
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
		while 1:
			await self.add_widgets()
			await asyncio.sleep(timeout)

	def on_enter(self, *args):
		#self.add_widgets()
		#Clock.schedule_interval(self.add_widgets, 1)
		#print(self.ids)
		asyncio.gather(self.interval(1))

	def on_leave(self, *args):
		container = self.ids["id_network_container"]
		container.clear_widgets()

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
				w.add_widget(w1)

				for id_property, property_name, value in db.get_property_list_by_device(id_device):
					# print("id_property: {}".format(id_property))
					w2 = Widget_property(text="{}:{}".format(property_name, value))
					w2.id_property = id_property
					w2.property_name = "{}:{}".format(property_name, value)
					w2.value = value
					w1.add_widget(w2)

class Screen_property(Screen):

	def on_enter(self, *args):
		app = App.get_running_app()
		#print(app.app_data)
		entries = db.get_property(id_device=app.app_data["id_device"])
		#print(entries)
		container = self.ids["id_prop_container"]
		for i in entries:
			w = Widget_property(text=i[4])
			#w.bind( on_release=self.goto_prop_page )
			container.add_widget( w )

	def on_leave(self, *args):
		container = self.ids["id_prop_container"]
		container.clear_widgets()

	def goto_prop_page(self, *args):
		app = App.get_running_app()
		app.change_screen("Screen_property")