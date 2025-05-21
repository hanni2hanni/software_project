from flask import Flask, Response, jsonify, stream_with_context
from flask_cors import CORS  # 导入 CORS
import pyaudio
import wave
import numpy as np
import os
import assemblyai as aai
import time
from pygame import mixer
from threading import Thread
import queue
from queue import Queue

app = Flask(__name__)
CORS(app)
message_queue = Queue()
is_listening = False  # 状态标志位

# 配置音频参数
SAMPLE_RATE = 16000  # 采样率 16000 Hz
CHANNELS = 1         # 单声道
SAMPLE_WIDTH = 2     # 16-bit PCM（2 字节）
CHUNK = 1024         # 每次读取的帧数
OUTPUT_DIR = "wavs"  # 临时文件保存目录
TRIGGER_FILE = os.path.join(OUTPUT_DIR, "trigger.wav")  # 触发词临时文件
COMMAND_FILE = os.path.join(OUTPUT_DIR, "command.wav")  # 指令文件
RMS_THRESHOLD = 0.0010  # RMS 能量阈值，用于 VAD
SILENCE_DURATION = 4  # 静音持续时间（秒）

has_started = False  # 标记是否已经触发“开始录音”


# 配置 AssemblyAI API
aai.settings.api_key = "0a91719634f847eebefd17e7b3005c72"

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 播放状态管理
is_playing = False
music_file = os.path.join(OUTPUT_DIR, "music1_converted.wav")
navigation_file = os.path.join(OUTPUT_DIR, "navigation_converted.wav")
security_file = os.path.join(OUTPUT_DIR, "security_converted.wav")

# 在全局控制录音状态
is_listening = False

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
    if squared_mean <= 0 or np.isnan(squared_mean):
        rms = 0.0
    else:
        rms = np.sqrt(squared_mean) / 32768.0

    #rms = np.sqrt(squared_mean) / 32768.0  # 归一化到 0-1
    return rms

def transcribe_audio(audio_path):
    """使用 AssemblyAI 转录音频"""
    #告诉 AssemblyAI 使用中文语音识别模型
    config = aai.TranscriptionConfig(language_code="zh")
    #创建转录器
    transcriber = aai.Transcriber(config=config)
    #发起转录请求
    transcript = transcriber.transcribe(audio_path)
    if transcript.status == "completed":
        return transcript.text
    print(f"转录状态: {transcript.status}")
    return None

def play_audio(file_path):
    """播放音频文件"""
    print(f"尝试播放文件: {file_path}, 存在: {os.path.exists(file_path)}")
    if os.path.exists(file_path):
        try:
            mixer.music.load(file_path)
            print("文件加载成功")
            mixer.music.play()
            print(f"播放: {file_path}")
            # 等待播放完成
            while mixer.music.get_busy():
                pass
            print("播放完成")
        except Exception as e:
            print(f"播放失败: {e}")
    else:
        print(f"错误: 文件 {file_path} 不存在")

def stop_audio():
    """停止播放音频"""
    global is_playing
    if is_playing:
        mixer.music.stop()
        is_playing = False
        print("停止播放")

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
#实时监听麦克风输入，并检测是否说出了“开始录音”，作为触发词来启动录音过程。
def record_trigger():
    """监听触发词 '开始录音'"""
    audio = pyaudio.PyAudio()
    # 打开音频流，用于实时读取麦克风数据
    stream = audio.open(format=pyaudio.paInt16,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    message_queue.put("正在监听触发词“开始录音”...")
    #print("监听中，请说 '开始录音' 触发录音...")
    frames = []
    silence_counter = 0
    recording = False
    max_trigger_duration = 3

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        rms = compute_rms(data)# 计算当前音频段的能量大小
        #如果声音大于阈值，则认为开始讲话 → recording = True
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
        #print("未检测到声音")
        message_queue.put("未检测到声音")
        return False
    #录音保存与语音识别
    with wave.open(TRIGGER_FILE, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))
    #将录音转换为文字，检查是否包含关键词 "开始录音"
    text = transcribe_audio(TRIGGER_FILE)
    message_queue.put(f"触发词识别结果：{text}")
    if text and any(keyword in text for keyword in ["开始录音", "開始錄音"]):
        #print("检测到触发词 '开始录音'")
        message_queue.put("✅ 检测到触发词“开始录音”")
        return True
    else:
        #print(f"未检测到触发词，识别结果: {text}")
        message_queue.put("❌ 未检测到触发词，继续监听...")
        return False

def record_command():
    """捕获指令音频，动态时长"""
    message_queue.put("准备录制指令，请讲话...")
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

    #print("请说出指令...")
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
        #print("未录制到有效指令")
        message_queue.put("❌ 未录制到有效指令")
        return None

    with wave.open(COMMAND_FILE, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))
    message_queue.put("正在识别语音指令...")
    #将音频文件 COMMAND_FILE（路径）转为文本
    command_text = transcribe_audio(COMMAND_FILE)
    if command_text:
        #print(f"识别到的指令: {command_text}")
        message_queue.put(f"✅ 识别结果：{command_text}")
        command = command_text.strip()
        handler = command_handlers.get(command)
        if handler:
            message_queue.put(f"执行指令：{command}")
            handler()
        else:
            #print(f"未知指令: {command_text}")
            message_queue.put(f"⚠️ 未知指令：{command}")
    else:
        #print("未成功识别指令")
        message_queue.put("❌ 语音识别失败")

    return COMMAND_FILE

# def record_audio():
#     """主函数：监听触发词并录制指令"""
#     while True:
#         if record_trigger():
#             command_file = record_command()
#             if command_file:
#                 return command_file
#         else:
#             print("继续监听...")
#             time.sleep(1)

def record_audio_async():
    global is_listening, has_started
    try:
        message_queue.put("🎙️ 语音助手开始监听（直到点击按钮手动关闭）...")
        while is_listening:
            if not has_started:
                # 还没触发“开始录音”，监听触发词
                if record_trigger():
                    message_queue.put("✅ 检测到触发词“开始录音”，进入指令监听模式")
                    has_started = True
                else:
                    time.sleep(1)
            else:
                # 已经触发，持续录制指令
                command_file = record_command()
                if command_file:
                    # 指令处理成功或失败都继续监听
                    pass
                else:
                    message_queue.put("⚠️ 未识别到有效指令，继续监听...")
                time.sleep(0.1)  # 轻微休眠避免CPU飙升
    except Exception as e:
        message_queue.put(f"❌ 监听过程中发生错误：{e}")
    finally:
        is_listening = False
        has_started = False  # 重置状态
        message_queue.put("👋 语音助手已停止监听（点击按钮关闭）。")

@app.route('/api/start-voice')
def start_voice():
    global is_listening
    if not is_listening:
        is_listening = True
        Thread(target=record_audio_async).start()
        return jsonify({"message": "✅ 语音助手已启动"})
    else:
        return jsonify({"message": "⚠️ 语音助手正在运行中"}), 400

@app.route('/api/stop-voice')
def stop_voice():
    global is_listening
    is_listening = False
    message_queue.put("🛑 语音助手已手动停止监听")
    return jsonify({"message": "🛑 语音助手已手动停止监听"})

@app.route('/api/stream')
def stream():
    def event_stream():
        try:
            while True:
                try:
                    message = message_queue.get(timeout=10)
                    yield f"data: {message}\n\n"
                except queue.Empty:
                    # 定期发送心跳，避免浏览器断连
                    yield "data: ping\n\n"
        except GeneratorExit:
            print("客户端断开 SSE 连接")
    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
