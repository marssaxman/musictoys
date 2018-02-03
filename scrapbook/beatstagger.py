#!/usr/bin/env python

import numpy
import librosa
import sys, os

path = sys.argv[1]
basepath = os.path.splitext(path)[0]
signal, samplerate = librosa.load(path, sr=44100, mono=False)
mono = librosa.to_mono(signal)

# Compute the onset envelope, then track beats and measure tempo.
onset_env = librosa.onset.onset_strength(y=mono, sr=samplerate)
tempo, beats = librosa.beat.beat_track(
		y=mono,
		sr=samplerate,
		onset_envelope=onset_env,
		units='samples'
)

# Get just the percussive component of the signal and use that for onset
# detection.
percussive = librosa.effects.percussive(y=mono)
onsets = librosa.onset.onset_detect(
		y=percussive,
		sr=samplerate,
		backtrack=True,
		units='samples'
)

# Match each beat time with the nearest percussive onset.
idx = librosa.util.match_events(beats, onsets, right=False)
better_beats = [onsets[match] for match in idx]

# Divide each beat into left and right, alternately.
left = numpy.zeros(mono.shape)
right = numpy.zeros(mono.shape)
for i in range(len(better_beats)-1):
	begindex = better_beats[i]
	endex = better_beats[i+1]
	if i % 2 == 0:
		left[begindex:endex] = mono[begindex:endex]
	else:
		right[begindex:endex] = mono[begindex:endex]


# Join the channels and write out as audio.
joined = numpy.vstack((left, right))
librosa.output.write_wav(basepath + "_stagger.wav", joined, samplerate)

