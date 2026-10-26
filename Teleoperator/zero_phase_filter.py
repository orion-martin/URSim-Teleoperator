from scipy import ndimage
from scipy import signal
import copy
import numpy as np

# data must 2d array with rows of [x, y, z]
def run_despike_on_data(data, threshold):

    # corresponds to data, each element is a bool indicating whether its a bad frame, and an xyz for the median point of that frame
    bad_frames = []

    medians = ndimage.median_filter(data, size=(7, 1), mode='mirror')


    for i in range(0, len(data)):

        cur_point = data[i]

        median_point = medians[i]

        axis = (median_point[0] - cur_point[0], median_point[1] - cur_point[1], median_point[2] - cur_point[2])

        dist_sqrd = (axis[0]**2) + (axis[1]**2) + (axis[2]**2)

        if (dist_sqrd > threshold*threshold):
            bad_frames.append(True)
        else:
            bad_frames.append(False)

    bad_frames = ndimage.binary_dilation(bad_frames, iterations=1)
    idx = np.arange(len(data))
    good_frames = ~bad_frames

    despiked_data = copy.deepcopy(data)
    for axis in range(3):
        despiked_data[bad_frames, axis] = np.interp(idx[bad_frames], idx[good_frames], despiked_data[good_frames, axis])

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