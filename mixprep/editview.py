
import Tkinter as tk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import math

# In the process of building this I have discovered that matplotlib has most
# of it built in, and this can all be done much, much better.
# SpanSelector class does interactive range selection:
#  https://stackoverflow.com/questions/44990722/how-to-select-area-within-a-plot-python-and-extract-the-data-within-the-area
# How to downsample a large input array in response to xlim_changed:
#  https://matplotlib.org/examples/event_handling/resample.html
# Using one plot to zoom in on another:
#  https://matplotlib.org/examples/event_handling/viewlims.html
# This might be useful for beat markers:
#  https://matplotlib.org/examples/event_handling/data_browser.html
# Signal smoothing example
#  https://matplotlib.org/gallery/misc/demo_agg_filter.html#sphx-glr-gallery-misc-demo-agg-filter-py


class Editview(tk.Frame):
	def __init__(self, container, signal, **kwargs):
		tk.Frame.__init__(self, container, **kwargs)
		self._signal = signal
		# Create a figure which will contain our various plots. Embed its
		# drawing canvas within a Tk widget.
		figure = self._figure = matplotlib.figure.Figure(figsize=(1,1), dpi=100)
		canvas = self._canvas = FigureCanvasTkAgg(figure, master=self)
		widget = canvas.get_tk_widget()
		widget.pack(fill=tk.BOTH, expand=True)
		# Create the waveform plot within the overall figure and configure its
		# various framing features the way we want them to look.
		axes = self._axes = figure.add_axes([0,0,1,1])
		axes.autoscale(enable=False)
		axes.get_xaxis().set_visible(False)
		axes.get_yaxis().set_visible(False)
		axes.set_xlim(0, signal.duration)
		axes.set_ylim(-1, 1)
		# Draw the waveform line on the plot axes.
		yvals = signal.mono
		xvals = np.linspace(0, signal.duration, num=len(yvals))
		linewidth = self._calc_waveplot_linewidth()
		self._waveplot, = axes.plot(xvals, yvals, lw=linewidth)
		# Set up an xlim callback so we can adjust the waveplot.
		axes.callbacks.connect('xlim_changed', self._xlim_changed)
		# Connect some handlers for GUI events for interactive editing.
		canvas.mpl_connect('scroll_event', self._scroll_event)
		# Ready to go? Make it visible and let it draw.
		canvas.show()

	def view(self, interval):
		# Display the slice of the signal specified by the fractional interval.
		# The interval is time-independent, referring to the whole length, so
		# we'll convert it to time-coordinates.
		begin, end = interval
		duration = self._signal.duration
		self._axes.set_xlim(begin * duration, end * duration)

	def _xlim_changed(self, axes):
		# The region of time we're viewing has changed. We may need to adjust
		# the width of the lines, if we've zoomed in or out, and we certainly
		# need to redraw the canvas whenever we get a good chance.
		self._waveplot.set_linewidth(self._calc_waveplot_linewidth())
		self._canvas.draw_idle()

	def _calc_waveplot_linewidth(self):
		# Use thicker lines when we're viewing a smaller range of samples, but
		# scale the lines down as we zoom out so they don't get crowded.
		begin, end = self._axes.get_xlim()
		duration = end - begin
		samplecount = duration * self._signal.samplerate
		resolution = self._canvas.get_tk_widget().winfo_width();
		samples_per_pixel = samplecount / resolution
		linewidth = min(1.0, math.pow(1 / math.log(samples_per_pixel), 1.0))
		return linewidth

	def _scroll_event(self, event):
		# mouse wheel has scrolled up or down; we'll use this for zoom
		# event is a MouseEvent
		assert event.inaxes == self._axes
		time = event.xdata

