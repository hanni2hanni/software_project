from __future__ import division
import cv2
from .pupil import Pupil


class Calibration(object):
    """
    This class calibrates the pupil detection algorithm by finding the
    best binarization threshold value for the person and the webcam.
    """

    def __init__(self):
        self.nb_frames = 20
        self.thresholds_left = []
        self.thresholds_right = []

    def is_complete(self):
        """Returns true if the calibration is completed"""
        return len(self.thresholds_left) >= self.nb_frames and len(self.thresholds_right) >= self.nb_frames

    def get_threshold(self, eye_side):
        """
        返回给定眼睛的阈值。

        参数：
            eye_side: 指示是左眼（0）还是右眼（1）
        """
        if eye_side == 0:
            return int(sum(self.thresholds_left) / len(self.thresholds_left))
        elif eye_side == 1:
            return int(sum(self.thresholds_right) / len(self.thresholds_right))

    @staticmethod
    def calculate_iris_size(eye_frame):
        """
        返回虹膜在眼睛表面所占的百分比。

        参数：
            eye_frame (numpy.ndarray): 二值化的虹膜帧
        """
        trimmed_frame = eye_frame[5:-5, 5:-5]
        frame_height, frame_width = trimmed_frame.shape[:2]
        total_pixels = frame_height * frame_width
        black_pixels = total_pixels - cv2.countNonZero(trimmed_frame)
        return black_pixels / total_pixels

    @staticmethod
    def determine_optimal_threshold(eye_image):
        """
        计算用于二值化给定眼睛帧的最佳阈值。

        参数：
            eye_image (numpy.ndarray): 要分析的眼睛图像
        """
        avg_iris_size = 0.48
        trial_results = {}

        for threshold in range(5, 100, 5):
            processed_image = Pupil.process_eye_image(eye_image, threshold)
            trial_results[threshold] = Calibration.calculate_iris_size(processed_image)

        optimal_threshold, iris_size = min(trial_results.items(), key=lambda pair: abs(pair[1] - avg_iris_size))
        return optimal_threshold

    def assess_calibration(self, eye_image, eye_side):
        """
        通过考虑给定的图像来改进校准。

        参数：
            eye_image (numpy.ndarray): 眼睛的图像
            eye_side: 指示是左眼（0）还是右眼（1）
        """
        optimal_threshold = self.determine_optimal_threshold(eye_image)

        if eye_side == 0:
            self.thresholds_left.append(optimal_threshold)
        elif eye_side == 1:
            self.thresholds_right.append(optimal_threshold)