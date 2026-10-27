from scipy import ndimage
from scipy import signal
import copy
import numpy as np

# data must 2d array with rows of [x, y, z]
def run_despike_on_data(data, threshold):

    medians = ndimage.median_filter(data, size=(7, 1), mode='mirror')

    bad_frames = np.abs(data - medians) > threshold

    bad_frames = ndimage.binary_dilation(bad_frames, structure=np.ones((3,1)), iterations=1)
    idx = np.arange(len(data))
    good_frames = ~bad_frames

    despiked_data = copy.deepcopy(data)
    for axis in range(3):
        despiked_data[bad_frames[:, axis], axis] = np.interp(idx[bad_frames[:, axis]], idx[good_frames[:, axis]], despiked_data[good_frames[:, axis], axis])

    return despiked_data


# data must 2d array with rows of [x, y, z]
def run_zero_phase_on_data(data, sampling_freq=30, cutoff_freq=4, order=4):

    butterworth_filter = signal.butter(N=order, Wn=cutoff_freq, fs=sampling_freq, output='sos', btype='lowpass')

    return signal.sosfiltfilt(butterworth_filter, data, axis=0)

# data must 2d array with rows of [x, y, z]
def data_clean(data):
    despiked_data = run_despike_on_data(data, 0.03)

    zero_phased_data = run_zero_phase_on_data(despiked_data)

    return zero_phased_data