# Copied from https://github.com/sankalpg/Infinite_Jukebox_Essentia

import sys, csv, os
import numpy as np
import matplotlib.pyplot as plt
import essentia as es
import essentia.standard as ess
import time
from scipy import ndimage
import scipy.stats as st
from scipy.ndimage import filters
import scipy.ndimage.filters as fi


def gkern(kernlen=21, nsig=3):
    """Returns a 2D Gaussian kernel array."""

    # create nxn zeros
    inp = np.zeros((kernlen, kernlen))
    # set element at the middle to one, a dirac delta
    inp[kernlen//2, kernlen//2] = 1
    # gaussian-smooth the dirac, resulting in a gaussian filter mask
    return fi.gaussian_filter(inp, nsig)



eps = np.finfo(np.float).eps

def peak_pick(inp, thsld=None):
    """
    pick all local maximas
    """
    diff1 = np.diff(inp[:-1])
    diff2 = np.diff(inp[1:])
    if thsld.any():
        pp = []
        for ii in range(inp.size-2):
            if ((diff1[ii]*diff2[ii]<0) & (diff1[ii] >0))& (inp[1+ii]>=thsld[1+ii]):
                pp.append(ii)
        pp = np.array(pp)
    else:
        pp = np.where((diff1*diff2<0) & (diff1 >0))[0] +1
    return pp
    


def peaks_pick_nc(n_curve, medlen=16):
    
    offset = np.mean(n_curve)/20.0
    n_curve = filters.gaussian_filter1d(n_curve, sigma=2)
    thsld = filters.median_filter(n_curve, size=medlen) + offset
    peaks = peak_pick(n_curve, thsld)
    
    return peaks


def eucDist(a, b):
	return np.sum(np.power(a-b, 2))

filename = 'KajraRe.mp3'

def get_beat_synced_HPCPS(audio,fs, hop_size=256, frame_size=2048, zp_factor=1, window='hann', perform_norm=True):
    """
    This function computes beat averaged HPCPs for the entire audio signal.
    Input:
    Output:
    """

    #TODO: params are given in sampels, take then in seconds and based on fs do a computation.
    # For now check if the audio is 44100 else exit
    #fs = 44100          #temp, should be read from the mp3 file (essentia had some problems reading fs)
    
    #init essentia funcs
    WINDOW = ess.Windowing(type=window, zeroPadding=frame_size*zp_factor) 
    SPECTRUM = ess.Spectrum(size=frame_size*(1+zp_factor))
    SPECPEAKS = ess.SpectralPeaks(minFrequency=100, maxFrequency=8000, maxPeaks=100, sampleRate=fs, 
                              magnitudeThreshold= -80, orderBy="magnitude")
    HPCP = ess.HPCP()

    #reading audio file
    #audio = ess.MonoLoader(filename = filename, sampleRate = fs)()

    #equal loudness filtering
    audioEL = ess.EqualLoudness()(audio)

    hpcp_arr = []
    frmCnt = 0
    for frame in ess.FrameGenerator(audioEL, frameSize=frame_size, hopSize=hop_size):
        frame = WINDOW(frame)
        mXFrame = SPECTRUM(frame)
        mXFrameDB = 20*np.log10(mXFrame+eps)
        pFreq, pMags = SPECPEAKS(mXFrameDB)
        pMags = np.power(10, pMags/20.0)
        hpcp_arr.append(HPCP(pFreq, pMags).tolist())

    #justing converting it into a nice np array
    hpcp_arr = np.array(hpcp_arr)

    #doing beat detecton
    beats, confs = ess.BeatTrackerMultiFeature()(audioEL)    

    #lets get frame indices corresponding (nearest ones) to the beat locations
    time_stamps = np.arange(hpcp_arr.shape[0])*float(hop_size)/float(fs)
    frame_ind_beats = []
    for beat in beats:
        frame_ind_beats.append(np.argmin(abs(time_stamps-beat)))

    #Now that we know frame indices lets avg out HPCPs within a beat duration
    agg_hpcps = []
    for ii, b in enumerate(frame_ind_beats[:-1]):   # no. of segments = no. of boundaries -1 
        temp = np.mean(hpcp_arr[frame_ind_beats[ii]:frame_ind_beats[ii+1],:],axis=0)
        s = np.max(temp)
        if s!=0 and perform_norm:   # first condition to just avoid div by zero
            temp = temp/s
        else:
            temp = temp        
        agg_hpcps.append(temp)

    agg_hpcps = np.array(agg_hpcps)
    return agg_hpcps, beats

def compute_similarity_matrix(arr1, arr2):
    """
    This function computes similarity matrix given two arrays
    arr1: we expect the features to be across column and frames to be in rows
    """
    #creating the similarity matrix from arr1 and arr2
    sim_mtx = np.zeros((arr1.shape[0], arr2.shape[0]))
    for ii in range(arr1.shape[0]):
        for jj in range(arr2.shape[0]):
            sim_mtx[ii,jj] = eucDist(arr1[ii,:], arr2[jj,:])
            #sim_mtx[jj,ii] = sim_mtx[ii,jj] #its a symmetric matrix

    return sim_mtx

def get_avg_beat_locs(beats):

    beat_diffs = np.diff(beats)
    bd_sorted = np.sort(beat_diffs)
    n_beats = bd_sorted.size
    mean_beat_dur = np.mean(bd_sorted[0.1*n_beats:0.9*n_beats])    #ignoring extreme values makes it more robust

    return mean_beat_dur

def load_diag_filt_kernel(ksize=5):
    #TODO: generate the kernel programatically, right now its hard coded!!
    kernel = np.array([[1,0,0,0,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0],[0,0,0,0,1] ])
    #kernel = np.array([[1,-.25,-.25,-.25,-.25],[-.25,1,-.25,-.25,-.25],[-.25,-.25,1,-.25,-.25],[-.25,-.25,-.25,1,-.25],[-.25,-.25,-.25,-.25,1] ])

    return kernel

def filter_matrix(mtx, kernel):
    """
    This function just performs a 2 dimensions convolution (filtering), very often done in image processing
    """
    mtx_filt = ndimage.convolve(mtx,kernel)

    return mtx_filt

def gen_lag_mtx(mtx):
    """
    Given a similarity matrix this function creates a time-lag matrix, which is essentially similarity matrix rotated by 45 degrees
    """

    mtx_lag = np.max(mtx)*np.ones(mtx.shape)
    for ii in range(mtx.shape[0]):
        for jj in range(ii, mtx.shape[1]):
            mtx_lag[ii, jj-ii] = mtx[ii,jj]

    return mtx_lag

def load_checkerboard_kernel(kernlen):
    """
    Given a kernel length this function computes a gaussian checker board function.
    The standard deviation of the gaussian is considerd as the len/4 of the kernel
    """
    if kernlen%2==1:    #forcing it to be odd
        kernlen+=1
        
    sigma = kernlen/4.0 #sigma of the gaussian
    g = gkern(kernlen, sigma)
    
    ckern = np.ones((kernlen, kernlen))
    lenb2 = kernlen/2
    for ii in np.arange(lenb2):
        ckern[ii,:lenb2]*=-1
        ckern[kernlen-(ii+1),kernlen-lenb2:]*=-1
    
    return ckern*g


def compute_jump_points(mtx_lag, npoints):
    """
    This function given a time-lag matrix (lag in columns) and novelty points compute jump points (time stamp pairs)
    """
    nn = [] #strongest repetition lag value, be careful to fold it
    mm = [] # the mean distance of the chunk at each lag values in nn
    mtx_lag[:,:4] = np.max(mtx_lag) #avoiding any very short delay repetitions, why 4 samples? arbit choice but going to work!!
    for ii in np.arange(npoints.size-1):
        mtx_slice = np.mean(mtx_lag[npoints[ii]:npoints[ii+1],:], axis=0)
        mm.append(np.min(mtx_slice))
        nn.append(np.argmin(mtx_slice))
    
    nn = np.array(nn)
    mm = np.array(mm)
    return nn, mm

def dump_transition_audio(output_dir, beat_locs, audio, extra_audio, lags, npoints):

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for ii, n in enumerate(lags):
        t1 = beats[npoints[ii]]
        p1 = int(t1*fs)
        t2 = beats[npoints[ii]+n]
        p2 = int(t2*fs)
        audio_out_prev = np.hstack((audio[max(p1-extra_audio,0):p1], audio[p1:min(p1+extra_audio, len(audio))]))
        audio_out_mix = np.hstack((audio[max(p1-extra_audio,0):p1], audio[p2:min(p2+extra_audio, len(audio))]))
        audio_out_post = np.hstack((audio[max(p2-extra_audio,0):p2], audio[p2:min(p2+extra_audio, len(audio))]))
        ess.MonoWriter(filename = os.path.join(output_dir, str(ii)+'_prev.mp3'), format="mp3")(audio_out_prev)
        ess.MonoWriter(filename = os.path.join(output_dir, str(ii)+'_mix.mp3'), format="mp3")(audio_out_mix)
        ess.MonoWriter(filename = os.path.join(output_dir, str(ii)+'_post.mp3'), format="mp3")(audio_out_post)





"""
plt.imshow(mtx_lag)
plt.hold(True)
for ii, p in enumerate(pp[:-1]):
    plt.plot([0,mtx_filt.shape[1]], [p, p])
    #plt.scatter(nn[ii][0], p, '*')
    
plt.show()
"""

if __name__ == "__main__":

    filename = sys.argv[1]
    if int(sys.argv[2]) == 0:
        load_stuff = True   #if false it computes all the stuff again
    else:
        load_stuff = False   #if false it computes all the stuff again
    
    output_dir = os.path.dirname(filename)

    

    fs = 44100  #read it dynamically
    print "Loading audio..."
    t1 = time.time()
    audio = ess.MonoLoader(filename = filename, sampleRate = fs)()
    print "time taken = %f"%(time.time()-t1)

    #Computing HPCPS (beat averaged)
    print "Computing beat averaged HPCPS..."
    t1 = time.time()
    if load_stuff:
        hpcps = np.load(os.path.join(output_dir, 'hpcps.npy'))
        beats = np.load(os.path.join(output_dir, 'beats.npy'))
    else:
        hpcps, beats = get_beat_synced_HPCPS(audio, fs, hop_size=256, frame_size=2048, zp_factor=1, window='hann', perform_norm=True)
        np.save(os.path.join(output_dir, 'hpcps.npy'), hpcps)
        np.save(os.path.join(output_dir, 'beats.npy'), beats)
    
    mean_beat_dur = get_avg_beat_locs(beats)
    print "Mean beat duration for this file: %f"%mean_beat_dur
    print "time taken = %f"%(time.time()-t1)

    #computing similarity matrix
    print "Computing similarity matrix..."
    t1 = time.time()
    if load_stuff:
        sim_mtx = np.load(os.path.join(output_dir, 'sim_mtx.npy'))
    else:
        sim_mtx = compute_similarity_matrix(hpcps, hpcps)
        np.save(os.path.join(output_dir, 'sim_mtx.npy'), sim_mtx)
    print "time taken = %f"%(time.time()-t1)

    #performing some diagonal smoothening of this matrix
    print "Performing diagonal smoothening..."
    t1 = time.time()
    kernel_size = 5 #TODO compute it dynamically!!
    kernel_diag_filt = load_diag_filt_kernel(kernel_size)
    if load_stuff:
        sim_mtx_smth = np.load(os.path.join(output_dir, 'sim_mtx_smth.npy'))
    else:
        sim_mtx_smth = filter_matrix(sim_mtx, kernel_diag_filt)
        np.save(os.path.join(output_dir, 'sim_mtx_smth.npy'), sim_mtx_smth)
    print "time taken = %f"%(time.time()-t1)

    #generating a checkerboard kernel for novelty point detection
    print "Loading checkboard kernel..."
    t1 = time.time()
    kernel_size = int(4/mean_beat_dur)
    kernel_cb = load_checkerboard_kernel(kernel_size)
    print "time taken = %f"%(time.time()-t1)

    # performing novelty curve estimation
    print "Performing novelty detection..."
    t1 = time.time()
    mtx_cb_filt = filter_matrix(sim_mtx, kernel_cb)
    if load_stuff:
        novelty_curve = np.load(os.path.join(output_dir, 'novelty_curve.npy'))
    else:
        novelty_curve = np.diag(mtx_cb_filt)
        np.save(os.path.join(output_dir, 'novelty_curve.npy'), novelty_curve)
    print "time taken = %f"%(time.time()-t1)

    #picking peaks in the novelty curve doing a smart thresholding (important change points)
    print "Picking peaks of novelty curve..."
    t1 = time.time()
    if load_stuff:
        npoints = np.load(os.path.join(output_dir, 'npoints.npy'))
    else:
        npoints = peaks_pick_nc(novelty_curve)
        np.save(os.path.join(output_dir, 'npoints.npy'), npoints)
    print "time taken = %f"%(time.time()-t1)

    #computing lag_matrix
    print "Generating lag matrix..."
    t1 = time.time()
    if load_stuff:
        mtx_lag = np.load(os.path.join(output_dir, 'mtx_lag.npy'))
    else:
        mtx_lag = gen_lag_mtx(sim_mtx_smth)
        np.save(os.path.join(output_dir, 'mtx_lag.npy'), mtx_lag)
    print "time taken = %f"%(time.time()-t1)

    #computing jump points
    print "Computing possible lags corresponding to jump points"
    t1 = time.time()
    lags, dists = compute_jump_points(mtx_lag, npoints)
    print "time taken = %f"%(time.time()-t1)

    print npoints, lags, dists

    #dumping audios
    print "Dumping transition audio..."
    t1 = time.time()
    dump_transition_audio(os.path.join(output_dir,'audio_clips'), beats, audio, 5*fs, lags, npoints)
    print "time taken = %f"%(time.time()-t1)















