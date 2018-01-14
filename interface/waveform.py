class Waveform:
	def __init__(self, signal, sample_rate):
		self.signal = signal
		self.sample_rate = sample_rate
	def draw(self, canvas):
		width = canvas.winfo_width()
		height = canvas.winfo_height()
		rate = float(self.sample_rate)
		duration = len(self.signal) / rate
		pixel_time = duration / float(width)
		vert_size = height / 2
		#if sample_count >= width:
		# each pixel displays the min and max in its range
		for x in xrange(width):
			pixel_begin = x * pixel_time
			sample_begin = int(round(pixel_begin * rate))
			pixel_end = pixel_begin + pixel_time
			sample_end = int(round(pixel_end * rate))
			slice = self.signal[sample_begin:sample_end]
			low = -min(slice) * vert_size + vert_size
			high = -max(slice) * vert_size + vert_size
			canvas.create_line(x, low, x, high)

