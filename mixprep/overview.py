import Tkinter as tk
import numpy as np
import librosa


def _framed_max_rms(signal, step):
	frames = librosa.util.frame(signal, frame_length=step, hop_length=step)
	maxmag = np.max(np.abs(frames), axis=0)
	rms = np.sqrt(np.mean(frames ** 2, axis=0))
	return maxmag, rms


class Overview(tk.Canvas):
	def __init__(self, container, track, **kwargs):
		if not 'background' in kwargs and not 'bg' in kwargs:
			kwargs['background'] = '#222222'
		tk.Canvas.__init__(self, container, **kwargs)
		self._track = track
		self._signal = track.signal
		self.view_command = None
		# interval represents the beginning and ending coordinates of the slice
		# of the signal that we are highlighting, from 0..1
		self._view_interval = (0, 1.0)
		self._selection = None
		# we keep track of the object ID we used to draw the interval frame so
		# we don't have to redraw the entire waveform while zooming/scrolling
		self._view_box_id = None
		self._selection_box_id = None
		self.bind("<Configure>", self.on_resize)
		self.bind("<MouseWheel>", self.on_mousewheel)
		self.bind("<Button-4>", self.on_mousewheel)
		self.bind("<Button-5>", self.on_mousewheel)
		self.bind("<ButtonPress-1>", self.on_mousedown)

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

	def on_mousedown(self, event):
		pos = float(event.x) / float(self.winfo_width())
		begin, end = self._view_interval
		if pos >= begin and pos <= end:
			self._mouse_drag_offset = pos - begin
			self.bind("<B1-Motion>", self.on_mousemove)
			self.bind("<ButtonRelease-1>", self.on_mouseup)

	def on_mousemove(self, event):
		pos = float(event.x) / float(self.winfo_width())
		begin, end = self._view_interval
		length = end - begin
		begin = pos - self._mouse_drag_offset
		self.view((begin, begin + length))

	def on_mouseup(self, event):
		self.unbind("<B1-Motion>")
		self.unbind("<ButtonRelease-1>")

	def zoom(self, factor, eventx=None):
		begin, end = self._view_interval
		length = end - begin
		pos = (begin + end) / 2.0
		length *= factor
		if eventx:
			pos = float(eventx) / float(self.winfo_width())
		newbegin = pos - (length / 2.0)
		newend = newbegin + length
		self.view((newbegin, newend))

	def view(self, interval):
		newbegin = max(0, interval[0])
		newend = min(1, interval[1])
		begin, end = self._view_interval
		if newbegin != begin or newend != end:
			self._view_interval = (newbegin, newend)
			self._draw_view_box()
			if self.view_command:
				self.view_command(self._view_interval)

	def select(self, interval):
		self._selection = interval
		self._draw_selection_box()

	def _draw(self):
		# Delete everything on the canvas and start over fresh. This would be
		# necessary if the canvas were resized or we changed the source data.
		self.delete('all')
		self._view_box_id = None
		self._selection_box_id = None
		width = self.winfo_width()
		height = self.winfo_height()
		# how many pixels tall should we draw things, and how far offset?
		vloc = height / 2
		vscale = height * 3 / 8

		# Chop the signal halves into frames, then get the maxmag and rms value
		# for each frame, where each frame corresponds to one pixel.
		framelen = int(len(self._signal) / float(width))
		left_max, left_rms = _framed_max_rms(self._signal, framelen)
		# Hmmmm. Maybe we want access to stereo data after all. Worry later.
		right_max, right_rms = left_max, left_rms
		for x in xrange(width):
			# Draw the left channel on top and the right channel below, using
			# dark grey for the max and a lighter grey for RMS.
			top_pos = vloc - (left_max[x] * vscale)
			bot_pos = vloc + (right_max[x] * vscale)
			self.create_line(x, top_pos, x, bot_pos, fill='#AAAAAA')
			top_pos = vloc - (left_rms[x] * vscale)
			bot_pos = vloc + (right_rms[x] * vscale)
			self.create_line(x, top_pos, x, bot_pos, fill='#CCCCCC')
		self._draw_view_box()
		self._draw_selection_box()

	def _draw_view_box(self):
		if self._view_box_id:
			self.delete(self._view_box_id)
			self._view_box_id = None
		# Draw a highlight box around the view interval.
		begin, end = self._view_interval
		if begin > 0 or end < 1:
			width, height = self.winfo_width(), self.winfo_height()
			color, pix = '#FF0000', 3
			top, bottom = pix + 1, height - pix - 2
			begin, end = int(begin * width), int(end * width)
			left, right = begin + pix + 1, end - pix - 1
			self._view_box_id = self.create_rectangle(
				left, top, right, bottom, outline=color, width=pix)

	def _draw_selection_box(self):
		if self._selection_box_id:
			self.delete(self._selection_box_id)
			self._selection_box_id = None
		if not self._selection:
			return
		# Draw a translucent overlay across the selection range.
		begin, end = self._selection
		width, height = self.winfo_width(), self.winfo_height()
		vloc = height / 2
		vscale = height * 3 / 8
		top, bottom = vloc - vscale, vloc + vscale
		left, right = int(begin * width), int(end * width)
		self._selection_box_id = self.create_rectangle(
			left, top, right, bottom, fill='blue', stipple='gray50', width=0)

