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
import argparse
import librosa
import sys
import math
from editview import Editview
from overview import Overview
from waveplot import Waveplot

def next_power_of_2(n):
	return 2 ** math.ceil(math.log(n, 2))


class AudioTrack:
	def __init__(self, path):
		self.path = path
		signal, self.samplerate = librosa.load(path, sr=44100, mono=False)
		self.left = signal[0, :]
		self.right = signal[1, :]
		self.mono = librosa.to_mono(signal)
		self.duration = len(self.mono) / float(self.samplerate)


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
	layout = tk.Frame(root, borderwidth=0, highlightthickness=0)
	layout.grid_rowconfigure(0, weight=0)
	layout.grid_rowconfigure(1, weight=1)
	layout.grid_columnconfigure(0, weight=1)
	layout.grid_rowconfigure(2, weight=0)
	controls = tk.Frame(layout, borderwidth=0, highlightthickness=0)
	controls.grid(row=0, column=0, sticky='nsew')
	waveplot = Waveplot(layout, signal)
	waveplot.grid(row=1, column=0, sticky='nsew')
	overview = Overview(layout, signal, height=80, bd=0)
	overview.grid(row=2, column=0, sticky='nsew')
	layout.pack(fill=tk.BOTH, expand=True)

	#editview.select_command = overview.select
	overview.view_command = waveplot.view

	root.mainloop()


if __name__=='__main__':
	main()
