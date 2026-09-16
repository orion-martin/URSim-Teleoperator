import filtering

x_filter = filtering.MovingAverage(10)
y_filter = filtering.MovingAverage(10)
z_filter = filtering.MovingAverage(10)

def filter_wrist_position(wrist_position, timestamp):

    x_filtered = x_filter.filter_value(wrist_position[0], timestamp)
    y_filtered = y_filter.filter_value(wrist_position[1], timestamp)
    z_filtered = z_filter.filter_value(wrist_position[2], timestamp)

    return [x_filtered, y_filtered, z_filtered]