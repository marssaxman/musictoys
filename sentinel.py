#!/usr/bin/env python

import Tkinter as Tk
from interface.console import Console

if __name__ == "__main__":
	root = Tk.Tk()
	root.title("sentinel: an audio environment")

	# The shell is divided horizontally.
	# The top pane holds an audio viewer.
	# The bottom pane holds a python console.
	window = Tk.PanedWindow(orient=Tk.VERTICAL)
	window.pack(fill=Tk.BOTH, expand=1)

	# Make space where can draw visualizations of data about audio.
	viewer = Tk.Canvas(window, bg="grey", height=200)
	window.add(viewer)

	# Build the console.
	builtins = {
		"quit": lambda: root.quit()
	}
	console = Console(parent=window, dict=builtins)
	# expose additional objects to the console like this:
	#c.dict["console"] = c
	window.add(console)

	# Go do things until the user is bored
	root.mainloop()
