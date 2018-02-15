
import Tkinter as tk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


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
		figure = matplotlib.figure.Figure(figsize=(1,1), dpi=100)
		plot = figure.add_axes([0,0,1,1])
		self._plot = plot
		plot.get_xaxis().set_visible(False)
		plot.set_xlim(0, signal.duration)
		plot.get_yaxis().set_visible(False)
		plot.set_ylim(-1, 1)
		canvas = FigureCanvasTkAgg(figure, master=self)
		yvals = signal.mono
		xvals = np.linspace(0, signal.duration, num=len(yvals))
		plot.plot(xvals, yvals, linewidth=0.05)
		canvas.show()
		widget = canvas.get_tk_widget()
		widget.pack(fill=tk.BOTH, expand=True)

	def view(self, interval):
		# Display the slice of the signal specified by the fractional interval.
		# Limit the interval to some reasonable scale for our signal length.
		begin, end = interval
		duration = self._signal.duration
		self._plot.set_xlim(begin * duration, end * duration)
		self._plot.figure.canvas.draw_idle()
