
import numpy as np
import matplotlib.mlab


def waveform(axes, samples):
    figure = axes.get_figure()
    resolution = figure.get_dpi() * figure.get_size_inches()[0]
    axes.get_xaxis().set_visible(False)
    axes.get_yaxis().set_visible(False)
    axes.set_ylim(-1, 1)
    axes.set_xlim(0, len(samples))
    # Draw a faint line across the horizontal axis.
    axes.axhline(0, color='lightgray', zorder=0)
    if len(samples) > resolution:
        # Matplotlib would choke if it tried to draw the entire sample array, so
        # we'll split the array into a bin for each pixel, get the min and max,
        # then fill between.
        splits = np.array_split(samples, resolution)
        mins = [x.min() for x in splits]
        maxes = [x.max() for x in splits]
        ticks = [len(x) for x in splits]
        axes.fill_between(ticks, mins, maxes, lw=0.0, edgecolor=None)
    if len(samples) * 4 < resolution:
        # Our points are getting spaced pretty far apart, so we'll mark each sample value
        # and interpolate a smooth curve between them.
        ticks = np.arange(len(samples))
        filltime = np.linspace(ticks[0], ticks[-1], resolution)
        interp = matplotlib.mlab.stineman_interp(filltime, ticks, samples, None)
        axes.plot(ticks, samples, '.', filltime, interp)
    else:
        # We have a reasonable number of samples, so draw an ordinary waveform.
        axes.plot(np.arange(len(samples)), samples)

