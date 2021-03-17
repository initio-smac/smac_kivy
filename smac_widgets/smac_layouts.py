from kivy.animation import Animation
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, ColorProperty, NumericProperty, BooleanProperty
from kivy.utils import get_color_from_hex


class Widget_base( ButtonBehavior, BoxLayout ):
	orientation = "vertical"
	text = StringProperty("")
	icon1 = StringProperty("")
	disable_icon1 = BooleanProperty(False)
	icon2 = StringProperty("")
	disable_icon2 = BooleanProperty(False)
	hide = BooleanProperty(False)
	
	def __init__(self, text, *args, **kwargs):
		#print(args)
		self.text = text
		super().__init__(**kwargs)


class Widget_network( Widget_base ):
	pass

class Widget_slider(Slider):
	value_min = NumericProperty(0)
	value_max = NumericProperty(1)
	value_copy = NumericProperty(0)

	def on_touch_up(self, touch):
		release = super(Widget_slider, self).on_touch_up(touch)
		if release:
			self.value_copy = self.value
		return release


	def on_value_min(self, *args):
		self.min = self.value_min

	def on_value_max(self, *args):
		self.max = self.value_max


class Widget_switch(ButtonBehavior, Widget):
	value = NumericProperty(0)
	value_min = 0
	value_max = 1
	color_ball = ColorProperty(get_color_from_hex("#e0e0e0"))
	color_bg = ColorProperty( get_color_from_hex("#c0c0c0") )
	margin = NumericProperty(0)

	def on_value(self, *args):
		ball = self.ids["id_ball"]
		x = (self.x + ball.width +dp(7.5)) if self.value else (self.x + dp(2.5) )
		color_bg = get_color_from_hex("#4a8111") if self.value else get_color_from_hex("#c0c0c0")
		#self.start_animation(ball, x, color_bg)
		ball.x = x
		ball.parent.color_bg = color_bg

	def on_pos(self, *args):
		self.on_value((self, self.value))

	def on_release(self):
		#self.value = 1-self.value
		pass

	def start_animation(self, wid, x, color_bg, *args):
		anim_ball = Animation(x=x, duration=.1)
		anim_wid = Animation(color_bg=color_bg, duration=.1)
		anim_ball.start(wid)
		anim_wid.start(wid.parent)


class Widget_property( BoxLayout ):
	#text = StringProperty("")
	value_min = NumericProperty(0)
	value_max = NumericProperty(1)
	value = NumericProperty(0)
	source = StringProperty("")
	text = StringProperty("")
	type_property = StringProperty("")
	id_property = None
	id_device = None
	hide = BooleanProperty(0)
	MSG_COUNTER = NumericProperty(0)
	is_busy = NumericProperty(0)

	def on_is_busy(self, wid, value, *args):
		slider = self.ids.get("id_slider", None)
		print("val", value)
		print(slider)
		if slider != None:
			slider.disable = value
			slider.opacity = 0 if value else 1
	
	def __init__(self, text, *args, **kwargs):
		#print(args)
		self.text = text
		super().__init__(**kwargs)

	def on_hide(self, wid, value, *args):
		height = 0 if value else self.minimum_height
		opacity = 1-value
		anim = Animation(height=height, opacity=opacity, duration=.1)
		anim.start(self)

	def on_value(self, *args):
		#if self.value_max == 1:
		#	self.text = "ON" if self.value else "OFF"
		#else:
		#	self.text = str(int(self.value))
		pass

class Widget_group( Widget_base ):
	pass

class Widget_device( Widget_base ):
	color = ColorProperty([1,1,1,1])




	def on_hide(self, wid, value, *args):
		#print(value)
		#print(args)
		height = 0 if value else self.minimum_height
		opacity = 1-value
		anim = Animation(height=height, opacity=opacity, duration=.1)
		anim.start(self)


class BoxLayout_header(BoxLayout):
	pass

class Image_icon(ButtonBehavior, Image):
	angle = NumericProperty(0)

	def on_angle(self, *args):
		if self.angle == -360:
			self.angle = 0

# box container
class BoxLayout_container( BoxLayout):
	pass


class BoxLayout_addGroupContent(BoxLayout_container):
	pass