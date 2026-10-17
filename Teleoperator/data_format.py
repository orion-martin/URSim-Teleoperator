import data_tracker
import data_saver
import zero_phase_filter
import arbitrary_data_filterer as arbitrary_data_filterer
import numpy as np
from numpy.lib.recfunctions import structured_to_unstructured

data_tracker.data_structure_add(
    "timestamps",
    [
        ('t_obtained', 'i8'),
        ('t_used', 'i8'),
        ('t_processed', 'i8'),
        ('t_published', 'i8'),
        ('frame_used', 'i8')
    ],
    [
        '%d',
        '%d',
        '%d',
        '%d',
        '%d'
    ]
)

data_tracker.data_structure_add(
    "pre_filter_position",
    [
        ('x', 'f8'),
        ('y', 'f8'),
        ('z', 'f8'),
        ('t_write', 'i8'), # the frame when this data was written
    ],
    [
        '%.16f',
        '%.16f',
        '%.16f',
        '%d',
    ]
)

data_tracker.data_structure_add(
    "post_filter_position",
    [
        ('x', 'f8'),
        ('y', 'f8'),
        ('z', 'f8'),
        ('t_write', 'i8'),
    ],
    [
        '%.16f',
        '%.16f',
        '%.16f',
        '%d',
    ]
)

data_tracker.data_structure_add(
    "robot_tcp_position",
    [
        ('x', 'f8'),
        ('y', 'f8'),
        ('z', 'f8'),
        ('t_write', 'i8'),
    ],
    [
        '%.16f',
        '%.16f',
        '%.16f',
        '%d',
    ]
)

def data_zero_phase(data): # returns zero phased data

    data_as_2d_array = structured_to_unstructured(data)

    data_zero_phased = zero_phase_filter.run_zero_phase_on_data(data_as_2d_array[:, :3])

    data_zero_phased_with_frame = np.column_stack((data_zero_phased, data_as_2d_array[:, 3]))

    return data_zero_phased_with_frame
# gets the frame by frame difference between two data sets. Converts both arrays into dictionaries before calculating, then returns an array
def data_difference_get(data_from, data_to):

    data_from_by_frame = { f:(x,y,z) for x,y,z,f in data_from }
    data_to_by_frame = { f:(x,y,z) for x,y,z,f in data_to }

    data_diffed = []
    for frame_cur in data_from_by_frame:

        if frame_cur not in data_to_by_frame:
            continue

        diff_xyz = (
            data_to_by_frame[frame_cur][0] - data_from_by_frame[frame_cur][0],
            data_to_by_frame[frame_cur][1] - data_from_by_frame[frame_cur][1],
            data_to_by_frame[frame_cur][2] - data_from_by_frame[frame_cur][2],
            frame_cur # also add the frame which is the same for data_from and data_to
        )

        data_diffed.append(diff_xyz)

    return data_diffed
# we compare the result of the filtering to the raw unfiltered through a zero-phased version of the raw unfiltered data
def data_postfilter_measurements_save(data_prefiltered_name, data_postfiltered_name):
    # get the base data (the "original" being compared against)
    data_prefiltered_suite = data_tracker.data_format(data_prefiltered_name)
    data_prefiltered = data_prefiltered_suite["data"]
    # remove noise from it
    data_noiseless = data_zero_phase(data_prefiltered)
    # lag it so we can compare our comparison data to it (since comparison data is lagged)
    data_noiseless_lagged = arbitrary_data_filterer.run_filter_arbitrarily(data_noiseless, 30)

    # get the comparison data to compare against the base data
    data_postfiltered_suite = data_tracker.data_format(data_postfiltered_name)
    data_postfiltered = data_postfiltered_suite["data"]

    data_noise = data_difference_get(data_noiseless_lagged, data_postfiltered) # gets the difference from the ideal-lagged signal to the real-time filtered signal, which is the noise still left over after filtering
    data_lag = data_difference_get(data_noiseless, data_noiseless_lagged) # gets the difference from the ideal signal to the ideal-lagged signal, which is the lag produced by the filter

    format = data_prefiltered_suite["format"]
    header = data_prefiltered_suite["header"]

    data_saver.data_save_singular("jitter_left_after_filtering", data_noise, format, header)
    data_saver.data_save_singular("lag_introduced_by_filter", data_lag, format, header)

    # these two saves aren't necessary, as what they save is just intermediary data used for calculating noise and lag.
    # I've left them commented out, but if you need them for some reason, just uncomment them and it should work out of the box.
    # data_saver.data_save_singular("prefilter_position_noiseless", data_noiseless, format, header)
    # data_saver.data_save_singular("prefilter_position_noiseless_lagged", data_noiseless_lagged, format, header)
# we compare the result of the filtering to the raw unfiltered through a zero-phased version of the raw unfiltered data
def data_TCP_measurements_save(data_prefiltered_name, data_TCP_name):
    # get the base data (the "original" being compared against)
    data_prefiltered_suite = data_tracker.data_format(data_prefiltered_name)
    data_prefiltered = data_prefiltered_suite["data"]
    # the raw hand position with noise removed
    data_prefiltered_noiseless = data_zero_phase(data_prefiltered)

    # get the comparison data to compare against the base data
    data_TCP_suite = data_tracker.data_format(data_TCP_name)
    data_TCP = data_TCP_suite["data"]
    # the raw TCP position with noise removed
    data_TCP_noiseless = data_zero_phase(data_TCP)

    data_noise = data_difference_get(data_TCP_noiseless, data_TCP) # gets the difference from the noiseless TCP position to the raw TCP position; measuring jitter
    data_lag = data_difference_get(data_prefiltered_noiseless, data_TCP_noiseless) # gets the difference from the ideal signal to the ideal TCP position, measuring lag

    format = data_prefiltered_suite["format"]
    header = data_prefiltered_suite["header"]

    data_saver.data_save_singular("TCP_jitter", data_noise, format, header)
    data_saver.data_save_singular("TCP_lag", data_lag, format, header)

    # these two saves aren't necessary, as what they save is just intermediary data used for calculating noise and lag.
    # I've left them commented out, but if you need them for some reason, just uncomment them and it should work out of the box.
    data_saver.data_save_singular("prefilter_position_noiseless", data_prefiltered_noiseless, format, header)
    data_saver.data_save_singular("TCP_position_noiseless", data_TCP_noiseless, format, header)
def data_save(name):
    data = data_tracker.data_format(name)

    data_saver.data_save_singular(name, data["data"], data["format"], data["header"])
def data_finalize():

    data_TCP_measurements_save("pre_filter_position", "robot_tcp_position")
    data_save("timestamps")
    data_save("pre_filter_position")
    data_save("post_filter_position")
    data_save("robot_tcp_position")
