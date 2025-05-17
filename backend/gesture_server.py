from flask import Flask, jsonify
from flask_cors import CORS
import mediapipe as mp
import cv2
import numpy as np
import time
import threading

app = Flask(__name__)
CORS(app)

class SignRe:
    def __init__(self):
        self.mp_drawing = mp.solutions.drawing_utils  # 和线样式
        self.mp_drawing_styles = mp.solutions.drawing_styles # 和线风格
        self.mp_hands = mp.solutions.hands  # 手势识别的API
        # 定义指尖索引
        self.TIP_IDS = [4, 8, 12, 16, 20]  # 拇指、食指、中指、无名指、小指
        self.cap = cv2.VideoCapture(0)
        self.image = None
        self.gesV = False
        self.fingers = []
        self.last_gesture = None
        self.last_gesture_time = 0
        self.gesture_cooldown = 3.0  # 改为3秒
        self.last_angle_print_time = 0
        self.angle_buffer = []
        self.joints_angle_buffer = []
        self.print_interval = 3.0  # 设置为3秒
        self.gesture_buffer = []

    def clear_last_gesture(self):
        """1秒后清空最后识别的手势"""
        time.sleep(1)  # 等待1秒
        self.last_gesture = None  # 清空手势

    def calculate_angle(self, a, b, c):
        """计算三个点之间的角度"""
        ba = a - b
        bc = c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.degrees(np.arccos(cosine_angle))
        return angle

    def finger_is_extended(self, landmarks, finger_tip_id):
        """检查指定的手指是否伸展"""
        if finger_tip_id == self.TIP_IDS[0]:  # 对于拇指，用不同的方法判断
            #print(self.TIP_IDS[0])
            #thumb_I = landmarks[self.TIP_IDS[0]]
            thumb_II = landmarks[self.TIP_IDS[0] - 1]
            thumb_III = landmarks[self.TIP_IDS[0] - 2]
            thumb_IV = landmarks[self.TIP_IDS[0] - 3]
            #thumb_V = landmarks[self.TIP_IDS[0] - 4]

            # 拇指需要特殊处理，因为它的方向与其他四指不同。
            angle2 = self.calculate_angle(
                np.array([thumb_II.x, thumb_II.y, thumb_II.z]),
                np.array([thumb_III.x, thumb_III.y, thumb_III.z]),
                np.array([thumb_IV.x, thumb_IV.y, thumb_IV.z])
            )
            return angle2 > 150  # 假设大于150度则认为拇指伸展

        else:
            finger_tip = landmarks[finger_tip_id]
            finger_dip = landmarks[finger_tip_id - 1]
            finger_pip = landmarks[finger_tip_id - 2]
            finger_mcp = landmarks[finger_tip_id - 3]

            # 计算两个角度: 指尖-远侧指间关节-近侧指间关节 和 远侧指间关节-近侧指间关节-掌骨基部
            angle_tip = self.calculate_angle(
                np.array([finger_tip.x, finger_tip.y, finger_tip.z]),
                np.array([finger_dip.x, finger_dip.y, finger_dip.z]),
                np.array([finger_pip.x, finger_pip.y, finger_pip.z])
            )

            angle_dip = self.calculate_angle(
                np.array([finger_dip.x, finger_dip.y, finger_dip.z]),
                np.array([finger_pip.x, finger_pip.y, finger_pip.z]),
                np.array([finger_mcp.x, finger_mcp.y, finger_mcp.z])
            )

            # 如果两个角度都足够大，则认为手指伸展
            return angle_tip > 160 and angle_dip > 90

    def calculate_thumb_angle_with_fingers(self, landmarks):
        # 计算拇指与其他手指的夹角
        thumb_direction = np.array([
            landmarks[4].x - landmarks[2].x,
            landmarks[4].y - landmarks[2].y
        ])
        
        # 使用中指作为其他手指的参考方向
        finger_direction = np.array([
            landmarks[12].x - landmarks[9].x,
            landmarks[12].y - landmarks[9].y
        ])
        
        # 计算夹角（度数）
        angle = np.degrees(np.arccos(
            np.clip(np.dot(thumb_direction, finger_direction) / 
            (np.linalg.norm(thumb_direction) * np.linalg.norm(finger_direction)), -1.0, 1.0)
        ))
        
        if angle > 90:
            angle = 180 - angle
        
       
        thumb_angle_joints = self.calculate_angle(
            np.array([landmarks[4].x, landmarks[4].y, landmarks[4].z]),
            np.array([landmarks[3].x, landmarks[3].y, landmarks[3].z]),
            np.array([landmarks[2].x, landmarks[2].y, landmarks[2].z])
        )
        
       
        self.angle_buffer.append(angle)
        self.joints_angle_buffer.append(thumb_angle_joints)
        
        # 每3秒计算并输出一次平均值
        current_time = time.time()
        if current_time - self.last_angle_print_time >= self.print_interval:
            if self.angle_buffer and self.joints_angle_buffer:
                avg_angle = sum(self.angle_buffer) / len(self.angle_buffer)
                avg_joints_angle = sum(self.joints_angle_buffer) / len(self.joints_angle_buffer)
              #  print(f" 拇指关节角度: {avg_joints_angle:.2f}度, 与其他手指夹角: {avg_angle:.2f}度")
                
                # 基于平均值进行手势判断
                if self.gesture_buffer:
                    most_common_gesture = max(set(self.gesture_buffer), key=self.gesture_buffer.count)
                    self.last_gesture = most_common_gesture
                    print(f"识别到手势：{most_common_gesture}")

                    threading.Thread(target=self.clear_last_gesture).start()
                
                # 清空所有缓冲区
                self.angle_buffer = []
                self.joints_angle_buffer = []
                self.gesture_buffer = []
                self.last_angle_print_time = current_time
            
        return angle, thumb_angle_joints

    def ges(self, hand_landmarks):
        """识别手势"""
        for tip in self.TIP_IDS:
            if self.finger_is_extended(hand_landmarks.landmark, tip):
                self.fingers.append(1)
            else:
                self.fingers.append(0)

        thumb_angle, thumb_joints_angle = self.calculate_thumb_angle_with_fingers(hand_landmarks.landmark)
        
        # 判断其他四指是否蜷缩
        other_fingers_folded = self.fingers[1:] == [0, 0, 0, 0]
        
        # 将手势判断结果存入缓冲区，不立即输出
        if other_fingers_folded:
            if thumb_angle < 45 and thumb_joints_angle < 160:
                self.gesture_buffer.append("握拳")
            elif 45 <= thumb_angle <= 90 and thumb_joints_angle > 160:
                self.gesture_buffer.append("竖拇指")
        elif self.fingers == [1, 1, 1, 1, 1]:
            self.gesture_buffer.append("挥手")

        gesture_value = int("".join(str(x) for x in self.fingers), 2)
        self.fingers = []
        return gesture_value

    def start(self):
        with self.mp_hands.Hands(
                static_image_mode=False,  # False表示为视频流检测
                max_num_hands=2,  # 最大可检测到两只手掌
                model_complexity=0,  # 可设为0或者1，主要跟模型复杂度有关
                min_detection_confidence=0.5,  # 最大检测阈值
                min_tracking_confidence=0.5  # 最小追踪阈值
        ) as hands:
            while True:  # 判断相机是否打开
                success, self.image = self.cap.read()  # 返回两个值：一个表示状态，一个是图像矩阵
                if self.image is None:
                    break
                self.image.flags.writeable = False  # 将图像矩阵修改为仅读模式
                self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                t0 = time.time()
                results = hands.process(self.image)  # 使用API处理图像图像
                '''
                results.multi_handedness
                包括label和score,label是字符串"Left"或"Right",score是置信度
                results.multi_hand_landmarks
                results.multi_hand_landmrks:被检测/跟踪的手的集合
                其中每只手被表示为21个手部地标的列表,每个地标由x、y和z组成。
                x和y分别由图像的宽度和高度归一化为[0.0,1.0]。Z表示地标深度
                以手腕深度为原点，值越小，地标离相机越近。 
                z的大小与x的大小大致相同。
                '''
                t1 = time.time()
        
                time_diff = t1 - t0
                fps = 1 / time_diff if time_diff > 0 else 0  # 如果时间差为0，则fps也设为0
                # print('++++++++++++++fps',fps)
                self.image.flags.writeable = True  # 将图像矩阵修改为读写模式
                self.image = cv2.cvtColor(self.image, cv2.COLOR_RGB2BGR)  # 将图像变回BGR形式
                dict_handnumber = {}  # 创建一个字典。保存左右手的手势情况
                if results.multi_handedness:  
                    if len(results.multi_handedness) == 2:  # 如果检测到两只手
                        for i in range(len(results.multi_handedness)):
                            label = results.multi_handedness[i].classification[0].label  # 获得Label判断是哪几手
                            index = results.multi_handedness[i].classification[0].index  # 获取左右手的索引号
                            hand_landmarks = results.multi_hand_landmarks[index]  # 根据相应的索引号获取xyz值
                            self.mp_drawing.draw_landmarks(
                                self.image,
                                hand_landmarks,
                                self.mp_hands.HAND_CONNECTIONS,  # 用于指定地标如何在图中连接。
                                self.mp_drawing_styles.get_default_hand_landmarks_style(),  # 如果设置为None.则不会在图上标出关键点
                                self.mp_drawing_styles.get_default_hand_connections_style())  # 关键点的连接风格
                            gesresult = self.ges(hand_landmarks)  # 传入21个关键点集合，返回数字
                            dict_handnumber[label] = gesresult  # 与对应的手进行保存为字典
                    else:  # 如果仅检测到一只手
                        label = results.multi_handedness[0].classification[0].label  # 获得Label判断
                        hand_landmarks = results.multi_hand_landmarks[0]

                        self.mp_drawing.draw_landmarks(
                            self.image,
                            hand_landmarks,
                            self.mp_hands.HAND_CONNECTIONS,  # 用于指定地标如何在图中连接。
                            self.mp_drawing_styles.get_default_hand_landmarks_style(),  # 如果设置为None.则不会在图上标出关键点
                            self.mp_drawing_styles.get_default_hand_connections_style())  # 关键点的连接风格
                        gesresult = self.ges(hand_landmarks)  # 传入21个关键点集合，返回数字
                        dict_handnumber[label] = gesresult  # 与对应的手进行保存为字典
                if len(dict_handnumber) == 2:  # 如果有两只手，则进入
                    # print(dict_handnumber)
                    leftnumber = dict_handnumber['Right']
                    rightnumber = dict_handnumber['Left']
                    '''
                    显示实时帧率，右手值，左手值，相加值
                    '''
                    s = 'FPS:{0}\nRighthand Value:{1}\nLefthand Value:{2}\nAdd is:{3}'.format(int(fps), rightnumber, leftnumber,
                                                                                              str(leftnumber + rightnumber))  # 图像上的文字内容
                elif len(dict_handnumber) == 1:  # 如果仅有一只手则进入
                    labelvalue = list(dict_handnumber.keys())[0]  # 判断检测到的是哪只手
                    if labelvalue == 'Left':  # 左手,不知为何，模型总是将左右手搞反，则引入人工代码纠正
                        number = list(dict_handnumber.values())[0]
                        s = 'FPS:{0}\nRighthand Value:{1}\nLefthand Value:0\nAdd is:{2}'.format(int(fps), number, number)
                    else:  # 右手
                        number = list(dict_handnumber.values())[0]
                        s = 'FPS:{0}\nLefthand Value:{1}\nRighthand Value:0\nAdd is:{2}'.format(int(fps), number, number)
                else:  # 如果没有检测到则只显示帧率
                    s = 'FPS:{0}\n'.format(int(fps))

                y0, dy = 50, 25  # 文字放置初始坐标
                self.image = cv2.flip(self.image, 1)  # 反转图像
                for i, txt in enumerate(s.split('\n')):  # 根据\n来竖向排列文字
                    y = y0 + i * dy
                    cv2.putText(self.image, txt, (50, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)
                cv2.imshow('MediaPipe Gesture Recognition', self.image)  # 显示图像

                # cv2.imwrite('save/{0}.jpg'.format(t1),image)
                if cv2.waitKey(5) & 0xFF == 27:
                    break
            self.cap.release()

@app.route('/api/gesture', methods=['GET'])
def get_gesture():
    if Sg.last_gesture:
        return jsonify({"gesture": Sg.last_gesture})
    return jsonify({"gesture": "无手势"})

if __name__ == "__main__":
    Sg = SignRe()
    threading.Thread(target=Sg.start).start()  # 在新线程中启动手势识别
    app.run(host='0.0.0.0', port=5000)
