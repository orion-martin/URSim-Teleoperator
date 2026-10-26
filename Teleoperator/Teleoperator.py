import time
import landmark_gatherer
import opencv_handler
import landmark_processor
import landmark_mapper
import robot_director
import data_format
import data_tracker
import cv2
import sys
import random
import numpy as np
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--filter", default="MOVING_AVERAGE")
parser.add_argument("--settings", nargs="+", type=float, default=[5.0])

args = parser.parse_args()

try:
    with landmark_gatherer.vision.PoseLandmarker.create_from_options(landmark_gatherer.options) as landmarker:

        is_first_run = True

        landmark_processor.init_filters(landmark_processor.string_to_filter_type(args.filter), tuple(args.settings))

        data_tracker.logging_start()
        robot_director.start()

        t0 = time.perf_counter_ns() // 1000000
        robot_director.t0 = t0

        opencv_handler.start()

        while (opencv_handler.frameCapOk):

            opencv_handler.frame_pushed.wait()
            opencv_handler.frame_pushed.clear()

            if (data_tracker.data_availability_queue_empty.is_set()):
                sys.exit(f"Data availability queue is empty. Exiting program.")

            with (opencv_handler.frame_lock):

                if not opencv_handler.frameCapOk:
                    break
                
                frame = opencv_handler.frame
            frame_counter = 0
            with opencv_handler.frame_counter_lock:
                frame_counter = opencv_handler.frame_counter

            landmark_gatherer.landmark_async_process_from_frame(landmarker, frame, (time.perf_counter_ns() // 1000000) - t0, frame_counter)

            if (landmark_gatherer.landmark_written.is_set()):
                landmarks, timestamp, screen_landmarks = landmark_gatherer.landmarks_get_with_timestamp()
                frame_ind_for_landmark = landmark_gatherer.frame_lookup_table[timestamp] # this is the frame from the video stream that was used to produce "landmarks", "timestamp", and "screen_landmarks". So this is the frame that should be referred to when talking about "this frame", rather than opencv_handler.frame_counter, as that is just the last frame processed, not the frame used for the variables

                if landmarks:

                    wrist_position = landmark_gatherer.wrist_position_get(landmarks)
                    
                    wrist_position_unfiltered = wrist_position
                    if wrist_position is not None:

                        data_ind = data_tracker.data_dict_init("timestamps")
                        data_tracker.data_element_add_group("timestamps", data_ind, ['t_obtained', 't_used', 'frame_used'], [timestamp, (time.perf_counter_ns() // 1000000) - t0, frame_ind_for_landmark])
                        data_tracker.data_quick_write("pre_filter_position", ['x', 'y', 'z', 't_write'], [wrist_position[0], wrist_position[1], wrist_position[2], frame_ind_for_landmark])

                        wrist_position = landmark_processor.filter_wrist_position(wrist_position, (time.perf_counter_ns() // 1000000) - t0, frame_ind_for_landmark)
                        data_tracker.data_quick_write("post_filter_position", ['x', 'y', 'z', 't_write'], [wrist_position[0], wrist_position[1], wrist_position[2], frame_ind_for_landmark])
                        position_mapped = landmark_mapper.wrist_map_to_robot(wrist_position)

                        data_tracker.data_element_add("timestamps", data_ind, "t_processed", (time.perf_counter_ns() // 1000000) - t0)

                        robot_director.update_target(position_mapped, data_ind, frame_ind_for_landmark)
                else:
                    print("empty landmarks")
            
            cv2.imshow("Teleoperator", frame)
            programOk = opencv_handler.finish_frame()
            if (not programOk):
                break

            if is_first_run:
                landmark_gatherer.landmark_written.wait()
                is_first_run = False

            


finally:

    robot_director.end()
    data_tracker.logging_end()

    opencv_handler.end()

# this code only runs on successful execution of the program. If an error occurs these remaining lines won't run. If something MUST run put in in the "finally" above

data_format.data_finalize()

print("Program End")
