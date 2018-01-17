# Extract representative thumbnails from an audio signal.
import numpy
import scipy
import scipy.signal


_eps = 0.00000001


def _ZCR(frame):
    count = len(frame)
    countZ = numpy.sum(numpy.abs(numpy.diff(numpy.sign(frame)))) / 2
    return (numpy.float64(countZ) / numpy.float64(count-1.0))


def _Energy(frame):
	return numpy.sum(frame ** 2) / numpy.float64(len(frame))


def _EnergyEntropy(frame, numOfShortBlocks=10):
	Eol = numpy.sum(frame ** 2)    # total frame energy
	L = len(frame)
	subWinLength = int(numpy.floor(L / numOfShortBlocks))
	if L != subWinLength * numOfShortBlocks:
		frame = frame[0:subWinLength * numOfShortBlocks]
	# subWindows is of size [numOfShortBlocks x L]
	subWindows = frame.reshape(subWinLength, numOfShortBlocks, order='F').copy()
	# Compute normalized sub-frame energies:
	s = numpy.sum(subWindows ** 2, axis=0) / (Eol + _eps)
	# Compute entropy of the normalized sub-frame energies:
	Entropy = -numpy.sum(s * numpy.log2(s + _eps))
	return Entropy


def _SpectralCentroidAndSpread(X, sample_rate):
	ind = (numpy.arange(1, len(X) + 1)) * (sample_rate/(2.0 * len(X)))
	Xt = X.copy()
	Xt = Xt / Xt.max()
	NUM = numpy.sum(ind * Xt)
	DEN = numpy.sum(Xt) + _eps
	centroid = (NUM / DEN)
	spread = numpy.sqrt(numpy.sum(((ind - centroid) ** 2) * Xt) / DEN)
	# Normalize:
	centroid /= (sample_rate / 2.0)
	spread /= (sample_rate / 2.0)
	return (centroid, spread)


def _SpectralEntropy(X, numOfShortBlocks=10):
	L = len(X)                         # number of frame samples
	Eol = numpy.sum(X ** 2)            # total spectral energy
	subWinLength = int(numpy.floor(L / numOfShortBlocks))   # length of sub-frame
	if L != subWinLength * numOfShortBlocks:
		X = X[0:subWinLength * numOfShortBlocks]
	subWindows = X.reshape(subWinLength, numOfShortBlocks, order='F').copy()  # define sub-frames (using matrix reshape)
	s = numpy.sum(subWindows ** 2, axis=0) / (Eol + _eps)                      # compute spectral sub-energies
	En = -numpy.sum(s*numpy.log2(s + _eps))                                    # compute spectral entropy
	return En


def _SpectralFlux(X, Xprev):
	# compute the spectral flux as the sum of square distances:
	sumX = numpy.sum(X + _eps)
	sumPrevX = numpy.sum(Xprev + _eps)
	F = numpy.sum((X / sumX - Xprev/sumPrevX) ** 2)
	return F


def _SpectralRollOff(X, c):
	totalEnergy = numpy.sum(X ** 2)
	fftLength = len(X)
	Thres = c*totalEnergy
	# Ffind the spectral rolloff as the frequency position where the respective spectral energy is equal to c*totalEnergy
	CumSum = numpy.cumsum(X ** 2) + _eps
	[a, ] = numpy.nonzero(CumSum > Thres)
	mC = numpy.float64(a[0]) / (float(fftLength)) if len(a) > 0 else 0.0
	return (mC)


def _Harmonic(frame, sample_rate):
	M = numpy.round(0.016 * sample_rate) - 1
	R = numpy.correlate(frame, frame, mode='full')
	g = R[len(frame)-1]
	R = R[len(frame):-1]
	# estimate m0 (as the first zero crossing of R)
	[a, ] = numpy.nonzero(numpy.diff(numpy.sign(R)))
	if len(a) == 0:
		m0 = len(R)-1
	else:
		m0 = a[0]
	if M > len(R):
		M = len(R) - 1
	Gamma = numpy.zeros((M), dtype=numpy.float64)
	CSum = numpy.cumsum(frame ** 2)
	Gamma[m0:M] = R[m0:M] / (numpy.sqrt((g * CSum[M:m0:-1])) + _eps)
	ZCR = _ZCR(Gamma)
	if ZCR > 0.15:
		HR = 0.0
		f0 = 0.0
	else:
		if len(Gamma) == 0:
			HR = 1.0
			blag = 0.0
			Gamma = numpy.zeros((M), dtype=numpy.float64)
		else:
			HR = numpy.max(Gamma)
			blag = numpy.argmax(Gamma)
		# Get fundamental frequency:
		f0 = sample_rate / (blag + _eps)
		if f0 > 5000:
			f0 = 0.0
		if HR < 0.1:
			f0 = 0.0
	return (HR, f0)


def _mfccInitFilterBanks(sample_rate, nfft):
	# filter bank params:
	lowfreq = 133.33
	linsc = 200/3.
	logsc = 1.0711703
	numLinFiltTotal = 13
	numLogFilt = 27
	if sample_rate < 8000:
		nlogfil = 5
	# Total number of filters
	nFiltTotal = numLinFiltTotal + numLogFilt
	# Compute frequency points of the triangle:
	freqs = numpy.zeros(nFiltTotal+2)
	freqs[:numLinFiltTotal] = lowfreq + numpy.arange(numLinFiltTotal) * linsc
	freqs[numLinFiltTotal:] = freqs[numLinFiltTotal-1] * logsc ** numpy.arange(1, numLogFilt + 3)
	heights = 2./(freqs[2:] - freqs[0:-2])
	# Compute filterbank coeff (in fft domain, in bins)
	fbank = numpy.zeros((nFiltTotal, nfft))
	nfreqs = numpy.arange(nfft) / (1. * nfft) * sample_rate
	for i in range(nFiltTotal):
		lowTrFreq = freqs[i]
		cenTrFreq = freqs[i+1]
		highTrFreq = freqs[i+2]
		lid = numpy.arange(numpy.floor(lowTrFreq * nfft / sample_rate) + 1, numpy.floor(cenTrFreq * nfft / sample_rate) + 1, dtype=numpy.int)
		lslope = heights[i] / (cenTrFreq - lowTrFreq)
		rid = numpy.arange(numpy.floor(cenTrFreq * nfft / sample_rate) + 1, numpy.floor(highTrFreq * nfft / sample_rate) + 1, dtype=numpy.int)
		rslope = heights[i] / (highTrFreq - cenTrFreq)
		fbank[i][lid] = lslope * (nfreqs[lid] - lowTrFreq)
		fbank[i][rid] = rslope * (highTrFreq - nfreqs[rid])
	return fbank, freqs


def _MFCC(X, fbank, nceps):
	from scipy.fftpack.realtransforms import dct
	mspec = numpy.log10(numpy.dot(X, fbank.T)+_eps)
	ceps = dct(mspec, type=2, norm='ortho', axis=-1)[:nceps]
	return ceps


def _ChromaFeaturesInit(nfft, sample_rate):
	freqs = numpy.array([((f + 1) * sample_rate) / (2 * nfft) for f in range(nfft)])
	Cp = 27.50
	nChroma = numpy.round(12.0 * numpy.log2(freqs / Cp)).astype(int)
	nFreqsPerChroma = numpy.zeros((nChroma.shape[0], ))
	uChroma = numpy.unique(nChroma)
	for u in uChroma:
		idx = numpy.nonzero(nChroma == u)
		nFreqsPerChroma[idx] = idx[0].shape
	return nChroma, nFreqsPerChroma


def _ChromaFeatures(X, sample_rate, nChroma, nFreqsPerChroma):
	spec = X**2
	if nChroma.max() < nChroma.shape[0]:
		C = numpy.zeros((nChroma.shape[0],))
		C[nChroma] = spec
		C /= nFreqsPerChroma[nChroma]
	else:
		I = numpy.nonzero(nChroma>nChroma.shape[0])[0][0]
		C = numpy.zeros((nChroma.shape[0],))
		C[nChroma[0:I-1]] = spec
		C /= nFreqsPerChroma
	finalC = numpy.zeros((12, 1))
	newD = int(numpy.ceil(C.shape[0] / 12.0) * 12)
	C2 = numpy.zeros((newD, ))
	C2[0:C.shape[0]] = C
	C2 = C2.reshape(C2.shape[0]/12, 12)
	finalC = numpy.matrix(numpy.sum(C2, axis=0)).T
	finalC /= spec.sum()
	return finalC


def _featureExtraction(signal, sample_rate, window, step):
	from scipy.fftpack import fft
	Win = int(window * sample_rate)
	Step = int(step * sample_rate)
	# Signal normalization
	signal = numpy.double(signal)
	signal = signal / (2.0 ** 15)
	DC = signal.mean()
	MAX = (numpy.abs(signal)).max()
	signal = (signal - DC) / (MAX + 0.0000000001)
	N = len(signal)                                # total number of samples
	curPos = 0
	countFrames = 0
	nFFT = Win / 2
	# compute the triangular filter banks used in the mfcc calculation
	[fbank, freqs] = _mfccInitFilterBanks(sample_rate, nFFT)
	nChroma, nFreqsPerChroma = _ChromaFeaturesInit(nFFT, sample_rate)
	numOfTimeSpectralFeatures = 8
	numOfHarmonicFeatures = 0
	nceps = 13
	numOfChromaFeatures = 13
	totalNumOfFeatures = numOfTimeSpectralFeatures + nceps + numOfHarmonicFeatures + numOfChromaFeatures
 	stFeatures = []
	while (curPos + Win - 1 < N):                        # for each short-term window until the end of signal
		countFrames += 1
		x = signal[curPos:curPos+Win]                    # get current window
		curPos = curPos + Step                           # update window position
		X = abs(fft(x))                                  # get fft magnitude
		X = X[0:nFFT]                                    # normalize fft
		X = X / len(X)
		if countFrames == 1:
			Xprev = X.copy()                             # keep previous fft mag (used in spectral flux)
		curFV = numpy.zeros((totalNumOfFeatures, 1))
		curFV[0] = _ZCR(x)                              # zero crossing rate
		curFV[1] = _Energy(x)                           # short-term energy
		curFV[2] = _EnergyEntropy(x)                    # short-term entropy of energy
		[curFV[3], curFV[4]] = _SpectralCentroidAndSpread(X, sample_rate)    # spectral centroid and spread
		curFV[5] = _SpectralEntropy(X)                  # spectral entropy
		curFV[6] = _SpectralFlux(X, Xprev)              # spectral flux
		curFV[7] = _SpectralRollOff(X, 0.90)        # spectral rolloff
		curFV[numOfTimeSpectralFeatures:numOfTimeSpectralFeatures+nceps, 0] = _MFCC(X, fbank, nceps).copy()    # MFCCs
		chromaF = _ChromaFeatures(X, sample_rate, nChroma, nFreqsPerChroma)
		curFV[numOfTimeSpectralFeatures + nceps: numOfTimeSpectralFeatures + nceps + numOfChromaFeatures - 1] = chromaF
		curFV[numOfTimeSpectralFeatures + nceps + numOfChromaFeatures - 1] = chromaF.std()
		stFeatures.append(curFV)
		Xprev = X.copy()
	stFeatures = numpy.concatenate(stFeatures, 1)
	return stFeatures


# 0: zero-crossing rate
# 1: energy
# 2: energy entropy
# 3: spectral centroid
# 4: spectral spread
# 5: spectral entropy
# 6: spectral flux
# 7: spectral rolloff
# 8..21: MFCC bands
# 22..35: chroma bands 


def _normalizeFeatures(features):
	X = numpy.array([])
	for count, f in enumerate(features):
		if f.shape[0] > 0:
			if count == 0:
				X = f
			else:
				X = numpy.vstack((X, f))
			count += 1
	MEAN = numpy.mean(X, axis=0)
	STD = numpy.std(X, axis=0)
	featuresNorm = []
	for f in features:
		ft = f.copy()
		for nSamples in range(f.shape[0]):
			ft[nSamples, :] = (ft[nSamples, :] - MEAN) / STD
		featuresNorm.append(ft)
	return (featuresNorm, MEAN, STD)


def _selfSimilarityMatrix(featureVectors):
	from scipy.spatial import distance
	[nDims, nVectors] = featureVectors.shape
	[featureVectors2, MEAN, STD] = _normalizeFeatures([featureVectors.T])
	featureVectors2 = featureVectors2[0].T
	return 1.0 - distance.squareform(distance.pdist(featureVectors2.T, 'cosine'))


def find_pair(signal, sample_rate, size=10.0, window=1.0, step=0.5):
	# Compute the features we will use to measure similarity.
	features = _featureExtraction(signal, sample_rate, window, step)
	# Create the diagonal matrix which lets us find self-similar regions.
	similarity = _selfSimilarityMatrix(features)

	# Apply a moving filter.
	M =int(round(size / step))
	B = numpy.eye(M, M)
	similarity = scipy.signal.convolve2d(similarity, B, 'valid')
	shape = similarity.shape

	# Remove main diagonal elements as a post-processing step.
	minVal = numpy.min(similarity)
	for i in range(shape[0]):
		for j in range(shape[1]):
			if abs(i-j) < 5.0 / step or i > j:
				similarity[i,j] = minVal

	# find the maximum position
	Limit1 = 0
	Limit2 = 1
	similarity[0:int(Limit1*shape[0]), :] = minVal
	similarity[:, 0:int(Limit1*shape[0])] = minVal
	similarity[int(Limit2*shape[0])::, :] = minVal
	similarity[:, int(Limit2*shape[0])::] = minVal

	maxVal = numpy.max(similarity)
	[I, J] = numpy.unravel_index(similarity.argmax(), shape)
	i1, i2 = I, I
	j1, j2 = J, J

	while i2-i1 < M:
		if i1 <= 0 or j1 <= 0 or i2 >= shape[0]-2 or j2 >= shape[1]-2:
			break
		if similarity[i1-1, j1-1] > similarity[i2+1,j2+1]:
			i1 -= 1
			j1 -= 1
		else:
			i2 += 1
			j2 += 1
	return ((step*i1, step*i2), (step*j1, step*j2))

