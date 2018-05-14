#!/usr/bin/env python

import numpy
import librosa
import sys, os

path = sys.argv[1]
basepath = os.path.splitext(path)[0]
signal, samplerate = librosa.load(path, sr=44100, mono=False)
left = signal[0, :]
right = signal[1, :]
mono = librosa.to_mono(signal)

# Track beats and measure tempo.
tempo, beats = librosa.beat.beat_track(
		y=mono,
		sr=samplerate,
		units='samples'
)

# Extract the percussive component of the signal and detect onsets, with
# backtracking toward the most recent minimal-energy moment. We'll use this to
# compute tempo-synced beat slice windows.
harmonic, percussive = librosa.effects.hpss(y=mono)
onsets = librosa.onset.onset_detect(
		y=percussive,
		sr=samplerate,
		backtrack=True,
		units='samples'
)

# For each beat, find the percussive onset immediately preceding, then get the
# delta between the percussive onset time and the beat time. We'll backtrack
# each beat time by the median beat-onset delta to compute reasonable slice
# points for beat-synchronized percussion manipulation effects.
pred_onsets = onsets[numpy.searchsorted(onsets, beats)-1]
median_backtrack = int(numpy.median(beats - pred_onsets))
beat_slices = beats - median_backtrack

# For each beat, separate the initial percussive event from the remainder.
# A single beat may include multiple percussive events, but we only care about
# the event most immediately associated with the beat itself.
succ_onsets = onsets[numpy.searchsorted(onsets, beats)]
beat_perc_events = zip(beat_slices, beats, succ_onsets)

# Cut out all the beat-synchronized percussion events.
newperc = numpy.zeros(percussive.shape)
newperc[:] = percussive

for begin, mid, end in beat_perc_events:
	silence = numpy.zeros((end-begin))
	newperc[begin:end] = silence

# Write the harmonics and percussives out as a single stereo track.
joined = numpy.vstack((harmonic, newperc))
librosa.output.write_wav(basepath + "_unbeated.wav", joined, samplerate)

