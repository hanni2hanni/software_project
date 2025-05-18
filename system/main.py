# system_management/main.py

import json
import os
import random
import time
import shutil # 引入 shutil 模块用于文件操作

# 确保可以正确导入同级目录或父级目录的模块
# 如果直接运行 main.py 遇到 ImportError, 可能需要调整 Python 路径或使用 -m 运行
try:
    from . import user_manager
    from . import interaction_logger
    from . import feedback_orchestrator
    from . import config # 引入config以使用事件类型常量等
    from .interaction_analyzer import InteractionAnalyzer # 引入日志分析模块
except ImportError:
    # Fallback for direct script execution if needed, though -m is preferred
    import user_manager
    import interaction_logger
    import feedback_orchestrator
    import config
    from interaction_analyzer import InteractionAnalyzer


# 当前活动用户ID (简化处理，实际系统中用户识别会更复杂)
# 初始化为默认访客，将在 __main__ 块的 initialize_system_management 中设置
_current_active_user_id = config.DEFAULT_USER_ID # 初始化为默认访客


# 初始化日志分析器 (Note: This might interact with files on import, but the cleanup in __main__ handles it)
# Analyzer 实例可以在这里创建，但其运行依赖的文件(logs, reports)会在__main__中处理
interaction_analyzer = InteractionAnalyzer()


def initialize_system_management(initial_active_user_id: str = None):
    """
    初始化系统管理模块的各个组件。
    可以指定初始的活动用户。
    注意：在调用此函数前，应确保所有必要的默认和测试用户已通过 user_manager.add_user 添加。
    """
    global _current_active_user_id

    # ensure reports directory exists *before* any analysis attempt later
    # This will create 'data/reports' if 'data' exists (which it should after user_manager runs)
    os.makedirs(os.path.dirname(config.ANALYSIS_REPORT_PATH), exist_ok=True)
    
    # 初始化视觉反馈管理器
    try:
        # 预热视觉反馈管理器
        from .feedback_orchestrator import visual_feedback_show_status
        # 显示系统初始化状态
        visual_feedback_show_status("info", "系统正在初始化...")
        print("视觉反馈管理器已成功初始化。")
    except Exception as e:
        print(f"警告：视觉反馈管理器初始化失败 - {e}")
    
    # 初始化语音引擎
    try:
        # 预热语音引擎，确保后续使用时更加流畅
        from .feedback_orchestrator import _get_tts_engine
        _get_tts_engine()
        print("语音引擎已成功初始化。")
    except Exception as e:
        print(f"警告：语音引擎初始化失败 - {e}。将仅使用文本输出。")

    # Try to set the initial active user
    if initial_active_user_id:
        # Check if the specified initial user exists and is not the default guest role using the currently loaded profiles
        profiles = user_manager._load_all_profiles() # Ensure we're working with the latest profiles loaded from file
        if initial_active_user_id in profiles and profiles[initial_active_user_id].get("role") != config.DEFAULT_ROLE:
             _current_active_user_id = initial_active_user_id
        else:
            # If the specified initial user doesn't exist or is the default guest role for a different ID
            print(f"警告：初始指定的用户ID '{initial_active_user_id}' 未找到或为默认访客，将使用默认访客用户 '{config.DEFAULT_USER_ID}'。")
            _current_active_user_id = config.DEFAULT_USER_ID
    else:
        # If no initial user specified, use the default guest user
        _current_active_user_id = config.DEFAULT_USER_ID

    print(f"系统管理模块已初始化。当前活动用户: '{_current_active_user_id}' ({user_manager.get_user_role(_current_active_user_id)})。")
    
    # 更新视觉反馈状态为初始化完成
    try:
        visual_feedback_show_status("success", "系统初始化完成")
    except Exception:
        pass


def set_active_user(user_id: str) -> bool:
    """
    设置当前系统的活动用户。
    确保用户ID存在于用户配置中。
    """
    global _current_active_user_id
    profiles = user_manager._load_all_profiles() # Load all to be sure

    # 简化检查：只要用户ID存在于已加载的配置文件中，就允许设置为活动用户。
    # 如果有特殊需求（例如，默认访客用户ID不能通过此接口设置），可以添加额外的条件。
    if user_id in profiles:
        _current_active_user_id = user_id
        # 在频繁调用的地方可以考虑不打印，或者打印调试级别的日志
        # print(f"活动用户已更改为: '{user_id}' ({user_manager.get_user_role(user_id)})。")
        return True
    else:
        # 用户ID未找到，无法设置活动用户
        print(f"错误：无法设置活动用户，用户ID '{user_id}' 未找到。")
        return False



def get_active_user_id() -> str:
    """获取当前活动用户的ID。"""
    return _current_active_user_id

# --- 用户管理接口 ---
def add_new_user(user_id: str, name: str, role: str, initial_preferences: dict = None) -> tuple[bool, str]:
    """
    添加新用户。
    返回 (是否成功, 消息)。打印内部信息（仅限警告/错误）。
    """
    try:
        user_manager.add_user(user_id, name, role, initial_preferences)
        # 移除这一行的打印，避免与 user_manager.add_user 内部的打印重复
        # print(f"用户 '{user_id}' ({name}) 已添加，角色为 '{role}'。") # 原来的打印行
        return True, f"用户 '{user_id}' 添加成功。"
    except ValueError as e:
        print(f"警告: {e}") # Print warning if user already exists
        return False, str(e)
    except Exception as e:
        print(f"错误: 添加用户 '{user_id}' 失败 - {e}") # Catch any other unexpected errors
        return False, f"添加用户失败: {e}"


def delete_existing_user(user_id: str) -> tuple[bool, str]:
    """删除用户。"""
    global _current_active_user_id

    profiles_before_delete = user_manager._load_all_profiles()
    if user_id not in profiles_before_delete:
        # 如果用户不存在，直接返回失败信息，避免调用 user_manager.delete_user 产生内部警告
        return False, f"错误：用户ID '{user_id}' 未找到，无法执行删除操作。"

    if user_id == _current_active_user_id:
         return False, f"错误：不能删除当前活动用户 '{user_id}'。请先切换用户。"
    if user_id == config.DEFAULT_USER_ID:
        return False, f"错误：不能通过此接口删除默认访客用户 '{config.DEFAULT_USER_ID}'。"
    try:
        user_manager.delete_user(user_id)
        # 删除操作后，重新加载配置文件以验证用户是否已被移除
        profiles_after_delete = user_manager._load_all_profiles()
        if user_id not in profiles_after_delete:
            # **修改点2：移除此处的打印语句，因为 user_manager.delete_user 可能会自行打印成功信息**
            # print(f"用户 '{user_id}' 已被删除。") # user_manager.delete_user 可能会有自己的打印，此处添加验证打印。
            return True, f"用户 '{user_id}' 删除成功。"
        else:
            # 这表明 user_manager.delete_user 可能没有实际删除用户但也没有抛出异常
            return False, f"警告：用户 '{user_id}' 的删除操作未成功（用户管理模块可能存在问题）。"
    except ValueError as e: # Catch ValueError from user_manager.delete_user (e.g. user not found)
        return False, str(e)
    except Exception as e: # Catch other potential exceptions
        return False, f"删除用户失败: {e}"


def modify_user_role(user_id: str, new_role: str) -> tuple[bool, str]:
    """修改用户角色。"""
    try:
        user_manager.change_user_role(user_id, new_role)
        print(f"用户 '{user_id}' 的角色已成功修改为 '{new_role}'。") # Print internal success
        return True, f"用户 '{user_id}' 的角色已成功修改为 '{new_role}'。"
    except ValueError as e:
        print(f"修改用户角色失败: {e}") # Print failure reason
        return False, str(e)

def get_user_profile(user_id: str = None) -> dict:
    """获取用户配置。如果未指定user_id，则获取当前活动用户的配置。"""
    target_user_id = user_id if user_id else _current_active_user_id
    # user_manager.load_user_profile will return default config if user doesn't exist, which is intended here
    return user_manager.load_user_profile(target_user_id)

def update_user_profile(profile_data: dict, user_id: str = None):
    """更新用户配置。如果未指定user_id，则更新当前活动用户的配置。"""
    target_user_id = user_id if user_id else _current_active_user_id
    # Note: This is a full replacement. If partial updates are needed, user_manager.save_user_profile needs to support merge logic
    user_manager.save_user_profile(target_user_id, profile_data)
    # print(f"用户 '{target_user_id}' 的配置已更新。") # Avoid frequent printing during simulation

# --- 权限检查接口 ---
def is_action_permitted(action_tag: str, user_id: str = None) -> bool:
    """检查指定用户 (默认为当前活动用户) 是否有权限执行某个动作。"""
    target_user_id = user_id if user_id else _current_active_user_id
    return user_manager.check_permission(target_user_id, action_tag)

# --- Core: Event Handling and Feedback Interface ---
def process_event_and_trigger_feedback(
    event_type: str,
    event_data: dict = None,
    # The following parameters are mainly for enriching log records
    target_user_id: str = None, # If the event is for a specific user, not the current active user
    input_modalities: str = "N/A", # e.g., "voice", "gesture;vision_gaze"
    input_data_summary: str = "N/A", # e.g., "Voice: Turn down AC to 20 degrees"
    recognized_intent: str = "N/A", # e.g., "OPEN_AC"
    system_action_taken: str = "N/A", # e.g., "AC controller API call successful"
    action_result: str = "N/A", # e.g., "success", "failure_hw_error"
    additional_notes: str = ""
) -> dict:
    """
    Processes a system event, triggers multimodal feedback based on user preferences, and logs the interaction.
    This is the primary entry point for other modules (like fusion_engine or main_application) to interact with the system management module.
    """
    if event_data is None:
        event_data = {}

    user_for_feedback = target_user_id if target_user_id else _current_active_user_id

    # Ensure the current active user ID is not None or guest_user if a specific user was intended.
    # In this simulation, _current_active_user_id is initialized to guest, so this check is less critical but good practice.
    if user_for_feedback is None: # This should not happen if initialized correctly
        print("错误: 当前活动用户未设置，无法处理事件并触发反馈。")
        return {"status": "failed", "message": "Active user not set"}

    user_role = user_manager.get_user_role(user_for_feedback)
    # 获取用户姓名，用于更详细的输出
    user_profile = user_manager.load_user_profile(user_for_feedback)
    user_name = user_profile.get('name', user_for_feedback)
    
    # 把用户信息添加到事件数据中
    event_data["user_id"] = user_for_feedback
    event_data["user_name"] = user_name
    event_data["user_role"] = user_role

    # 预处理input_data_summary，确保它可以被正确处理
    # 增强事件数据，添加更多信息供feedback_orchestrator使用
    if "目光区域" in input_data_summary:
        parts = input_data_summary.split(":")
        if len(parts) > 1:
            event_data["gaze_area"] = parts[1].strip()
    elif "头部姿态" in input_data_summary:
        parts = input_data_summary.split(":")
        if len(parts) > 1:
            event_data["head_pose"] = parts[1].strip()
    
    # 把input_data_summary添加到事件数据中
    event_data["input_data_summary"] = input_data_summary
    
    # 对于权限拒绝事件，确保事件数据包含完整的用户和操作信息
    if event_type == config.EVENT_PERMISSION_DENIED and "action_tag" in event_data:
        if "attempted_command" not in event_data and input_data_summary != "N/A":
            event_data["attempted_command"] = input_data_summary
        if "user_display_info" not in event_data:
            event_data["user_display_info"] = f"{user_name} ({user_role})"

    # 2. Trigger the feedback orchestrator
    feedback_outcome = feedback_orchestrator.trigger_feedback(user_for_feedback, event_type, event_data)

    # 3. Prepare and log the interaction
    log_entry = {
        # "timestamp": "", # interaction_logger will auto-fill if empty
        "user_id": user_for_feedback,
        "user_role": user_role,
        "event_type": event_type,
        "input_modalities": input_modalities,
        # Only convert event_data to string for logging if input_data_summary is not provided
        "input_data_summary": input_data_summary if input_data_summary != "N/A" else str(event_data),
        "recognized_intent": recognized_intent,
        "system_action_taken": system_action_taken,
        "action_result": action_result,
        "feedback_modalities_triggered": ", ".join(feedback_outcome.get("modalities_triggered", [])),
        "feedback_content_summary": feedback_outcome.get("summary_for_log", ""),
        "notes": additional_notes
    }
    interaction_logger.log_interaction(log_entry)

    # 4. Return the processing result, including feedback details
    return {
        "status": "processed",
        "user_id": user_for_feedback,
        "event_type_processed": event_type,
        "feedback_details": feedback_outcome
    }

# --- Log Analysis Function Entry Point ---
def run_log_analysis_and_update_personalization():
    """
    Runs log analysis and updates user personalization configurations based on the results.
    """
    global interaction_analyzer
    # interaction_analyzer needs the user_manager instance to update user configurations
    # Ensure user profiles are loaded before analysis attempts to update them
    # user_manager._load_all_profiles() # Analysis module should handle loading profiles or take profiles as input
    interaction_analyzer.run_analysis(user_manager)
    print(f"分析报告已生成至: {config.ANALYSIS_REPORT_PATH}")


# --- Example: Simulate Multimodal Interaction and Logging (Simulator classes remain unchanged) ---
# These simulation functions help generate log data for analysis testing

class VoiceInputSimulator:
    def get_input(self):
        commands = [
            ("打开空调", "CONTROL_AC"),
            ("播放音乐", "PLAY_MUSIC"),
            ("调低音量", "SET_VOLUME"),
            ("已注意道路", "CONFIRM_ACTION"),
            ("导航到公司", "START_NAVIGATION"),
            ("发送短信给刘阳", "SEND_MESSAGE"),
            ("显示诊断信息", "VIEW_DIAGNOSTICS"),
            ("重置系统", "RESET_SYSTEM"),
            ("今天天气怎么样", "GET_WEATHER"),
            ("讲个笑话", "TELL_JOKE"),
        ]
        import random
        input_data, intent = random.choice(commands)
        return {"modality": "voice", "input_data_summary": f"语音:{input_data}", "recognized_intent": intent}

class GestureInputSimulator:
    def get_input(self):
        gestures = [
            ("握拳", "PAUSE_MUSIC"),
            ("竖起大拇指", "CONFIRM_ACTION"),
            ("摇手", "REJECT_ACTION"),
            ("向左滑动", "PREVIOUS_SONG"),
            ("向右滑动", "NEXT_SONG"),
            ("双指捏合", "ZOOM_OUT_MAP"),
        ]
        import random
        input_data, intent = random.choice(gestures)
        return {"modality": "gesture", "input_data_summary": f"手势:{input_data}", "recognized_intent": intent}

class VisionInputSimulator:
    def get_input(self):
        gaze_areas = ["道路", "仪表盘", "手机", "乘客", "导航屏", "车外"]
        head_poses = [("点头", "CONFIRM_ACTION"), ("摇头", "REJECT_ACTION"), ("直视", "LOOKING_STRAIGHT"), ("看向左后视镜", "LOOKING_SIDE")]
        eye_states = ["睁眼", "闭眼"]
        import random
        gaze = random.choice(gaze_areas)
        head_pose_data, head_pose_intent = random.choice(head_poses)
        eye_state = random.choice(eye_states)

        vision_events = []

        # Simulate gaze detection event
        vision_events.append({
             "modality": "vision_gaze",
             "event_type": config.EVENT_GENERIC_INFO, # Or a more specific event type.
             "input_data_summary": f"目光区域:{gaze}",
             "recognized_intent": f"GAZE_ON_{gaze.upper().replace(' ', '_')}",
             "system_action_taken": f"记录目光区域: {gaze}"
        })

        # Simulate head pose detection event
        vision_events.append({
             "modality": "vision_headpose",
             "event_type": config.EVENT_GENERIC_INFO,
             "input_data_summary": f"头部姿态:{head_pose_data}",
             "recognized_intent": head_pose_intent,
             "system_action_taken": f"记录头部姿态: {head_pose_data}"
        })
        
        # Simulate eye state detection event
        vision_events.append({
             "modality": "vision_eye_state",
             "event_type": config.EVENT_GENERIC_INFO,
             "input_data_summary": f"眼睛状态:{eye_state}",
             "recognized_intent": f"EYE_STATE_{eye_state.upper().replace(' ', '_')}",
             "system_action_taken": f"记录眼睛状态: {eye_state}"
        })


        # Simulate distraction event trigger (if gaze is not on road AND is driver)
        active_user_id = get_active_user_id()
        active_user_role = user_manager.get_user_role(active_user_id)

        if gaze not in ["道路", "仪表盘", "导航屏"] and active_user_role == "driver":
             # Randomly decide whether to trigger a distraction warning
             if random.random() < 0.6:
                       vision_events.append({
                          "modality": "vision_gaze",
                          "event_type": config.EVENT_USER_DISTRACTED,
                          "input_data_summary": f"视线偏离道路 ({gaze})",
                          "recognized_intent": config.EVENT_USER_DISTRACTED,
                          "event_data": {"gaze_off_duration": round(random.uniform(2, 10), 1), "current_speed": random.randint(20, 120)},
                          "system_action_taken": "外部模块检测到驾驶员分心"
                     })
        
        # Simulate closed eyes detection (if eyes are closed AND is driver)
        if eye_state == "闭眼" and active_user_role == "driver":
            # Randomly decide whether to trigger an eyes closed warning
            if random.random() < 0.7:
                eyes_closed_duration = round(random.uniform(1.5, 5.0), 1)
                vision_events.append({
                    "modality": "vision_eye_state",
                    "event_type": config.EVENT_EYES_CLOSED,
                    "input_data_summary": f"检测到闭眼 (持续时间: {eyes_closed_duration}秒)",
                    "recognized_intent": config.EVENT_EYES_CLOSED,
                    "event_data": {
                        "eyes_closed_duration": eyes_closed_duration,
                        "current_speed": random.randint(20, 120),
                        "confidence": round(random.uniform(0.85, 0.98), 2)
                    },
                    "system_action_taken": "外部模块检测到驾驶员闭眼超过警戒时间"
                })

        return vision_events


# Simulate input module instances
voice_simulator = VoiceInputSimulator()
gesture_simulator = GestureInputSimulator()
vision_simulator = VisionInputSimulator()


def simulate_user_interaction(user_id: str):
    """
    Simulates a multimodal interaction process for the specified user.
    Includes setting active user and handling potential failures.
    """
    # Attempt to set the current active user. If it fails, skip simulation for this user.
    if not set_active_user(user_id):
         print(f"跳过模拟用户 '{user_id}' 的交互，未能设置活动用户。")
         return # Skip interaction simulation if setting active user failed

    active_user_id = get_active_user_id() # Get the actually set user ID
    user_role = user_manager.get_user_role(active_user_id)
    print(f"\n--- 模拟用户 '{active_user_id}' 进行随机交互 ({user_role}) ---")

    # Randomly pick a modality to simulate input from
    simulators = [voice_simulator, gesture_simulator, vision_simulator]
    chosen_simulator = random.choice(simulators)

    # Handle vision simulator which can return multiple events
    if chosen_simulator == vision_simulator:
        vision_inputs = chosen_simulator.get_input()
        if vision_inputs:
             print(f"  模拟视觉输入:")
             for vision_event_data in vision_inputs:
                  # For visual events, we directly process and log them, no permission check involved
                  print(f"    -> 检测到: {vision_event_data['input_data_summary']} (事件类型: {vision_event_data['event_type']})")
                  
                  # 增强视觉事件数据，添加更多信息
                  event_data_enhanced = vision_event_data.get("event_data", {})
                  input_summary = vision_event_data['input_data_summary']
                  
                  # 提取目光区域或头部姿态信息
                  if "目光区域" in input_summary:
                      parts = input_summary.split(":")
                      if len(parts) > 1:
                          event_data_enhanced["gaze_area"] = parts[1].strip()
                  elif "头部姿态" in input_summary:
                      parts = input_summary.split(":")
                      if len(parts) > 1:
                          event_data_enhanced["head_pose"] = parts[1].strip()
                  
                  # 添加回事件数据
                  vision_event_data["event_data"] = event_data_enhanced
                  
                  process_event_and_trigger_feedback(
                     event_type=vision_event_data["event_type"],
                     event_data=vision_event_data.get("event_data", {}),
                     target_user_id=active_user_id,
                     input_modalities=vision_event_data["modality"],
                     input_data_summary=vision_event_data["input_data_summary"],
                     recognized_intent=vision_event_data["recognized_intent"],
                     system_action_taken=vision_event_data["system_action_taken"],
                     action_result="N/A",
                     additional_notes=f"由 {vision_event_data['modality']} 模态触发"
                 )
                  time.sleep(0.1) # Simulate small interval between visual events
        else:
             print("  模拟视觉输入: 未检测到特定事件。")
    else: # Handle voice and gesture simulators
         input_data = chosen_simulator.get_input()
         modality = input_data["modality"]
         intent = input_data["recognized_intent"]
         summary = input_data["input_data_summary"]

         # Determine action tag for permission check (simplified: use intent, with some overrides)
         action_tag = intent
         # Apply broader action tags for permission checks as defined in simulate_user_interaction
         if modality == "voice":
             if intent in ["GET_WEATHER", "TELL_JOKE", "SEND_MESSAGE"]:
                  action_tag = "EXECUTE_COMMAND"
             elif intent == "RESET_SYSTEM":
                  action_tag = "RESET_SYSTEM"
             elif intent == "VIEW_DIAGNOSTICS":
                  action_tag = "VIEW_DIAGNOSTICS"
             elif intent == "SET_VOLUME":
                  action_tag = "SET_VOLUME"
         elif modality == "gesture":
             if intent in ["ZOOM_OUT_MAP"]:
                  action_tag = "ZOOM_OUT_MAP"
             elif intent in ["PREVIOUS_SONG", "NEXT_SONG", "PAUSE_MUSIC"]:
                  action_tag = "CONTROL_MUSIC"
             # CONFIRM_ACTION and REJECT_ACTION permissions would be checked based on their specific tags

         print(f"  模拟 {modality} 输入: '{summary}' (意图: {intent}, 检查权限: {action_tag})")

         # Check permission and trigger event/feedback
         if is_action_permitted(action_tag, active_user_id):
             # Simulate successful command processing
             process_event_and_trigger_feedback(
                 event_type=config.EVENT_COMMAND_SUCCESS,
                 event_data={"command_name": summary, "recognized_intent": intent},
                 target_user_id=active_user_id,
                 input_modalities=modality,
                 input_data_summary=summary,
                 recognized_intent=intent,
                 system_action_taken=f"执行 {modality} 指令: {intent}",
                 action_result="success"
             )
         else:
              # Simulate insufficient permissions
              process_event_and_trigger_feedback(
                 event_type=config.EVENT_PERMISSION_DENIED,
                 event_data={"action_tag": action_tag, "attempted_command": summary, "recognized_intent": intent},
                 target_user_id=active_user_id,
                 input_modalities=modality,
                 input_data_summary=summary,
                 recognized_intent=intent,
                 system_action_taken=f"{modality} 指令 '{intent}' (权限 '{action_tag}') 被拒绝",
                 action_result="failure_permission_denied"
             )
    time.sleep(0.2) # Simulate processing delay after each interaction attempt


# --- NEW SIMULATION SCENARIOS ---

def simulate_distraction_warning_and_response(driver_user_id: str):
    """模拟驾驶员分心警告和响应过程"""
    print("\n=== 模拟驾驶员分心情景 ===")
    
    # 测试视觉反馈：分心检测开始
    try:
        from .feedback_orchestrator import visual_feedback_show_status
        visual_feedback_show_status("info", "开始分心检测模拟")
    except Exception as e:
        print(f"视觉反馈错误: {e}")
    
    # 设置活动用户为司机
    if set_active_user(driver_user_id):
        print(f"当前用户设置为司机: '{driver_user_id}'")
    else:
        print(f"错误：无法设置活动用户为 '{driver_user_id}'，将使用当前活动用户 '{_current_active_user_id}'")
        
    # Step 1: 模拟检测到驾驶员视线离开道路
    print("\n1. 模拟检测到驾驶员视线离开道路...")
    
    # 模拟检测到视线离开道路的数据
    detection_data = {
        "gaze_off_duration": "3.5秒",  # 视线离开道路的时间
        "gaze_direction": "右下方",    # 视线方向
        "head_position": "向右偏转15度", # 头部位置
        "eye_closure": "睁眼",         # 眼睛状态
        "confidence": 0.87             # 检测置信度
    }
    
    # 直接更新"注意力"状态指示灯
    try:
        visual_feedback_show_status("error", "注意力警告：视线离开道路")
    except Exception as e:
        print(f"视觉反馈错误: {e}")
    
    # 触发分心警告反馈
    feedback_result = process_event_and_trigger_feedback(
        event_type=config.EVENT_USER_DISTRACTED,
        event_data=detection_data,
        input_modalities="vision_gaze",
        input_data_summary=f"视线检测: 目光离开道路 {detection_data['gaze_off_duration']}，方向: {detection_data['gaze_direction']}",
        recognized_intent="DRIVER_DISTRACTION",
        system_action_taken="触发分心警告",
        action_result="success"
    )
    
    # 打印反馈结果 - 修复引用错误
    print(f"已触发分心警告反馈")
    if 'feedback_details' in feedback_result and 'summary_for_log' in feedback_result['feedback_details']:
        print(f"反馈详情: {feedback_result['feedback_details']['summary_for_log']}")
    
    # 模拟用户响应延迟
    print("\n2. 等待驾驶员响应...")
    time.sleep(2.5)  # 模拟2.5秒的响应时间
    
    # 视觉反馈：用户正在响应
    try:
        visual_feedback_show_status("warning", "等待驾驶员注意力恢复...")
    except Exception as e:
        print(f"视觉反馈错误: {e}")
    
    # Step 2: 模拟驾驶员将视线重新转回道路
    print("\n3. 模拟驾驶员视线重新转回道路...")
    
    recovery_data = {
        "gaze_area": "前方道路",
        "head_pose": "正向前方",
        "response_time": "2.5秒",
        "response_type": "主动纠正"
    }
    
    # 记录用户响应到分心警告
    feedback_result = process_event_and_trigger_feedback(
        event_type=config.EVENT_WARNING_CONFIRMED, # 用户确认了警告并采取行动
        event_data=recovery_data,
        input_modalities="vision_gaze",
        input_data_summary=f"视线检测: 目光区域: {recovery_data['gaze_area']}, 头部姿态: {recovery_data['head_pose']}",
        recognized_intent="DRIVER_ATTENTION_RESTORED",
        system_action_taken="记录警告响应",
        action_result="success",
        additional_notes=f"用户在警告后 {recovery_data['response_time']} 内恢复注意力"
    )
    
    # 打印反馈结果 - 修复引用错误
    print(f"已触发注意力恢复反馈")
    if 'feedback_details' in feedback_result and 'summary_for_log' in feedback_result['feedback_details']:
        print(f"反馈详情: {feedback_result['feedback_details']['summary_for_log']}")
    
    # 视觉反馈：注意力已恢复
    try:
        visual_feedback_show_status("success", "驾驶员注意力已恢复")
        time.sleep(1)
        visual_feedback_show_status("normal", "")
    except Exception as e:
        print(f"视觉反馈错误: {e}")
    
    print("\n=== 分心情景模拟完成 ===")

def simulate_eyes_closed_warning_and_response(driver_user_id: str):
    """模拟驾驶员闭眼超过警戒时间的警告和响应过程"""
    print("\n=== 模拟驾驶员闭眼警告情景 ===")
    
    # 测试视觉反馈：闭眼检测开始
    try:
        from .feedback_orchestrator import visual_feedback_show_status
        visual_feedback_show_status("info", "开始闭眼检测模拟")
    except Exception as e:
        print(f"视觉反馈错误: {e}")
    
    # 设置活动用户为司机
    if set_active_user(driver_user_id):
        print(f"当前用户设置为司机: '{driver_user_id}'")
    else:
        print(f"错误：无法设置活动用户为 '{driver_user_id}'，将使用当前活动用户 '{_current_active_user_id}'")
        
    # Step 1: 模拟检测到驾驶员闭眼超过警戒时间
    print("\n1. 模拟检测到驾驶员闭眼超过警戒时间...")
    
    # 模拟检测到闭眼的数据
    detection_data = {
        "eyes_closed_duration": "2.8秒",  # 闭眼持续时间
        "current_speed": 85,              # 当前车速
        "confidence": 0.92,               # 检测置信度
        "timestamp": time.time()          # 事件时间戳
    }
    
    # 更新视觉状态指示灯
    try:
        visual_feedback_show_status("error", "警告：检测到驾驶员闭眼")
    except Exception as e:
        print(f"视觉反馈错误: {e}")
    
    # 触发闭眼警告反馈
    feedback_result = process_event_and_trigger_feedback(
        event_type=config.EVENT_EYES_CLOSED,
        event_data=detection_data,
        input_modalities="vision_eye_state",
        input_data_summary=f"眼睛状态检测: 闭眼持续 {detection_data['eyes_closed_duration']}，车速: {detection_data['current_speed']}km/h",
        recognized_intent="DRIVER_EYES_CLOSED",
        system_action_taken="触发闭眼警告",
        action_result="success"
    )
    
    # 打印反馈结果
    print(f"已触发闭眼警告反馈")
    if 'feedback_details' in feedback_result and 'summary_for_log' in feedback_result['feedback_details']:
        print(f"反馈详情: {feedback_result['feedback_details']['summary_for_log']}")
    
    # 模拟用户响应延迟
    print("\n2. 等待驾驶员响应...")
    time.sleep(2.0)  # 模拟2秒的响应时间
    
    # 视觉反馈：用户正在响应
    try:
        visual_feedback_show_status("warning", "等待驾驶员睁眼...")
    except Exception as e:
        print(f"视觉反馈错误: {e}")
    
    # Step 2: 模拟驾驶员睁眼响应
    print("\n3. 模拟驾驶员睁眼响应...")
    
    recovery_data = {
        "eyes_state": "睁眼",
        "response_time": "2.0秒",
        "head_pose": "直视前方",
        "gaze_area": "前方道路"
    }
    
    # 记录用户响应到闭眼警告
    feedback_result = process_event_and_trigger_feedback(
        event_type=config.EVENT_WARNING_CONFIRMED,
        event_data=recovery_data,
        input_modalities="vision_eye_state",
        input_data_summary=f"眼睛状态检测: 状态: {recovery_data['eyes_state']}, 注视区域: {recovery_data['gaze_area']}",
        recognized_intent="DRIVER_EYES_OPENED",
        system_action_taken="记录警告响应",
        action_result="success",
        additional_notes=f"用户在警告后 {recovery_data['response_time']} 内睁眼"
    )
    
    # 打印反馈结果
    print(f"已触发睁眼响应反馈")
    if 'feedback_details' in feedback_result and 'summary_for_log' in feedback_result['feedback_details']:
        print(f"反馈详情: {feedback_result['feedback_details']['summary_for_log']}")
    
    # 视觉反馈：注意力已恢复
    try:
        visual_feedback_show_status("success", "驾驶员已睁眼，注意力恢复")
        time.sleep(1)
        visual_feedback_show_status("normal", "")
    except Exception as e:
        print(f"视觉反馈错误: {e}")
    
    print("\n=== 闭眼警告情景模拟完成 ===")


# --- System Main Entry Point ---
if __name__ == '__main__':
    print("--- 启动车载多模态智能交互系统原型 ---")

    # **ACTION 1: Clean data folder**
    # This must be the very first action in the main execution block to ensure a clean state
    data_folder = 'data'
    print(f"\n--- 清理旧数据 ({data_folder} 文件夹) ---")
    if os.path.exists(data_folder):
        try:
            # Use ignore_errors=True to attempt deletion even if some files are in use (less robust but avoids stopping)
            # Or handle OSError specifically if permissions or open files are expected issues
            shutil.rmtree(data_folder)
            print(f"成功删除旧数据文件夹: {data_folder}")
        except OSError as e:
            print(f"错误：无法删除旧数据文件夹 '{data_folder}': {e}. 请确保没有其他程序正在使用该文件夹中的文件。")
            # Depending on desired behavior, could exit here or try to continue
            # For a simulation, we'll print the error and attempt to continue,
            # but be aware that subsequent operations might fail if cleanup wasn't complete.
        except Exception as e:
            print(f"删除旧数据文件夹失败: {e}")
    else:
        print(f"数据文件夹不存在: {data_folder}，无需清理。")

    # **ACTION 2: Add all test users (including default guest if user_manager doesn't guarantee it)**
    # Ensure users are added BEFORE initializing system management and setting initial active user.
    # This will also likely trigger the creation of the 'data' folder and 'user_profiles.json' by user_manager.
    print("\n--- 添加测试用户 ---")
    try:
         # Ensure default guest user is added first (user_manager.add_user handles "already exists")
         add_new_user(config.DEFAULT_USER_ID, "访客", config.DEFAULT_ROLE)

         # Add the core test users with updated IDs (no leading zeros)
         add_new_user("driver_1", "刘沛鑫", "driver")
         add_new_user("passenger_1", "高艺轩", "passenger")
         # Add maintenance and admin users with updated IDs
         add_new_user("maintenance_1", "延嵩", "vehicle_maintenance")
         add_new_user("admin_1", "张瑜", "system_administrator")

         # Add the new users requested
         add_new_user("driver_2", "房书睿", "driver")
         add_new_user("passenger_2", "刘阳", "passenger")
         add_new_user("passenger_3", "冯子函", "passenger")
         add_new_user("maintenance_2", "崔交军", "vehicle_maintenance")

    except Exception as e:
         print(f"错误：添加测试用户过程中发生异常: {e}")


    # **ACTION 3: Initialize system management**
    # Now that users are added and saved (user_manager should save), initializing with "driver_1" should succeed.
    print("\n--- 初始化系统管理模块 ---")
    # initialize_system_management relies on users existing in user_manager's files/state
    initialize_system_management(initial_active_user_id="driver_1")


    # **ACTION 4: Initialize/Check Log File**
    # The data folder was just deleted and potentially re-created by user_manager.
    # Explicitly ensure the log file is created/initialized with headers *after* the folder exists.
    print("\n--- 检查并初始化日志文件 ---")
    try:
         interaction_logger.initialize_log() # This should create the log file and write headers if it doesn't exist
         print(f"日志文件已准备就绪: {config.INTERACTION_LOG_PATH}")
    except Exception as e:
         print(f"错误：初始化日志文件失败: {e}")


    # 5. (Optional) Run initial log analysis (based on old data)
    # This would simulate system startup analysis. Since we cleared data, there is no old log.
    # print("\n--- Initial Log Analysis (based on old data) ---")
    # run_log_analysis_and_update_personalization() # First run will likely report no data

    # **ACTION 6: Simulate multiple rounds of user interaction to generate log data**
    print("\n--- 开始模拟多轮用户随机交互以生成日志数据 ---")

    # List of users to simulate interaction for, including all roles and default guest
    # Ensure this list contains the IDs of users you expect to be in the system
    simulation_users = [config.DEFAULT_USER_ID, "driver_1", "passenger_1", "maintenance_1", "admin_1",
                        "driver_2", "passenger_2", "passenger_3", "maintenance_2"]
    # 为不同角色的用户设置权重，让admin和driver用户更可能被选中
    user_weights = {
        "admin_1": 3,      # 管理员权重高，拥有所有权限
        "driver_1": 2.5,   # 驾驶员权重较高
        "driver_2": 2.5,   # 驾驶员权重较高
        "passenger_1": 1,  # 普通乘客权重正常
        "passenger_2": 1,  
        "passenger_3": 1,
        "maintenance_1": 1.5, # 维护人员权重稍高
        "maintenance_2": 1.5,
        config.DEFAULT_USER_ID: 0.5 # 访客权限低，降低选择概率
    }
    
    weighted_users = []
    for user_id, weight in user_weights.items():
        # 为每个用户添加对应权重个实例到列表中
        weighted_users.extend([user_id] * int(weight * 10))
        
    num_interactions = 30 # Increase interaction count to cover more users and scenarios

    # Workaround: Explicitly load profiles again right before simulation loop
    # This helps ensure set_active_user has the latest user list if user_manager had caching issues
    # The real fix is in user_manager's save/load logic.
    print("--- 模拟前加载用户配置 ---")
    user_manager._load_all_profiles()


    for i in range(num_interactions):
        # 从带权重的用户列表中随机选择
        user_id_to_simulate = random.choice(weighted_users)
        simulate_user_interaction(user_id_to_simulate)
        time.sleep(0.3) # Simulate time interval


    print("\n--- 随机模拟交互结束 ---")

    # **ACTION 7: Simulate specific warning and response scenarios**
    print("\n--- 开始模拟特定警告与响应场景测试 ---")
    # Workaround: Explicitly load profiles again right before specific scenario tests
    print("--- 特定场景模拟前加载用户配置 (尝试解决用户未找到问题) ---")
    user_manager._load_all_profiles()

    # 模拟分心警告场景
    # Simulate for driver_1
    simulate_distraction_warning_and_response("driver_1")
    time.sleep(1) # Pause between scenarios
    # Simulate for driver_2
    simulate_distraction_warning_and_response("driver_2")
    time.sleep(1)
    
    # 模拟闭眼警告场景
    # Simulate for driver_1
    simulate_eyes_closed_warning_and_response("driver_1")
    time.sleep(1) # Pause between scenarios
    # Simulate for driver_2
    simulate_eyes_closed_warning_and_response("driver_2")
    time.sleep(1)

    print("\n--- 特定场景模拟结束 ---")


    # **ACTION 8: Simulate user deletion tests**
    print("\n--- 开始模拟用户删除测试 ---")
    # Workaround: Explicitly load profiles again right before deletion tests
    print("--- 用户删除测试前加载用户配置 (尝试解决用户未找到问题) ---")
    user_manager._load_all_profiles()

    # Attempt to delete the current active user (should fail)
    current_active = get_active_user_id()
    print(f"\n试图删除当前活动用户 ('{current_active}'):")
    success, message = delete_existing_user(current_active)
    print(f"删除结果: {message}") # Print the message returned by the wrapper
    time.sleep(0.1)

    # Attempt to delete the default guest user (should fail via this function)
    print(f"\n试图删除默认访客用户 ('{config.DEFAULT_USER_ID}'):")
    success, message = delete_existing_user(config.DEFAULT_USER_ID)
    print(f"删除结果: {message}")
    time.sleep(0.1)

    # Attempt to delete a non-existent user (should fail with ValueError)
    print("\n试图删除不存在的用户 ('non_existent_user'):")
    success, message = delete_existing_user("non_existent_user")
    print(f"删除结果: {message}")
    time.sleep(0.1)

    # Attempt to delete a user that exists and is not active or default (should succeed)
    # Let's delete passenger_3
    print("\n试图删除用户 'passenger_3':")
    success, message = delete_existing_user("passenger_3")
    print(f"删除结果: {message}")
    time.sleep(0.1)

    # Verify passenger_3 is no longer in the user list
    # Workaround: Explicitly load profiles again after deletion attempt to verify
    profiles_after_deletion = user_manager._load_all_profiles()
    if "passenger_3" not in profiles_after_deletion:
         print("验证: 用户 'passenger_3' 不再存在于用户列表中。")
    else:
         print("验证: 错误，用户 'passenger_3' 仍然存在于用户列表中。") # This would indicate a bug in user_manager.delete_user

    print("\n--- 用户删除测试结束 ---")


    # **ACTION 9: After simulation ends, run log analysis and update user personalization configurations**
    print("\n--- 运行日志分析并更新用户配置 ---")
    # Add a print here to indicate analysis start before the call
    print("--- 开始加载并分析交互日志 ---") # Keep this print as the *only* start indicator
    run_log_analysis_and_update_personalization()

    # 10. View updated user configurations (especially personalization data)
    print("\n--- 系统运行结束 ---")
    print("请检查生成的日志文件和分析报告：")
    print(f"- 日志文件: {config.INTERACTION_LOG_PATH}")
    print(f"- 分析报告: {config.ANALYSIS_REPORT_PATH}")

    print("\n--- 更新后的用户配置摘要 ---")
    # Ensure we iterate through user IDs that were actually intended to be in the system.
    # Get the latest profiles after analysis has potentially updated them, AND after deletion test.
    # Workaround: Explicitly load profiles one last time for accurate summary
    profiles_final = user_manager._load_all_profiles()

    # Use the keys from the final loaded profiles for summary
    users_to_summarize = list(profiles_final.keys())
    # Add default guest explicitly if somehow not in keys (shouldn't happen if added)
    if config.DEFAULT_USER_ID not in users_to_summarize:
         users_to_summarize.append(config.DEFAULT_USER_ID)


    for user_id in users_to_summarize:
         # Use get_user_profile which will load/get profile, potentially returning default if user is deleted or analysis didn't save one
         profile = get_user_profile(user_id) # get_user_profile will load the profile, or return default if not found

         # Check if the profile returned is actually for the user_id, or if it's the default profile
         # returned because the user_id wasn't found (e.g., passenger_3 after deletion).
         # A simple check is if the user_id is still a key in the *final* profiles list.
         if user_id not in profiles_final:
              print(f"\n用户ID: {user_id} (已删除或不存在)")
              print("-" * 20)
              continue # Skip printing details for deleted users

         # For existing users, print summary
         print(f"\n用户ID: {user_id} (角色: {profile.get('role', 'N/A')})")
         print(f"  常用指令: {profile.get('common_commands', {})}")
         # Print warning response habit from the profile
         warning_habit = profile.get('interaction_habits', {}).get('warning_response_habit', {'确认': 0, '拒绝': 0, '无响应/其他': 0})
         print(f"  警告响应习惯: {warning_habit}")
         # print(f"  Feedback Preferences: {profile.get('feedback_preferences', {})}") # Preferences might be detailed, print summary only
         print("-" * 20)

    # Optional: Print full configuration for a specific user (e.g., admin_1)
    # print("\nFull User Configuration (Admin 1):")
    # admin_profile = get_user_profile("admin_1")
    # print(json.dumps(admin_profile, indent=4, ensure_ascii=False))

    # --- 清理资源函数 ---
    def cleanup_resources():
        """清理系统资源，如语音引擎等"""
        try:
            # 尝试关闭语音引擎
            from .feedback_orchestrator import _tts_engine
            if _tts_engine is not None:
                try:
                    _tts_engine.stop()
                    print("语音引擎资源已释放。")
                except Exception as e:
                    print(f"警告：停止语音引擎时出错 - {e}")
        except Exception as e:
            print(f"警告：清理语音引擎资源时出错 - {e}")
        
        # 等待所有语音线程结束
        time.sleep(0.5)  # 给予语音线程足够的时间结束

    try:
        # ...模拟代码和测试代码...
        pass
    finally:
        # 确保在程序结束时清理资源
        cleanup_resources()

# 添加一个测试视觉反馈的函数
def test_visual_feedback():
    """测试视觉反馈功能"""
    
    # 导入视觉反馈函数
    from .feedback_orchestrator import visual_feedback_show_status, wait_for_feedback_completion
    
    print("开始测试视觉反馈...")
    
    # 测试正常状态
    print("测试正常状态...")
    visual_feedback_show_status("normal", "系统处于正常状态")
    wait_for_feedback_completion()  # 等待反馈完成
    time.sleep(2)
    
    # 测试信息状态
    print("测试信息状态...")
    visual_feedback_show_status("info", "这是一条系统信息\n可能包含多行内容")
    wait_for_feedback_completion()  # 等待反馈完成
    time.sleep(2)
    
    # 测试成功状态
    print("测试成功状态...")
    visual_feedback_show_status("success", "操作已成功完成\n任务顺利执行")
    wait_for_feedback_completion()  # 等待反馈完成
    time.sleep(2)
    
    # 测试警告状态
    print("测试警告状态...")
    visual_feedback_show_status("warning", "系统检测到潜在风险\n请注意安全")
    wait_for_feedback_completion()  # 等待反馈完成
    time.sleep(3)
    
    # 测试错误状态
    print("测试错误状态...")
    visual_feedback_show_status("error", "发现严重错误，请立即处理！\n需要立即采取行动")
    wait_for_feedback_completion()  # 等待反馈完成
    time.sleep(3)
    
    # 恢复正常状态
    print("恢复正常状态...")
    visual_feedback_show_status("normal", "测试完成，系统恢复正常")
    wait_for_feedback_completion()  # 等待反馈完成
    
    print("视觉反馈测试完成")


# Run for script mode only, skipped when imported as module
if __name__ == "__main__":
    # Move back to the project root to ensure correct data file paths
    # (Only needed if not running with -m from project root)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # project_root = os.path.dirname(current_dir) # Redundant - we already set PROJECT_ROOT in config
    
    # Ensure data directory exists
    os.makedirs(config.DATA_DIR, exist_ok=True)
    
    # Force clean start if needed (for testing or development)
    def cleanup_resources():
        """Only for development and testing: Reset user profiles and log files"""
        try:
            if os.path.exists(config.USER_PROFILES_PATH):
                print(f"删除用户配置文件: {config.USER_PROFILES_PATH}")
                os.remove(config.USER_PROFILES_PATH)
            
            if os.path.exists(config.INTERACTION_LOG_PATH):
                print(f"删除交互日志文件: {config.INTERACTION_LOG_PATH}")
                os.remove(config.INTERACTION_LOG_PATH)
                
            # 如果分析报告文件存在，也删除它
            if os.path.exists(config.ANALYSIS_REPORT_PATH):
                print(f"删除分析报告文件: {config.ANALYSIS_REPORT_PATH}")
                os.remove(config.ANALYSIS_REPORT_PATH)
                
            print("已清理所有资源文件，系统将以干净状态启动")
        except Exception as e:
            print(f"清理资源文件时出错: {e}")
    
    CLEAN_START = False
    if CLEAN_START:
        cleanup_resources()
    
    print("\n=== 系统管理模块测试启动 ===")
    
    # Ensure we have the default guest user
    if not os.path.exists(config.USER_PROFILES_PATH):
        print("用户配置文件不存在，创建默认用户...")
        # Will add the default guest user with default role
        result, msg = add_new_user(
            config.DEFAULT_USER_ID, 
            "默认访客", 
            config.DEFAULT_ROLE
        )
        if result:
            print(f"已创建默认用户: {msg}")
        else:
            print(f"创建默认用户失败: {msg}")
            # Continue anyway - the user manager will create a default profile
    
    # Add test users for different roles
    test_users = [
        {"id": "driver1", "name": "测试司机", "role": "driver", "preferences": None},
        {"id": "passenger1", "name": "测试乘客", "role": "passenger", "preferences": None},
        {"id": "admin1", "name": "测试管理员", "role": "admin", "preferences": None},
    ]
    
    for user in test_users:
        result, msg = add_new_user(user["id"], user["name"], user["role"], user["preferences"])
        if result:
            print(f"添加测试用户: {msg}")
    
    # Initialize the system management module
    initialize_system_management("driver1")  # Use the first driver as initial active user
    
    # 运行视觉反馈测试
    print("\n=== 测试视觉反馈功能 ===")
    try:
        test_visual_feedback()
    except Exception as e:
        print(f"视觉反馈测试失败: {e}")
    
    # Run through some test scenarios
    # 1. Test driver distraction warning first
    simulate_distraction_warning_and_response("driver1")
    
    # 2. Test driver eyes closed warning
    simulate_eyes_closed_warning_and_response("driver1")
    
    # 3. Test regular voice interactions
    simulate_user_interaction("driver1")
    simulate_user_interaction("passenger1")
    # Additional simulations for various users and scenarios
    
    # 4. Run an analysis based on collected logs
    print("\n=== 运行交互日志分析 ===")
    try:
        run_log_analysis_and_update_personalization()
    except Exception as e:
        print(f"日志分析失败: {e}")
    
    print("\n=== 系统管理模块测试完成 ===")
    
    # 5秒后关闭视觉反馈窗口
    print("系统将在5秒后关闭...")
    time.sleep(5)
    
    # 隐藏视觉反馈窗口
    try:
        from .feedback_orchestrator import VisualFeedbackManager
        feedback_manager = VisualFeedbackManager.get_instance()
        feedback_manager.hide()
    except Exception:
        pass
