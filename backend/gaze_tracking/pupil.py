import numpy as np
import cv2


class Pupil(object):
    """
    This class detects the iris of an eye and estimates
    the position of the pupil
    """

    def __init__(self, eye_frame, threshold):
        self.iris_frame = None
        self.threshold = threshold
        self.x = None
        self.y = None

        self.detect_iris(eye_frame)

    @staticmethod
    def process_eye_image(eye_frame, threshold):
        """Performs operations on the eye frame to isolate the iris

        Arguments:
            eye_frame (numpy.ndarray): Frame containing an eye and nothing else
            threshold (int): Threshold value used to binarize the eye frame

        Returns:
            A frame with a single element representing the iris
        """
        # 创建一个3x3的结构元素
        structuring_element = np.ones((3, 3), np.uint8)

        # 对眼睛图像进行双边滤波，以减少噪声并保持边缘
        filtered_eye_image = cv2.bilateralFilter(eye_frame, 10, 15, 15)

        # 使用结构元素对图像进行腐蚀操作，以去除小的干扰
        eroded_image = cv2.erode(filtered_eye_image, structuring_element, iterations=3)

        # 使用给定的阈值对图像进行二值化处理
        binary_image = cv2.threshold(eroded_image, threshold, 255, cv2.THRESH_BINARY)[1]

        # 返回处理后的二值化图像
        return binary_image

    def detect_iris(self, eye_frame):
        """Detects the iris and estimates the position of the iris by
        calculating the centroid.

        Arguments:
            eye_frame (numpy.ndarray): Frame containing an eye and nothing else
        """
        self.iris_frame = self.process_eye_image(eye_frame, self.threshold)

        contours, _ = cv2.findContours(self.iris_frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)[-2:]
        sorted_contours = sorted(contours, key=cv2.contourArea)

        try:
            # 计算轮廓的矩
            contour_moments = cv2.moments(sorted_contours[-2])
            # 计算质心的 x 和 y 坐标
            self.x = int(contour_moments['m10'] / contour_moments['m00'])
            self.y = int(contour_moments['m01'] / contour_moments['m00'])
        except (IndexError, ZeroDivisionError):
            # 如果发生错误，跳过
            pass
