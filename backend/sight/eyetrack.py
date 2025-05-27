"""
Demonstration of the GazeTracking library.
Check the README.md for complete documentation.
"""

import cv2
from gaze_tracking import GazeTracking

eyetrack = GazeTracking()
webcam = cv2.VideoCapture(0)

while True:
    # We get a new frame from the webcam
    _, frame = webcam.read()

    # We send this frame to GazeTracking to analyze it
    eyetrack.refresh(frame)

    frame = eyetrack.annotated_frame()
    text = ""

    if eyetrack.look_down():
        text = "looking down"
        print(f"向下看")
    elif eyetrack.look_right():
        text = "Looking right"
        print(f"向右看")
    elif eyetrack.look_left():
        text = "Looking left"
        print(f"向左看")
    elif eyetrack.look_center():
        text = "Looking center"
        print(f"保持居中")


    cv2.putText(frame, text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)

    cv2.imshow("eyetrack", frame)

    if cv2.waitKey(1) == 27:
        break
   
webcam.release()
cv2.destroyAllWindows()
