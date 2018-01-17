#!/usr/bin/env python

import sys
if sys.version_info[0] < 3:
	import Tkinter as Tk
else:
	# The Tk interface module has a different name under Python 3.
	import tkinter as Tk

from console import Console
from display import Display
from waveform import Waveform
from events import Events


# viewer options:
# signal, level, spectrogram, events, regions
# base level is either a stack of one or more signals, or a spectrogram
# level traces, events, and regions can be superimposed onto either
# but! multiple viewers can be stacked vertically
# and! we could have a spectral-signal base layer, too, combining a single
# signal and its spectrogram into one colorful waveform chart

def view(display, viewer):
	display.delete("all")
	viewer.draw(display)

if __name__ == "__main__":
	root = Tk.Tk()
	root.title("sentinel: an audio environment")

	# The shell is divided horizontally.
	# The top pane holds an audio viewer.
	# The bottom pane holds a python console.
	window = Tk.PanedWindow(orient=Tk.VERTICAL)
	window.pack(fill=Tk.BOTH)

	# Make space where can draw visualizations of data about audio.
	upperframe = Tk.Frame(window)
	display = Display(upperframe, bg="grey", height=200)
	xscrollbar = Tk.Scrollbar(upperframe, orient=Tk.HORIZONTAL)
	xscrollbar.pack(side=Tk.BOTTOM, fill=Tk.X, expand=True)
	display.pack(side=Tk.TOP, fill=Tk.BOTH, expand=True)
	window.add(upperframe)

	# Build the console.
	builtins = {
		"quit": lambda: root.quit(),
		"view": lambda viewer: display.view(viewer),
		"Waveform": Waveform,
		"Events": Events,
	}
	console = Console(parent=window, dict=builtins)
	# expose additional objects to the console like this:
	#c.dict["console"] = c
	window.add(console)

	# fix tkinter's weird layout glitch
	root.update()
	root.geometry(root.geometry())

	# Go do things until the user is bored
	root.mainloop()
