
import numpy as np
import mel

def amp_to_power(s):
    return s ** 2.0


def power_to_db(s):
    log_s = 10.0 * np.log10(np.maximum(1e-10, s))
    return log_s - 10.0 * np.log10(np.maximum(1e-10, 1.0))


def hz_to_mel(spectrum, samplerate, num_bands=40):
    return np.dot(spectrum, mel.filter(samplerate, len(spectrum), num_bands).T)


def _windows(source, samplerate, resolution=128, window_size=2048):
    # Yield a sequence of views onto the source, which must be normalized mono.
    # We'll pad the beginning by half a window so that time zero happens at
    # index zero, and we'll pad the end by whatever we need to line things up.
    mask = np.hamming(window_size)
    for i in range(0, len(source), resolution):
        start = i - (window_size / 2)
        stop = start + window_size
        frame = None
        if start < 0:
            frame = np.zeros(window_size)
            frame[-start:] = source[0:stop]
        elif stop > len(source):
            frame = np.zeros(window_size)
            frame[:len(source)-stop] = source[start:]
        else:
            frame = source[start:stop]
        yield frame * mask


def analyze(sound):
    print "Analyzing"

    samples = sound.frames
    samplerate = sound.samplerate

    # Prepare for analysis by mixing down to a single channel, if necessary.
    if samples.ndim > 1:
        samples = np.mean(samples, axis=1)

    # The ultimate goal of this analysis will be to generate a beat grid and
    # segmentation points. In order to run the beat tracker, we will need an
    # array of onset strengths; we generate that by computing a variety of
    # frequency-level features.  Begin with a mel-scaled spectrogram.

    # Compute sliding windowed FFTs.
    frames = _windows(samples, samplerate, resolution=256, window_size=2048)
    spectrogram = (np.abs(np.fft.rfft(f)) for f in frames)
    # Convert to power spectrum and then rescale to Mel bands.
    melbands = (hz_to_mel(amp_to_power(s), samplerate) for s in spectrogram)
    melbands = (power_to_db(m) for m in melbands)
    # Compute the cosine difference between each pair of spectra.

