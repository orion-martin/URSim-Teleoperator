import data_tracker
import data_saver
import zero_phase_filter
import arbitrary_data_filterer as arbitrary_data_filterer
import numpy as np
from numpy.lib.recfunctions import structured_to_unstructured
import math

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

def data_clean(data): # returns zero phased data

    data_as_2d_array = structured_to_unstructured(data)

    data_zero_phased = zero_phase_filter.data_clean(data_as_2d_array[:, :3])

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
# gets the RMSE of an array of values
def RMSE_get_from_error_array(arr):

    count = len(arr)
    
    total_squared = 0.0
    averaged_total_squared = 0.0
    root_mean_squared_error = 0.0

    for cur_val in arr:
        total_squared += cur_val**2

    averaged_total_squared = total_squared / count
    root_mean_squared_error = math.sqrt(averaged_total_squared)

    return root_mean_squared_error
# takes in an array of arrays (structured like [[x,y,z],[x,y,z]]) and gets the RMSE per axis, and the total RMSE.
# returns an array containing RMSE for x, y, z, and the total across all axes 
def RMSE_get_from_error_data(data):
    RMSEs = [0.0, 0.0, 0.0, 0.0]

    for cur_axis in range(0, 3):
        # the data parameter is structured like [[x,y,z],[x,y,z]], but we need our data arrays like [x0,x1,x2]
        # so we restructure it into data_cur
        data_cur = []

        for cur_data_point in data:
            data_cur.append(cur_data_point[cur_axis])
        
        RMSEs[cur_axis] = RMSE_get_from_error_array(data_cur)
    RMSEs[3] = math.sqrt((RMSEs[0]**2) + (RMSEs[1]**2) + (RMSEs[2]**2))

    return [[RMSEs[0], RMSEs[1], RMSEs[2], RMSEs[3]]]
def average_get_from_error_array(arr):

    count = len(arr)
    
    total = 0.0
    averaged_total = 0.0

    for cur_val in arr:
        total += abs(cur_val)

    averaged_total = total / count

    return averaged_total
# returns an array containing an array that has x-lag, y-lag, z-lag, and full position-lag
def average_get_from_error_data(data):
    averages = [0.0, 0.0, 0.0, 0.0]

    for cur_axis in range(0, 3):
        # the data parameter is structured like [[x,y,z],[x,y,z]], but we need our data arrays like [x0,x1,x2]
        # so we restructure it into data_cur
        data_cur = []

        for cur_data_point in data:
            data_cur.append(cur_data_point[cur_axis])
        
        averages[cur_axis] = average_get_from_error_array(data_cur)

    total_position_error = 0
    for cur_data_point in data:
        total_position_error += math.sqrt((cur_data_point[0]**2) + (cur_data_point[1]**2) + (cur_data_point[2]**2))
    average_position_error = total_position_error / len(data)

    return [[averages[0], averages[1], averages[2], average_position_error]]

def data_TCP_measurements_save(data_prefiltered_name, data_TCP_name):
    # get the base data (the "original" being compared against)
    data_prefiltered_suite = data_tracker.data_format(data_prefiltered_name)
    data_prefiltered = data_prefiltered_suite["data"][30:]
    # the raw hand position with noise removed
    data_prefiltered_noiseless = data_clean(data_prefiltered)

    # get the comparison data to compare against the base data
    data_TCP_suite = data_tracker.data_format(data_TCP_name)
    data_TCP = data_TCP_suite["data"][30:]
    # the raw TCP position with noise removed
    data_TCP_noiseless = data_clean(data_TCP)

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

    data_saver.data_save_singular("RMSE_jitter", RMSE_get_from_error_data(data_noise), ['%.16f', '%.16f', '%.16f', '%.16f'], header)
    data_saver.data_save_singular("average_lag", average_get_from_error_data(data_lag), ['%.16f', '%.16f', '%.16f', '%.16f'], header)
    
def data_save(name):
    data = data_tracker.data_format(name)

    data_saver.data_save_singular(name, data["data"], data["format"], data["header"])
def data_finalize():

    data_TCP_measurements_save("pre_filter_position", "robot_tcp_position")
    data_save("timestamps")
    data_save("pre_filter_position")
    data_save("post_filter_position")
    data_save("robot_tcp_position")
