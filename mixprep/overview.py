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
		# interval represents the beginning and ending coordinates of the slice
		# of the signal that we are highlighting, from 0..1
		self.interval = (0, 1.0)
		# we keep track of the object ID we used to draw the interval frame so
		# we don't have to redraw the entire waveform while zooming/scrolling
		self._interval_box_id = None
		self.bind("<Configure>", self.on_resize)
		self.bind("<MouseWheel>", self.on_mousewheel)
		self.bind("<Button-4>", self.on_mousewheel)
		self.bind("<Button-5>", self.on_mousewheel)
		self._draw()

	def on_resize(self, event):
		self._draw()

	def on_mousewheel(self, event):
		# tk produces different events on different platforms
		if event.num == 5 or event.delta == -120:
			# mousewheel up: zoom in
			self.zoom(9.0 / 8.0, event.x)
		elif event.num == 4 or event.delta == 120:
			# mousewheel down: zoom out
			self.zoom(7.0 / 8.0, event.x)

	def zoom(self, factor, eventx=None):
		begin, end = self.interval
		length = end - begin
		pos = (begin + end) / 2.0
		length *= factor
		if eventx:
			pos = float(eventx) / float(self.winfo_width())
		begin = max(0, pos - (length / 2.0))
		end = min(1, begin + length)
		self.interval = (begin, end)
		self._draw_interval()

	def _draw(self):
		self.delete('all')
		self._interval_box_id = None
		width = self.winfo_width()
		height = self.winfo_height()
		samplecount = len(self.signal.mono)
		left_channel = self.signal.left
		right_channel = self.signal.right
		vloc = height / 2
		vscale = height * 3 / 8
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
		self._draw_interval()

	def _draw_interval(self):
		if self._interval_box_id:
			self.delete(self._interval_box_id)
			self._interval_box_id = None
		# Draw a highlight box around the view interval.
		begin, end = self.interval
		if begin > 0 or end < 1:
			width, height = self.winfo_width(), self.winfo_height()
			color, pix = '#FF0000', 3
			top, bottom = pix + 1, height - pix - 2
			begin, end = int(begin * width), int(end * width)
			left, right = begin + pix + 1, end - pix - 1
			self._interval_box_id = self.create_rectangle(
				left, top, right, bottom, outline=color, width=pix)


