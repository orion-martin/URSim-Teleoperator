import mediapipe
from mediapipe.tasks.python import vision
from pathlib import Path
import threading

MODEL_PATH = Path(__file__).parent / "pose_landmarker_full.task"

snapshot = {"landmarks": None, "timestamp": 0, "screen_landmarks": None}
landmark_lock = threading.Lock()
landmark_written = threading.Event()
landmark_written.clear()

frame_lookup_table = {}

def on_result(result, output_image, timestamp_ms):
    with landmark_lock:
        snapshot["landmarks"] = result.pose_world_landmarks
        snapshot["screen_landmarks"] = result.pose_landmarks
        snapshot["timestamp"] = timestamp_ms 
        landmark_written.set()
    
base_options = mediapipe.tasks.BaseOptions(model_asset_path = str(MODEL_PATH))
options = vision.PoseLandmarkerOptions(base_options=base_options, running_mode = vision.RunningMode.LIVE_STREAM, result_callback = on_result)

# wrist ID in mediapipe is 16
WRIST_ID = 16

VIS_THRESHOLD = 0.1

def wrist_position_get(world_landmarks):
    wrist = world_landmarks[0][WRIST_ID]
    if wrist.visibility < VIS_THRESHOLD:
        raise Exception(f"NOT ENOUGH VISIBLITY ON HAND! PLEASE SELECT DIFFERENT VIDEO")
    return [wrist.x, wrist.y, wrist.z]

def landmark_async_process_from_frame(landmarker, frame, timestamp, frame_ind):
    mediapipe_image = mediapipe.Image(image_format = mediapipe.ImageFormat.SRGB, data = frame)
    landmarker.detect_async(mediapipe_image, timestamp)

    frame_lookup_table[timestamp] = frame_ind


def landmarks_get_with_timestamp():
    with landmark_lock:
        landmark_written.clear()
        return (snapshot["landmarks"], snapshot["timestamp"], snapshot["screen_landmarks"])