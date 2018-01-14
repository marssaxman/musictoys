import Tkinter as Tk

class Display(Tk.Canvas):
	def __init__(self, parent, **kwargs):
		Tk.Canvas.__init__(self, parent, **kwargs)
		self._viewer = None
		self._interval = (0, 1.0)
		self.bind("<Configure>", self.on_resize)
		self.bind("<4>", lambda event: self._zoom(event.x, 0.9))
		self.bind("<5>", lambda event: self._zoom(event.x, 1.1))

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
		self._interval = (0, viewer.duration())
		self._draw()

	def _draw(self):
		self.delete("all")
		if self._viewer:
			self._viewer.draw(self, self._interval)

	def _zoom(self, x, scale):
		# change time interval by some factor, centered on time at position X
		old_begin, old_end = self._interval
		old_duration = old_end - old_begin
		new_duration = min(old_duration * scale, self._viewer.duration())
		new_begin = self.time_at(x) - (new_duration / 2.0)
		new_end = new_begin + new_duration
		max_duration = self._viewer.duration()
		self._interval = max(new_begin, 0), min(new_end, max_duration)
		self._draw()

