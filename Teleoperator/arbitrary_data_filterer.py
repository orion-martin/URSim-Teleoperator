import landmark_processor

# runs the current filter on a set of data arbitrarily.
# note that this will reset our filters so don't use this until the teleop program is finished running
#
# data is a list of lists, where each list contains an x,y,z and frame ind.
# fps is just the framerate our filter assumes.
def run_filter_arbitrarily(data, fps):

    landmark_processor.init_filters()

    data_len = len(data)

    result = []

    period = 1/fps

    for i in range(data_len):

        x = data[i][0]
        y = data[i][1]
        z = data[i][2]
        frame = data[i][3]

        idealized_time_stamp = frame * period

        data_filtered_singular = landmark_processor.filter_wrist_position([x, y, z], idealized_time_stamp)

        result.append([data_filtered_singular[0], data_filtered_singular[1], data_filtered_singular[2], frame])

    return result