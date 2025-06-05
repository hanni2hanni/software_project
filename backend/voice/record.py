import pyaudio
import wave
import numpy as np
import os
import assemblyai as aai
import time
from pygame import mixer
import threading

# 配置音频参数
SAMPLE_RATE = 16000  # 采样率 16000 Hz
CHANNELS = 1         # 单声道
SAMPLE_WIDTH = 2     # 16-bit PCM（2 字节）
CHUNK = 1024         # 每次读取的帧数
OUTPUT_DIR = "temp"  # 临时文件保存目录
TRIGGER_FILE = os.path.join(OUTPUT_DIR, "trigger.wav")  # 触发词临时文件
COMMAND_FILE = os.path.join(OUTPUT_DIR, "command.wav")  # 指令文件
RMS_THRESHOLD = 0.0010  # RMS 能量阈值，用于 VAD
SILENCE_DURATION = 4  # 静音持续时间（秒）

# 配置 AssemblyAI API
aai.settings.api_key = "0a91719634f847eebefd17e7b3005c72"

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 播放状态管理
is_playing = False
music_file = os.path.join(OUTPUT_DIR, "music1_converted.wav")
navigation_file = os.path.join(OUTPUT_DIR, "navigation_converted.wav")
security_file = os.path.join(OUTPUT_DIR, "security_converted.wav")

# 初始化 pygame mixer
mixer.init(frequency=SAMPLE_RATE, size=-16, channels=CHANNELS)

# def compute_rms(audio_data):
#     """计算音频数据的 RMS（均方根）值"""
#     audio_array = np.frombuffer(audio_data, dtype=np.int16)
#     if len(audio_array) == 0:
#         print("警告：音频数据为空")
#         return 0.0
#     squared_mean = np.mean(audio_array**2)
#     if not np.isfinite(squared_mean):
#         print("警告：RMS 计算结果无效，squared_mean =", squared_mean)
#         return 0.0
#     rms = np.sqrt(squared_mean) / 32768.0  # 归一化到 0-1
#     return rms
def compute_rms(audio_data):
    """计算音频数据的 RMS（均方根）值"""
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    if len(audio_array) == 0:
        print("警告：音频数据为空")
        return 0.0
    squared_mean = np.mean(audio_array**2)
    if not np.isfinite(squared_mean):
        print("警告：RMS 计算结果无效，squared_mean =", squared_mean)
        return 0.0
    if squared_mean <= 0 or np.isnan(squared_mean):
        rms = 0.0
    else:
        rms = np.sqrt(squared_mean) / 32768.0

    #rms = np.sqrt(squared_mean) / 32768.0  # 归一化到 0-1
    return rms


def transcribe_audio(audio_path):
    """使用 AssemblyAI 转录音频"""
    #print(f"[DEBUG] 调用transcribe_audio, audio_path={audio_path}")
    config = aai.TranscriptionConfig(language_code="zh")
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(audio_path)
    #print(f"[DEBUG] transcript.status={transcript.status}")
    if transcript.status == "completed":
        #print(f"[DEBUG] transcript.text={transcript.text}")
        return transcript.text
    #print(f"转录状态: {transcript.status}")
    return None

def play_audio(file_path):
    def _play():
        try:
            mixer.music.stop()  # 先停掉之前的
            if os.path.exists(file_path):
                mixer.music.load(file_path)
                mixer.music.play()
                print(f"播放: {file_path}")
            else:
                print(f"错误: 文件 {file_path} 不存在")
        except Exception as e:
            print(f"播放失败: {e}")
    threading.Thread(target=_play, daemon=True).start()

def stop_audio():
    def _stop():
        try:
            mixer.music.stop()
            print("停止播放")
        except Exception as e:
            print(f"停止播放失败: {e}")
    threading.Thread(target=_stop, daemon=True).start()

# 指令处理函数
def handle_open_music():
    play_audio(music_file)

def handle_notice_road():
    play_audio(security_file)

def handle_open_navigation():
    play_audio(navigation_file)

def handle_close_music():
    stop_audio()

# 指令标准化映射（模糊变体 → 标准指令）
command_normalization = {
    "已经注意到路": "已经注意道路",
    "已经注意到": "已经注意道路",
    "请打开音乐": "打开音乐",
    "导航": "打开导航",
    "開啓音樂": "打开音乐",
    "已經注意道路": "已经注意道路",
    "打開導航": "打开导航",
    "關閉音樂": "关闭音乐",
}

# 指令映射字典（模拟 switch...case）
command_handlers = {
    "打开音乐": handle_open_music,
    "已经注意道路": handle_notice_road,
    "打开导航": handle_open_navigation,
    "关闭音乐": handle_close_music
}
# trigger_keywords = {
#     "开始录音",
#     "開始錄音",
#     "开始录入",
#     "开始录音吧",
#     "请开始录音",
#     "录音开始",
#     "我要开始录音"
# }
# 触发词集合，包含简体和繁体变体
trigger_keywords = {
    "小贝", "小貝",         # 基础简繁形式
    "小贝小贝","小貝小貝", 
    "小北",                # 简繁相同，误识别为běi
    "嘿，小贝", "嘿，小貝",  # 前缀“嘿”的简繁变体
    "你好，小贝", "你好，小貝",  # 前缀“你好”的简繁变体
    "小贝，启动", "小貝，啟動",  # 带“启动/啟動”的简繁变体
    "小贝，嘿", "小貝，嘿",    # 后缀“嘿”的简繁变体
    "小辈", "小輩",         # 误识别为“辈/輩”
    "小杯",                # 简繁相同，误识别为bēi
    "小蓓",                 # 简繁相同，误识别为bèi
    "小被",
    "小背"
}


def record_trigger():
    """监听触发词 '小贝'"""
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

    print("监听中，请说 '小贝' 触发录音...")
    frames = []
    silence_counter = 0
    recording = False
    max_trigger_duration = 3

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        rms = compute_rms(data)

        if rms > RMS_THRESHOLD:
            recording = True
            frames.append(data)
            silence_counter = 0
        elif recording:
            silence_counter += CHUNK / SAMPLE_RATE
            frames.append(data)
            if silence_counter > SILENCE_DURATION:
                break

        if recording and len(frames) * CHUNK / SAMPLE_RATE > max_trigger_duration:
            break

    stream.stop_stream()
    stream.close()
    audio.terminate()

    if not frames:
        print("未检测到声音")
        return False

    with wave.open(TRIGGER_FILE, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))



    text = transcribe_audio(TRIGGER_FILE)
    if text:
        for keyword in trigger_keywords:
            if keyword in text:
                print(f"检测到触发词 '{keyword}'")
                return True
        print(f"未检测到触发词，识别结果: {text}")
        return False
    else:
        print("未识别到任何语音")
        return False



# def record_command():
#     """捕获指令音频，动态时长"""
#     audio = pyaudio.PyAudio()
#     stream = audio.open(format=pyaudio.paInt16,
#                         channels=CHANNELS,
#                         rate=SAMPLE_RATE,
#                         input=True,
#                         frames_per_buffer=CHUNK)

#     print("请说出指令...")
#     frames = []
#     silence_counter = 0
#     recording = False
#     max_duration = 10

#     while True:
#         data = stream.read(CHUNK, exception_on_overflow=False)
#         rms = compute_rms(data)

#         if rms > RMS_THRESHOLD:
#             recording = True
#             frames.append(data)
#             silence_counter = 0
#         elif recording:
#             silence_counter += CHUNK / SAMPLE_RATE
#             frames.append(data)
#             if silence_counter > SILENCE_DURATION:
#                 break

#         if len(frames) * CHUNK / SAMPLE_RATE > max_duration:
#             break

#     stream.stop_stream()
#     stream.close()
#     audio.terminate()

#     if not frames:
#         print("未录制到有效指令")
#         return None

#     with wave.open(COMMAND_FILE, 'wb') as wf:
#         wf.setnchannels(CHANNELS)
#         wf.setsampwidth(SAMPLE_WIDTH)
#         wf.setframerate(SAMPLE_RATE)
#         wf.writeframes(b''.join(frames))

#     command_text = transcribe_audio(COMMAND_FILE)
#     print(f"[DEBUG] transcribe_audio返回: {command_text}")
#     if command_text:
#         print(f"[DEBUG] 识别到的指令: {command_text}")
#         command = command_text.strip()
#         handler = command_handlers.get(command)
#         if handler:
#             print(f"[DEBUG] 匹配到指令处理函数: {handler}")
#             handler()
#         else:
#             print(f"[DEBUG] 未知指令: {command_text}")
#         return command_text
#     else:
#         print("[DEBUG] 未成功识别指令")
#         return None

def record_command():
    """捕获指令音频，动态时长"""
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

    print("请说出指令...")
    frames = []
    silence_counter = 0
    recording = False
    max_duration = 10

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        rms = compute_rms(data)

        if rms > RMS_THRESHOLD:
            recording = True
            frames.append(data)
            silence_counter = 0
        elif recording:
            silence_counter += CHUNK / SAMPLE_RATE
            frames.append(data)
            if silence_counter > SILENCE_DURATION:
                break

        if len(frames) * CHUNK / SAMPLE_RATE > max_duration:
            break

    stream.stop_stream()
    stream.close()
    audio.terminate()

    if not frames:
        print("未录制到有效指令")
        return None

    with wave.open(COMMAND_FILE, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))

        command_text = transcribe_audio(COMMAND_FILE)
    print(f"[DEBUG] transcribe_audio返回: {command_text}")
    if command_text:
        print(f"[DEBUG] 识别到的指令: {command_text}")
        command = command_text.strip()

        # 指令标准化处理
        normalized_command = command_normalization.get(command, command)
        print(f"[DEBUG] 标准化指令: {normalized_command}")

        handler = command_handlers.get(normalized_command)
        if handler:
            print(f"[DEBUG] 匹配到指令处理函数: {handler}")
            handler()
        else:
            print(f"[DEBUG] 未知指令: {normalized_command}")
        return normalized_command


# def record_audio():
#     """主函数：监听触发词并录制指令"""
#     while True:
#         print("[DEBUG] 等待触发词...")
#         if record_trigger():
#             print("[DEBUG] 触发词检测到，开始录制指令")
#             command_text = record_command()
#             print(f"[DEBUG] record_command返回: {command_text}")
#             if command_text:
#                 return command_text
#         else:
#             print("[DEBUG] 未检测到触发词，继续监听...")
#             time.sleep(1)

# 状态变量
import time
is_listening = True
has_started = False

def record_audio_loop(callback=None):
    """持续监听触发词与指令，使用 callback 实时回传文本到 UI"""
    global is_listening, has_started
    try:
        if callback is None:
            callback = print  # 默认用print输出
        callback("开始监听...")
        while is_listening:
            if not has_started:
                callback("等待触发词...")
                if record_trigger():
                    callback("监听指令...")
                    has_started = True
                else:
                    time.sleep(1)
                    continue
            else:
                command_text = record_command()
                if command_text:
                    callback(f"{command_text}")
                    def reset_to_listening():
                        if is_listening:  # 避免在已停止时调用
                            callback("监听指令...")
                    threading.Timer(2.0, reset_to_listening).start()
                else:
                    callback("识别失败...")
                def reset_to_listening():
                    if is_listening:
                        callback("监听指令...")
                threading.Timer(2.0, reset_to_listening).start()
                time.sleep(0.1)  # 稍微等待防止CPU过载
    except KeyboardInterrupt:
        callback(" 终止监听")
    except Exception as e:
        callback(f" 发生错误：{e}")
    finally:
        is_listening = False
        has_started = False
        callback(" 停止监听")

if __name__ == "__main__":
    audio_file = record_audio_loop()
    if audio_file:
        print(f"指令音频已保存为: {audio_file}")
    else:
        print("未录制到指令")
