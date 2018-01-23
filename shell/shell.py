#!/usr/bin/env python

import Tkinter as tk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as pyplot
import matplotlib.figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Display(tk.Frame):
	def __init__(self, container, **kwargs):
		tk.Frame.__init__(self, container, **kwargs)
		self.figure = pyplot.Figure((5,2), dpi=100)
		self.canvas = FigureCanvasTkAgg(self.figure, master=self)
		self.canvas.show()
		plot_widget = self.canvas.get_tk_widget()
		plot_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
		# Use canvas.mpl_connect to receive UI events.
		# https://matplotlib.org/users/event_handling.html
		# notes on matplotlib performance:
		# http://bastibe.de/2013-05-30-speeding-up-matplotlib.html
		# a cheat sheet for matplotlib:
		# https://s3.amazonaws.com/assets.datacamp.com/blog_assets/Python_Matplotlib_Cheat_Sheet.pdf


class Console(tk.Frame):
	def __init__(self, container, **kwargs):
		tk.Frame.__init__(self, container, **kwargs)
		self.text = tk.Text(master=self)
		self.scroll = tk.Scrollbar(master=self, command=self.text.yview)
		self.text.config(
			borderwidth=0,
			yscrollcommand=self.scroll.set
		)
		self.scroll.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
		self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		self.text.focus()
		# python-prompt-toolkit?
		# pygments for syntax highlighting?
		# nice demo here: http://effbot.org/zone/vroom.htm


class Shell(tk.Frame):
	def __init__(self, container, **kwargs):
		tk.Frame.__init__(self, container, **kwargs)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=1)
		self.grid_columnconfigure(0, weight=1)
		display = Display(self, height=100)
		display.grid(row=0, column=0, sticky="nsew")
		console = Console(self)
		console.grid(row=1, column=0, sticky="nsew")


if __name__ == "__main__":
	root = tk.Tk()
	root.title("interactive display shell")
	root.minsize(480, 256)
	width = root.winfo_screenwidth() / 2
	height = root.winfo_screenheight() * 4 / 5
	root.geometry('%sx%s' % (width, height))
	app = Shell(root)
	app.pack(fill=tk.BOTH, expand=True)
	root.mainloop()

