import Tkinter as tk
import numpy as np
import librosa


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


class Waveplot(tk.Canvas):
	def __init__(self, container, signal, **kwargs):
		if not 'background' in kwargs and not 'bg' in kwargs:
			kwargs['background'] = '#FFFFFF'
		tk.Canvas.__init__(self, container, **kwargs)
		self._signal = signal
		self._histograms = None
		# Create the initial image buffer, which we will replace as soon as we
		# have been configured with our actual dimensions.
		self._image_buffer = tk.PhotoImage(width=1, height=1)
		self._image_handle = self.create_image(
				0, 0, anchor=tk.NW, image=self._image_buffer)
		# Generate the array of HTML color names we must supply to PhotoImage.
		self._colormap = ["#%02x%02x%02x" % (n,n,n) for n in xrange(256)]
		# interval represents the beginning and ending coordinates of the slice
		# of the signal that we are highlighting, from 0..1
		self._view_interval = (0, 1.0)
		self.bind("<Configure>", self.on_resize)

	def on_resize(self, event):
		width = self.winfo_width()
		height = self.winfo_height()
		self._image_buffer = tk.PhotoImage(width=width, height=height)
		self.itemconfig(self._image_handle, image=self._image_buffer)
		self._histograms = None
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
				self._histograms = None
			self._view_interval = (newbegin, newend)
			self._draw()

	def _get_view_signal(self):
		# Return the slice of signal data we are currently viewing.
		begin, end = self._view_interval
		signal = self._signal.mono
		begin_index = int(begin * float(len(signal)))
		end_index = int(end * float(len(signal)))
		return signal[begin_index:end_index]

	def _draw(self):
		begin, end = self._view_interval
		width, height = self.winfo_width(), self.winfo_height()
		if not self._histograms:
			# Compute the frame step, which is equal to the number of samples
			# per pixel we'd have if we were displaying the whole signal.
			view_fraction = end - begin
			total_samples = len(self._signal.mono)
			view_samples = total_samples * view_fraction
			samples_per_pixel = view_samples / width
			step = int(samples_per_pixel)
			# We'll create one histogram bin per pixel of column height.
			bins = height + 1
			# Divide the original signal into frames, with lazy histogram
			# generators we'll call on as needed.
			self._histograms = _FramedHistograms(self._signal.mono, step, bins)
		# Turn all those levels into a giant string, because that's the only
		# interface Tkinter's PhotoImage class gives us for altering pixels.
		num_frames = len(self._histograms)
		indices = xrange(int(begin * num_frames), int(end * num_frames))
		for x, frame_index in enumerate(indices):
			levels = self._histograms[frame_index]
			# Add some gamma correction to make it prettier
			levels = levels ** (0.25)
			# Map levels to entries in our color palette.
			pix = [self._colormap[int(levels[y]*255)] for y in xrange(height)]
			self._image_buffer.put(" ".join(pix), (x,0))
		self.update()
