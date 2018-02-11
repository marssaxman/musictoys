
import Tkinter as tk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class Editview(tk.Frame):
	def __init__(self, container, signal, **kwargs):
		tk.Frame.__init__(self, container, **kwargs)
		self.signal = signal
		self.figure = matplotlib.figure.Figure(figsize=(6,1), dpi=100)
		self.axes = self.figure.add_axes([0,0,1,1])
		self.axes.get_xaxis().set_visible(False)
		self.axes.get_yaxis().set_visible(False)
		self.canvas = FigureCanvasTkAgg(self.figure, master=self)
		self.canvas.show()
		widget = self.canvas.get_tk_widget()
		widget.pack(fill=tk.BOTH, expand=True)
		self.bind('<Configure>', self.on_resize)
		self.plot()
	def plot(self):
		self.axes.clear()
		resolution = self.winfo_width()
		samples = self.signal.mono
		self.axes.set_ylim(-1, 1)
		self.axes.set_xlim(0, len(samples))
		# Draw a faint line across the horizontal axis.
		self.axes.axhline(0, color='lightgray', zorder=0)
		if len(samples) > resolution:
			self._plot_bins(samples, resolution)
		if len(samples) * 4 < resolution:
			self._plot_points(samples, resolution)
		else:
			self._plot_line(samples, resolution)
	def _plot_bins(self, samples, resolution):
		# Matplotlib would choke if it tried to draw the entire sample array,
		# so we'll slice it up with one bin per pixel, find the min and max
		# values in each bin, then plot a vertical line between them. 
		splits = np.array_split(samples, resolution)
		mins = [x.min() for x in splits]
		maxes = [x.max() for x in splits]
		ticks = [len(x) for x in splits]
		self.axes.fill_between(ticks, mins, maxes, lw=0.0, edgecolor=None)
	def _plot_points(self, samples, resolution):
		# Our points are getting spaced pretty far apart, so we'll mark each
		# sample value and interpolate a smooth curve between them.
		ticks = np.arange(len(samples))
		filltime = np.linspace(ticks[0], ticks[-1], resolution)
		stineman = matplotlib.mlab.stineman_interp
		interp = stineman(filltime, ticks, samples, None)
		self.axes.plot(ticks, samples, '.', filltime, interp)
	def _plot_line(self, samples, resolution):
		# We have a reasonable number of samples, so draw an ordinary waveform.
		self.axes.plot(np.arange(len(samples)), samples, lw=0.5)
	def on_resize(self, event):
		self.plot()

