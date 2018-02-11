
import Tkinter as tk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class Editview(tk.Frame):
	def __init__(self, container, signal, **kwargs):
		tk.Frame.__init__(self, container, **kwargs)
		self._signal = signal
		self._view_interval = (0,1)
		self._selection = None
		self._redraw_waiting = False
		self._selection_box = None
		self.select_command = None
		self._figure = matplotlib.figure.Figure(figsize=(1,1), dpi=100)
		self._axes = self._figure.add_axes([0,0,1,1])
		self._axes.get_xaxis().set_visible(False)
		self._axes.get_yaxis().set_visible(False)
		self._canvas = FigureCanvasTkAgg(self._figure, master=self)
		self._canvas.show()
		widget = self._canvas.get_tk_widget()
		widget.pack(fill=tk.BOTH, expand=True)
		self.bind('<Configure>', self.on_resize)
		self._canvas.mpl_connect('button_press_event', self.on_mousedown)
		self._draw()

	def on_resize(self, event):
		self._draw()

	def on_mousedown(self, event):
		# If there is no selection, start one.
		# If there is a selection, and the shift key is down, extend it.
		# Otherwise, drop the selection and start a new one.
		pos = self._viewx_to_track_pos(event.x)
		self.select((pos, pos))
		self._mousemove_event_id = self._canvas.mpl_connect(
				'motion_notify_event', self.on_mousemove)
		self._mouseup_event_id = self._canvas.mpl_connect(
				'button_release_event', self.on_mouseup)

	def on_mousemove(self, event):
		self._select_to(self._viewx_to_track_pos(event.x))

	def on_mouseup(self, event):
		self._select_to(self._viewx_to_track_pos(event.x))
		self._canvas.mpl_disconnect(self._mousemove_event_id)
		self._canvas.mpl_disconnect(self._mouseup_event_id)

	def select(self, interval):
		# Mark the specified slice of our signal as the current selection, if
		# any (or None if no selection). Notify the overview and redraw the
		# selection overlay rectangle. Note that we accept a reversed interval
		# internally, but we will always provide a properly-ordered interval.
		self._selection = interval
		self._draw_selection_box()
		if self.select_command:
			if interval:
				begin, end = interval
				interval = (begin, end) if begin <= end else (end, begin)
			self.select_command(interval)

	def _viewx_to_track_pos(self, eventx):
		# Convert the pixel coordinate to view coordinates, then adjust for
		# the view interval, then return position as fraction of track length.
		viewpos = float(eventx) / float(self.winfo_width())
		begin, end = self._view_interval
		length = end - begin
		return viewpos * length + begin

	def _select_to(self, pos):
		self.select((self._selection[0], pos))

	def view(self, interval):
		# Display the slice of the signal specified by the fractional interval.
		# Limit the interval to some reasonable scale for our signal length.
		minlength = 32.0 / float(len(self._signal.mono))
		begin, end = interval
		length = max(minlength, end - begin)
		pos = (begin + end) / 2.0
		begin = max(0, pos - length / 2.0)
		end = min(1.0, begin + length)
		self._view_interval = (begin, end)
		self._draw()

	def _draw(self):
		if not self._redraw_waiting:
			self._redraw_waiting = True
			self.after(100, self._plot)

	def _plot(self):
		self._redraw_waiting = False
		self._axes.clear()
		self._selection_box = None
		resolution = self.winfo_width()
		samples = self._signal.mono
		begin, end = self._view_interval
		# Slice the interval down to the sample array we are interested in.
		samples = samples[int(begin * len(samples)):int(end * len(samples))]
		# Set the axis limits, since we just cleared them.
		self._axes.set_ylim(-1, 1)
		self._axes.set_xlim(0, len(samples))
		# Draw a faint origin line across the horizontal axis.
		self._axes.axhline(0, color='lightgray', zorder=0)
		if len(samples) > resolution:
			self._plot_bins(samples, resolution)
		if len(samples) * 4 < resolution:
			self._plot_points(samples, resolution)
		else:
			self._plot_line(samples, resolution)
		# If there is a selection, draw a translucent overlay.
		self._plot_selection()
		self._canvas.draw()

	def _plot_bins(self, samples, resolution):
		# Matplotlib would choke if it tried to draw the entire sample array,
		# so we'll slice it up with one bin per pixel, find the min and max
		# values in each bin, then plot a vertical line between them. 
		splits = np.array_split(samples, resolution)
		mins = [x.min() for x in splits]
		maxes = [x.max() for x in splits]
		ticks = [len(x) for x in splits]
		self._axes.fill_between(ticks, mins, maxes, lw=0.0, edgecolor=None)

	def _plot_points(self, samples, resolution):
		# Our points are getting spaced pretty far apart, so we'll mark each
		# sample value and interpolate a smooth curve between them.
		ticks = np.arange(len(samples))
		filltime = np.linspace(ticks[0], ticks[-1], resolution)
		stineman = matplotlib.mlab.stineman_interp
		interp = stineman(filltime, ticks, samples, None)
		self._axes.plot(ticks, samples, '.', filltime, interp)

	def _plot_line(self, samples, resolution):
		# We have a reasonable number of samples, so draw an ordinary waveform.
		self._axes.plot(np.arange(len(samples)), samples, lw=0.5)

	def _plot_selection(self):
		if not self._selection:
			return
		# The axvspan method does not appear to work, so we'll abuse axhspan;
		# it's easy enough to specify the selection range in axis coordinates,
		# so we'll just pass our actual values in as xmin and xmax.
		sel_begin, sel_end = self._selection
		view_begin, view_end = self._view_interval
		view_len = view_end - view_begin
		zoom = 1.0 / view_len
		draw_begin = max(0, sel_begin * zoom - view_begin)
		draw_end = min(1, sel_end * zoom - view_begin)
		self._selection_box = self._axes.axhspan(
				-1,1, xmin=draw_begin, xmax=draw_end, alpha=0.7, zorder=3)

	def _draw_selection_box(self):
		if self._selection_box:
			self._selection_box.remove()
			self._selection_box = None
		self._plot_selection()
		self._canvas.draw()

