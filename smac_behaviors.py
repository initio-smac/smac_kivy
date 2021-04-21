from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Line
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty


class SelectBehavior(object):
    is_selectable = BooleanProperty(True)
    select = BooleanProperty(False)
    mask_select = BooleanProperty(False)
    is_border_animating = BooleanProperty(False)
    border_clock = None
    border_line = None
    border_color = [1,1,1,1]
    # options --> top, left, right, bottom, all
    border_options = StringProperty("all")
    max_border_width = NumericProperty(2)
    min_border_width = NumericProperty(0.01)
    border_width = NumericProperty(1)
    anime_duration = 0.4

    def __init__(self, **kwargs):
        super(SelectBehavior, self).__init__(**kwargs)
        app = App.get_running_app()
        self.padding = (5, 5)
        #self.width = self.width + self.border_width*4
        if app != None:
            self.border_color = app.colors["COLOR_THEME_HIGHLIGHT"]

    def _border(self, *args):
        w = round(self.border_line.width, 1)
        width = self.max_border_width if w <= self.min_border_width else self.min_border_width
        anim = Animation(
            #size=size,
            #pos = pos,
            width = width,
            duration=self.anime_duration
        )
        anim.start(self.border_line)

    def on_pos(self, *args):
        #print(args)
        #print(self.is_border_animating)
        self.update_points()
        if self.is_border_animating:
            self.stop_border_animation()
            self.start_border_animation()

    def on_size(self, *args):
        self.update_points()
        if self.is_border_animating:
            self.stop_border_animation()
            self.start_border_animation()

    def start_border_animation(self, *args):
        if not self.is_border_animating:
            self.is_border_animating = True
            self.show_border()
            self.border_clock = Clock.schedule_interval(self._border, 2 * self.anime_duration)

    def stop_border_animation(self, *args):
        if self.border_clock != None:
            self.border_clock.cancel()
            self.border_clock = None
            self.is_border_animating = False
            #self.border_line = None
            self.hide_border()

    '''def on_touch_up(self, touch):
        super(SelectBehavior, self).on_touch_up(touch)
        if not self.collide_point(*touch.pos):
            self.select = False
            return True
        if self.mask_select or (not self.disabled and self.is_selectable and ('button' not in touch.profile or not touch.button.startswith('scroll'))):
            self.select = True
        return True'''

    def get_points(self):
        node = self
        if self.border_options == "left":
            points = [node.x, node.y, node.x, node.y + node.height]
        elif self.border_options == "right":
            points = [node.x + node.width, node.y, node.x + node.width, node.y + node.height]
        elif self.border_options == "top":
            points = [node.x, node.y + node.height, node.x + node.width, node.y + node.height]
        elif self.border_options == "bottom":
            points = [node.x, node.y, node.x + node.width, node.y]
        else:
            points = [node.x + self.max_border_width, node.y + self.max_border_width*2,
                      node.x + self.max_border_width, node.top - self.max_border_width*2,
                      node.x + node.width, node.top - self.max_border_width*2,
                      node.x + node.width, node.y + self.max_border_width*2,
                      node.x + self.max_border_width, node.y + self.max_border_width*2]
        return points

    def show_border(self,  group="border_group",  *args):
        node = self
        if (self.border_line != None):
            self.border_width = self.max_border_width
            self.border_line.width = self.border_width
        else:
            points = self.get_points()
            with node.canvas.after:
                #self.border_color = Color(rgba=[1,1,1,1])
                Color(rgba=self.border_color)
                self.border_line = Line(points=points, width=self.max_border_width, group=group)
        #node.canvas.ask_update()

    def update_points(self):
        if self.border_line != None:
            self.border_line.points = self.get_points()
            #self.canvas.ask_update()

    def hide_border(self, node=None, *args):
        if self.border_line != None:
            self.border_line.width = self.min_border_width

    def on_select(self, node, value, *args):
        group = "border_group"
        print(self)
        print(value)
        if value:
            self.stop_border_animation()
            self.show_border( )
        else:
            #if node != None:
            self.hide_border()
            #node.canvas.remove_group(group)