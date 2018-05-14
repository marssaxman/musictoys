# Feature extraction example
import numpy as np
import librosa
import sys
import os

path = sys.argv[1]
y, sr = librosa.load(path)
D = librosa.stft(y)
harm_margin = 2.0
perc_margin = 2.0
H, P = librosa.decompose.hpss(D, margin=4.0)
R = D - (H+P)
y_harm = librosa.core.istft(H)
y_perc = librosa.core.istft(P)
y_resi = librosa.core.istft(R)

basepath = os.path.splitext(path)[0]
librosa.output.write_wav(basepath + "_perc.wav", y_perc, sr)
librosa.output.write_wav(basepath + "_harm.wav", y_harm, sr)
librosa.output.write_wav(basepath + "_resi.wav", y_resi, sr)

