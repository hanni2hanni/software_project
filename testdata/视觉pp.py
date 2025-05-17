import os
import json
import pandas as pd
from pathlib import Path

def preprocess_gazecapture(dataset_path, output_csv):
    """
    预处理GazeCapture数据集
    参数：
        dataset_path: 包含所有受试者目录的根路径
        output_csv: 预处理结果保存路径
    """
    all_data = []
    
    for subject_dir in Path(dataset_path).iterdir():
        if not subject_dir.is_dir(): continue
        
        # 加载公共元数据
        with open(subject_dir/'info.json') as f:
            info = json.load(f)
        with open(subject_dir/'screen.json') as f:
            screen = json.load(f)
            
        # 加载时序数据
        with open(subject_dir/'appleFace.json') as f:
            face_data = json.load(f)
        with open(subject_dir/'dotInfo.json') as f:
            dot_data = json.load(f)
            
        # 遍历有效帧
        for frame_idx in range(info['TotalFrames']):
            # 有效性检查
            if not (face_data['IsValid'][frame_idx] and 
                    dot_data['IsValid'][frame_idx]):
                continue
                
            # 坐标系转换核心逻辑
            screen_w, screen_h = screen['W'], screen['H']
            orientation = screen['Orientation']
            
            # 根据屏幕方向调整坐标
            if orientation in [3,4]:  # 横屏
                x_screen = dot_data['XPts'][frame_idx] / screen_h
                y_screen = dot_data['YPts'][frame_idx] / screen_w
            else:  # 竖屏
                x_screen = dot_data['XPts'][frame_idx] / screen_w
                y_screen = dot_data['YPts'][frame_idx] / screen_h
                
            # 构建数据记录
            record = {
                'subject': subject_dir.name,
                'frame_id': f"{subject_dir.name}_{frame_idx:06d}",
                'timestamp': dot_data['Time'][frame_idx],
                'x_screen': round(x_screen, 4),
                'y_screen': round(y_screen, 4),
                'x_cam': dot_data['XCam'][frame_idx],
                'y_cam': dot_data['YCam'][frame_idx],
                'face_valid': face_data['IsValid'][frame_idx],
                'screen_orientation': orientation,
                'dataset_split': info['Dataset'],
                'image_path': str(subject_dir/'frames'/f"{frame_idx}.jpg")
            }
            all_data.append(record)
    
    # 保存结构化数据
    pd.DataFrame(all_data).to_csv(output_csv, index=False)
    print(f"预处理完成，共处理{len(all_data)}条有效数据")

# 使用示例
preprocess_gazecapture(
    dataset_path="./GazeCapture/gazecapture",
    output_csv="./preprocessed_data.csv"
)