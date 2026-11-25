import threading
import data_tracker
import time
from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface

position_lock = threading.Lock()
robot_stop_flag = threading.Event()

robot_ready = threading.Event()
control_error = None

enable_safety_limits = threading.Event()

target = [0.5, -0.2, 0.35, 0, 0, 0]
data_ind = -1
frame_of_update = -1
t0 = 0

# this is always running asynchronously at the update speed of the robot arm
def update_arm(robot_ip, stop_event:threading.Event):

    global control_error
    global ts_grab_last

    rtde = None
    rtde_receive = None

    try:
        rtde = RTDEControlInterface(robot_ip)
        rtde_receive = RTDEReceiveInterface(robot_ip, 500.0, ["actual_TCP_pose", "timestamp"])
    except Exception as e:
        control_error = e
        for iface in (rtde, rtde_receive):
            if iface is None:
                continue
            for cleanup in ((iface.stopScript, iface.disconnect) if iface is rtde else (iface.disconnect,)):
                try:
                    cleanup()
                except Exception as ce:
                    print("Robot disconnection/cleanup failed: ", ce)
        robot_ready.set()
        return
    
    robot_ready.set()

    data_ind_last = -1

    ts_last = 0

    try:
        while not stop_event.is_set():

            start_time = rtde.initPeriod()

            with (position_lock):
                tcp_pose = list(target)
                data_ind_threaded = data_ind
                frame_of_update_threaded = frame_of_update

            if (enable_safety_limits.is_set() and tcp_pose[2] < 0.225):
                print("TARGET EXCEEDED SAFETY LIMITS! Z TOO LOW!")
                break
            
            if (data_ind_threaded != data_ind_last):
                data_tracker.data_element_add("timestamps", data_ind_threaded, "t_published", (time.perf_counter_ns() // 1000000) - t0)
                data_tracker.data_report("timestamps", data_ind_threaded)

                robot_tcp = rtde_receive.getActualTCPPose()
                ts = rtde_receive.getTimestamp()
                if ts == ts_last:
                    stale_count += 1
                    if stale_count > 15:   # ~0.5 s of frames with no new data
                        control_error = "receive feed stale"
                        break
                else:
                    stale_count = 0
                ts_last = ts


                re_defined_x = robot_tcp[1]   # our X = robot Y
                re_defined_y = -robot_tcp[2]  # our Y = robot -Z
                re_defined_z = -robot_tcp[0]  # our Z = robot -X
                
                if (enable_safety_limits.is_set() and robot_tcp[2] < 0.225):
                    print("ROBOT EXCEEDED SAFETY LIMITS! Z TOO LOW!")
                    break

                data_tracker.data_quick_write("robot_tcp_position", ['x', 'y', 'z', 't_write'], [re_defined_x, re_defined_y, re_defined_z, frame_of_update_threaded])

                data_ind_last = data_ind_threaded

            rtde.servoL(tcp_pose, 0.5, 0.5, 1.0/500, 0.03, 300)

            rtde.waitPeriod(start_time)

    finally:
        for cleanup in (rtde.servoStop, rtde.stopScript, rtde.disconnect, rtde_receive.disconnect):
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
        return True

    robot_stop_flag.clear()
    robot_ready.clear()
    control_error = None
    
    control_thread = threading.Thread(target=update_arm, args=(control_ip, robot_stop_flag))

    control_thread.start()

    if not robot_ready.wait(timeout=10.0):
        robot_stop_flag.set()
        print("Robot Control Failed: connection timed out")
        return False
    elif control_error is not None:
        print("Robot Control Failed: ", control_error)
        return False
    return True
    
#ends the control thread safely
def end():
    robot_stop_flag.set()
    if control_thread.is_alive():
        control_thread.join()