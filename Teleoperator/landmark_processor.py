import filtering


x_filter = None
y_filter = None
z_filter = None

def init_filters():

    global x_filter
    global y_filter
    global z_filter

    # x_filter = filtering.OneEuro(0.25, 1/30, 0.1, 5)
    # y_filter = filtering.OneEuro(0.25, 1/30, 0.1, 5)
    # z_filter = filtering.OneEuro(0.25, 1/30, 0.1, 5)

    x_filter = filtering.LaViola(1.0, 1/30)
    y_filter = filtering.LaViola(1.0, 1/30)
    z_filter = filtering.LaViola(1.0, 1/30)

def filter_wrist_position(wrist_position, timestamp):

    x_filtered = x_filter.filter_value(wrist_position[0], timestamp)
    y_filtered = y_filter.filter_value(wrist_position[1], timestamp)
    z_filtered = z_filter.filter_value(wrist_position[2], timestamp)

    return [x_filtered, y_filtered, z_filtered]