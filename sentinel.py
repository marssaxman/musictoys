#!/usr/bin/env python

import Tkinter as Tk
from interface.console import Console
from interface.display import Display
from interface.waveform import Waveform

class Clip:
	def __init__(self, signal, samplerate):
		self.signal = signal
		self.samplerate = samplerate

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
	window.pack(fill=Tk.BOTH, expand=1)

	# Make space where can draw visualizations of data about audio.
	display = Display(window, bg="grey", height=200)
	window.add(display)

	# Build the console.
	builtins = {
		"quit": lambda: root.quit(),
		"view": lambda viewer: display.view(viewer),
		"Waveform": Waveform,
		"Clip": Clip
	}
	console = Console(parent=window, dict=builtins)
	# expose additional objects to the console like this:
	#c.dict["console"] = c
	window.add(console)

	# Go do things until the user is bored
	root.mainloop()
