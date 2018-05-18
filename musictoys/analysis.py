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


def zcr(frames):
    count = frames.shape[-1]
    # reduce each sample to its sign, then compute each difference
    diff = np.diff(np.sign(frames), axis=-1)
    # absolute value yields 1 for zero crossings, 0 for non-crossing
    crossings = np.sum(np.abs(diff), axis=-1) / 2.0
    return (np.float64(crossings) / np.float64(frames.shape[-1]-1.0))


def iterframes(signal, size, step=None):
    if len(signal) == 0:
        return
    assert size > 0
    if step is None:
        step = size
    else:
        assert step > 0
    # Yield a sequence of views onto the signal sample array.
    # The first frame will be centered on index zero. We will pad to the left
    # with zeros until the left edge of the window reaches the sample data.
    for start in range(-(size/2), 0, step):
        frame = np.zeros(size)
        stop = start + size
        frame[:start] = signal[:stop]
        yield frame
    # Most frames will simply be non-copied views on the source array.
    for start in range(0, len(signal)-size, step):
        stop = start + size
        yield signal[start:stop]
    # Trailing frames will be padded to the right with zeros, until the
    # center of the frame has reached or passed the end of the array.
    for start in range(start+step, start+size/2, step):
        frame = np.zeros(size)
        view = signal[start:]
        frame[:len(view)] = view
        yield frame


def split_frames(*args, **kwargs):
    return list(iterframes(*args, **kwargs))


def hamming(frame_size):
    # improved hamming window coefficients: the original version used
    # (0.54, 0.46).
    i = np.arange(N).astype(np.float)
    return 0.53836 - (0.46164 * np.cos(np.pi * 2.0 * i / (N-1)))


def spectrogram(frames):
    frames = np.asarray(frames)
    frame_size = frames.shape[-1]
    spectra = np.zeros((frames.shape[0], frame_size/2+1), dtype=np.complex64)
    mask = hamming(frame_size)
    for i, clip in enumerate(frames):
        spectra[i,:] = np.fft.rfft(clip * mask)[:]
    return spectra


def stft(signal, frame_size=2048, step_size=1024):
    return spectrogram(split_frames(signal, frame_size, step_size))
