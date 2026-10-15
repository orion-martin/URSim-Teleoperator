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
    ],
    [1, 1]
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

def data_zero_phase(name, data): # returns zero phased data

    data_as_2d_array = structured_to_unstructured(data["data"])

    print(data_as_2d_array)

    data_zero_phased = zero_phase_filter.run_zero_phase_on_data(data_as_2d_array[:, :3])

    data_zero_phased_with_frame = np.column_stack((data_zero_phased, data_as_2d_array[:, 3]))

    return data_zero_phased_with_frame
def data_save(name):
    data = data_tracker.data_format(name)

    data_flags = data["flags"]

    do_zero_phase_on_data = data_flags[0]
    do_zero_phase_then_lag_on_data = data_flags[0]

    data_noiseless = data_zero_phase(name, data) if (do_zero_phase_on_data or do_zero_phase_then_lag_on_data) else None

    if (do_zero_phase_on_data):
        data_saver.data_save_singular(name + "_noiseless", data_noiseless, data["format"], data["header"])
    if (do_zero_phase_then_lag_on_data):
        lagged_data = arbitrary_data_filterer.run_filter_arbitrarily(data_noiseless, 30)
        data_saver.data_save_singular(name + "_noiseless_lagged", lagged_data, data["format"], data["header"])

    data_saver.data_save_singular(name, data["data"], data["format"], data["header"])
def data_finalize():

    data_save("timestamps")
    data_save("pre_filter_position")
    data_save("post_filter_position")
    data_save("robot_tcp_position")
