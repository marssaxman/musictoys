#!/usr/bin/env python

import numpy
import librosa
import sys, os

# Load the target audio file, then split into left and right.
path = sys.argv[1]
signal, samplerate = librosa.load(path, sr=44100, mono=False)
left = signal[0, :]
right = signal[1, :]

# Divide left and right into harmonic and percussive components.
harmonic_left, percussive_left = librosa.effects.hpss(left)
harmonic_right, percussive_right = librosa.effects.hpss(right)

# Rejoin each left and right channel
harmonic = numpy.vstack((harmonic_left, harmonic_right))
percussive = numpy.vstack((percussive_left, percussive_right))

# Write each component back out as a separate audio file
basepath = os.path.splitext(path)[0]
librosa.output.write_wav(basepath + "_perc.wav", percussive, samplerate)
librosa.output.write_wav(basepath + "_harm.wav", harmonic, samplerate)


