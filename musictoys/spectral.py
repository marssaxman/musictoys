import numpy as np


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
    eps = np.finfo(spec.dtype).eps
    return centroids / (spec.sum(axis=-1) + eps)


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
    deviation = np.square(freqs[np.newaxis,:] - centroids[:,np.newaxis])
    weighted = np.sum(deviation * spec, axis=-1)
    eps = np.finfo(spec.dtype).eps
    spread = np.sqrt(weighted / (spec.sum(axis=-1) + eps))
    return spread


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
    magspec = spec / np.max(spec, axis=-1)[:,None]
    eps = np.finfo(spec.dtype).eps
    return np.max(magspec, axis=-1) / (np.mean(magspec, axis=-1) + eps)


def entropy(spec):
    """Entropy represents the complexity of a spectrum distribution.

    High entropy is associated with flatter, less distinct spectra, and lower
    entropy correlates with the peakiness of the distribution, spectra with
    multiple distinctly prominent frequencies.

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
    eps = np.finfo(spec.dtype).eps
    return -np.sum(spec * np.log2(spec + eps), axis=-1) / (scale + eps)


def flatness(spec, power=1.0):
    """Flatness is the ratio of the geometric to the arithmetic mean.

    A harmonic signal tends to have low flatness, while noisy signals are
    flatter, with a maximum flatness of 1.

    Parameters
    ----------
    spec : np.ndarray [shape=(frames, bins)]
        spectrogram
    power : float > 0
        Exponent for the magnitude spectrum.
        Typically power spectrograms are most useful for spectral flatness.

    Returns
    -------
    flatness : np.ndarray [shape=(frames)]
        a measure in the range 0..1 for each frame
    """
    scaled = spec ** power
    geometric = np.exp(np.mean(np.log(scaled), axis=-1))
    arithmetic = np.mean(scaled, axis=-1)
    eps = np.finfo(arithmetic.dtype).eps
    return geometric / (arithmetic + eps)


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
    total_energy = np.cumsum(spec, axis=-1)
    threshold = fraction * total_energy[:,-1]
    mask = np.where(total_energy >= threshold[:,None], 1, np.nan)
    freqs = np.linspace(0, samplerate / 2.0, spec.shape[-1], endpoint=True)
    return np.nanmin(mask * freqs, axis=-1, keepdims=True)


def variance(spec):
    """Compute the variance of frequency bin levels across a spectrum..

    Parameters
    ----------
    spec : np.ndarray [shape=(frames, bins)]
        spectrogram

    Returns
    -------
    variance : np.ndarray [shape=(frames)]
        average variance from the mean for each frame

    """
    return np.var(np.abs(spec), axis=-1)


