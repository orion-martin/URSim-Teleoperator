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

def project_filtered_world_to_pixel(
    original_landmarks,
    original_world_landmarks,
    filtered_world_point,
    idx,
    img_width,
    img_height,
):
    """Approximately project a filtered world point into image pixels."""
    world = np.array(
        [[p.x, p.y, p.z] for p in original_world_landmarks],
        dtype=float,
    )
    pixels = np.array(
        [[p.x * img_width, p.y * img_height]
         for p in original_landmarks],
        dtype=float,
    )
    filtered = np.asarray(filtered_world_point, dtype=float).reshape(3)

    if len(world) != len(pixels):
        raise ValueError("World and image landmark counts must match.")

    if not (
        np.isfinite(filtered).all()
        and np.isfinite(world[idx]).all()
        and np.isfinite(pixels[idx]).all()
    ):
        raise ValueError("The target landmark contains invalid coordinates.")

    # Favor visible landmarks when estimating the mapping.
    weights = np.array(
        [getattr(p, "visibility", 1.0) for p in original_landmarks],
        dtype=float,
    )
    valid = (
        np.isfinite(world).all(axis=1)
        & np.isfinite(pixels).all(axis=1)
        & np.isfinite(weights)
        & (weights > 0)
    )
    if valid.sum() < 4:
        raise ValueError("Need at least four valid landmark pairs.")

    w = np.clip(weights[valid], 0.0, 1.0)
    xyz = world[valid]
    uv = pixels[valid]

    # Center the paired coordinates to remove translation.
    xyz = xyz - np.average(xyz, axis=0, weights=w)
    uv = uv - np.average(uv, axis=0, weights=w)

    xyz *= np.sqrt(w)[:, None]
    uv *= np.sqrt(w)[:, None]

    # Regularization limits unstable scaling in nearly flat poses.
    gram = xyz.T @ xyz
    regularization = max(1e-4 * np.trace(gram), 1e-10)
    mapping = np.linalg.solve(
        gram + regularization * np.eye(3),
        xyz.T @ uv,
    )

    # Project the filtering displacement relative to the raw pixel.
    displacement = filtered - world[idx]
    projected = pixels[idx] + displacement @ mapping

    return int(round(projected[0])), int(round(projected[1]))


try:
    with landmark_gatherer.vision.PoseLandmarker.create_from_options(landmark_gatherer.options) as landmarker:

        data_tracker.logging_start()
        robot_director.start()

        t0 = time.perf_counter_ns() // 1000000
        robot_director.t0 = t0

        while (opencv_handler.frameCapOk):

            opencv_handler.frame_pushed.wait()
            opencv_handler.frame_pushed.clear()

            if (data_tracker.data_availability_queue_empty.is_set()):
                sys.exit(f"Data availability queue is empty. Exiting program.")

            with (opencv_handler.frame_lock):

                if not opencv_handler.frameCapOk:
                    break
                
                frame = opencv_handler.frame



            programOk = opencv_handler.finish_frame()
            if (not programOk):
                break

            landmark_gatherer.landmark_async_process_from_frame(landmarker, frame, (time.perf_counter_ns() // 1000000) - t0)

            if (landmark_gatherer.landmark_written.is_set()):
                landmarks, timestamp, screen_landmarks = landmark_gatherer.landmarks_get_with_timestamp()

                if not landmarks:
                    continue


                wrist_position = landmark_gatherer.wrist_position_get(landmarks)
                if wrist_position is not None:

                    frame_counter = 0
                    with opencv_handler.frame_counter_lock:
                        frame_counter = opencv_handler.frame_counter

                    data_ind = data_tracker.data_dict_init("timestamps")
                    data_tracker.data_element_add_group("timestamps", data_ind, ['t_obtained', 't_used', 'frame_used'], [timestamp, (time.perf_counter_ns() // 1000000) - t0, frame_counter])
                    data_tracker.data_quick_write("pre_filter_position", ['x', 'y', 'z', 't_write'], [wrist_position[0], wrist_position[1], wrist_position[2], timestamp])

                    wrist_position = landmark_processor.filter_wrist_position(wrist_position, (time.perf_counter_ns() // 1000000) - t0)
                    data_tracker.data_quick_write("post_filter_position", ['x', 'y', 'z', 't_write'], [wrist_position[0], wrist_position[1], wrist_position[2], timestamp])
                    position_mapped = landmark_mapper.wrist_map_to_robot(wrist_position)

                    data_tracker.data_element_add("timestamps", data_ind, "t_processed", (time.perf_counter_ns() // 1000000) - t0)

                    robot_director.update_target(position_mapped, data_ind)

                filtered_circle_point = project_filtered_world_to_pixel(screen_landmarks[0], landmarks[0], wrist_position, 16, 1920, 1080)
                cv2.circle(frame, (round(filtered_circle_point[0]), round(filtered_circle_point[1])), 12, (0, 255, 0), -1)

                unfiltered_circle_point = project_filtered_world_to_pixel(screen_landmarks[0], landmarks[0], wrist_position_unfiltered, 16, 1920, 1080)
                cv2.circle(frame, (round(unfiltered_circle_point[0]), round(unfiltered_circle_point[1])), 12, (0, 0, 255), -1)

            cv2.imshow("Teleoperator", frame)
            


finally:

    robot_director.end()
    data_tracker.logging_end()

    opencv_handler.end()

# this code only runs on successful execution of the program. If an error occurs these remaining lines won't run. If something MUST run put in in the "finally" above

data_format.data_finalize()

print("Program End")
