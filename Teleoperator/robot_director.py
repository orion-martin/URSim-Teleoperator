import threading
import data_tracker
import time
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface

position_lock = threading.Lock()
robot_stop_flag = threading.Event()

robot_ready = threading.Event()
control_error = None

target = [0.2, -0.2, 0.6, 0.0, 3.14159, 0.0]
data_ind = -1
frame_of_update = -1
t0 = 0

# this is always running asynchronously at the update speed of the robot arm
def update_arm(robot_ip, stop_event:threading.Event):

    global control_error
    global ts_grab_last

    try:
        rtde = RTDEControlInterface(robot_ip)
    except Exception as e:
        control_error = e
        robot_ready.set()
        return
    try:
        rtde_receive = RTDEReceiveInterface(robot_ip)
    except Exception as e:
        control_error = e
        robot_ready.set()
        return
    
    robot_ready.set()

    data_ind_last = -1

    try:
        while not stop_event.is_set():

            start_time = rtde.initPeriod()

            with (position_lock):
                tcp_pose = list(target)
                data_ind_threaded = data_ind
                frame_of_update_threaded = frame_of_update
            
            if (data_ind_threaded != data_ind_last):
                data_tracker.data_element_add("timestamps", data_ind_threaded, "t_published", (time.perf_counter_ns() // 1000000) - t0)
                data_tracker.data_report("timestamps", data_ind_threaded)

                robot_tcp = rtde_receive.getActualTCPPose()

                re_defined_x = robot_tcp[1]   # our X = robot Y
                re_defined_y = -robot_tcp[2]  # our Y = robot -Z
                re_defined_z = -robot_tcp[0]  # our Z = robot -X

                data_tracker.data_quick_write("robot_tcp_position", ['x', 'y', 'z', 't_write'], [re_defined_x, re_defined_y, re_defined_z, frame_of_update_threaded])

                data_ind_last = data_ind_threaded

            rtde.servoL(tcp_pose, 0.5, 0.5, 1.0/500, 0.03, 500)

            rtde.waitPeriod(start_time)

    finally:
        for cleanup in (rtde.servoStop, rtde.stopScript, rtde.disconnect):
            try:
                cleanup()
            except Exception as e:
                print("Robot disconnection/cleanup failed: ", e)

    return
# this is called to update the target used in update_arm
def update_target(target_new, data_ind_new, frame_ind):
    global target
    global data_ind
    global frame_of_update
    with (position_lock):
        target = list(target_new)
        data_ind = data_ind_new
        frame_of_update = frame_ind

control_ip = "localhost"
control_thread = threading.Thread()

# starts the control thread
def start():
    global control_thread, control_error

    if (control_thread.is_alive()):
        return

    robot_stop_flag.clear()
    robot_ready.clear()
    control_error = None
    
    control_thread = threading.Thread(target=update_arm, args=(control_ip, robot_stop_flag))

    control_thread.start()

    if not robot_ready.wait(timeout=10.0):
        robot_stop_flag.set()
        print("Robot Control Failed: connection timed out")
    elif control_error is not None:
        print("Robot Control Failed: ", control_error)
    
#ends the control thread safely
def end():
    robot_stop_flag.set()
    if control_thread.is_alive():
        control_thread.join()