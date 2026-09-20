import math
import queue

class Filter:
    def __init__(self):
        self.val_filtered_prev = (None, None, None)
        self.first_run = True
        self.timestamp_last = 0 # an absolute value in time, not a difference, just the last time that the filter was called

class LowPass(Filter):

    def __init__(self, cutoff_freq, sampling_period):
        self.val_filtered_prev = 0
        self.first_run = True
        self.sampling_period = sampling_period
        self.calc_alpha(cutoff_freq)

    def calc_alpha(self, cutoff_freq):
        tau = 1 / (2 * math.pi * cutoff_freq)
        self.alpha = 1 / (1 + (tau / self.sampling_period))

    def filter_value(self, val, timestamp):

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
    
    def filter_value(self, val, timestamp):

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

    def __init__(self, min_cutoff_freq, sampling_period, beta, derivative_cutoff):
        self.val_filtered_prev = 0
        self.first_run = True
        self.sampling_period = sampling_period
        self.min_cutoff_freq = min_cutoff_freq
        self.beta = beta
        self.internal_lowpass = LowPass(1, sampling_period)
        self.derivative_lowpass = LowPass(derivative_cutoff, sampling_period)

    def filter_value(self, val, timestamp):

        data_update_rate = 1 / self.sampling_period

        # we need to set a value for val_filtered_prev if we've never run before, so we assign it to val on the first run.
        # this basically makes our first run's filtered value just be the unfilitered value, but just for the first run
        if (self.first_run):
            self.first_run = False
            change_speed = 0 # the derivative of our value
        else:
            change_speed = (val - self.internal_lowpass.val_filtered_prev) * data_update_rate # the derivative of our value

        change_speed_filtered = self.derivative_lowpass.filter_value(change_speed, timestamp)

        dynamic_cutoff = self.min_cutoff_freq + (self.beta*abs(change_speed_filtered))

        self.internal_lowpass.calc_alpha(dynamic_cutoff)
        val_filtered = self.internal_lowpass.filter_value(val, timestamp)

        return val_filtered

