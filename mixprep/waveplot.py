import Tkinter as tk
import numpy as np
import librosa


def _rasterize(signal, width, height):
	# Slice the signal up into frames, one frame per column.
	step = int(len(signal) / float(width))
	frames = librosa.util.frame(signal, frame_length=step, hop_length=step)
	# Compute a histogram for each frame.
	bins = np.linspace(-1, 1, num=height+1)
	func = lambda x: np.histogram(x, bins=bins)
	hist, edges = np.apply_along_axis(func, 0, frames)
	# The result is a list of lists; join them into a 2D array, then normalize.
	return (np.vstack(hist) / float(step)) ** (0.25)


class Waveplot(tk.Canvas):
	def __init__(self, container, signal, **kwargs):
		if not 'background' in kwargs and not 'bg' in kwargs:
			kwargs['background'] = '#FFFFFF'
		tk.Canvas.__init__(self, container, **kwargs)
		self._signal = signal
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
		self._resize_buffer()
		self._draw()

	def view(self, interval):
		newbegin = max(0, interval[0])
		newend = min(1, interval[1])
		begin, end = self._view_interval
		if newbegin != begin or newend != end:
			self._view_interval = (newbegin, newend)
			self._draw()

	def _resize_buffer(self):
		width = self.winfo_width()
		height = self.winfo_height()
		self._image_buffer = tk.PhotoImage(width=width, height=height)
		self.itemconfig(self._image_handle, image=self._image_buffer)

	def _get_view_signal(self):
		# Return the slice of signal data we are currently viewing.
		begin, end = self._view_interval
		signal = self._signal.mono
		begin_index = int(begin * float(len(signal)))
		end_index = int(end * float(len(signal)))
		return signal[begin_index:end_index]

	def _draw(self):
		# Rasterize the signal into our backing buffer.
		signal = self._get_view_signal()
		width = self.winfo_width()
		height = self.winfo_height()
		levels = _rasterize(signal, width, height)
		# Turn all those levels into a giant string, because that's the only
		# interface Tkinter's PhotoImage class gives us for altering pixels.
		colormap = ["#%02x%02x%02x" % (n,n,n) for n in xrange(256)]
		for x in xrange(width):
			pix = [colormap[int(levels[x][y]*255)] for y in xrange(height)]
			self._image_buffer.put(" ".join(pix), (x,0))
		self.update()
