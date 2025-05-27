# import the necessary packages
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
from PIL import Image, ImageDraw, ImageFont

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

class HeadTracker:
    def __init__(self, predictor_path='sight/gaze_tracking/trained_models/shape_predictor_68_face_landmarks.dat'):
        self.face_detector = dlib.get_frontal_face_detector()
        self.landmark_predictor = dlib.shape_predictor(predictor_path)
        self.left_counter = 0
        self.right_counter = 0
        self.total_face_movements = 0
        self.nod_counter = 0
        self.total_nods = 0
        self.last_status = '静止'
        self.nod_flag = False
        self.shake_flag = False
        self.nod_time = 0
        self.shake_time = 0
        self.last_nod_time = 0
        self.last_shake_time = 0

    def get_status(self, frame):
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected_faces = self.face_detector(gray_frame, 0)
        status = '静止'
        for face in detected_faces:
            landmarks = self.landmark_predictor(gray_frame, face)
            landmarks = face_utils.shape_to_np(landmarks)
            # 头部点
            (nose_start, nose_end) = face_utils.FACIAL_LANDMARKS_IDXS["nose"]
            (jaw_start, jaw_end) = face_utils.FACIAL_LANDMARKS_IDXS['jaw']
            (eyebrow_start, eyebrow_end) = face_utils.FACIAL_LANDMARKS_IDXS['left_eyebrow']
            nose_points = landmarks[nose_start:nose_end]
            jaw_points = landmarks[jaw_start:jaw_end]
            left_eyebrow_points = landmarks[eyebrow_start:eyebrow_end]
            # 点头检测
            distance_eyebrow_left = np.linalg.norm(left_eyebrow_points[2] - jaw_points[0])
            distance_eyebrow_right = np.linalg.norm(left_eyebrow_points[2] - jaw_points[16])
            jaw_width = np.linalg.norm(jaw_points[0] - jaw_points[16])
            if distance_eyebrow_left + distance_eyebrow_right <= jaw_width + 3:
                self.nod_counter += 1
            elif self.nod_counter != 0 and distance_eyebrow_left + distance_eyebrow_right >= jaw_width + 3:
                self.total_nods += 1
                self.nod_counter = 0
                self.last_nod_time = time.time()
                status = '点头'
            # 摇头检测
            distance_left1 = np.linalg.norm(nose_points[0] - jaw_points[0])
            distance_right1 = np.linalg.norm(nose_points[0] - jaw_points[16])
            distance_left2 = np.linalg.norm(nose_points[3] - jaw_points[2])
            distance_right2 = np.linalg.norm(nose_points[3] - jaw_points[14])
            if distance_left1 >= distance_right1 + 4 and distance_left2 >= distance_right2 + 4:
                self.left_counter += 1
            if distance_right1 >= distance_left1 + 4 and distance_right2 >= distance_left2 + 4:
                self.right_counter += 1
            if self.left_counter != 0 and self.right_counter != 0:
                self.total_face_movements += 1
                self.right_counter = 0
                self.left_counter = 0
                self.last_shake_time = time.time()
                status = '摇头'
        # 状态保持1秒
        now = time.time()
        if status == '静止':
            if now - self.last_nod_time < 1:
                status = '点头'
            elif now - self.last_shake_time < 1:
                status = '摇头'
        self.last_status = status
        return status

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

if __name__ == '__main__':
    main()
