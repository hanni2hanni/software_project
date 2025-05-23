import cv2
from gaze_tracking import GazeTracking
from flask import Flask, jsonify
from flask_cors import CORS
import threading
import time

app = Flask(__name__)
CORS(app)

eyetrack = GazeTracking()
webcam = cv2.VideoCapture(0)
current_gaze = "保持居中"

def main():
    global current_gaze
    while True: 
        _, frame = webcam.read()
        eyetrack.refresh(frame)

        frame = eyetrack.annotated_frame()
        text = ""

        if eyetrack.look_down():
            text = "looking down"
            current_gaze = "向下看"
        elif eyetrack.look_right():
            text = "Looking right"
            current_gaze = "向右看"
        elif eyetrack.look_left():
            text = "Looking left"
            current_gaze = "向左看"
        elif eyetrack.look_center():
            text = "Looking center"
            current_gaze = "保持居中"

        print("main: ", current_gaze)
        cv2.putText(frame, text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)
        cv2.imshow("eyetrack", frame)

        if cv2.waitKey(1) == 27:
            break

    webcam.release()
    cv2.destroyAllWindows()

@app.route('/api/eye-tracking', methods=['GET'])
def get_gaze():
    global current_gaze
    print("get_gaze: ", current_gaze)
    return jsonify({'eye-tracking': current_gaze})

if __name__ == '__main__':
    threading.Thread(target=main).start()
    app.run(host='0.0.0.0', port=5000)
