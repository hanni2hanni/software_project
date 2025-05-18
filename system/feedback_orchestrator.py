from . import user_manager
from .config import EVENT_USER_DISTRACTED, EVENT_COMMAND_SUCCESS, EVENT_COMMAND_FAILURE, EVENT_PERMISSION_DENIED, EVENT_GENERIC_INFO
import pyttsx3
import threading
import time
import win32com.client
import tkinter as tk
from tkinter import ttk
import threading

# 初始化全局TTS引擎
_tts_engine = None
_win32_speaker = None
_visual_feedback_window = None  # 全局变量存储视觉反馈窗口

# 视觉反馈管理器类
class VisualFeedbackManager:
    """
    提供图形化视觉反馈的管理器类，使用tkinter创建可视化的状态提示和警告。
    支持多种视觉反馈元素，包括状态图标、颜色变化和动画效果。
    """
    _instance = None  # 单例模式
    _window = None    # 主窗口
    _elements = {}    # 存储不同类型的视觉元素
    _colors = {
        "normal": "#777777",     # 灰色（正常/默认状态）
        "info": "#2196F3",       # 蓝色（信息状态）
        "success": "#4CAF50",    # 绿色（成功状态）
        "warning": "#FF9800",    # 橙色（警告状态）
        "error": "#F44336",      # 红色（错误状态）
        "background": "#333333", # 背景深灰色
        "text": "#FFFFFF"        # 文本白色
    }
    _current_status = "normal"   # 当前系统状态
    _is_running = False
    _animation_thread = None
    _current_message = "系统正常运行中..."
    _safe_mode = True            # 启用安全模式，避免线程错误
    _is_busy = False             # 指示反馈器是否正在处理事件
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = VisualFeedbackManager()
        return cls._instance
    
    def __init__(self):
        """初始化视觉反馈管理器"""
        if VisualFeedbackManager._instance is not None:
            raise Exception("VisualFeedbackManager是单例类，请使用get_instance()方法")
        
        # 创建主窗口
        self._create_ui()
        VisualFeedbackManager._instance = self
    
    def _create_ui(self):
        """创建基本UI界面"""
        # 创建主窗口
        self._window = tk.Tk()
        self._window.title("系统视觉反馈")
        self._window.geometry("500x350")  # 增加窗口尺寸
        self._window.configure(bg=self._colors["background"])
        
        # 设置窗口置顶
        self._window.attributes("-topmost", True)
        
        # 添加标题标签
        title_label = tk.Label(
            self._window, 
            text="系统状态监控", 
            font=("微软雅黑", 16, "bold"),
            fg=self._colors["text"],
            bg=self._colors["background"]
        )
        title_label.pack(pady=10)
        
        # 创建单一状态指示器框架
        status_frame = tk.Frame(self._window, bg=self._colors["background"])
        status_frame.pack(pady=20, fill=tk.X)
        
        # 创建单一大型状态指示圆形
        canvas = tk.Canvas(status_frame, width=100, height=100, bg=self._colors["background"], highlightthickness=0)
        canvas.pack()
        
        # 绘制圆形指示灯
        circle = canvas.create_oval(10, 10, 90, 90, fill=self._colors["normal"], outline="")
        
        # 状态标签
        status_label = tk.Label(
            status_frame, 
            text="状态正常",
            fg=self._colors["text"],
            bg=self._colors["background"],
            font=("微软雅黑", 12, "bold")
        )
        status_label.pack(pady=5)
        
        # 存储元素引用
        self._elements["status"] = {
            "canvas": canvas,
            "circle": circle,
            "label": status_label,
            "status": "normal"  # 初始状态
        }
        
        # 创建消息显示区域
        message_frame = tk.Frame(self._window, bg=self._colors["background"])
        message_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # 消息标签 - 增加高度和字体大小
        self._message_label = tk.Label(
            message_frame,
            text=self._current_message,
            font=("微软雅黑", 13),    # 增加字体大小
            fg=self._colors["text"],
            bg=self._colors["background"],
            wraplength=450,         # 增加文本换行宽度
            justify=tk.CENTER,      # 文本居中显示
            height=5                # 固定高度，保证有足够空间显示多行
        )
        self._message_label.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # 存储消息标签
        self._elements["message"] = self._message_label
        
        # 关闭窗口时的处理
        self._window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 启动UI主循环（在新线程中）
        self._is_running = True
        if not self._safe_mode:
            # 仅在非安全模式使用线程
            threading.Thread(target=self._run_ui_loop, daemon=True).start()
        
        # 初始状态下显示窗口（而不是隐藏）
        self.show()  # 修改为默认显示窗口
    
    def _on_close(self):
        """处理窗口关闭事件"""
        self._is_running = False
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=0.5)
        self._window.destroy()
        self._window = None
    
    def _run_ui_loop(self):
        """运行UI主循环（仅在非安全模式使用）"""
        try:
            if self._window:
                self._window.mainloop()
        except Exception as e:
            print(f"[视觉反馈UI错误] {e}")
    
    def show(self):
        """显示视觉反馈窗口"""
        if self._window:
            self._window.deiconify()
            if self._safe_mode:
                # 在安全模式下，使用update而不是mainloop
                try:
                    self._window.update()
                except Exception as e:
                    print(f"[视觉反馈更新错误] {e}")
    
    def hide(self):
        """隐藏视觉反馈窗口"""
        if self._window:
            self._window.withdraw()
            if self._safe_mode:
                try:
                    self._window.update()
                except Exception:
                    pass
    
    def is_busy(self):
        """返回反馈管理器当前是否正在处理事件"""
        return self._is_busy
    
    def update_status(self, state, message=None):
        """
        更新状态指示器
        
        参数:
            state: 状态值 ('normal', 'info', 'success', 'warning', 'error')
            message: 可选的状态消息
        """
        if not self._window:
            return False
            
        # 设置忙碌状态
        self._is_busy = True
        
        try:
            element = self._elements["status"]
            
            # 获取对应状态的颜色
            color = self._colors.get(state, self._colors["normal"])
            
            # 更新状态文本
            status_text = {
                "normal": "状态正常",
                "info": "系统信息",
                "success": "操作成功",
                "warning": "系统警告",
                "error": "严重警告"
            }.get(state, "状态正常")
            
            # 更新圆形指示灯颜色和标签
            if self._safe_mode:
                try:
                    element["canvas"].itemconfig(element["circle"], fill=color)
                    element["label"].config(text=status_text)
                    self._current_status = state
                    
                    # 如果提供了消息，更新消息显示
                    if message:
                        self._current_message = message
                        if "message" in self._elements:
                            self._elements["message"].config(text=message)
                    
                    # 确保窗口可见
                    self.show()
                except Exception as e:
                    print(f"[视觉反馈更新错误] {e}")
                    self._is_busy = False
                    return False
            else:
                # 使用UI线程安全的方式更新
                self._window.after(0, lambda: self._safe_update(element, color, status_text, message))
            
            # 如果是警告或错误状态，添加闪烁效果
            if state in ["warning", "error"] and not self._safe_mode:
                self._start_blink_animation(color)
                
            return True
        except Exception as e:
            print(f"[视觉反馈状态更新错误] {e}")
            self._is_busy = False
            return False
    
    def _safe_update(self, element, color, status_text, message):
        """在UI线程中安全地更新界面元素"""
        try:
            element["canvas"].itemconfig(element["circle"], fill=color)
            element["label"].config(text=status_text)
            
            # 如果提供了消息，更新消息显示
            if message and "message" in self._elements:
                self._elements["message"].config(text=message)
                
            # 确保窗口可见
            self.show()
        except Exception as e:
            print(f"[视觉反馈安全更新错误] {e}")
        finally:
            self._is_busy = False
    
    def _start_blink_animation(self, color):
        """为状态启动闪烁动画（仅在非安全模式使用）"""
        # 安全模式不使用动画
        if self._safe_mode:
            return
            
        # 停止现有动画
        self._is_running = False
        if self._animation_thread and self._animation_thread.is_alive():
            self._animation_thread.join(timeout=0.5)
        
        # 启动新动画
        self._is_running = True
        self._animation_thread = threading.Thread(
            target=self._run_blink_animation,
            args=(color,),
            daemon=True
        )
        self._animation_thread.start()
    
    def _run_blink_animation(self, color):
        """运行闪烁动画的线程函数（仅在非安全模式使用）"""
        # 安全模式不使用动画
        if self._safe_mode:
            return
            
        element = self._elements["status"]
        status = self._current_status
        
        # 闪烁次数
        blink_count = 10 if status == "error" else 6
        
        # 执行闪烁
        for _ in range(blink_count):
            if not self._is_running or not self._window:
                break
                
            # 闪烁频率根据严重程度调整
            blink_speed = 0.2 if status == "error" else 0.3
            
            try:
                # 切换颜色（灰色）
                self._window.after(0, lambda: element["canvas"].itemconfig(element["circle"], fill=self._colors["normal"]))
                time.sleep(blink_speed)
                
                # 切换回原来的颜色
                self._window.after(0, lambda: element["canvas"].itemconfig(element["circle"], fill=color))
                time.sleep(blink_speed)
            except Exception:
                break
                
        # 保持最终状态
        if self._window and self._is_running:
            try:
                self._window.after(0, lambda: element["canvas"].itemconfig(element["circle"], fill=color))
            except Exception:
                pass
        
        # 动画完成，重置忙碌状态
        self._is_busy = False

# 修改wait_for_feedback_completion函数，缩短等待时间
def wait_for_feedback_completion(max_wait_seconds=2):
    """
    等待所有反馈（视觉、语音等）完成
    
    参数:
        max_wait_seconds: 最大等待时间（秒）
    """
    global _visual_feedback_window
    
    # 如果视觉反馈窗口未初始化，无需等待
    if _visual_feedback_window is None:
        return
    
    # 等待视觉反馈完成
    start_time = time.time()
    while _visual_feedback_window.is_busy() and time.time() - start_time < max_wait_seconds:
        time.sleep(0.05)  # 缩短休眠间隔，提高响应速度
        
        # 更新UI以保持响应
        try:
            if _visual_feedback_window._window:
                _visual_feedback_window._window.update()
        except Exception:
            pass

def visual_feedback_show_status(state, message=None):
    """
    显示视觉反馈状态
    
    参数:
        state: 'normal', 'info', 'success', 'warning', 'error'中的一种
        message: 可选的状态消息
    """
    # 获取视觉反馈管理器实例
    global _visual_feedback_window
    try:
        if _visual_feedback_window is None:
            _visual_feedback_window = VisualFeedbackManager.get_instance()
        
        # 更新状态
        return _visual_feedback_window.update_status(state, message)
    except Exception as e:
        print(f"[视觉反馈错误] {e}")
        return False

def simple_speak(text):
    """最简单的语音合成函数，直接使用Windows SAPI输出语音"""
    try:
        # 直接创建SAPI.SpVoice对象
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        
        # 设置音量和语速
        speaker.Volume = 100  # 最大音量
        
        # 查找并设置中文语音
        voices = speaker.GetVoices()
        for i in range(voices.Count):
            voice = voices.Item(i)
            desc = voice.GetDescription()
            if "chinese" in desc.lower() or "zh-cn" in desc.lower() or "huihui" in desc.lower():
                speaker.Voice = voice
                break
        
        # 直接输出语音，不使用线程
        print(f"[语音输出] '{text}'")
        speaker.Speak(text)
        
        # 语音合成完成后，重置视觉反馈状态但不隐藏窗口
        try:
            if _visual_feedback_window:
                # 将状态重置为正常，保持窗口可见
                _visual_feedback_window.update_status("normal", "系统正常运行中...")
        except Exception as e:
            print(f"[视觉反馈重置错误] {e}")
        
        return True
    except Exception as e:
        print(f"[语音输出错误] {e}")
        return False

def _get_tts_engine():
    """获取或初始化TTS引擎，使用单例模式"""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = pyttsx3.init()
        try:
            # 打印可用语音信息，帮助调试
            voices = _tts_engine.getProperty('voices')
            print(f"[TTS] 检测到 {len(voices)} 个可用语音引擎")
            
            # 设置默认语速和音量
            _tts_engine.setProperty('rate', 150)  # 默认语速
            _tts_engine.setProperty('volume', 1.0)  # 最大音量
            
            # 尝试设置中文语音为默认
            for voice in voices:
                if "chinese" in voice.name.lower() or "zh" in voice.id.lower() or "huihui" in voice.name.lower():
                    print(f"[TTS] 设置默认中文语音: {voice.name}")
                    _tts_engine.setProperty('voice', voice.id)
                    break
        except Exception as e:
            print(f"[TTS初始化警告] {e}")
    return _tts_engine

def speak_text(text, volume=100, lang="zh-CN"):
    """尝试使用所有可用方法输出语音，确保至少有一种能工作"""
    # 方法1: 直接使用Windows SAPI (最可靠)
    if simple_speak(text):
        return True
    
    # 方法2: 使用pyttsx3
    try:
        engine = _get_tts_engine()
        print(f"[pyttsx3语音] '{text}'")
        engine.say(text)
        engine.runAndWait()
        return True
    except Exception as e:
        print(f"[pyttsx3错误] {e}")
    
    # 如果所有方法都失败，返回False
    print("[警告] 所有语音输出方法都失败了")
    return False

# --- 模拟外部输出服务的调用 ---
# 当其他组员完成他们的输出模块后，你需要用真实的调用替换掉这些模拟函数。
# 你需要和他们约定好函数接口（函数名、参数等）。

def SIMULATE_tts_manager_speak(text: str, lang: str = "zh-CN", volume: int = 70, user_id: str = None, event_type: str = None, event_data: dict = None):
    """模拟语音合成服务，现在会真实调用语音引擎，同时提供详细的控制台输出"""
    # 生成详细的控制台输出，包括用户和操作信息
    if event_data:
        # 优先使用event_data中的用户名称
        user_name = event_data.get("user_name", "")
        user_role = event_data.get("user_role", "")
        if user_name and user_role:
            user_info = f"用户[{user_name}({user_role})]"
        elif user_name:
            user_info = f"用户[{user_name}]"
        else:
            user_info = f"用户[{user_id}]" if user_id else ""
    else:
        user_info = f"用户[{user_id}]" if user_id else ""
        
    output_prefix = "\n[模拟TTS输出]"
    
    # 为不同的事件类型提供更详细的控制台输出
    if event_type == EVENT_PERMISSION_DENIED and event_data:
        action_tag = event_data.get("action_tag", "未知操作")
        command = event_data.get("attempted_command", "")
        intent = event_data.get("recognized_intent", "")
        detail = command if command else intent
        if user_info and detail:
            print(f"{output_prefix} {user_info} 尝试执行 '{detail}' (权限: {action_tag})，但权限不足")
        else:
            print(f"{output_prefix} 权限不足: 尝试执行 '{action_tag}'")
    elif event_type == EVENT_COMMAND_SUCCESS and event_data:
        command = event_data.get("command_name", "")
        if user_info and command:
            print(f"{output_prefix} {user_info} 成功执行: '{command}'")
        else:
            print(f"{output_prefix} 操作成功: '{command}'")
    elif event_type == EVENT_USER_DISTRACTED and event_data:
        duration = event_data.get("gaze_off_duration", "")
        if user_info and duration:
            print(f"{output_prefix} {user_info} 分心警告: 视线离开道路 {duration} 秒")
        else:
            print(f"{output_prefix} 分心警告")
    elif "检测到目光区域" in text:
        area = text.split("在")[-1] if "在" in text else ""
        if user_info and area:
            print(f"{output_prefix} {user_info} 视线检测: 目光区域在{area}")
        else:
            print(f"{output_prefix} 视线检测: {text}")
    elif "检测到头部姿态" in text:
        pose = text.split("态")[-1] if "态" in text else ""
        if user_info and pose:
            print(f"{output_prefix} {user_info} 姿态检测: 头部姿态{pose}")
        else:
            print(f"{output_prefix} 姿态检测: {text}")
    else:
        # 默认详细输出格式
        if user_info:
            print(f"{output_prefix} {user_info} 内容: '{text}'")
        else:
            print(f"{output_prefix} 内容: '{text}'")
    
    # 使用简单直接的语音输出方法
    simple_speak(text)
    
    # 语音完成后，将视觉反馈状态重置为正常
    try:
        if _visual_feedback_window:
            _visual_feedback_window.update_status("normal", "系统正常运行中...")
            # 不再隐藏窗口，让它保持可见
            # 移除: _visual_feedback_window.hide()
    except Exception as e:
        print(f"[视觉反馈重置错误] {e}")
    
    # 无需再等待视觉反馈完成，因为我们已经重置了它

def SIMULATE_text_display_manager_show_message(text: str, style: str = "info", duration_ms: int = 3000, position: str = "status_bar"):
    """模拟文本显示服务"""
    print(f"[模拟文本显示] 位置: {position}, 样式: {style}, 持续时间: {duration_ms}ms, 内容: '{text}'")

def SIMULATE_visual_alert_manager_trigger(alert_type: str = "warning_blink", intensity: str = "medium", color: str = "red"):
    """模拟视觉警报服务 (如仪表盘灯)"""
    print(f"[模拟视觉警报] 类型: {alert_type}, 强度: {intensity}, 颜色: {color}")

# --- 实际的反馈编排逻辑 ---

def _generate_feedback_message(event_type: str, event_data: dict, voice_detail_level: str) -> str:
    """根据事件类型和数据生成反馈文本"""
    message_text = f"收到事件：{event_type}" # 默认消息

    if event_type == EVENT_USER_DISTRACTED:
        duration = event_data.get("gaze_off_duration", "一段时间")
        if voice_detail_level == "brief":
            message_text = "请注意前方！"
        elif voice_detail_level == "urgent":
            message_text = f"警告！检测到您已分神 {duration} 秒！请立即注视前方道路！"
        else: # normal
            message_text = f"请保持注意力集中在驾驶上。检测到您已分神 {duration}。"
    
    elif event_type == EVENT_COMMAND_SUCCESS:
        command_name = event_data.get("command_name", "操作")
        if voice_detail_level == "brief":
            message_text = f"{command_name}，已完成。"
        else:
            message_text = f"指令 '{command_name}' 已成功执行。"
            
    elif event_type == EVENT_COMMAND_FAILURE:
        command_name = event_data.get("command_name", "操作")
        reason = event_data.get("reason", "未知原因")
        if voice_detail_level == "brief":
            message_text = f"{command_name}，失败。"
        else:
            message_text = f"抱歉，指令 '{command_name}' 执行失败。原因是：{reason}。"

    elif event_type == EVENT_PERMISSION_DENIED:
        action_tag = event_data.get("action_tag", "该操作")
        if voice_detail_level == "brief":
            message_text = "权限不足。"
        else:
            message_text = f"抱歉，您没有权限执行 '{action_tag}'。"
            
    elif event_type == EVENT_GENERIC_INFO:
        # 处理通用信息事件，优先使用message字段
        custom_message = event_data.get("message", "")
        
        # 检查是否有视觉相关的输入数据
        input_summary = event_data.get("input_data_summary", "")
        gaze_area = event_data.get("gaze_area", "")
        head_pose = event_data.get("head_pose", "")
        
        # 如果有目光区域信息，生成对应的消息
        if gaze_area or "目光区域" in input_summary:
            area = gaze_area or (input_summary.split(":")[-1].strip() if ":" in input_summary else "")
            message_text = f"检测到目光区域在{area}"
        # 如果有头部姿态信息，生成对应的消息
        elif head_pose or "头部姿态" in input_summary:
            pose = head_pose or (input_summary.split(":")[-1].strip() if ":" in input_summary else "")
            message_text = f"检测到头部姿态{pose}"
        # 使用自定义消息或默认消息
        elif custom_message:
            message_text = custom_message
        else:
            message_text = "收到一条新信息。"
        
    return message_text

def trigger_feedback(user_id: str, event_type: str, event_data: dict = None) -> dict:
    """
    根据用户偏好和事件类型，编排并触发多模态反馈。
    返回一个字典，包含实际触发的反馈模态和内容的摘要。
    """
    # 不再需要等待前一个反馈完成，因为语音结束后已经重置了视觉反馈
    # 移除: wait_for_feedback_completion()
    
    if event_data is None:
        event_data = {}

    prefs = user_manager.get_feedback_preferences(user_id, event_type)
    voice_detail_level = prefs.get("voice_detail_level", "normal")
    
    # 生成核心反馈文本
    feedback_text = _generate_feedback_message(event_type, event_data, voice_detail_level)

    triggered_modalities_summary = [] # 用于日志记录
    
    # 检查是否是高优先级事件，如驾驶员分心警告
    is_high_priority = event_type == EVENT_USER_DISTRACTED
    
    # 首先触发视觉反馈，使其与语音并行
    # 4. 图形化视觉反馈 (状态图标和颜色变化) - 简化版本，只有一个状态指示器
    if "visual_graphic_feedback" in prefs.get("enabled_modalities", []):
        # 根据事件类型设置不同的状态
        state = "info"  # 默认状态
        
        if event_type == EVENT_USER_DISTRACTED:
            # 分心警告 - 红色错误状态
            state = "error" if voice_detail_level == "urgent" else "error"
        elif event_type == EVENT_COMMAND_SUCCESS:
            # 操作成功 - 绿色成功状态
            state = "success"
        elif event_type == EVENT_COMMAND_FAILURE:
            # 操作失败 - 橙色警告状态
            state = "warning"
        elif event_type == EVENT_PERMISSION_DENIED:
            # 权限不足 - 橙色警告状态
            state = "warning"
            
        # 调用视觉反馈，只更新单一状态指示器
        visual_feedback_show_status(state, feedback_text)
        triggered_modalities_summary.append(f"图形视觉反馈: 状态={state}, 消息='{feedback_text}'")

    # 3. 视觉反馈 (仪表盘灯等)
    if "visual_dashboard_light" in prefs.get("enabled_modalities", []):
        alert_type = "info_blink_blue" # 默认视觉警报
        intensity = "medium"
        color = "blue"
        
        if event_type == EVENT_USER_DISTRACTED:
            # 分心警告 - 红色
            alert_type = "warning_solid_red" if voice_detail_level == "urgent" else "warning_blink_red"
            intensity = "high" if voice_detail_level == "urgent" else "medium"
            color = "red"
        elif event_type == EVENT_COMMAND_FAILURE:
            alert_type = "error_blink_orange"
            intensity = "medium"
            color = "orange"
        elif event_type == EVENT_PERMISSION_DENIED:
            # 权限不足 - 橙色
            alert_type = "error_blink_orange"
            intensity = "medium"
            color = "orange"

        # 调用模拟的视觉提醒服务
        SIMULATE_visual_alert_manager_trigger(alert_type=alert_type, intensity=intensity, color=color)
        triggered_modalities_summary.append(f"视觉警报: 类型={alert_type}, 强度={intensity}, 颜色={color}")

    # 2. 文本反馈 (UI显示)
    if "text_display" in prefs.get("enabled_modalities", []) and prefs.get("text_display_enabled", True):
        text_style = "info" # 默认样式
        if event_type == EVENT_USER_DISTRACTED:
            # 分心警告 - 错误样式
            text_style = "error"
        elif event_type == EVENT_COMMAND_FAILURE:
            text_style = "warning"
        elif event_type == EVENT_PERMISSION_DENIED:
            # 权限不足 - 警告样式
            text_style = "warning"
        
        # 调用文本显示服务
        SIMULATE_text_display_manager_show_message(text=feedback_text, style=text_style)
        triggered_modalities_summary.append(f"文本显示: '{feedback_text}' (样式:{text_style})")

    # 1. 语音反馈 - 语音播报会同步显示视觉反馈，并在结束时自动关闭视觉反馈
    if "voice" in prefs.get("enabled_modalities", []) and not prefs.get("disable_all_audio_feedback", False):
        volume = prefs.get("general_voice_volume", 70)
        
        # 对于高优先级事件，使用更高的音量
        if is_high_priority and voice_detail_level == "urgent":
            volume = min(90, volume + 20)  # 增加音量但不超过90
            
        # 调用语音输出 - 语音结束后将自动关闭视觉反馈
        SIMULATE_tts_manager_speak(text=feedback_text, volume=volume, lang="zh-CN", user_id=user_id, event_type=event_type, event_data=event_data)
        triggered_modalities_summary.append(f"语音: '{feedback_text}' (音量:{volume})")
    else:
        # 即使用户偏好中没有启用语音，也尝试为检测结果提供语音反馈
        # 这确保所有类型的消息都能被语音播报
        gaze_area = event_data.get("gaze_area", "")
        head_pose = event_data.get("head_pose", "")
        input_summary = event_data.get("input_data_summary", "")
        
        # 为检测到的目光区域和头部姿态提供语音反馈
        if "目光区域" in str(input_summary) or "头部姿态" in str(input_summary) or gaze_area or head_pose:
            speak_text = feedback_text
            if "收到一条新信息" in speak_text:
                # 如果是检测到的目光区域或头部姿态，提供更具体的语音反馈
                if "目光区域" in str(input_summary):
                    area = input_summary.split(":")[-1] if ":" in input_summary else ""
                    speak_text = f"检测到目光区域在{area}"
                elif "头部姿态" in str(input_summary):
                    pose = input_summary.split(":")[-1] if ":" in input_summary else ""
                    speak_text = f"检测到头部姿态{pose}"
            
            # 调用语音输出 - 语音结束后将自动关闭视觉反馈
            SIMULATE_tts_manager_speak(text=speak_text, volume=70, lang="zh-CN", user_id=user_id, event_type=event_type, event_data=event_data)
            triggered_modalities_summary.append(f"语音: '{speak_text}' (音量:70)")
        else:
            # 如果没有语音反馈，则需要手动重置视觉反馈，但不关闭窗口
            if _visual_feedback_window:
                try:
                    _visual_feedback_window.update_status("normal", "系统正常运行中...")
                    # 移除: _visual_feedback_window.hide()
                except Exception:
                    pass

    # 不再需要等待所有反馈完成，因为语音结束时已经重置了视觉反馈
    # 移除: wait_for_feedback_completion()

    return {
        "modalities_triggered": [item.split(":")[0].lower().replace(" ", "_") for item in triggered_modalities_summary], # 例如 ["语音", "文本显示"]
        "summary_for_log": "; ".join(triggered_modalities_summary) # 完整的摘要，方便写入日志
    }
