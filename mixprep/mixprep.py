#!/usr/bin/env python

# Prepare a track for convenient mixing in a dance club style DJ set.
# Open an original track, select bars or phrases, then cut and paste sections
# to shorten, lengthen, or reorganize the track according to your taste. 
# Selection ranges are beat-aligned and quantized to power-of-2 lengths, so you
# can easily manipulate musically meaningful blocks without having to zoom in
# and precisely locate transition points in the waveform.

# Feature goals:
# 1 - cut or copy selection, paste at some other point
# 2 - adjustable crossfade across each transition point
# 3 - halve a section's length by crossfading it into itself
# 4 - change crossfade type: volume, filter up, or filter down


import Tkinter as tk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as pyplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import argparse
import librosa
import sys
import math

def next_power_of_2(n):
	return 2 ** math.ceil(math.log(n, 2))


def rms(samples):
	return np.sqrt(np.mean(samples ** 2))


class AudioTrack:
	def __init__(self, path):
		self.path = path
		signal, self.samplerate = librosa.load(path, sr=44100, mono=False)
		self.left = signal[0, :]
		self.right = signal[1, :]
		self.mono = librosa.to_mono(signal)


class SignalViewer(tk.Frame):
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


class Overview(tk.Canvas):
	def __init__(self, container, signal, **kwargs):
		if not 'background' in kwargs and not 'bg' in kwargs:
			kwargs['background'] = '#222222'
		tk.Canvas.__init__(self, container, **kwargs)
		self.signal = signal
		self.bind("<Configure>", self.on_resize)
		self._draw()
	def on_resize(self, event):
		self._draw()
	def _draw(self):
		self.delete('all')
		width = self.winfo_width()
		height = self.winfo_height()
		samplecount = len(self.signal.mono)
		left_channel = self.signal.left
		right_channel = self.signal.right
		vloc = height / 2
		vscale = height * 7 / 16
		for x in xrange(width):
			# Get the left and right channel sample bins for this pixel.
			begin = samplecount * x / width
			end = samplecount * (x+1) / width
			left_bin = left_channel[begin:end]
			right_bin = right_channel[begin:end]
			# Get the maximum (absolute) and RMS values for these bins.
			left_max, left_rms = max(np.abs(left_bin)), rms(left_bin)
			right_max, right_rms = max(np.abs(right_bin)), rms(right_bin)
			# Draw the left channel on top and the right channel below, using
			# dark grey for the max and a lighter grey for RMS.
			top_pos = vloc - (left_max * vscale)
			bot_pos = vloc + (right_max * vscale)
			self.create_line(x, top_pos, x, bot_pos, fill='#AAAAAA')
			top_pos = vloc - (left_rms * vscale)
			bot_pos = vloc + (right_rms * vscale)
			self.create_line(x, top_pos, x, bot_pos, fill='#CCCCCC')


class UI(tk.Tk):
	def __init__(self, *args, **kwargs):
		tk.Tk.__init__(self, *args, **kwargs)
		self.title("music prep tool for custom club edits")
		self.minsize(480, 256)
		screenwidth = self.winfo_screenwidth()
		screenheight = self.winfo_screenheight()
		width = screenwidth * 4 / 5
		height = screenheight * 2 / 3
		hpos = (screenwidth - width) / 2
		vpos = (screenheight - height) / 2
		self.geometry('%dx%d+%d+%d' % (width, height, hpos, vpos))
		self.protocol('WM_DELETE_WINDOW', self.delete_window)
	def delete_window(self):
		# don't know why this won't quit normally when you close the window,
		# but that's what seems to be happening, so we'll exit manually
		sys.exit(0)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("filename", type=str, help="Audio file to edit")
	args = parser.parse_args()

	signal = AudioTrack(args.filename)

	root = UI()
	layout = tk.Frame(root)
	layout.grid_rowconfigure(0, weight=0)
	layout.grid_rowconfigure(1, weight=1)
	layout.grid_columnconfigure(0, weight=1)
	layout.grid_rowconfigure(2, weight=0)
	controls = tk.Frame(layout)
	controls.grid(row=0, column=0, sticky='nsew')
	editor = SignalViewer(layout, signal)
	editor.grid(row=1, column=0, sticky='nsew')
	overview = Overview(layout, signal, height=64)
	overview.grid(row=2, column=0, sticky='nsew')
	layout.pack(fill=tk.BOTH, expand=True)
	root.mainloop()


if __name__=='__main__':
	main()
