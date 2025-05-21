from __future__ import division
import os
import cv2
import dlib
from .eye import Eye
from .calibration import Calibration


class GazeTracking(object):
    """
    This class tracks the user's eyetrack.
    It provides useful information like the position of the eyes
    and pupils and allows to know if the eyes are open or closed
    """

    def __init__(self):
        self.frame = None
        self.eye_left = None
        self.eye_right = None
        self.calibration = Calibration()

        # _face_detector is used to detect faces
        self._face_detector = dlib.get_frontal_face_detector()

        # _predictor is used to get facial landmarks of a given face
        cwd = os.path.abspath(os.path.dirname(__file__))
        model_path = os.path.abspath(os.path.join(cwd, "trained_models/shape_predictor_68_face_landmarks.dat"))
        self._predictor = dlib.shape_predictor(model_path)

    @property
    def pupils_located(self):
        """Check that the pupils have been located"""
        try:
            int(self.eye_left.pupil.x)
            int(self.eye_left.pupil.y)
            int(self.eye_right.pupil.x)
            int(self.eye_right.pupil.y)
            return True
        except Exception:
            return False

    def _analyze(self):
        """Detects the face and initialize Eye objects"""
        frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        faces = self._face_detector(frame)

        try:
            landmarks = self._predictor(frame, faces[0])
            self.eye_left = Eye(frame, landmarks, 0, self.calibration)
            self.eye_right = Eye(frame, landmarks, 1, self.calibration)

        except IndexError:
            self.eye_left = None
            self.eye_right = None

    def refresh(self, frame):
        """Refreshes the frame and analyzes it.

        Arguments:
            frame (numpy.ndarray): The frame to analyze
        """
        self.frame = frame
        self._analyze()

    def get_left_eye_position(self):
        """Returns the coordinates of the left pupil"""
        if self.pupils_located:
            left_x = self.eye_left.origin[0] + self.eye_left.pupil.x
            left_y = self.eye_left.origin[1] + self.eye_left.pupil.y
            return (left_x, left_y)

    def get_right_eye_position(self):
        """Returns the coordinates of the right pupil"""
        if self.pupils_located:
            right_x = self.eye_right.origin[0] + self.eye_right.pupil.x
            right_y = self.eye_right.origin[1] + self.eye_right.pupil.y
            return (right_x, right_y)

    def get_horizontal_ratio(self):
        """Returns a number between 0.0 and 1.0 that indicates the
        horizontal direction of the eyetrack. The extreme right is 0.0,
        the center is 0.5 and the extreme left is 1.0
        """
        if self.pupils_located:
            left_eye_ratio = self.eye_left.pupil.x / (self.eye_left.center[0] * 2 - 10)
            right_eye_ratio = self.eye_right.pupil.x / (self.eye_right.center[0] * 2 - 10)
            return (left_eye_ratio + right_eye_ratio) / 2


    def look_right(self):
        """Returns true if the user is looking to the right"""
        if self.pupils_located:
            return self.get_horizontal_ratio() <= 0.55

    def look_left(self):
        """Returns true if the user is looking to the left"""
        if self.pupils_located:
            return self.get_horizontal_ratio() >= 0.45

    def look_center(self):
        """Returns true if the user is looking to the center"""
        if self.pupils_located:
            return self.look_right() is not True and self.look_left() is not True

    def look_down(self):
        """Returns true if the user closes his eyes"""
        if self.pupils_located:
            blinking_ratio = (self.eye_left.blinking + self.eye_right.blinking) / 2
            return blinking_ratio > 3.8



    def annotated_frame(self):
        """Returns the main frame with pupils highlighted"""
        annotated_frame = self.frame.copy()

        if self.pupils_located:
            highlight_color = (0, 255, 0)
            left_x, left_y = self.get_left_eye_position()
            right_x, right_y = self.get_right_eye_position()

            cv2.line(annotated_frame, (left_x - 5, left_y), (left_x + 5, left_y), highlight_color)
            cv2.line(annotated_frame, (left_x, left_y - 5), (left_x, left_y + 5), highlight_color)
            cv2.line(annotated_frame, (right_x - 5, right_y), (right_x + 5, right_y), highlight_color)
            cv2.line(annotated_frame, (right_x, right_y - 5), (right_x, right_y + 5), highlight_color)

        return annotated_frame
