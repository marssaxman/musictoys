import Tkinter as Tk

class Display(Tk.Canvas):
	def __init__(self, parent, **kwargs):
		Tk.Canvas.__init__(self, parent, **kwargs)
		self._viewer = None
		self.bind("<Configure>", self.on_resize)

	def on_resize(self, event):
		self.config(width=event.width, height=event.height)
		self._draw()

	def view(self, viewer):
		self._viewer = viewer
		self._draw()

	def _draw(self):
		self.delete("all")
		if self._viewer:
			self._viewer.draw(self)

