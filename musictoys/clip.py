import numpy as np


class Clip(np.ndarray):
    """Array of audio samples at some known sample rate."""
    __array_priority__ = 1.0

    def __new__(cls, samples, sample_rate):
        obj = np.asarray(samples).view(cls)
        obj.sample_rate = sample_rate
        return obj

    def __array_finalize__(self, obj):
        if obj is None: return
        self.sample_rate = getattr(obj, 'sample_rate', None)

    def __array_wrap__(self, obj, context=None):
        return super(Clip, self).__array_wrap__(self, obj, context)

