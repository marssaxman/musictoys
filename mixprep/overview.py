import Tkinter as tk
import numpy as np

def rms(samples):
	return np.sqrt(np.mean(samples ** 2))


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

