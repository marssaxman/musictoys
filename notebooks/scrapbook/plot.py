import numpy as np
import matplotlib
import matplotlib.pyplot as plt
# Inline plots always come out really narrow by default, but when visualizing
# audio data we typically want graphs which are much wider than they are tall.
plt.rc('figure', figsize=(16,3))
plt.rc('image', aspect='auto', interpolation='bicubic')


def _hide_xticks():
    plt.tick_params(
        axis='x',         # changes apply to the specified axis
        which='both',      # both major and minor ticks are affected
        bottom=False,      # ticks along the bottom edge are off
        top=False,         # ticks along the top edge are off
        labelbottom=False) # labels along the bottom edge are of


def _hide_yticks():
    plt.tick_params(
        axis='y',          # changes apply to the specified axis
        which='both',      # both major and minor ticks are affected
        left=False,        # ticks along the bottom edge are off
        right=False,       # ticks along the top edge are off
        labelleft=False)   # labels along the bottom edge are of


def _xscale(data, x):
    if x is None:
        x = np.arange(0, data.shape[0])
        _hide_xticks()
    if isinstance(x, float) or isinstance(x, int):
        x = np.arange(0, data.shape[0]) / float(x)
    return x


def line(samples, x=None, y=None):
    # Plot a one-dimensional sample series.
    x = _xscale(samples, x)
    plt.plot(x, samples)
    plt.show()


def _yscale(data, y):
    if y is None:
        y = np.arange(0, data.shape[1])
        _hide_yticks()
    return y


def gram(matrix, x=None, y=None, cmap='gray'):
    # Plot a matrix with shape[observations, features].
    x = _xscale(matrix, x)
    y = _yscale(matrix, y)
    plt.pcolormesh(x, y, matrix.T, cmap=cmap)
    plt.show()


def colorgram(matrix, x=None, y=None):
    # Plot a matrix with shape [observations, features, 3]; that is,
    # a feature matrix to which a colormap has already been applied.
    # We can use imshow but it has the irritating expectation that the
    # orientation will be reversed, so we must transpose axes 0 and 1.
    x = _xscale(matrix, x)
    y = _yscale(matrix, y)
    plt.imshow(np.swapaxes(matrix, 0, 1))
    plt.show()

