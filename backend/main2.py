import threading
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import datetime
import dlib
import numpy as np
from imutils import face_utils

import sys
sys.path.append(r'C:\Users\张瑜\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages')
from flask import Flask, jsonify
from flask_cors import CORS

# 视觉识别
from sight.gaze_tracking import GazeTracking
from sight.headtrack import HeadTracker
# 手势识别
from gesture.gesture import SignRe
# 语音识别
from voice import record
# 用户管理
from user_manager import UserManager

# 日志分析和用户分析
from log_analyzer import LogAnalyzer
from profile_analytics import ProfileAnalytics

LOG_FILE = 'log.txt'
app = Flask(__name__)
CORS(app)

# 用于存储识别结果的全局字典
recognition_results = {
    'gaze': '',
    'headpose': '',
    'gesture': '',
    'voice': ''
}

# 头部姿态检测类
class HeadPoseDetector:
    def __init__(self, predictor_path='sight/gaze_tracking/trained_models/shape_predictor_68_face_landmarks.dat'):
        self.face_detector = dlib.get_frontal_face_detector()
        self.landmark_predictor = dlib.shape_predictor(predictor_path)
        self.nod_counter = 0
        self.shake_counter = 0
        self.last_status = '静止'
        self.nod_flag = False
        self.shake_flag = False
        self.nod_time = 0
        self.shake_time = 0

    def get_pose(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector(gray, 0)
        status = '静止'
        for face in faces:
            shape = self.landmark_predictor(gray, face)
            shape = face_utils.shape_to_np(shape)
            # 点头检测
            brow = shape[21:27]  # 左右眉毛
            jaw = shape[6:11]    # 下颌
            brow_y = np.mean(brow[:, 1])
            jaw_y = np.mean(jaw[:, 1])
            dist = jaw_y - brow_y
            if dist > 70 and not self.nod_flag:
                self.nod_counter += 1
                self.nod_flag = True
                self.nod_time = time.time()
                status = '点头'
            elif dist <= 70:
                self.nod_flag = False
            # 摇头检测
            jaw_left = shape[6]
            jaw_right = shape[10]
            nose = shape[30]
            if (jaw_left[0] - nose[0] > 40 or nose[0] - jaw_right[0] > 40) and not self.shake_flag:
                self.shake_counter += 1
                self.shake_flag = True
                self.shake_time = time.time()
                status = '摇头'
            elif abs(jaw_left[0] - nose[0]) <= 40 and abs(nose[0] - jaw_right[0]) <= 40:
                self.shake_flag = False
        if status == '静止' and (self.nod_flag or self.shake_flag):
            status = self.last_status
        self.last_status = status
        return status

USER_TYPES = ['驾驶员', '乘客', '维护人员', '管理人员']
USER_PERMISSIONS = {
    '驾驶员': '可操作驾驶相关功能，查看多模态识别结果',
    '乘客': '仅可查看多模态识别结果，部分操作受限',
    '维护人员': '可查看系统日志，维护系统',
    '管理人员': '可管理所有用户和系统设置，拥有全部权限'
}

class User:
    def __init__(self, username, user_type):
        self.username = username
        self.user_type = user_type
        self.permissions = USER_PERMISSIONS.get(user_type, '')

class MultiModalApp:
    def __init__(self, root):
        self.root = root
        self.root.title('车载多模态交互系统')
        self.root.geometry('1200x700')
        self.root.resizable(False, False)
        self.root.configure(bg='#f0f4f8')

        self.flash_flag = True
        self.last_gaze_time = time.time()
        self.gaze_off_road = False
        self.warning_active = False
        self.music_playing = True
        self.music_checked = False
        self.navigation_checked = False
        self.last_status = ''
        self.gesture_pause_buffer = []  # 用于音乐场景挥手去抖动

        # 左侧功能区
        self.scene_frame = tk.Frame(self.root, bg='#e3eaf2')
        self.scene_frame.place(x=0, y=0, width=260, height=700)

        # 多模态输出区
        self.result_frame = tk.Frame(self.scene_frame, bg='#f7fafc', highlightbackground='#1a73e8', highlightthickness=2)
        self.result_frame.place(x=10, y=10, width=240, height=650)
        self.result_title = tk.Label(self.result_frame, text='多模态识别结果', font=('微软雅黑', 14, 'bold'), fg='#1a73e8', bg='#f7fafc')
        self.result_title.pack(pady=(10, 0))
        self.result_text = tk.Text(self.result_frame, font=('微软雅黑', 12), wrap='word', bg='#f7fafc', fg='#222',
                                   relief='flat', borderwidth=0, height=20)
        self.result_text.pack(fill='both', expand=True, padx=8, pady=8)
        self.result_text.tag_configure('label', foreground='#1a73e8', font=('微软雅黑', 12, 'bold'))
        self.result_text.tag_configure('value', foreground='#222', font=('微软雅黑', 12))

        # 右侧摄像头画面
        self.video_label = tk.Label(self.root, bg='#222')
        self.video_label.place(x=270, y=10, width=900, height=480)

        # 状态栏和仪表盘图标
        self.status_label = tk.Label(self.root, text='', font=('微软雅黑', 18, 'bold'), bg='#f0f4f8')
        self.status_label.place(x=270, y=500, width=700, height=40)

        # 用户管理
        self.user_manager = UserManager()
        self.create_user_panel()

        # 初始化识别器
        self.gaze = GazeTracking()
        self.gesture = SignRe()
        self.headpose = HeadTracker()
        self.cap = cv2.VideoCapture(0)

        self.last_gaze = ''
        self.last_gesture = ''
        self.last_voice = ''
        self.last_headpose = '静止'

        self.update_frame()

        # 新增
        self.log_analyzer = LogAnalyzer()
        self.profile_analytics = ProfileAnalytics()

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(30, self.update_frame)
            return

        # 头部姿态
        headpose_result = self.headpose.get_status(frame)
        self.last_headpose = headpose_result

        # 手势识别
        gesture_result = self.detect_gesture(frame)

        # 目光区域
        self.gaze.refresh(frame)
        gaze_result = ''
        if self.gaze.look_down():
            gaze_result = '向下看'
        elif self.gaze.look_right():
            gaze_result = '向右看'
        elif self.gaze.look_left():
            gaze_result = '向左看'
        elif self.gaze.look_center():
            gaze_result = '眼睛居中'
        else:
            gaze_result = '未检测到眼动'
        self.last_gaze = gaze_result

        # 更新全局字典
        recognition_results['gaze'] = gaze_result
        recognition_results['headpose'] = headpose_result
        recognition_results['gesture'] = gesture_result
        recognition_results['voice'] = self.last_voice

        # 画面显示
        show_frame = self.gaze.annotated_frame()
        if show_frame is None:
            show_frame = frame

        display_frame = cv2.cvtColor(show_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(display_frame)
        img = img.resize((900, 480))
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

        # 结果文本美化输出
        self.result_text.config(state='normal')
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, '视觉: ', 'label')
        self.result_text.insert(tk.END, f'{gaze_result}\n', 'value')
        self.result_text.insert(tk.END, '头部姿态: ', 'label')
        self.result_text.insert(tk.END, f'{headpose_result}\n', 'value')
        self.result_text.insert(tk.END, '手势: ', 'label')
        self.result_text.insert(tk.END, f'{gesture_result}\n', 'value')
        self.result_text.insert(tk.END, '语音: ', 'label')
        self.result_text.insert(tk.END, f'{self.last_voice}\n', 'value')
        self.result_text.config(state='disabled')

        self.root.after(30, self.update_frame)

    def detect_gesture(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        with self.gesture.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as hands:
            results = hands.process(rgb_frame)
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.gesture.ges(hand_landmarks)
                gesture = self.gesture.get_last_gesture()
                return gesture if gesture else '无手势'
        return '无手势'

    def voice_recognition_loop(self):
        print("[DEBUG] 语音识别线程启动")

        def update_voice_message(msg):
            def _update():
                self.last_voice = msg
                self.result_text.config(state='normal')

                # 清除旧的“语音”行
                start = self.result_text.search("语音:", "1.0", stopindex="end")
                if start:
                    line = start.split('.')[0]
                    self.result_text.delete(f"{line}.0", f"{int(line)+1}.0")

                # 插入新的“语音”信息
                self.result_text.insert(tk.END, '语音: ', 'label')
                self.result_text.insert(tk.END, f'{msg}\n', 'value')

                self.result_text.config(state='disabled')

            # 保证 UI 更新在主线程中执行
            self.result_text.after(0, _update)

        # 启动语音识别监听
        record.record_audio_loop(update_voice_message)

    def log_result(self, mode, content):
        if not content or content == '无手势' or content == '未检测到眼动':
            return
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user = self.user_manager.get_current_user().username if hasattr(self, 'user_manager') and self.user_manager else 'unknown'
        log_line = f'[{now}] [{user}] {mode}: {content}\n'
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_line)

    def create_user_panel(self):
        self.user_var = tk.StringVar(value=self.user_manager.get_current_user().username)
        user_names = self.user_manager.get_usernames()
        self.user_menu = ttk.Combobox(self.root, textvariable=self.user_var, values=user_names, state='readonly')
        self.user_menu.place(x=1050, y=10, width=120, height=30)
        self.user_menu.bind('<<ComboboxSelected>>', self.on_user_change)
        # 权限显示标签
        user = self.user_manager.get_current_user()
        self.permission_label = tk.Label(
            self.root,
            text=f"当前用户: {user.username} ({user.user_type})\n权限: {user.permissions}",
            font=('微软雅黑', 10), fg='#666', bg='#f0f4f8', anchor='w', justify='left'
        )
        self.permission_label.place(x=900, y=45, width=270, height=50)

    def on_user_change(self, event=None):
        username = self.user_var.get()
        self.user_manager.set_current_user(username)
        self.update_user_permission()

    def update_user_permission(self):
        user = self.user_manager.get_current_user()
        self.permission_label.config(
            text=f"当前用户: {user.username} ({user.user_type})\n权限: {user.permissions}"
        )

# Flask API 端点
@app.route('/api/recognition', methods=['GET'])
def get_recognition_results():
    return jsonify(recognition_results)

if __name__ == '__main__':
    # 启动 Flask 线程
    flask_thread = threading.Thread(target=lambda: app.run(port=5000), daemon=True)
    flask_thread.start()

    # 启动 Tkinter 应用
    root = tk.Tk()
    app = MultiModalApp(root)

    # 启动语音识别线程
    def start_voice_thread():
        app.voice_thread = threading.Thread(target=app.voice_recognition_loop, daemon=True)
        app.voice_thread.start()
    root.after(1000, start_voice_thread)  # 延迟1秒再启动线程

    root.mainloop()
