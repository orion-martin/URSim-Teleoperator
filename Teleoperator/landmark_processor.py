import filtering

x_filter = None
y_filter = None
z_filter = None

NOTHING = -1
LOW_PASS = 0
MOVING_AVERAGE = 1
LA_VIOLA = 2
ONE_EURO = 3
KALMAN = 4

def string_to_filter_type(string):
    match string:
        case "NOTHING":
            return NOTHING
        case "LOW_PASS":
            return LOW_PASS
        case "MOVING_AVERAGE":
            return MOVING_AVERAGE
        case "LA_VIOLA":
            return LA_VIOLA
        case "ONE_EURO":
            return ONE_EURO
        case "KALMAN":
            return KALMAN
        case _:
            print("ERROR: INVALID FILTER TYPE SPECIFIED")
            return LOW_PASS

filter_type = None

# initialization of filters
def init_filters(filter_for_run, filter_settings):

    global filter_type

    filter_type = filter_for_run

    match filter_type:
        case 0: # LOW_PASS
            return
        case 1: # MOVING_AVERAGE
            init_filters_as_moving_average(filter_settings)
            return
        case 2: # LA_VIOLA
            init_filters_as_LaViola(filter_settings)
            return
        case 3: # ONE_EURO
            init_filters_as_OneEuro(filter_settings)
            return
        case 4: # KALMAN
            init_filters_as_Kalman(filter_settings)
            return

def init_filters_as_moving_average(settings):
    global x_filter
    global y_filter
    global z_filter

    x_filter = filtering.MovingAverage(*settings)
    y_filter = filtering.MovingAverage(*settings)
    z_filter = filtering.MovingAverage(*settings)

def init_filters_as_OneEuro(settings):
    global x_filter
    global y_filter
    global z_filter

    x_filter = filtering.OneEuro(1/30, *settings)
    y_filter = filtering.OneEuro(1/30, *settings)
    z_filter = filtering.OneEuro(1/30, *settings)
def init_filters_as_LaViola(settings):
    global x_filter
    global y_filter
    global z_filter

    x_filter = filtering.LaViola(1/30, *settings)
    y_filter = filtering.LaViola(1/30, *settings)
    z_filter = filtering.LaViola(1/30, *settings)
def init_filters_as_Kalman(settings):
    global x_filter
    global y_filter
    global z_filter

    y_filter = filtering.Kalman(1/30, *settings)
    z_filter = filtering.Kalman(1/30, *settings)
    x_filter = filtering.Kalman(1/30, *settings)
# resetting of filters
def reset_filters_for_measurements(filter_type, settings):
    match filter_type:
        case 0: # LOW_PASS
            return
        case 1: # MOVING_AVERAGE
            reset_moving_average(settings)
            return
        case 2: # LA_VIOLA
            reset_LaViola(settings)
            return
        case 3: # ONE_EURO
            reset_OneEuro(settings)
            return
        case 4: # KALMAN
            reset_Kalman(settings)
            return

def reset_moving_average(settings):
    init_filters_as_moving_average(settings)    
def reset_OneEuro(settings):
    global x_filter
    global y_filter
    global z_filter

    x_filter.reset_but_keep_frames_to_alphas(*settings)
    y_filter.reset_but_keep_frames_to_alphas(*settings)
    z_filter.reset_but_keep_frames_to_alphas(*settings)
def reset_LaViola(settings):
    init_filters_as_LaViola(settings)
def reset_Kalman(settings):
    init_filters_as_Kalman(settings)


def filter_wrist_position(wrist_position, timestamp, frame):

    if (filter_type == NOTHING):
        return wrist_position

    x_filtered = x_filter.filter_value(wrist_position[0], timestamp, frame)
    y_filtered = y_filter.filter_value(wrist_position[1], timestamp, frame)
    z_filtered = z_filter.filter_value(wrist_position[2], timestamp, frame)

    return [x_filtered, y_filtered, z_filtered]