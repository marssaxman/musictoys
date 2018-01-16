import math
class Waveform:
	def __init__(self, signal, sample_rate):
		self.signal = signal
		self.sample_rate = sample_rate
	def duration(self):
		return len(self.signal) / float(self.sample_rate)
	def draw(self, canvas, interval):
		width = canvas.winfo_width()
		height = canvas.winfo_height()
		rate = float(self.sample_rate)
		view_begin, view_end = interval
		view_duration = view_end - view_begin
		pixel_time = view_duration / float(width)
		vert_size = height / 2
		samples_per_pixel = pixel_time * self.sample_rate
		sample_count = len(self.signal)
		if samples_per_pixel >= 2:
			# each pixel displays the min and max in its range
			for x in xrange(width):
				pixel_begin = x * pixel_time + view_begin
				sample_begin = int(round(pixel_begin * rate))
				sample_begin = min(sample_begin, sample_count)
				pixel_end = pixel_begin + pixel_time
				sample_end = int(round(pixel_end * rate))
				sample_end = min(sample_end, sample_count)
				if sample_begin == sample_end:
					continue
				slice = self.signal[sample_begin:sample_end]
				low = -min(slice) * vert_size + vert_size
				high = -max(slice) * vert_size + vert_size
				canvas.create_line(x, low, x, high)
		else:
			sample_begin = int(math.floor(view_begin * self.sample_rate))
			sample_begin = max(sample_begin, 0)
			sample_end = int(math.ceil(view_end * self.sample_rate))
			sample_end = min(sample_end, len(self.signal))
			prev_x, prev_y = -1, vert_size
			for i in range(sample_begin, sample_end):
				val = self.signal[i]
				x = int(round(i / float(samples_per_pixel)))
				y = val * vert_size + vert_size
				canvas.create_line(prev_x, prev_y, x, y)
				prev_x, prev_y = x, y
			canvas.create_line(prev_x, prev_y, width+1, vert_size)
			
