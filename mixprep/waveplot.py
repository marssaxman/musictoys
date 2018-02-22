import Tkinter as tk
import numpy as np
import librosa
import time


class _FramedHistograms:
	def __init__(self, signal, step, bins):
		self.signal = signal
		self.normalize = 1 / float(step)
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
			histogram = histogram * self.normalize
			self.histograms[key] = histogram
		return histogram


class _Rasterizer:
	def __init__(self, source, height):
		self._source = source
		self._pixels = [None] * len(source)
		self._rowspec = "#{:0>2x}{:0>2x}{:0>2x} " * height
	def __len__(self):
		return len(self._pixels)
	def __getitem__(self, index):
		pixels = self._pixels[index]
		if pixels is None:
			levels = self._source[index]
			# Add some gamma correction to make it prettier
			levels = levels ** (0.25)
			# multiply our 0..1 level values by 255 and convert to uint8,
			# then repeat each element three times for RGB
			levels = np.asarray(levels * 255, dtype=np.uint8).repeat(3)
			# apply all the channel values to create one big string param
			pixels = self._rowspec.format(*levels)
			# that's the weirdness PhotoImage.put() calls for!
			self._pixels[index] = pixels
		return pixels


class Waveplot(tk.Canvas):
	def __init__(self, container, signal, **kwargs):
		if not 'background' in kwargs and not 'bg' in kwargs:
			kwargs['background'] = '#FFFFFF'
		tk.Canvas.__init__(self, container, **kwargs)
		self._signal = signal
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
		total_samples = len(self._signal.mono)
		view_samples = total_samples * view_fraction
		samples_per_pixel = view_samples / width
		step = int(samples_per_pixel)
		# We'll create one histogram bin per pixel of column height.
		bins = height + 1
		# Divide the original signal into frames, with a lazy memoizing 
		# histogram generator we can use for density information.
		histograms = _FramedHistograms(self._signal.mono, step, bins)
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

