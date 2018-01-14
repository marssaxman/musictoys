class Events:
	def __init__(self, timestamps, duration):
		self.timestamps = timestamps
		self._duration = duration
	def duration(self):
		return self._duration
	def draw(self, canvas, interval):
		width = canvas.winfo_width()
		height = canvas.winfo_height()
		pixel_time = width / float(self._duration)
		for event in self.timestamps:
			x = int(round(event * pixel_time))
			canvas.create_line(x, 0, x, height)

