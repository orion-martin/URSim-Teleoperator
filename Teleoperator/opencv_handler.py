import cv2
import threading
import time
import queue

# create window
cv2.namedWindow("Teleoperator")
# get the video path for our video
video_path = "Videos/test_video_1.mp4"
# declare and initialize video capture from default webcame, allows you to read webcam data on demand
videoCapture = cv2.VideoCapture(video_path)

# if this is true, the frame processor will fully process every single frame in the video, storing them to frame_queue, before any frames are pushed.
# if this is false, frames will be processed at the same time as they are pushed (note that a single frame is always processed first so that there is a frame to be pushed)
PROCESS_FRAMES_FIRST = True

frameCapOk, frame = videoCapture.isOpened(), None
cap_good = frameCapOk
frame_lock = threading.Lock()

allow_frame_pushing = threading.Event()
allow_frame_pushing.clear()

frame_pushed = threading.Event()
frame_pushed.clear()

frame_counter = 0
frame_counter_lock = threading.Lock()

frame_queue = queue.Queue(maxsize=(0 if PROCESS_FRAMES_FIRST else 4))

def process_frame():

    frameCapOkThreaded, frameThreaded = videoCapture.read()


    if not PROCESS_FRAMES_FIRST:
        allow_frame_pushing.set()

    while (frameCapOkThreaded):

        frameCapOkThreaded, frameThreaded = videoCapture.read()    

        frame_queue.put((frameCapOkThreaded, frameThreaded))

    if PROCESS_FRAMES_FIRST:
        allow_frame_pushing.set()

def push_frame():

    allow_frame_pushing.wait()

    global frameCapOk
    global frame
    global cap_good
    global frame_counter

    PERIOD:int = (1e9/30) # 30 fps, in nanoseconds
    BUFFER_LEN:int = 2e6 # 2ms buffer, in nanoseconds

    frameCapOkThreaded, frameThreaded = True, None

    t_ns_start = time.perf_counter_ns()
    frameCount = 0

    # fps_timer = 0
    # second_timer_milli = 0
    # t_ns_prev = 0

    while (frameCapOkThreaded):

        if not videoCapture.isOpened():
            break

        t_ns_now = time.perf_counter_ns()

        t_ns_deadline = t_ns_start + (frameCount * PERIOD)

        if (t_ns_now >= t_ns_deadline):
            pass
        elif (t_ns_now > (t_ns_deadline - BUFFER_LEN)): # if we are within the buffer, busy wait and then continue the next iteration
            continue
        else:
            t_ns_diff  = (t_ns_deadline - t_ns_now) - BUFFER_LEN

            if (t_ns_diff > 0):
                time.sleep(float(t_ns_diff) / 1e9)

            continue

        while (t_ns_now >= (t_ns_start + (frameCount * PERIOD))):
            frameCount += 1
            frameCapOkThreaded, frameThreaded = frame_queue.get()

        with frame_lock:
            frameCapOk, frame = frameCapOkThreaded, frameThreaded
        with frame_counter_lock:
            frame_counter = frameCount

        frame_pushed.set()

frame_process_thread = threading.Thread(target=process_frame)
frame_push_thread = threading.Thread(target=push_frame)

# this ends a frame and returns whether the program should continue running, if it's False, the program should end
def finish_frame():
    # check if esc was pressed, if it was, return false which ends the program
    keyPress = cv2.waitKey(1)
    return not (keyPress == 27)

def start():
    frame_process_thread.start()
    frame_push_thread.start()

def end():
    # close window and release webcam VideoCapture device
    cv2.destroyWindow("Teleoperator")
    videoCapture.release()
    frame_process_thread.join()
    frame_push_thread.join()
