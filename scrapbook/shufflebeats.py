# Feature extraction example
import numpy as np
import librosa
import sys

# Load the example clip
path = sys.argv[1]
y, sr = librosa.load(path)

#y_harmonic, y_percussive = librosa.effects.hpss(y)


_, beat_times = librosa.beat.beat_track(
	y=y, sr=sr, start_bpm=138.0, hop_length=256, units='time')
with open(path+".txt", 'w+') as labels:
	for time in beat_times:
		labels.write(str(time) + '\n')

_, beat_samples = librosa.beat.beat_track(
	y=y, sr=sr, start_bpm=138.0, hop_length=256, units='samples')

print "beat_samples = " + repr(beat_samples)

beat_samples = np.concatenate([[0], beat_samples, [len(y)]])
print "beat_samples = " + repr(beat_samples)

intervals = librosa.util.frame(beat_samples, frame_length=2,
                                hop_length=1).T

print "intervals = " + repr(intervals)


y_out = librosa.effects.remix(y, intervals[::-1])

librosa.output.write_wav("reverse_" + path, y_out, sr)

