# Feature extraction example
import numpy as np
import librosa
import sys
import matplotlib.pyplot as plt
import math

def extract_max(pitches,magnitudes, shape):
    new_pitches = []
    new_magnitudes = []
    new_times = []
    for i in range(0, shape[1]):
        new_pitches.append(np.max(pitches[:,i]))
        new_magnitudes.append(np.max(magnitudes[:,i]))
    return (new_pitches,new_magnitudes)


# Load the example clip
path = sys.argv[1]
y, sr = librosa.load(path)

# Set the hop length; at 22050 Hz, 512 samples ~= 23ms
hop_length = 512

# Separate harmonics and percussives into two waveforms
y_harmonic, y_percussive = librosa.effects.hpss(y)


pitches, magnitudes = librosa.piptrack(y=y_harmonic, sr=sr)
bands = []
for i in xrange(np.shape(pitches)[1]):
	frame_pitches = pitches[:,i]
	frame_magnitudes = magnitudes[:,i]
	max_bin = np.argmax(frame_magnitudes)
	max_pitch = frame_pitches[max_bin]
	max_mag = frame_magnitudes[max_bin] if max_pitch < 330 else 0
	time = librosa.frames_to_time([i], sr)[0]
	bands.append((time, max_pitch, max_mag))

with open("notes_" + path + ".txt", 'w+') as out:
	for time, pitch, mag in bands:
		if mag > 0:
			out.write("%f\t%f\t%f\n" % (time, time, pitch))

y_really_harmonic = librosa.effects.harmonic(y, power=10.0)
librosa.output.write_wav("bass_" + path, y_really_harmonic, sr)


if 0:
	notes = []
	start_time = 0
	last_time = bands[-1][0]
	cur_pitches = 0
	cur_mags = []
	while len(bands):
		time, pitch, mag = bands.pop(0)
		if mag > 0:
			start_time = time if not start_time else 0
			cur_pitches += pitch
			cur_mags.append(mag)
		else:
			if start_time > 0:
				avg_pitch = cur_pitches / len(cur_mags)
				notes.append((start_time, time, avg_pitch, cur_mags))
				start_time = 0
				cur_pitches = 0
				cur_mags = []
	if start_time > 0:
		avg_pitch = cur_pitches / len(cur_mags)
		notes.append((start_time, last_time, avg_pitch, cur_mags))

	with open("notes_" + path + ".txt", 'w+') as out:
		for start, end, pitch, env in notes:
			out.write("%f\t%f\t%f\n" % (start, end, pitch))

#librosa.output.write_wav("perc_" + path, y_percussive, sr)
#librosa.output.write_wav("harm_" + path, y_harmonic, sr)

