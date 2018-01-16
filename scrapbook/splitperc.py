# Feature extraction example
import numpy as np
import librosa
import sys
import nussl
import os

# Load the example clip
path = sys.argv[1]
y, sr = librosa.load(path)

# Separate harmonics and percussives into two waveforms
y_harmonic, y_percussive = librosa.effects.hpss(y)

basepath = os.path.splitext(path)[0]
librosa.output.write_wav(basepath + "_perc.wav", y_percussive, sr)
librosa.output.write_wav(basepath + "_harm.wav", y_harmonic, sr)


