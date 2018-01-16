import Tkinter as Tk

class Display(Tk.Canvas):
	def __init__(self, parent, **kwargs):
		Tk.Canvas.__init__(self, parent, **kwargs)
		self._xscrollcommand = None
		if "xscrollcommand" in kwargs:
			self._xscrollcommand = kwargs["xscrollcommand"]
		self._viewer = None
		self._set_interval(0, 1.0)
		self.bind("<Configure>", self.on_resize)
		self.bind("<MouseWheel>", self._mouse_wheel)
		self.bind("<Button-4>", self._mouse_wheel)
		self.bind("<Button-5>", self._mouse_wheel)

	def config(self, **options):
		if "xscrollcommand" in options:
			self._xscrollcommand = options["xscrollcommand"]
		Tk.Canvas.config(self, **options)

	def time_at(self, x_pos):
		width = self.winfo_width()
		begin_time, end_time = self._interval
		pixel_time = (end_time - begin_time) / float(width)
		return begin_time + pixel_time * x_pos

	def on_resize(self, event):
		self.config(width=event.width, height=event.height)
		self._draw()

	def view(self, viewer):
		self._viewer = viewer
		self._set_interval(0, viewer.duration())
		self._draw()

	def _set_interval(self, begin, end):
		self._interval = begin, end
		duration = float(self._viewer.duration()) if self._viewer else 1.0
		if self._xscrollcommand:
			self._xscrollcommand(begin / duration, end / duration)

	def _draw(self):
		self.delete("all")
		if self._viewer:
			self._viewer.draw(self, self._interval)

	def _mouse_wheel(self, event):
		# we get different events on different platforms
		if event.num == 5 or event.delta == -120:
			print "zoom in at " + str(event.x)
			self._zoom(event.x, 0.9)
		elif event.num == 4 or event.delta == 120:
			print "zoom out at " + str(event.x)
			self._zoom(event.x, 1.1)

	def _zoom(self, x, scale):
		# change time interval by some factor, centered on time at position X
		old_begin, old_end = self._interval
		old_duration = old_end - old_begin
		new_duration = old_duration * scale
		new_begin = self.time_at(x) - (new_duration / 2.0)
		new_end = new_begin + new_duration
		max_duration = self._viewer.duration()
		self._set_interval(max(new_begin, 0), min(new_end, max_duration))
		self._draw()

	def xview(self, how, *args):
		# override default canvas scrolling behavior with our custom rendering
		if how == "moveto":
			self.xview_moveto(*args)
		elif how == "scroll":
			self.xview_scroll(*args)
		else:
			raise ValueError("how argument must be 'moveto' or 'scroll'")

	def xview_moveto(self, fraction):
		# move to this fraction of the viewable range
		max_duration = self._viewer.duration()
		pass

	def xview_scroll(self, number, what):
		# what will be "units" or "pages"
		pass

