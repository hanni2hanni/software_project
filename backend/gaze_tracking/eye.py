import math
import numpy as np
import cv2
from .pupil import Pupil


class Eye(object):
    """
    This class creates a new frame to isolate the eye and
    initiates the pupil detection.
    """

    LEFT_EYE_POINTS = [36, 37, 38, 39, 40, 41]
    RIGHT_EYE_POINTS = [42, 43, 44, 45, 46, 47]

    def __init__(self, original_frame, landmarks, side, calibration):
        self.frame = None
        self.origin = None
        self.center = None
        self.pupil = None
        self.landmark_points = None

        self._analyze(original_frame, landmarks, side, calibration)

    @staticmethod
    def _middle_point(p1, p2):
        """Returns the middle point (x,y) between two points

        Arguments:
            p1 (dlib.point): First point
            p2 (dlib.point): Second point
        """
        x = int((p1.x + p2.x) / 2)
        y = int((p1.y + p2.y) / 2)
        return (x, y)

    def extract_eye(self, img_frame, face_landmarks, eye_indices):
        """
        隔离一只眼睛，以获得一个不包含面部其他部分的帧。

        参数：
            img_frame (numpy.ndarray): 包含面部的帧
            face_landmarks (dlib.full_object_detection): 面部特征点
            eye_indices (list): 眼睛的特征点（从68个Multi-PIE特征点中提取）
        """
        eye_region = np.array([(face_landmarks.part(idx).x, face_landmarks.part(idx).y) for idx in eye_indices])
        eye_region = eye_region.astype(np.int32)
        self.landmark_points = eye_region

        # 应用掩模以仅获取眼睛部分
        frame_height, frame_width = img_frame.shape[:2]
        black_background = np.zeros((frame_height, frame_width), np.uint8)
        mask_layer = np.full((frame_height, frame_width), 255, np.uint8)
        cv2.fillPoly(mask_layer, [eye_region], (0, 0, 0))
        isolated_eye = cv2.bitwise_not(black_background, img_frame.copy(), mask=mask_layer)

        # 对眼睛进行裁剪
        crop_margin = 5
        min_x = np.min(eye_region[:, 0]) - crop_margin
        max_x = np.max(eye_region[:, 0]) + crop_margin
        min_y = np.min(eye_region[:, 1]) - crop_margin
        max_y = np.max(eye_region[:, 1]) + crop_margin

        self.frame = isolated_eye[min_y:max_y, min_x:max_x]
        self.origin = (min_x, min_y)

        eye_height, eye_width = self.frame.shape[:2]
        self.center = (eye_width / 2, eye_height / 2)

    def calculate_blinking_ratio(self, landmarks, eye_points):
        """
        计算一个比率，该比率可以指示眼睛是否闭合。
        它是眼睛宽度与高度的比值。

        参数：
            landmarks (dlib.full_object_detection): 面部特征点
            eye_points (list): 眼睛的特征点（从68个Multi-PIE特征点中提取）

        返回：
            计算出的比率
        """
        left_point = (landmarks.part(eye_points[0]).x, landmarks.part(eye_points[0]).y)
        right_point = (landmarks.part(eye_points[3]).x, landmarks.part(eye_points[3]).y)
        top_point = self._middle_point(landmarks.part(eye_points[1]), landmarks.part(eye_points[2]))
        bottom_point = self._middle_point(landmarks.part(eye_points[5]), landmarks.part(eye_points[4]))

        eye_width = math.hypot((left_point[0] - right_point[0]), (left_point[1] - right_point[1]))
        eye_height = math.hypot((top_point[0] - bottom_point[0]), (top_point[1] - bottom_point[1]))

        try:
            ratio = eye_width / eye_height
        except ZeroDivisionError:
            ratio = None

        return ratio

    def _analyze(self, input_frame, facial_landmarks, eye_side, calib):
        """
        检测并隔离新帧中的眼睛，将数据发送到校准模块，并初始化瞳孔对象。

        参数：
            input_frame (numpy.ndarray): 用户传递的帧
            facial_landmarks (dlib.full_object_detection): 面部特征点
            eye_side: 指示是左眼（0）还是右眼（1）
            calib (calibration.Calibration): 管理二值化阈值
        """
        if eye_side == 0:
            eye_points = self.LEFT_EYE_POINTS
        elif eye_side == 1:
            eye_points = self.RIGHT_EYE_POINTS
        else:
            return

        self.blinking = self.calculate_blinking_ratio(facial_landmarks, eye_points)
        self.extract_eye(input_frame, facial_landmarks, eye_points)

        if not calib.is_complete():
            calib.assess_calibration(self.frame, eye_side)

        threshold_value = calib.get_threshold(eye_side)
        self.pupil = Pupil(self.frame, threshold_value)
