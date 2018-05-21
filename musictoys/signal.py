import numpy as np
from spectrum import Spectrum


class Clip(np.ndarray):
    """Array of audio samples at some sample rate."""

    def __new__(cls, samples, sample_rate):
        obj = np.asarray(samples).view(cls)
        obj.sample_rate = sample_rate
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.sample_rate = getattr(obj, 'sample_rate', None)

    @property
    def num_channels(self):
        return self.shape[0] if self.ndim > 1 else 1

    @property
    def num_samples(self):
        return self.shape[-1]

    def rms(self):
        return np.sqrt(np.sum(self ** 2))

    def zcr(self):
        """Return the zero-crossing rate, relative to signal length."""
        # reduce each sample to its sign, then compute each difference
        diffs = np.diff(np.sign(self))
        # absolute value yields 1 for zero crossings, 0 for non-crossing
        crossings = np.float(np.sum(np.abs(diffs))) / 2.0
        # divide number of crossings by length of the clip
        return crossings / np.float(self.num_samples - 1.0)

    def frames(self, frame_size, step_size=None):
        # Generator which divides this clip into frames, which are views onto
        # the signal sample array.
        if self.num_samples == 0:
            return
        if step_size is None:
            step_size = frame_size
        assert frame_size > 0 and step_size > 0
        # The first frame will be centered on index zero. We will pad to the left
        # with zeros until the left edge of the window reaches the sample data.
        for i in range(-(frame_size/2), 0, step_size):
            frame = np.pad(self[:i+frame_size], (-i, 0), 'constant')
            yield Clip(frame, self.sample_rate)
        # Most frames will simply be non-copied views on the source array.
        for i in range(0, self.num_samples - frame_size, step_size):
            yield self[i:i+frame_size]
        # Trailing frames will be padded to the right with zeros, until the
        # center of the frame has reached or passed the end of the array.
        for i in range(i+step_size, i+frame_size/2, step_size):
            frame = np.pad(self[i:], (0, frame_size-i), 'constant')
            yield Clip(frame, self.sample_rate)


def processor(func):
    """Decorator which creates a signal object from a plain ndarray parameter.

    The function's first positional argument will be the signal object. If it
    is a plain ndarray, the kwargs must include 'sample_rate', and the ndarray
    will be passed along to the func as a Clip instance.

    This can be used to expose instance methods as generic functions.
    It can also be convenient for other analysis methods.
    """
    def wrapper(data, *args, **kwargs):
        if isinstance(data, Clip):
            return func(data, *args, **kwargs)
        else:
            clip = Clip(data, sample_rate=kwargs.pop('sample_rate'))
            return func(clip, *args, **kwargs)
    return wrapper


num_channels = processor(Clip.num_channels)
num_samples = processor(Clip.num_samples)
rms = processor(Clip.rms)
zcr = processor(Clip.zcr)
frames = processor(Clip.frames)
