
import numpy as np
import matplotlib.mlab

def waveform(axes, samples, resolution):
    length = samples.shape[0]
    axes.set_ylim(-1, 1)
    axes.set_xlim(0, length)
    # Draw a faint line across the horizontal axis.
    axes.axhline(0, color='lightgray', zorder=0)
    if length > resolution:
        # Matplotlib would choke if it tried to draw the entire sample array, so
	# we'll split the array into a bin for each pixel, get the min and max,
	# then fill between.
        splits = np.array_split(samples, resolution)
        mins = [x.min() for x in splits]
        maxes = [x.max() for x in splits]
        ticks = [len(x) for x in splits]
        axes.fill_between(ticks, mins, maxes, lw=0.0, edgecolor=None)
    if length * 4 < resolution:
        # Our points are getting spaced pretty far apart, so we'll mark each sample value
        # and interpolate a smooth curve between them.
        ticks = np.arange(length)
        filltime = np.linspace(ticks[0], ticks[-1], resolution)
        interp = matplotlib.mlab.stineman_interp(filltime, ticks, samples, None)
        axes.plot(ticks, samples, '.', filltime, interp)
    else:
        # We have a reasonable number of samples, so draw an ordinary waveform.
        axes.plot(np.arange(length), samples)    