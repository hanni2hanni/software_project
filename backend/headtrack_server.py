from scipy.spatial import distance as dist
from imutils.video import FileVideoStream
from imutils.video import VideoStream
from imutils import face_utils
import argparse
import imutils
import time
import dlib
import cv2
import numpy as np
from flask import Flask, jsonify
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)

head_movement = "无头部动作"
movement_lock = threading.Lock()  # 用于保护 head_movement 的线程锁

def calculate_nose_to_jaw_distances(nose_points, jaw_points):
    distance_left1 = dist.euclidean(nose_points[0], jaw_points[0])  # 27, 0
    distance_right1 = dist.euclidean(nose_points[0], jaw_points[16])  # 27, 16
    distance_left2 = dist.euclidean(nose_points[3], jaw_points[2])  # 30, 2
    distance_right2 = dist.euclidean(nose_points[3], jaw_points[14])  # 30, 14
    result_distances = (distance_left1, distance_right1, distance_left2, distance_right2)
    return result_distances

def calculate_eyebrow_to_jaw_distances(left_eyebrow_points, jaw_points):
    distance_eyebrow_left = dist.euclidean(left_eyebrow_points[2], jaw_points[0])  # 24, 0
    distance_eyebrow_right = dist.euclidean(left_eyebrow_points[2], jaw_points[16])  # 24, 16
    distance_jaw_width = dist.euclidean(jaw_points[0], jaw_points[16])  # 0, 16
    result_distances = (distance_eyebrow_left, distance_eyebrow_right, distance_jaw_width)
    return result_distances

# 参数解析器
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--shape-predictor", default="gaze_tracking/trained_models/shape_predictor_68_face_landmarks.dat",
                help="path to facial landmark predictor")
ap.add_argument("-v", "--video", type=str, default="camera",
                help="path to input video file")

def reset_head_movement():
    global head_movement
    while True:
        time.sleep(3)  # 每3秒执行一次
        with movement_lock:
            head_movement = "无头部动作"  # 重置为无头部动作
            print("head_movement 已重置为无头部动作")

def main():
    # Parse command line arguments
    arguments = vars(ap.parse_args())

    # Initialize face detector and facial landmark predictor
    face_detector = dlib.get_frontal_face_detector()
    landmark_predictor = dlib.shape_predictor(arguments["shape_predictor"])

    # Initialize counters
    left_counter = 0
    right_counter = 0
    total_face_movements = 0
    nod_counter = 0
    total_nods = 0

    # Get facial landmark indices
    (nose_start, nose_end) = face_utils.FACIAL_LANDMARKS_IDXS["nose"]
    (jaw_start, jaw_end) = face_utils.FACIAL_LANDMARKS_IDXS['jaw']
    (eyebrow_start, eyebrow_end) = face_utils.FACIAL_LANDMARKS_IDXS['left_eyebrow']

    # Initialize video stream
    if arguments['video'] == "camera":
        video_stream = VideoStream(src=0).start()
        is_file_stream = False
    else:
        video_stream = FileVideoStream(arguments["video"]).start()
        is_file_stream = True

    time.sleep(1.0)

    global head_movement
    while True:
        # Check if there are more frames in the video stream
        if is_file_stream and not video_stream.more():
            break

        # Read a frame from the video stream
        frame = video_stream.read()
        if frame is None:
            break

        # Resize the frame and convert to grayscale
        frame = imutils.resize(frame, width=600)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected_faces = face_detector(gray_frame, 0)

        # Default status is "still"
        current_status = "Still"
        
        for face in detected_faces:
            landmarks = landmark_predictor(gray_frame, face)
            landmarks = face_utils.shape_to_np(landmarks)

            nose_points = landmarks[nose_start:nose_end]
            jaw_points = landmarks[jaw_start:jaw_end]
            nose_jaw_distances = calculate_nose_to_jaw_distances(nose_points, jaw_points)

            left_eyebrow_points = landmarks[eyebrow_start:eyebrow_end]
            eyebrow_jaw_distances = calculate_eyebrow_to_jaw_distances(left_eyebrow_points, jaw_points)

            nose_jaw_left1 = nose_jaw_distances[0]
            nose_jaw_right1 = nose_jaw_distances[1]
            nose_jaw_left2 = nose_jaw_distances[2]
            nose_jaw_right2 = nose_jaw_distances[3]

            eyebrow_jaw_left = eyebrow_jaw_distances[0]
            eyebrow_jaw_right = eyebrow_jaw_distances[1]
            jaw_width = eyebrow_jaw_distances[2]

            # Nod detection
            if eyebrow_jaw_left + eyebrow_jaw_right <= jaw_width + 3:
                nod_counter += 1
            elif nod_counter != 0 and eyebrow_jaw_left + eyebrow_jaw_right >= jaw_width + 3:
                total_nods += 1
                print(f"检测到第{total_nods}次点头")
                with movement_lock:
                    head_movement = "点头"
                current_status = "Nod"
                nod_counter = 0

            # If not nodding, check for head shaking
            if current_status == "Still":
                if nose_jaw_left1 >= nose_jaw_right1 + 4 and nose_jaw_left2 >= nose_jaw_right2 + 4:
                    left_counter += 1
                if nose_jaw_right1 >= nose_jaw_left1 + 4 and nose_jaw_right2 >= nose_jaw_left2 + 4:
                    right_counter += 1
                if left_counter != 0 and right_counter != 0:
                    total_face_movements += 1
                    print(f"检测到第{total_face_movements}次摇头")
                    with movement_lock:
                        head_movement = "摇头"
                    current_status = "Shake"
                    right_counter = 0
                    left_counter = 0

        # Display the frame
        cv2.imshow("headtrack", frame)
        key = cv2.waitKey(1) & 0xFF

        # Exit on 'q' key press
        if key == ord("q"):
            break

    # Clean up
    cv2.destroyAllWindows()
    video_stream.stop()

@app.route('/api/head-movement', methods=['GET'])
def get_head_movement():
    with movement_lock:  # 保护对 head_movement 的读取
        return jsonify({"head_movement": head_movement})

if __name__ == "__main__":
    # 启动一个线程来重置 head_movement
    threading.Thread(target=reset_head_movement, daemon=True).start()
    threading.Thread(target=main).start()  # 在新线程中启动手势识别
    app.run(host='0.0.0.0', port=5000)
