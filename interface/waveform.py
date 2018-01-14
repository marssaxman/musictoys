import Tkinter as Tk

# waveform displays an array of samples
# source must have attributes
#	signal - list of values
#	samplerate - number of samples per second


class Waveform:
	def __init__(self, source):
		self.source = source
	def draw(self, canvas):
		width = canvas.winfo_width()
		height = canvas.winfo_height()
		samplecount = len(self.source.signal)
		samplerate = float(self.source.samplerate)
		duration = samplecount / samplerate
		pixel_time = duration / float(width)
		vert_size = height / 2
		#if sample_count >= width:
		# each pixel displays the min and max in its range
		for x in xrange(width):
			pixel_begin = x * pixel_time
			sample_begin = int(round(pixel_begin * samplerate))
			pixel_end = pixel_begin + pixel_time
			sample_end = int(round(pixel_end * samplerate))
			slice = self.source.signal[sample_begin:sample_end]
			low = -min(slice) * vert_size + vert_size
			high = -max(slice) * vert_size + vert_size
			canvas.create_line(x, low, x, high)

