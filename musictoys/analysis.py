import numpy as np
from resample import resample
import signal
from spectrum import Spectrum


@signal.processor
def floatscale(clip):
    """Convert the signal to floating point with a range of -1..1."""
    if clip.dtype.kind == 'i':
        scale = float(np.iinfo(clip.dtype).max)
        return clip.astype(np.float32) / scale
    elif clip.dtype.kind == 'u':
        scale = float(np.iinfo(clip.dtype).max)
        return clip.astype(np.float32) * 2.0 / scale - 1.0
    elif clip.dtype != np.float32:
        return clip.astype(np.float32)
    else:
        return clip


@signal.processor
def normalize(clip):
    # Convert to 32-bit floating point first of all.
    clip = floatscale(clip)
    # If there are multiple channels, mix down to mono.
    if clip.num_channels > 1:
        clip = clip.mean(axis=0)
    assert 1 == clip.ndim
    # Resample down to no more than 22050 Hz.
    if clip.sample_rate > 22050:
        clip = resample(clip, 22050)
    return clip


def hamming(frame_size):
    # improved hamming window coefficients: the original version used
    # (0.54, 0.46).
    i = np.arange(frame_size, dtype=np.float)
    return 0.53836 - (0.46164 * np.cos(np.pi * 2.0 * i / (frame_size-1)))


@signal.processor
def fft(clip, window=hamming):
    bin_frequencies = np.fft.rfftfreq(clip.num_samples, d=1./clip.sample_rate)
    mask = window(clip.num_samples)
    mag_scale = float(clip.num_samples / 2) * mask.mean()
    return Spectrum(np.fft.rfft(clip), bin_frequencies, mag_scale)


@signal.processor
def stft(clip, frame_size, step_size=None, window=hamming):
    bin_frequencies = np.fft.rfftfreq(frame_size, d=1./clip.sample_rate)
    mask = window(frame_size)
    mag_scale = np.float(frame_size/2) * mask.mean()
    for frame in clip.frames(frame_size, step_size):
        yield Spectrum(np.fft.rfft(frame * mask), bin_frequencies, mag_scale)

