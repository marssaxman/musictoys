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

print "Estimated tempo: " + str(tempo)

# Extract the percussive component of the signal and detect onsets, with
# backtracking toward the most recent minimal-energy moment. We'll use this to
# compute tempo-synced beat slice windows.
percussive = librosa.effects.percussive(y=mono)
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
median_backtrack = numpy.median(beats - pred_onsets)
beat_slices = beats - median_backtrack

# For each beat, separate the initial percussive event from the remainder.
# A single beat may include multiple percussive events, but we only care about
# the event most immediately associated with the beat itself.
succ_onsets = onsets[numpy.searchsorted(onsets, beats)]
beat_perc_events = zip(beat_slices, succ_onsets)

fd = open(basepath + "_beats.txt", 'w')
for begin, end in beat_perc_events:
	beginstamp = str(begin / float(samplerate))
	endstamp = str(end / float(samplerate))
	fd.write(beginstamp + "\t" + endstamp + "\n")
fd.close()

