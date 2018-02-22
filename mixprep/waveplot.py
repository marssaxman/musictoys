import Tkinter as tk
import numpy as np
import librosa
import time


class _FramedHistograms:
	def __init__(self, signal, step, bins):
		self.signal = signal
		self.frames = librosa.util.frame(
				signal, frame_length=step, hop_length=step)
		self.bins = np.linspace(-1, 1, num=bins)
		self.histograms = [None] * self.frames.shape[1]
	def __len__(self):
		return len(self.histograms)
	def __getitem__(self, key):
		histogram = self.histograms[key]
		if histogram is None:
			frame = self.frames[:,key]
			histogram, edges = np.histogram(frame, bins=self.bins)
			normalize = np.max(histogram)
			histogram = histogram / float(np.max(histogram))
			self.histograms[key] = histogram
		return histogram


class _Rasterizer:
	def __init__(self, source, height):
		self._source = source
		self._pixels = [None] * len(source)
	def __len__(self):
		return len(self._pixels)
	def __getitem__(self, index):
		pixels = self._pixels[index]
		if pixels is None:
			pixels = ''.join(self._doformat(self._source[index]))
			self._pixels[index] = pixels
		return pixels
	def _doformat(self, levels):
		# Emit a sequence of ASCII values corresponding to the HTML color
		# literals which would produce a grey tone whose brightness corresponds
		# to the input value's position in the range 0..1. This is messy
		# because it is speed-critical. By constructing a string from this
		# generator using join(), we only have to perform one allocation. Why
		# on earth are we constructing a string at all? Because that's the only
		# form of input PhotoImage.put() accepts.
		for floatval in levels:
			yield ' '
			yield '#'
			# Add some gamma correction to make it prettier, then map to the
			# RGB24 range 0..255.
			intval = int(floatval * 255)
			hexes = '0123456789abcdef'
			hi = hexes[(intval >> 4) & 0x0F]
			lo = hexes[intval & 0x0F]
			yield hi
			yield lo
			yield hi
			yield lo
			yield hi
			yield lo


class Waveplot(tk.Canvas):
	def __init__(self, container, track, **kwargs):
		if not 'background' in kwargs and not 'bg' in kwargs:
			kwargs['background'] = '#FFFFFF'
		tk.Canvas.__init__(self, container, **kwargs)
		self._track = track
		self._signal = track.signal
		self._rasterizer = None
		self._must_render = False
		# Create the initial image buffer, which we will replace as soon as we
		# have been configured with our actual dimensions.
		self._image_buffer = tk.PhotoImage(width=1, height=1)
		self._image_handle = self.create_image(
				0, 0, anchor=tk.NW, image=self._image_buffer)
		# interval represents the beginning and ending coordinates of the slice
		# of the signal that we are highlighting, from 0..1
		self._view_interval = (0, 1.0)
		self.bind("<Configure>", self.on_resize)

	def on_resize(self, event):
		width = self.winfo_width()
		height = self.winfo_height()
		self._image_buffer = tk.PhotoImage(width=width, height=height)
		self.itemconfig(self._image_handle, image=self._image_buffer)
		self._rasterizer = None
		self._draw()

	def view(self, interval):
		newbegin = max(0, interval[0])
		newend = min(1, interval[1])
		begin, end = self._view_interval
		if newbegin != begin or newend != end:
			old_duration = end - begin
			new_duration = newend - newbegin
			if old_duration != new_duration:
				# zoom level has changed
				self._rasterizer = None
			self._view_interval = (newbegin, newend)
			self._draw()

	def _gen_rasterizer(self):
		begin, end = self._view_interval
		width, height = self.winfo_width(), self.winfo_height()
		# Compute the frame step, which is equal to the number of samples
		# per pixel we'd end up with if we displayed the whole signal at this
		# zoom level.
		view_fraction = end - begin
		total_samples = len(self._signal)
		view_samples = total_samples * view_fraction
		samples_per_pixel = view_samples / width
		step = int(samples_per_pixel)
		# We'll create one histogram bin per pixel of column height.
		bins = height + 1
		# Divide the original signal into frames, with a lazy memoizing 
		# histogram generator we can use for density information.
		histograms = _FramedHistograms(self._signal, step, bins)
		self._rasterizer = _Rasterizer(histograms, height)

	def _draw(self):
		if not self._must_render:
			self._must_render = True
			self.after(1, self._render)

	def _render(self):
		self._must_render = False
		if not self._rasterizer:
			self._gen_rasterizer()
		begin, end = self._view_interval
		width, height = self.winfo_width(), self.winfo_height()
		# Turn all those levels into a giant string, because that's the only
		# interface Tkinter's PhotoImage class gives us for altering pixels.
		num_frames = len(self._rasterizer)
		indices = xrange(int(begin * num_frames), int(end * num_frames))
		for x, frame_index in enumerate(indices):
			pixels = self._rasterizer[frame_index]
			self._image_buffer.put(pixels, (x,0))
		self.update()

