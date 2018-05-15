import numpy as np
import matplotlib
import matplotlib.pyplot as plt
# Inline plots always come out really narrow by default, but when visualizing
# audio data we typically want graphs which are much wider than they are tall.
plt.rc('figure', figsize=(16,3))
plt.rc('image', aspect='auto', interpolation='bicubic')


def hide_xticks():
    plt.tick_params(
        axis='x',         # changes apply to the specified axis
        which='both',      # both major and minor ticks are affected
        bottom=False,      # ticks along the bottom edge are off
        top=False,         # ticks along the top edge are off
        labelbottom=False) # labels along the bottom edge are of


def hide_yticks():
    plt.tick_params(
        axis='y',          # changes apply to the specified axis
        which='both',      # both major and minor ticks are affected
        left=False,        # ticks along the bottom edge are off
        right=False,       # ticks along the top edge are off
        labelleft=False)   # labels along the bottom edge are of


def _xscale(data, x):
    if x is None:
        x = np.arange(0, data.shape[0])
        hide_xticks()
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
        y = np.arange(0, 1+data.shape[1])
        hide_yticks()
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


def hsl_to_rgb(h, s, l):
    # vectorized convertion of hue, saturation, lightness planes into
    # corresponding red, green, blue planes
    shape = h.shape

    # all inputs and outputs range 0..1
    r = np.zeros(shape)
    g = np.zeros(shape)
    b = np.zeros(shape)

    # where the color is totally desaturated, use only luminance
    grey = (s==0)
    r[grey] = l[grey]
    g[grey] = l[grey]
    b[grey] = l[grey]

    # scale the saturation differently around medium luminance
    q = np.zeros(shape)
    low_luma = l < 0.5
    q[low_luma] = l[low_luma] * (1 + s[low_luma])
    hi_luma = l >= 0.5
    q[hi_luma] = l[hi_luma] + s[hi_luma] - l[hi_luma] * s[hi_luma]
    # the other hue factor is proportional
    p = 2 * l - q;

    def channel(t):
        # enforce limits
        t[t < 0] += 1.0
        t[t > 1] -= 1.0
        x = np.zeros(shape)
        tA = t < 1/6.
        x[tA] = p[tA] + (q[tA] - p[tA]) * 6 * t[tA]
        tB = (t >= 1/6.) & (t < 1/2.)
        x[tB] = q[tB]
        tC = (t >= 1/2.) & (t < 2/3.)
        x[tC] = p[tC] + (q[tC] - p[tC]) * (2/3. - t[tC]) * 6
        tD = t >= 2/3.
        x[tD] = p[tD]
        return x

    chroma = (s != 0)
    r[chroma] = channel(h + 1./3.)[chroma]
    g[chroma] = channel(h)[chroma]
    b[chroma] = channel(h - 1./3.)[chroma]

    return r, g, b

