import numpy as np


class Spectrum(np.ndarray):

    def __new__(cls, values, bin_frequencies, mag_scale=1.0):
        obj = np.asarray(values).view(cls)
        obj._mag_scale = mag_scale
        obj.bin_frequencies = bin_frequencies
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self._mag_scale = getattr(obj, '_mag_scale', 1.0)
        self.bin_frequencies = getattr(obj, 'bin_frequencies', None)

    @property
    def eps(self):
        return np.finfo(self.dtype).eps

    @property
    def num_bins(self):
        return self.shape[-1]

    def magnitude(self):
        return np.abs(self) / self._mag_scale

    def phase(self):
        return np.phase(self)

    def power(self):
        return self.magnitude() ** 2

    def logpower(self):
        return 20 * np.log10(self.magnitude())

    def centroid(self):
        """Centroid is the weighted average frequency; the "center of mass"."""
        centroid = np.sum(self.bin_frequencies * self)
        return centroid / (self.sum() + self.eps)

    def spread(self):
        """Spread is the average frequency deviation around the centroid."""
        deviation = np.square(self.bin_frequencies - self.centroid())
        weighted = np.sum(self * deviation)
        return np.sqrt(weighted / (self.sum() + self.eps))

    def crest(self):
        """Crest factor is the ratio of the maximum magnitude to the average.

        Spectra with a distinct frequency peak tend to have a higher crest
        factor, while flatter (noisier) spectra have a lower crest; the lowest
        possible crest is 1.0.
        """
        return self.max() / (self.mean() + self.eps)

    def entropy(self):
        """Entropy represents the complexity of a spectrum distribution.

        High entropy is associated with flatter, noisier spectra. Lower entropy
        indicates a peakier distribution, with distinct, tonal frequencies.
        """
        prob_dist = self / self.sum()
        log_dist = np.log2(prob_dist + self.eps)
        scale = np.log2(len(self))
        return -np.sum(self * log_dist) / (scale + self.eps)

    def flatness(self):
        """Flatness is the ratio of the geometric to the arithmetic mean.

        A harmonic signal tends to have low flatness, while noisy signals are
        flatter; values range from 0..1. This is also called "Wiener entropy."
        """
        geometric = np.exp(np.mean(np.log(self + self.eps)))
        arithmetic = self.mean()
        return geometric / (arithmetic + self.eps)

    def rolloff(self, fraction=0.9):
        """Find the frequency some fraction of total energy occurs below."""
        assert 0.0 < fraction < 1.0
        total_energy = np.cumsum(self)
        threshold = fraction * total_energy
        mask = np.where(total_energy >= threshold, 1, np.nan)
        return np.nanmin(mask * freqs)


def processor(func):
    """Decorator allowing a function expecting a Spectrum to accept an ndarray.

    The func's first positional argument is the spectrum object. If the caller
    passes in a plain ndarray, the kwargs must include 'bin_frequencies', and
    the ndarray will be wrapped in a Spectrum before being passed on.
    """
    def wrapper(data, *args, **kwargs):
        if isinstance(data, Spectrum):
            return func(data, *args, **kwargs)
        else:
            clip = Spectrum(data, kwargs.pop('bin_frequencies'))
            return func(clip, *args, **kwargs)
    return wrapper


magnitude = processor(Spectrum.magnitude)
phase = processor(Spectrum.phase)
power = processor(Spectrum.power)
logpower = processor(Spectrum.logpower)
centroid = processor(Spectrum.centroid)
spread = processor(Spectrum.spread)
crest = processor(Spectrum.crest)
entropy = processor(Spectrum.entropy)
flatness = processor(Spectrum.flatness)
rolloff = processor(Spectrum.rolloff)
