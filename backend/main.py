import threading
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import datetime
import os
import dlib
import numpy as np
from imutils import face_utils

# 视觉识别
from sight.gaze_tracking import GazeTracking
from sight.headtrack import HeadTracker
#from sight.eyetrack import EyeTracker
# 手势识别
from gesture.gesture import SignRe
# 语音识别
from voice import record
from user_manager import UserManager

# 新增
from log_analyzer import LogAnalyzer
from profile_analytics import ProfileAnalytics


LOG_FILE = 'log.txt'

SCENES = [
    {
        'name': '自由多模态识别',
        'desc': '实时展示视觉、头部姿态、手势、语音等多模态识别结果，无场景联动。',
        'icon': '',
        'color': '#f0f4f8',
    },
    {
        'name': '场景1 分心检测',
        'desc': '分心检测：偏离3秒触发警告，需手势/语音确认。\n输入：眼动偏离3秒，语音"已经注意道路"，手势竖拇指/挥手。\n输出：红色警告栏，语音播报，警告灯闪烁。',
        'icon': '🚨',
        'color': '#ff3333',
        'audio1': r'E:\system\voice\temp\security_converted.wav',  # "已注意行车安全"
        'audio2': r'E:\system\voice\temp\look_straight.wav',      # "请立即目视前方"
    },
    {
        'name': '场景2 导航确认',
        'desc': '导航确认：向下看后点头为确认，摇头为重选。\n输入：眼动向下，点头/摇头。\n输出：蓝/黄状态栏，语音播报，导航图标闪烁。',
        'icon': '🧭',
        'color': '#3399ff',
        'color2': '#ffd700',
        'audio1': r'E:\system\voice\temp\navigation_converted.wav',  # "已开启导航"
        'audio2': r'E:\system\voice\temp\navigation_converted.wav',
    },
    {
        'name': '场景3 音乐状态',
        'desc': '音乐状态：向左看竖拇指为播放，挥手为暂停。\n输入：眼动向左，手势竖拇指/挥手。\n输出：绿/黄状态栏，语音播报，音乐图标闪烁。',
        'icon': '🎵',
        'color': '#33cc66',
        'color2': '#ffd700',
        'audio1': r'E:\system\voice\temp\music1_converted.wav',  # 音乐播放
        'audio2': r'',
    },
]

# 头部姿态检测类（集成自sight/headtrack.py核心逻辑，输出点头/摇头/静止）
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
            # 点头检测（眉毛到下颌距离变化）
            brow = shape[21:27]  # 左右眉毛
            jaw = shape[6:11]    # 下颌
            brow_y = np.mean(brow[:, 1])
            jaw_y = np.mean(jaw[:, 1])
            dist = jaw_y - brow_y
            # 阈值可根据实际情况调整
            if dist > 70 and not self.nod_flag:
                self.nod_counter += 1
                self.nod_flag = True
                self.nod_time = time.time()
                status = '点头'
            elif dist <= 70:
                self.nod_flag = False
            # 摇头检测（左右下颌距离变化）
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
            # 状态保持1秒
            if self.nod_flag and time.time() - self.nod_time < 1:
                status = '点头'
            elif self.shake_flag and time.time() - self.shake_time < 1:
                status = '摇头'
        if status == '静止' and (self.nod_flag or self.shake_flag):
            # 保持上一次状态直到动作结束
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

        self.scene_idx = 0
        self.scene_state = {}
        self.flash_flag = True
        self.last_gaze_time = time.time()
        self.gaze_off_road = False
        self.warning_active = False
        self.last_warning_time = 0
        self.music_playing = True
        self.music_checked = False
        self.navigation_checked = False
        self.navigation_reselect = False
        self.last_status = ''
        self.gesture_pause_buffer = []  # 用于音乐场景挥手去抖动

        # 左侧场景切换栏
        self.scene_frame = tk.Frame(self.root, bg='#e3eaf2')
        self.scene_frame.place(x=0, y=0, width=260, height=700)
        self.scene_buttons = []
        for i, scene in enumerate(SCENES):
            btn = tk.Button(self.scene_frame, text=scene['name'], font=('微软雅黑', 13, 'bold'),
                            bg='#e3eaf2', fg='#1a73e8', bd=0, relief='flat',
                            activebackground='#c6dafc', activeforeground='#d32f2f',
                            command=lambda idx=i: self.switch_scene(idx))
            btn.place(x=20, y=30 + i*60, width=220, height=50)
            self.scene_buttons.append(btn)
        self.update_scene_buttons()

        # 多模态输出区（左下）
        self.result_frame = tk.Frame(self.scene_frame, bg='#f7fafc', highlightbackground='#1a73e8', highlightthickness=2)
        self.result_frame.place(x=10, y=320, width=240, height=350)
        self.result_title = tk.Label(self.result_frame, text='多模态识别结果', font=('微软雅黑', 14, 'bold'), fg='#1a73e8', bg='#f7fafc')
        self.result_title.pack(pady=(10, 0))
        self.result_text = tk.Text(self.result_frame, font=('微软雅黑', 12), wrap='word', bg='#f7fafc', fg='#222',
                                   relief='flat', borderwidth=0, height=16)
        self.result_text.pack(fill='both', expand=True, padx=8, pady=8)
        self.result_text.tag_configure('label', foreground='#1a73e8', font=('微软雅黑', 12, 'bold'))
        self.result_text.tag_configure('value', foreground='#222', font=('微软雅黑', 12))

        # 右侧场景描述区
        self.welcome_label = tk.Label(self.root, text='欢迎进入车载多模态交互系统',
                                      font=('微软雅黑', 18, 'bold'), fg='#1a73e8', bg='#f0f4f8', anchor='w')
        self.welcome_label.place(x=270, y=10, width=1100, height=32)
        self.scene_desc = tk.Label(self.root, text=SCENES[self.scene_idx]['desc'],
                                   font=('微软雅黑', 11), fg='#333', bg='#f0f4f8', justify='left', anchor='nw')
        self.scene_desc.place(x=270, y=45, width=1100, height=140)
        self.sep1 = tk.Frame(self.root, bg='#1a73e8')
        self.sep1.place(x=270, y=190, width=1100, height=2)

        # 右侧摄像头画面
        self.video_label = tk.Label(self.root, bg='#222')
        self.video_label.place(x=270, y=190, width=900, height=480)

        # 状态栏和仪表盘图标（右上角，摄像头画面上方）
        self.status_label = tk.Label(self.root, text='', font=('微软雅黑', 18, 'bold'), bg='#f0f4f8')
        self.status_label.place(x=270, y=150, width=700, height=40)
        self.icon_label = tk.Label(self.root, text='', font=('微软雅黑', 40), bg='#f0f4f8')
        self.icon_label.place(x=980, y=150, width=80, height=40)

        # 用户管理
        self.user_manager = UserManager()
        self.create_user_panel()

        # 初始化识别器
        self.gaze = GazeTracking()
        self.gesture = SignRe()
        self.headpose = HeadTracker()
        self.cap = cv2.VideoCapture(0)
        #self.eyetracker = EyeTracker()

        self.last_gaze = ''
        self.last_gesture = ''
        self.last_voice = ''
        self.last_gaze_type = ''
        self.last_gesture_type = ''
        self.last_voice_type = ''
        self.last_headpose = '静止'

        self.update_frame()
        # self.voice_thread = threading.Thread(target=self.voice_recognition_loop, daemon=True)
        # self.voice_thread.start()
        self.flash_timer()

        # 新增
        self.log_analyzer = LogAnalyzer()
        self.profile_analytics = ProfileAnalytics()

    # 新增
    def on_interaction_complete(self, mode, content):
        # 在交互完成后调用分析
        if hasattr(self, 'user_manager') and self.user_manager:
            username = self.user_manager.get_current_user().username
            self.log_analyzer.analyze_user_behavior(username)

    def switch_scene(self, idx):
        self.scene_idx = idx
        self.scene_desc.config(text=SCENES[self.scene_idx]['desc'])
        self.update_scene_buttons()
        # 重置场景状态
        self.gaze_off_road = False
        self.warning_active = False
        self.last_gaze_time = time.time()
        self.music_checked = False
        self.navigation_checked = False
        self.navigation_reselect = False
        self.status_label.config(text='', bg='#f0f4f8')
        self.icon_label.config(text='', bg='#f0f4f8')

    def update_scene_buttons(self):
        for i, btn in enumerate(self.scene_buttons):
            if i == self.scene_idx:
                btn.config(bg='#1a73e8', fg='white')
            else:
                btn.config(bg='#e3eaf2', fg='#1a73e8')

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
        # gaze_result = self.eyetracker.get_status(frame)
        # self.last_gaze = gaze_result# self.gaze.refresh(frame)
        self.gaze.refresh(frame)
        #frame = self.gaze.annotated_frame()
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

        # 画面显示
        #display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        show_frame = self.gaze.annotated_frame()
        if show_frame is None:
            show_frame = frame

        display_frame = cv2.cvtColor(show_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(display_frame)
        img = img.resize((900, 480))
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

        # 场景逻辑
        self.handle_scene_logic(gaze_result, headpose_result, gesture_result)

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

    def handle_scene_logic(self, gaze_result, headpose_result, gesture_result):
        scene = SCENES[self.scene_idx]
        # 自由多模态识别模式：只展示，不联动
        if self.scene_idx == 0:
            self.status_label.config(text='', bg='#f0f4f8')
            self.icon_label.config(text='', bg='#f0f4f8')
            return
        # 场景1 分心检测
        if self.scene_idx == 1:
            if gaze_result in ['向左看', '向右看', '向下看']:
                if not self.gaze_off_road:
                    self.gaze_off_road = True
                    self.last_gaze_time = time.time()
                elif time.time() - self.last_gaze_time > 3 and not self.warning_active:
                    self.warning_active = True
                    self.status_label.config(text='警告！请目视前方', bg=scene['color'], fg='white')
                    self.icon_label.config(text=scene['icon'], bg=scene['color'])
                    record.play_audio(scene['audio1'])
                    self.log_result('警告', '请目视前方')
            else:
                self.gaze_off_road = False
                self.last_gaze_time = time.time()
                # 只有解除警告时才重置状态栏
                # if self.warning_active:
                #     self.status_label.config(text='', bg='#f0f4f8')
                #     self.icon_label.config(text='', bg='#f0f4f8')
                #     self.warning_active = False
            # 解除警告逻辑，警告期间每帧都检测
            if self.warning_active:
                if self.last_voice == '已经注意道路' or gesture_result == '竖拇指':
                    self.status_label.config(text='安全已确认', bg='#33cc66', fg='white')
                    self.icon_label.config(text=scene['icon'], bg='#33cc66')
                    self.warning_active = False
                    self.log_result('确认', '安全已确认')
                elif gesture_result == '挥手':
                    self.status_label.config(text='警告未解除', bg=scene['color'], fg='white')
                    self.icon_label.config(text=scene['icon'], bg=scene['color'])
                    self.log_result('拒绝', '警告未解除')
        # 场景2 导航确认
        elif self.scene_idx == 2:
            if gaze_result == '向下看' and not self.navigation_checked:
                self.status_label.config(text='请点头确认导航路线', bg=scene['color'], fg='white')
                self.icon_label.config(text=scene['icon'], bg=scene['color'])
                self.navigation_checked = True
            if self.navigation_checked:
                if headpose_result == '点头':
                    self.status_label.config(text='导航路线已确认', bg=scene['color'], fg='white')
                    self.icon_label.config(text=scene['icon'], bg=scene['color'])
                    record.play_audio(scene['audio1'])
                    self.log_result('导航', '导航路线已确认')
                elif headpose_result == '摇头':
                    self.status_label.config(text='请重新选择导航路线', bg=scene['color2'], fg='black')
                    self.icon_label.config(text=scene['icon'], bg=scene['color2'])
                    record.play_audio(scene['audio2'])
                    self.log_result('导航', '请重新选择导航路线')
        # 场景3 音乐状态
        elif self.scene_idx == 3:
            if gaze_result == '向左看' and not self.music_checked:
                self.status_label.config(text='请竖拇指确认音乐状态', bg=scene['color'], fg='white')
                self.icon_label.config(text=scene['icon'], bg=scene['color'])
                self.music_checked = True
            if self.music_checked:
                if gesture_result == '竖拇指':
                    self.status_label.config(text='音乐正在播放', bg=scene['color'], fg='white')
                    self.icon_label.config(text=scene['icon'], bg=scene['color'])
                    record.play_audio(scene['audio1'])
                    self.log_result('音乐', '音乐正在播放')
                    self.gesture_pause_buffer.clear()
                elif gesture_result == '挥手':
                    self.gesture_pause_buffer.append('挥手')
                    if len(self.gesture_pause_buffer) >= 2 and all(g == '挥手' for g in self.gesture_pause_buffer[-2:]):
                        self.status_label.config(text='音乐已暂停', bg=scene['color2'], fg='black')
                        self.icon_label.config(text=scene['icon'], bg=scene['color2'])
                        record.stop_audio()  # 立即停止音乐
                        self.log_result('音乐', '音乐已暂停')
                        self.gesture_pause_buffer.clear()
                else:
                    self.gesture_pause_buffer.clear()

        # 新增
        # 更新用户配置
        if hasattr(self, 'user_manager') and self.user_manager:
            username = self.user_manager.get_current_user().username
            self.profile_analytics.update_profile_based_on_interaction(
                username,
                SCENES[self.scene_idx]['name'],
                f"{gaze_result}|{gesture_result}"
            )


    def flash_timer(self):
        # 仪表盘和状态栏闪烁
        scene = SCENES[self.scene_idx]
        if self.status_label.cget('text') and self.status_label.cget('bg') != '#f0f4f8':
            if self.flash_flag:
                self.status_label.config(bg=scene.get('color', '#ff3333'))
                self.icon_label.config(bg=scene.get('color', '#ff3333'))
            else:
                self.status_label.config(bg='#f0f4f8')
                self.icon_label.config(bg='#f0f4f8')
            self.flash_flag = not self.flash_flag
        self.root.after(500, self.flash_timer)

    # def voice_recognition_loop(self):
    #     print("[DEBUG] 语音识别线程启动")
    #     while True:
    #         try:
    #             print("[DEBUG] 调用record_audio()")
    #             result = record.record_audio()
    #             print(f"[DEBUG] record_audio返回: {result}")
    #             if result:
    #                 self.last_voice = result
    #             else:
    #                 self.last_voice = ''
    #         except Exception as e:
    #             self.last_voice = f'语音识别异常: {e}'
    #             import traceback
    #             traceback.print_exc()
    #         time.sleep(1)
    # def voice_recognition_loop(self):
    #     print("[DEBUG] 语音识别线程启动")

    #     def update_voice_message(msg):
    #         self.last_voice = msg
    #         self.result_text.config(state='normal')

    #         # 先清除之前的“语音”行（找到包含“语音:”标签的行）
    #         start = self.result_text.search("语音:", "1.0", stopindex="end")
    #         if start:
    #             line = start.split('.')[0]
    #             self.result_text.delete(f"{line}.0", f"{int(line)+1}.0")

    #         # 插入新的“语音”信息
    #         self.result_text.insert(tk.END, '语音: ', 'label')
    #         self.result_text.insert(tk.END, f'{msg}\n', 'value')

    #     k    self.result_text.config(state='disabled')

    #     record.record_audio_loop(update_voice_message)
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

if __name__ == '__main__':
    root = tk.Tk()
    app = MultiModalApp(root)

    # 新增 等待主界面完成初始化后再启动线程
    def start_voice_thread():
        app.voice_thread = threading.Thread(target=app.voice_recognition_loop, daemon=True)
        app.voice_thread.start()
    root.after(1000, start_voice_thread)  # 延迟1秒再启动线程

    root.mainloop()