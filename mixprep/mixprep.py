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


def plot_waveform(axes, samples):
    figure = axes.get_figure()
    resolution = figure.get_dpi() * figure.get_size_inches()[0]
    axes.get_xaxis().set_visible(False)
    axes.get_yaxis().set_visible(False)
    axes.set_ylim(-1, 1)
    axes.set_xlim(0, len(samples))
    # Draw a faint line across the horizontal axis.
    axes.axhline(0, color='lightgray', zorder=0)
    if len(samples) > resolution:
        # Matplotlib would choke if it tried to draw the entire sample array, so
        # we'll split the array into a bin for each pixel, get the min and max,
        # then fill between.
        splits = np.array_split(samples, resolution)
        mins = [x.min() for x in splits]
        maxes = [x.max() for x in splits]
        ticks = [len(x) for x in splits]
        axes.fill_between(ticks, mins, maxes, lw=0.0, edgecolor=None)
    if len(samples) * 4 < resolution:
        # Our points are getting spaced pretty far apart, so we'll mark each
        # sample value and interpolate a smooth curve between them.
        ticks = np.arange(len(samples))
        filltime = np.linspace(ticks[0], ticks[-1], resolution)
        interp = matplotlib.mlab.stineman_interp(filltime, ticks, samples, None)
        axes.plot(ticks, samples, '.', filltime, interp)
    else:
        # We have a reasonable number of samples, so draw an ordinary waveform.
        axes.plot(np.arange(len(samples)), samples)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("filename", type=str, help="Audio file to edit")
	args = parser.parse_args()

	signal, samplerate = librosa.load(args.filename, sr=44100, mono=False)
	left = signal[0, :]
	right = signal[1, :]
	mono = librosa.to_mono(signal)

	root = tk.Tk()
	root.title("music prep tool for custom club edits")
	root.minsize(480, 256)
	screenwidth = root.winfo_screenwidth()
	screenheight = root.winfo_screenheight()
	width = screenwidth * 4 / 5
	height = screenheight * 2 / 3
	hpos = (screenwidth - width) / 2
	vpos = (screenheight - height) / 2
	root.geometry('%dx%d+%d+%d' % (width, height, hpos, vpos))
	# don't know why it won't quit normally, but we have to kill it explicitly
	root.protocol('WM_DELETE_WINDOW', lambda: sys.exit(0))

	# row 0: control buttons
	# row 1: editor detail view
	# row 2: navigation overview

	shell = tk.Frame(root)
	shell.grid_rowconfigure(0, weight=0)
	shell.grid_rowconfigure(1, weight=1)
	shell.grid_rowconfigure(2, weight=0)
	shell.grid_columnconfigure(0, weight=1)

	controls = tk.Frame(shell)
	controls.grid(row=0, column=0, sticky='nsew')

	canvas_figure = pyplot.figure(num=None, figsize=(5,2), dpi=100)
	canvas_axes = canvas_figure.add_axes([0,0,1,1])
	canvas = FigureCanvasTkAgg(canvas_figure, master=shell)
	canvas.show()
	canvas_widget = canvas.get_tk_widget()
	canvas_widget.grid(row=1, column=0, sticky='nsew')

	plot_waveform(canvas_axes, mono)

	shell.pack(fill=tk.BOTH, expand=True)
	#root.update()
	root.mainloop()


if __name__=='__main__':
	main()
