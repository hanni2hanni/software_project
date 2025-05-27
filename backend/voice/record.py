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
    rms = np.sqrt(squared_mean) / 32768.0  # 归一化到 0-1
    return rms

def transcribe_audio(audio_path):
    """使用 AssemblyAI 转录音频"""
    print(f"[DEBUG] 调用transcribe_audio, audio_path={audio_path}")
    config = aai.TranscriptionConfig(language_code="zh")
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(audio_path)
    print(f"[DEBUG] transcript.status={transcript.status}")
    if transcript.status == "completed":
        print(f"[DEBUG] transcript.text={transcript.text}")
        return transcript.text
    print(f"转录状态: {transcript.status}")
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

# 指令映射字典（模拟 switch...case）
command_handlers = {
    "打开音乐": handle_open_music,
    "已经注意道路": handle_notice_road,
    "打开导航": handle_open_navigation,
    "关闭音乐": handle_close_music,
    "開啓音樂": handle_open_music,
    "已經注意道路": handle_notice_road,
    "打開導航": handle_open_navigation,
    "關閉音樂": handle_close_music
}

def record_trigger():
    """监听触发词 '开始录音'"""
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    
    print("监听中，请说 '开始录音' 触发录音...")
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
    if text and any(keyword in text for keyword in ["开始录音", "開始錄音"]):
        print("检测到触发词 '开始录音'")
        return True
    else:
        print(f"未检测到触发词，识别结果: {text}")
        return False

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
        handler = command_handlers.get(command)
        if handler:
            print(f"[DEBUG] 匹配到指令处理函数: {handler}")
            handler()
        else:
            print(f"[DEBUG] 未知指令: {command_text}")
        return command_text
    else:
        print("[DEBUG] 未成功识别指令")
        return None

def record_audio():
    """主函数：监听触发词并录制指令"""
    while True:
        print("[DEBUG] 等待触发词...")
        if record_trigger():
            print("[DEBUG] 触发词检测到，开始录制指令")
            command_text = record_command()
            print(f"[DEBUG] record_command返回: {command_text}")
            if command_text:
                return command_text
        else:
            print("[DEBUG] 未检测到触发词，继续监听...")
            time.sleep(1)

if __name__ == "__main__":
    audio_file = record_audio()
    if audio_file:
        print(f"指令音频已保存为: {audio_file}")
    else:
        print("未录制到指令")