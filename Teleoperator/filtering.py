import math
import queue
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
import numpy as np


class Filter:
    def __init__(self):
        self.val_filtered_prev = (None, None, None)
        self.first_run = True
        self.timestamp_last = 0 # an absolute value in time, not a difference, just the last time that the filter was called

class Kalman(Filter):
    def __init__(self, sampling_period, R, sweep):
        self.first_run = True
        self.sampling_period = sampling_period

        dt = sampling_period

        self.kalman_filter = KalmanFilter(dim_x=2, dim_z=1) # the actual kalman filter we'll be using
        self.kalman_filter.F = np.array([[1, dt], [0, 1]]) # the predicition model we'll be using, built from a position and a velocity. Basically it's how position is updated, and how velocity is updated.
        self.kalman_filter.R = R # the noise covariance, basically how much we distrust our own inputs
        self.kalman_filter.H = np.array([[1, 0]]) # our update model, which says how new inputs affect our current state
        # Q is basically how much we distrust our prediction model, R and Q together form our final x value;
        # if we distrust our prediction a ton, we'll rely more on our measurements, and vice versa.
        self.kalman_filter.Q = Q_discrete_white_noise(dim=2, dt=dt, var=sweep)

        self.kalman_filter.x = np.array([0., 0.]) # the actual current value the kalman filter is saying as its "final" answer
        self.kalman_filter.P *= 100 # this is basically how the model trusts its current output vs the measurements; it trusts its predictions more and more after more time since a measurement

    def filter_value(self, val, timestamp, frame):

        if (self.first_run):
            self.first_run = False
            self.kalman_filter.x[0] = val
        self.kalman_filter.predict()

        self.kalman_filter.update(val)

        return self.kalman_filter.x[0]
class LowPass(Filter):

    def __init__(self, cutoff_freq, sampling_period):
        self.val_filtered_prev = 0
        self.first_run = True
        self.sampling_period = sampling_period
        self.calc_alpha(cutoff_freq)

    def calc_alpha(self, cutoff_freq):
        tau = 1 / (2 * math.pi * cutoff_freq)
        self.alpha = 1 / (1 + (tau / self.sampling_period))

    def filter_value(self, val, timestamp, frame):

        alpha = self.alpha

        # we need to set a value for val_filtered_prev if we've never run before, so we assign it to val on the first run.
        # this basically makes our first run's filtered value just be the unfilitered value, but just for the first run
        if (self.first_run):
            self.first_run = False
            self.val_filtered_prev = val

        val_filtered = (alpha * val) + ((1.0 - alpha) * self.val_filtered_prev)
        self.val_filtered_prev = val_filtered

        return val_filtered

class MovingAverage(Filter):

    def __init__(self, look_back_size):
        self.timestamp_last = 0 # an absolute value in time, not a difference, just the last time that the filter was called
        self.points_last = queue.Queue() # array of last few points. Used for the moving average.
        self.look_back_size = look_back_size # the amount of points that the moving average will look back
    
    def filter_value(self, val, timestamp, frame):

        dt = timestamp - self.timestamp_last
        self.timestamp_last = timestamp


        self.points_last.put_nowait(val)
        if (self.points_last.qsize() > self.look_back_size):
            self.points_last.get_nowait()

        averaged_val = 0

        queue_elements = list(self.points_last.queue)
        queue_elements_len = len(queue_elements)

        for cur_past_point in queue_elements:
            averaged_val += cur_past_point

        averaged_val /=  queue_elements_len

        return averaged_val

class OneEuro(Filter):

    def __init__(self, min_cutoff_freq, sampling_period, beta, derivative_cutoff, map_and_use_alphas=True):
        self.val_filtered_prev = 0
        self.first_run = True
        self.sampling_period = sampling_period
        self.min_cutoff_freq = min_cutoff_freq
        self.beta = beta
        self.internal_lowpass = LowPass(1, sampling_period)
        self.derivative_lowpass = LowPass(derivative_cutoff, sampling_period)

        # a dictionary that maps frames to alpha values for each frame.
        # in a normal run this will only be saving values and will never be used, just written.
        # but then at the end of the program we rerun the One Euro starting from frame zero,
        # and that run will use the alpha for each frame, so it'll filter identically as the inital run
        self.frames_to_alphas = {-1:0}
        self.map_and_use_alphas = map_and_use_alphas

    def reset_but_keep_frames_to_alphas(self, min_cutoff_freq, sampling_period, beta, derivative_cutoff):
        self.val_filtered_prev = 0
        self.first_run = True
        self.sampling_period = sampling_period
        self.min_cutoff_freq = min_cutoff_freq
        self.beta = beta
        self.internal_lowpass = LowPass(1, sampling_period)
        self.derivative_lowpass = LowPass(derivative_cutoff, sampling_period)

    # One Euro uses the frame parameter because we need to save the alpha for each frame to rerun the exact filtering process again and measure lag later
    def filter_value(self, val, timestamp, frame):

        data_update_rate = 1 / self.sampling_period

        # we need to set a value for val_filtered_prev if we've never run before, so we assign it to val on the first run.
        # this basically makes our first run's filtered value just be the unfilitered value, but just for the first run
        if (self.first_run):
            self.first_run = False
            change_speed = 0 # the derivative of our value
        else:
            change_speed = (val - self.internal_lowpass.val_filtered_prev) * data_update_rate # the derivative of our value

        change_speed_filtered = self.derivative_lowpass.filter_value(change_speed, timestamp, frame)

        dynamic_cutoff = self.min_cutoff_freq + (self.beta*abs(change_speed_filtered))

        dynamic_alpha = 0

        if (not self.map_and_use_alphas): # if we aren't supposed to map or use the mapped alpha values then just calculate our alpha and use it as normal
            self.internal_lowpass.calc_alpha(dynamic_cutoff) # update alpha
            dynamic_alpha = self.internal_lowpass.alpha # get our updated alpha value
        else: # otherwise, go through and record the alpha if it has not been recorded yet, or use a previous one if it's been recorded already

            if (not frame in self.frames_to_alphas): # if current frame hasn't run with an alpha before
                
                self.internal_lowpass.calc_alpha(dynamic_cutoff) # update alpha
                dynamic_alpha = self.internal_lowpass.alpha # get our updated alpha value
                
                self.frames_to_alphas[frame] = dynamic_alpha # map our alpha value to the current frame
            else: # otherwise, if the alpha has already been recorded in a previous run, then use that recorded alpha value
                dynamic_alpha = self.frames_to_alphas[frame]

        self.internal_lowpass.alpha = dynamic_alpha
        val_filtered = self.internal_lowpass.filter_value(val, timestamp, frame)

        return val_filtered


class LaViola(Filter):

    def __init__(self, cutoff_freq, sampling_period):
        self.val_filtered_prev = 0
        self.first_run = True

        self.cutoff_freq = cutoff_freq
        self.sampling_period = sampling_period

        self.lowpass_first_order = LowPass(cutoff_freq, sampling_period)
        self.lowpass_second_order = LowPass(cutoff_freq, sampling_period)

    def filter_value(self, val, timestamp, frame):

        data_update_rate = 1 / self.sampling_period

        # we need to set a value for val_filtered_prev if we've never run before, so we assign it to val on the first run.
        # this basically makes our first run's filtered value just be the unfilitered value, but just for the first run
        if (self.first_run):
            self.first_run = False

            return self.lowpass_first_order.filter_value(val, timestamp, frame)

        val_first_order = self.lowpass_first_order.filter_value(val, timestamp, frame)
        val_second_order = self.lowpass_second_order.filter_value(val_first_order, timestamp, frame)

        val_filtered = (2*val_first_order) - (val_second_order)

        return val_filtered

