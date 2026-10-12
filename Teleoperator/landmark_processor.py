import filtering


x_filter = None
y_filter = None
z_filter = None

LOW_PASS = 0
MOVING_AVERAGE = 1
LA_VIOLA = 2
ONE_EURO = 3

our_filter = ONE_EURO

# initialization of filters
def init_filters():

    match our_filter:
        case 0: # LOW_PASS
            return
        case 1: # MOVING_AVERAGE
            return
        case 2: # LA_VIOLA
            init_filters_as_LaViola()
            return
        case 3: # ONE_EURO
            init_filters_as_OneEuro()
            return

def init_filters_as_OneEuro():
    global x_filter
    global y_filter
    global z_filter

    x_filter = filtering.OneEuro(0.25, 1/30, 0.7, 10)
    y_filter = filtering.OneEuro(0.25, 1/30, 0.7, 10)
    z_filter = filtering.OneEuro(0.25, 1/30, 0.7, 10)
def init_filters_as_LaViola():
    global x_filter
    global y_filter
    global z_filter

    x_filter = filtering.LaViola(1.0, 1/30)
    y_filter = filtering.LaViola(1.0, 1/30)
    z_filter = filtering.LaViola(1.0, 1/30)
# resetting of filters
def reset_filters_for_measurements():
    match our_filter:
        case 0: # LOW_PASS
            return
        case 1: # MOVING_AVERAGE
            return
        case 2: # LA_VIOLA
            reset_LaViola()
            return
        case 3: # ONE_EURO
            reset_OneEuro()
            return
def reset_OneEuro():
    global x_filter
    global y_filter
    global z_filter

    x_filter.reset_but_keep_frames_to_alphas(0.25, 1/30, 0.1, 5)
    y_filter.reset_but_keep_frames_to_alphas(0.25, 1/30, 0.1, 5)
    z_filter.reset_but_keep_frames_to_alphas(0.25, 1/30, 0.1, 5)
def reset_LaViola():
    global x_filter
    global y_filter
    global z_filter

    x_filter = filtering.LaViola(1.0, 1/30)
    y_filter = filtering.LaViola(1.0, 1/30)
    z_filter = filtering.LaViola(1.0, 1/30)

def filter_wrist_position(wrist_position, timestamp, frame):

    x_filtered = x_filter.filter_value(wrist_position[0], timestamp, frame)
    y_filtered = y_filter.filter_value(wrist_position[1], timestamp, frame)
    z_filtered = z_filter.filter_value(wrist_position[2], timestamp, frame)

    return [x_filtered, y_filtered, z_filtered]