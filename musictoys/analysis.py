import numpy as np
from resample import resample

def normalize(signal, samplerate):
    # Whatever we're working with, it should become a numpy array.
    signal = np.asarray(signal)
    # If there are multiple channels, mix down to mono.
    if signal.ndim > 1:
        # We accomodate either [channels, samples] or [samples, channels];
        # we assume there will always be fewer channels than samples.
        axis = 0 if signal.shape[0] < signal.shape[1] else 1
        signal = signal.mean(axis=axis)
    assert 1 == signal.ndim
    # Convert to 32-bit floating point before we downsample.
    if signal.dtype.kind == 'i':
        scale = float(np.iinfo(signal.dtype).max)
        signal = signal.astype(np.float32) / scale
    elif signal.dtype.kind == 'u':
        scale = float(np.iinfo(signal.dtype).max)
        signal = signal.astype(np.float32) * 2.0 / scale - 1.0
    elif signal.dtype != np.float32:
        signal = signal.astype(np.float32)
    # Resample down to no more than 22050 Hz.
    if samplerate > 22050:
        signal = resample(signal, samplerate, 22050)
        samplerate = 22050
    return signal, samplerate

