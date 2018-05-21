"""resample converts audio samples from one sampling rate to another.

This module contains no actual resampling code; it simply tries a series of
options in descending order of preference, using the best one available.
"""

import numpy as np
import signal


@signal.processor
def resample(clip, new_rate):
    # this would be a good place to make sure that the sampling rate requested
    # is reasonable.
    data = _engine(clip, clip.sample_rate, new_rate)
    return signal.Clip(data, new_rate)


def _scikits(data, old_rate, new_rate):
    ratio = float(new_rate) / float(old_rate)
    # samples must run along axis 0 and there is no option to change
    # that, so we'll have to transpose our array in each direction.
    return scikits.samplerate.resample(data.T, ratio).T


def _samplerate(data, old_rate, new_rate):
    ratio = float(new_rate) / float(old_rate)
    # samplerate expects data to be in [samples, channels] order, with no
    # option to specify the axis.
    return samplerate.resample(data.T, ratio).T


def _resampy(data, old_rate, new_rate):
    # resampy assumes [channels, samples] unless you tell it otherwise
    return resampy.resample(data, old_rate, new_rate)


def _nnresample(data, old_rate, new_rate):
    # nnresample copies scipy.signal's API, so it assumes time is axis 0
    # unless you specify otherwise
    return nnresample.resample(data, new_rate, old_rate, axis=-1)


def _scipy_signal(data, old_rate, new_rate):
    ratio = float(new_rate) / float(old_rate)
    new_length = int(np.ceil(data.shape[-1] * ratio))
    # scipy.signal assumes [samples, channels] unless you specify axis
    return scipy.signal.resample(data, new_length, axis=-1)


def _audioop(data, old_rate, new_rate):
    nchannels = data.shape[0] if data.ndim > 1 else 1
    orig_type = data.dtype
    if data.dtype.kind == "f":
        # ratecv only works on integer arrays, so we'll have to convert floats.
        data = (data * np.iinfo(np.int16).max).astype(np.int16)
    width = data.dtype.itemsize
    buf, _ = audioop.ratecv(data, width, nchannels, old_rate, new_rate, None)
    out = np.frombuffer(buf, dtype=data.dtype)
    if orig_type.kind == "f":
        out = out.astype(orig_type) / float(np.iinfo(np.int16).max)
    return out


# On initialization, try different options until we find a resampling library.
_engine = None

# scikits.samplerate is fast and good, but it is based on libsamplerate
# so it won't load if the library is not installed; it also hasn't been
# updated for python 3, or in a while at all.
if not _engine:
    try:
        import scikits.samplerate
        _engine = _scikits
    except ImportError:
        pass

# samplerate is a separate fork of scikits.samplerate, also based on
# libsamplerate, with the same interface.
if not _engine:
    try:
        import samplerate
        _engine = _samplerate
    except ImportError:
        pass

# resampy is fast and good.
if not _engine:
    try:
        import resampy
        _engine = _resampy
    except ImportError:
        pass

# nnresample is a better wrapper around scipy.signal.resample
if not _engine:
    try:
        import nnresample
        _engine = _nnresample
    except ImportError:
        pass

# scipy.signal.resample works but the audio quality is poor
if not _engine:
    try:
        import scipy.signal
        _engine = _scipy_signal
    except ImportError:
        pass

# audioop.ratecv isn't good, but it's built in.
if not _engine:
    import audioop
    _engine = _audioop
