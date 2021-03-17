from kivy.uix.screenmanager import Screen
from kivy.app import App

from smac_widgets.smac_layouts import *

from smac_db import db


class Screen_network(Screen):
	def on_enter(self, *args):
		groups = db.get_network_entry()
		print(groups)
		container = self.ids["id_group_container"]
		for i in groups:
			w = Widget_group(text=i[2])
			w.bind( on_release=self.goto_device_page )
			container.add_widget( w )

	def on_leave(self, *args):
		container = self.ids["id_group_container"]
		container.clear_widgets()

	def goto_device_page(self, *args):
		app = App.get_running_app()
		app.change_screen("Screen_devices")


class Screen_groups(Screen):
	
	def on_enter(self, *args):
		groups = db.get_group()
		print(groups)
		container = self.ids["id_group_container"]
		for i in groups:
			w = Widget_group(text=i[2])
			w.bind( on_release=self.goto_device_page )
			container.add_widget( w )

	def on_leave(self, *args):
		container = self.ids["id_group_container"]
		container.clear_widgets()

	def goto_device_page(self, *args):
		app = App.get_running_app()
		app.change_screen("Screen_devices")



class Screen_devices(Screen):

	def on_enter(self, *args):
		devices = db.get_device(group_id=0)
		print(devices)
		container = self.ids["id_device_container"]
		for i in devices:
			device_id2name = db.get_device_id2name_by_id(i[1])
			w = Widget_device(text=device_id2name[1])
			w.bind( on_release=self.goto_prop_page )
			container.add_widget( w )

	def on_leave(self, *args):
		container = self.ids["id_device_container"]
		container.clear_widgets()

	def goto_prop_page(self, *args):
		app = App.get_running_app()
		app.change_screen("Screen_deviceProperty")

class Screen_deviceProperty(Screen):
	pass