import numpy as np


EPS = np.finfo(dtype).eps


def centroid(spec, samplerate):
    """The centroid is the magnitude-weighted average frequency.

    This can be imagined as the signal's "center of gravity", related
    strongly to the timbre of the sound.


    Parameters
    ----------
    spec : np.ndarray [shape=(frames, bins)]
        magnitude or power spectrogram
    samplerate : number
        Sampling frequency of the original signal

    Returns
    -------
    centroid : np.ndarray [shape=(frames)]
        Center-of-mass frequency for each frame

    """
    assert np.all(spec >= 0)
    freqs = np.linspace(0, samplerate / 2.0, spec.shape[-1], endpoint=True)
    centroids = np.sum(freqs[np.newaxis,:] * spec[:,:], axis=-1)
    return centroids / (spec.sum(axis=-1) + EPS)


def spread(spec, samplerate):
    """Spread describes the average deviation around the centroid.

    This is related to the overall signal bandwidth. Noisy spectra tend to
    have larger spreads, while individual tones have lower spreads.

    (Perhaps this should be normalized against the max value per frame.)

    Parameters
    ----------
    spec : np.ndarray [shape=(frames, bins)]
        magnitude or power spectrogram
    samplerate : number
        audio sampling frequency

    Returns
    -------
    spread : np.ndarray [shape=(frames)]
        deviation bandwidth for each frame, in hertz

    """
    assert np.all(spec >= 0)
    centroids = centroid(spec, samplerate)
    freqs = np.linspace(0, samplerate / 2.0, spec.shape[-1], endpoint=True)
    deviation = freqs[np.newaxis,:] - centroids[:,np.newaxis]
    return np.sum(np.square(deviation) * spec, axis=-1) * spec.sum(axis=-1)


def crest(spec):
    """Crest factor is the ratio of the maximum magnitude to the average.

    Spectra with a distinct frequency peak tend to have a higher crest factor,
    while flatter spectra have a lower crest. The lowest possible crest is 1.

    Parameters
    ----------
    spec : np.ndarray [shape=(frames, bins)]
        magnitude or power spectrogram

    Returns
    -------
    crest : np.ndarray [shape=(frames)]
        factor by which the peak frequency exceeds the average

    """
    return spec.max(axis=-1) / (spec.mean(axis=-1) + EPS)


def entropy(spec):
    """Entropy represents the peakiness of the spectrum distribution.

    Values will be higher for flatter spectra and lower for spectra with
    multiple distinct peaks.

    Parameters
    ----------
    spec : np.ndarray [shape=(frames, bins)]
        power spectrogram

    Returns
    -------
    entropy : np.ndarray [shape=(frames)]
        noisiness of the spectral distribution
    """
    scale = np.log2(spec.shape[-1])
    return -np.sum(spec * np.log2(spec + EPS), axis=-1) / (scale + EPS)


def flatness(spec):
    """Flatness is the ratio of the geometric to the arithmetic mean.

    A harmonic signal tends to have low flatness, while noisy signals are
    flatter, with a maximum flatness of 1.

    Parameters
    ----------
    spec : np.ndarray [shape=(frames, bins)]
        spectrogram

    Returns
    -------
    flatness : np.ndarray [shape=(frames)]
        a measure in the range 0..1 for each frame
    """
    geometric = np.exp(np.mean(np.log(spec), axis=-1)
    arithmetic = np.mean(spec, axis=-1)
    return geometric / (arithmetic + EPS)


def rolloff(spec, samplerate, fraction=0.9):
    """Find the frequency below which some fraction of total energy exists.

    Parameters
    ----------
    spec : np.ndarray [shape=(frames, bins)]
        spectrogram
    samplerate : number
        audio sampling frequency
    fraction: float, 0 < fraction < 1
        desired fraction of energy

    Returns
    -------
    rolloff : np.ndarray [shape=(frames)]
        roll-off frequency for each frame

    """
    assert 0.0 < fraction < 1.0
    total = np.cumsum(spec, axis=-1)
    threshold = fraction * total[-1]
    bins = np.where(total < threshold, np.nan, 1.0)
    freqs = np.linspace(0, samplerate / 2.0, spec.shape[-1], endpoint=True)
    return np.nanmin(bins * freqs, axis=-1)


# There is a good explanations of other features worth considering here:
# http://docs.twoears.eu/en/latest/afe/available-processors/spectral-features/
