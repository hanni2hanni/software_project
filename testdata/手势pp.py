import cv2
import os
import json
import mediapipe as mp

# ==== 路径配置 ====shaking_hands
video_path = 'shaking_hands/10/10.mp4'   # 输入视频路径
output_dir = 'shaking_hands/10'   # 输出文件夹
frames_dir = os.path.join(output_dir, 'frames')
os.makedirs(frames_dir, exist_ok=True)

# ==== 初始化 ====
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=1,
                       min_detection_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# ==== 结果保存结构 ====
frame_list = []
keypoints_dict = {}
labels_dict = {}

# ==== 视频读取 ====
cap = cv2.VideoCapture(video_path)
frame_idx = 0

while True:
    success, frame = cap.read()
    if not success:
        break

    frame_name = f"{frame_idx:05d}.jpg"
    frame_path = os.path.join(frames_dir, frame_name)

    # 保存帧图像
    cv2.imwrite(frame_path, frame)
    frame_list.append(frame_name)

    # 提取关键点
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    keypoints = []
    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        for lm in hand_landmarks.landmark:
            keypoints.append([lm.x, lm.y, lm.z])
    else:
        keypoints = [[0.0, 0.0, 0.0]] * 21  # 没识别到就全零

    keypoints_dict[frame_name] = keypoints

    # 统一打标签为 pause（握拳）
    #labels_dict[frame_name] = "pause"

    frame_idx += 1

cap.release()
hands.close()

# ==== 写入 frames.json、keypoints.json、labels.json ====
with open(os.path.join(output_dir, 'frames.json'), 'w') as f:
    json.dump(frame_list, f, indent=2)

with open(os.path.join(output_dir, 'keypoints.json'), 'w') as f:
    json.dump(keypoints_dict, f, indent=2)

#with open(os.path.join(output_dir, 'labels.json'), 'w') as f:
 #   json.dump(labels_dict, f, indent=2)

print("✅ 预处理完成！共提取帧数：", frame_idx)
