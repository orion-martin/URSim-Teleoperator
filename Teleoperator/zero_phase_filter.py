from scipy import signal

# data must 2d array with rows of [x, y, z]
def run_zero_phase_on_data(data, sampling_freq=30, cutoff_freq=6, order=8):

    butterworth_filter = signal.butter(N=order, Wn=cutoff_freq, fs=sampling_freq, output='sos', btype='lowpass')

    return signal.sosfiltfilt(butterworth_filter, data, axis=0)

