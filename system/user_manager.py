# user_manager.py

import json
import os
from .config import USER_PROFILES_PATH, DEFAULT_USER_ID, DEFAULT_ROLE
from .config import EVENT_USER_DISTRACTED, EVENT_COMMAND_SUCCESS, EVENT_COMMAND_FAILURE, EVENT_PERMISSION_DENIED, EVENT_GENERIC_INFO # 导入事件类型

# 角色及其权限定义 (可以考虑将其移至单独的 permissions_config.json 文件)
# 权限标签 (action_tag) 建议使用英文，方便代码内部处理
ROLES_PERMISSIONS = {
    "driver": [
        "CONTROL_AC", "PLAY_MUSIC", "PAUSE_MUSIC", "STOP_MUSIC", "PREVIOUS_SONG", "NEXT_SONG", 
        "CONFIRM_ACTION", "REJECT_ACTION", "CONTROL_MUSIC", "SET_VOLUME", "SET_VOLUME_HIGH",
        "START_NAVIGATION", "NAVIGATE", "ANSWER_CALL", "VIEW_CRITICAL_ALERTS", "EXECUTE_COMMAND",
        "GET_WEATHER", "TELL_JOKE", "SEND_MESSAGE", "VIEW_DIAGNOSTICS", "RESET_SYSTEM"
        # ... 驾驶员可以执行的所有动作标签
    ],
    "passenger": [
        "PLAY_MUSIC", "PAUSE_MUSIC", "STOP_MUSIC", "PREVIOUS_SONG", "NEXT_SONG", 
        "CONTROL_MUSIC", "SET_VOLUME", "SET_VOLUME_MEDIUM", "CONFIRM_ACTION", "REJECT_ACTION",
        "REQUEST_NAVIGATION_DESTINATION", "EXECUTE_PASSENGER_COMMAND", "GET_WEATHER", "TELL_JOKE",
        "SEND_MESSAGE", "ZOOM_OUT_MAP"
        # 注意：根据实际指令设计，可能需要更细粒度的权限标签
    ],
    "vehicle_maintenance": [ # 车辆维护人员
        "VIEW_SYSTEM_DIAGNOSTICS", "RESET_SYSTEM_SETTINGS", "RESET_SYSTEM", "VIEW_DIAGNOSTICS", 
        "RUN_TESTS", "CONTROL_AC", "SET_VOLUME", "PLAY_MUSIC", "PAUSE_MUSIC", "CONFIRM_ACTION", "REJECT_ACTION"
    ],
    "system_administrator": ["ALL_PERMISSIONS"], # 系统管理员拥有所有权限
    DEFAULT_ROLE: [ # 访客角色权限
        "PLAY_GUEST_PLAYLIST", "PLAY_MUSIC", "PAUSE_MUSIC", "CONFIRM_ACTION", "REJECT_ACTION",
        "GET_WEATHER", "TELL_JOKE", "SET_VOLUME", "PREVIOUS_SONG", "NEXT_SONG", "CONTROL_MUSIC"
    ]
}

def _ensure_data_dir_exists():
    """确保 data 目录存在"""
    data_dir = os.path.dirname(USER_PROFILES_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

def _load_all_profiles() -> dict:
    """辅助函数：从JSON文件加载所有用户配置。"""
    _ensure_data_dir_exists()
    if not os.path.exists(USER_PROFILES_PATH) or os.stat(USER_PROFILES_PATH).st_size == 0:
        # 如果文件不存在或为空, 创建一个包含默认访客的配置
        default_profiles = {
            DEFAULT_USER_ID: {
                "name": "访客",
                "role": DEFAULT_ROLE,
                "common_commands": {}, # 用于存储常用指令分析结果
                "interaction_habits": {}, # 用于存储交互习惯分析结果
                "feedback_preferences": { # 默认的反馈偏好
                    EVENT_USER_DISTRACTED: {
                        "enabled_modalities": ["voice", "text_display", "visual_dashboard_light", "visual_graphic_feedback"], 
                        "voice_detail_level": "normal"
                    },
                    EVENT_COMMAND_SUCCESS: {
                        "enabled_modalities": ["voice_brief", "visual_graphic_feedback"], 
                        "text_display_enabled": False
                    },
                    EVENT_COMMAND_FAILURE: {
                        "enabled_modalities": ["voice", "text_display", "visual_graphic_feedback", "visual_dashboard_light"], 
                        "voice_detail_level": "normal"
                    },
                    EVENT_PERMISSION_DENIED: {
                        "enabled_modalities": ["voice", "text_display", "visual_graphic_feedback", "visual_dashboard_light"], 
                        "voice_detail_level": "brief"
                    },
                    EVENT_GENERIC_INFO: {
                        "enabled_modalities": ["text_display", "visual_graphic_feedback"], 
                        "voice_detail_level": "normal"
                    },
                    "general_voice_volume": 70, # 整体语音音量
                    "disable_all_audio_feedback": False, # 是否完全禁用音频反馈
                    "visual_graphic_feedback_enabled": True, # 是否启用图形视觉反馈
                    "visual_animation_enabled": True # 是否启用动画效果
                }
            }
        }
        _save_all_profiles(default_profiles)
        print(f"创建默认用户配置文件: {USER_PROFILES_PATH}")
        return default_profiles
    try:
        with open(USER_PROFILES_PATH, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
            # 确保默认用户始终存在，如果不存在则添加
            if DEFAULT_USER_ID not in profiles:
                 profiles[DEFAULT_USER_ID] = {
                    "name": "访客", 
                    "role": DEFAULT_ROLE, 
                    "common_commands": {},
                    "interaction_habits": {}, 
                    "feedback_preferences": {
                        EVENT_USER_DISTRACTED: {
                            "enabled_modalities": ["voice", "text_display", "visual_dashboard_light", "visual_graphic_feedback"], 
                            "voice_detail_level": "normal"
                        },
                        EVENT_COMMAND_SUCCESS: {
                            "enabled_modalities": ["voice_brief", "visual_graphic_feedback"], 
                            "text_display_enabled": False
                        },
                        EVENT_COMMAND_FAILURE: {
                            "enabled_modalities": ["voice", "text_display", "visual_graphic_feedback", "visual_dashboard_light"], 
                            "voice_detail_level": "normal"
                        },
                        EVENT_PERMISSION_DENIED: {
                            "enabled_modalities": ["voice", "text_display", "visual_graphic_feedback", "visual_dashboard_light"], 
                            "voice_detail_level": "brief"
                        },
                        EVENT_GENERIC_INFO: {
                            "enabled_modalities": ["text_display", "visual_graphic_feedback"], 
                            "voice_detail_level": "normal"
                        },
                        "general_voice_volume": 70, # 整体语音音量
                        "disable_all_audio_feedback": False, # 是否完全禁用音频反馈
                        "visual_graphic_feedback_enabled": True, # 是否启用图形视觉反馈
                        "visual_animation_enabled": True # 是否启用动画效果
                    }
                }
                 _save_all_profiles(profiles) # 添加默认用户后保存
            return profiles
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"加载用户配置文件失败 ({e})，将返回一个包含默认访客的配置。")
        # 如果文件损坏或找不到，也返回一个包含默认访客的配置
        return {DEFAULT_USER_ID: {"name": "访客", "role": DEFAULT_ROLE, "common_commands": {}, "interaction_habits": {}, "feedback_preferences": {}}}


def _save_all_profiles(profiles: dict):
    """辅助函数：将所有用户配置保存到JSON文件。"""
    _ensure_data_dir_exists()
    with open(USER_PROFILES_PATH, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, ensure_ascii=False, indent=4)
    # print(f"用户数据已保存到: {USER_PROFILES_PATH}") # 通常生产环境不会打印每次保存

def load_user_profile(user_id: str) -> dict:
    """加载指定用户的配置。如果用户不存在，则返回默认访客的配置。"""
    profiles = _load_all_profiles()
    # 使用 get，如果user_id不存在，再尝试获取默认访客。确保始终返回一个字典。
    return profiles.get(user_id, profiles.get(DEFAULT_USER_ID, {}))

def save_user_profile(user_id: str, profile_data: dict):
    """保存或更新指定用户的配置。"""
    profiles = _load_all_profiles()
    # 这里简单替换，如果需要合并现有数据，需要更复杂的逻辑
    profiles[user_id] = profile_data
    _save_all_profiles(profiles)
    print(f"用户 '{user_id}' 的配置已更新。")

def add_user(user_id: str, name: str, role: str, initial_preferences: dict = None):
    """添加一个新用户。"""
    if role not in ROLES_PERMISSIONS:
        raise ValueError(f"错误：角色 '{role}' 未在系统中定义。")
    profiles = _load_all_profiles()
    if user_id in profiles:
        raise ValueError(f"错误：用户ID '{user_id}' 已存在。")

    # 为新用户设置默认的个性化字段和反馈偏好，允许通过 initial_preferences 覆盖
    default_profile_data = {
        "name": name,
        "role": role,
        "common_commands": {},
        "interaction_habits": {},
        "feedback_preferences": { # 默认的反馈偏好，可以从 DEFAULT_USER_ID 拷贝或硬编码
             EVENT_USER_DISTRACTED: {
                 "enabled_modalities": ["voice", "text_display", "visual_dashboard_light", "visual_graphic_feedback"],
                 "voice_detail_level": "normal"
             },
             EVENT_COMMAND_SUCCESS: {
                 "enabled_modalities": ["voice_brief", "visual_graphic_feedback"],
                 "text_display_enabled": False
             },
             EVENT_COMMAND_FAILURE: {
                 "enabled_modalities": ["voice", "text_display", "visual_graphic_feedback", "visual_dashboard_light"],
                 "voice_detail_level": "normal"
             },
             EVENT_PERMISSION_DENIED: {
                 "enabled_modalities": ["voice", "text_display", "visual_graphic_feedback", "visual_dashboard_light"],
                 "voice_detail_level": "brief"
             },
             EVENT_GENERIC_INFO: {
                 "enabled_modalities": ["text_display", "visual_graphic_feedback"],
                 "voice_detail_level": "normal"
             },
             "general_voice_volume": 70,
             "disable_all_audio_feedback": False,
             "visual_graphic_feedback_enabled": True,
             "visual_animation_enabled": True
        }
    }
    # 合并初始偏好
    if initial_preferences:
         # 简单的 update，如果 initial_preferences 结构复杂需要递归合并
        default_profile_data.update(initial_preferences)


    profiles[user_id] = default_profile_data
    _save_all_profiles(profiles)
    print(f"用户 '{user_id}' ({name}) 已添加，角色为 '{role}'。")

def delete_user(user_id: str):
    """删除一个用户。"""
    profiles = _load_all_profiles()
    if user_id == DEFAULT_USER_ID:
        print(f"警告：不能删除默认访客用户 '{DEFAULT_USER_ID}'。")
        return
    if user_id in profiles:
        del profiles[user_id]
        _save_all_profiles(profiles)
        print(f"用户 '{user_id}' 已被删除。")
    else:
        print(f"警告：用户 '{user_id}' 未找到，无法删除。")

def change_user_role(user_id: str, new_role: str):
    """修改用户的角色。"""
    if new_role not in ROLES_PERMISSIONS:
        raise ValueError(f"错误：新角色 '{new_role}' 未在系统中定义。")
    profiles = _load_all_profiles()
    if user_id not in profiles:
        raise ValueError(f"错误：用户ID '{user_id}' 未找到。")

    profiles[user_id]["role"] = new_role
    _save_all_profiles(profiles)
    print(f"用户 '{user_id}' 的角色已更改为 '{new_role}'。")

def get_user_role(user_id: str) -> str:
    """获取用户的角色。"""
    profile = load_user_profile(user_id)
    return profile.get("role", DEFAULT_ROLE) # 如果role字段缺失，返回默认角色

def check_permission(user_id: str, action_tag: str) -> bool:
    """检查用户是否有权限执行某个动作 (action_tag)。"""
    role = get_user_role(user_id)
    permissions = ROLES_PERMISSIONS.get(role, [])
    if "ALL_PERMISSIONS" in permissions:
        return True
    return action_tag in permissions

def get_feedback_preferences(user_id: str, event_type: str) -> dict:
    """获取用户针对特定事件类型的反馈偏好。"""
    profile = load_user_profile(user_id)
    feedback_prefs_all = profile.get("feedback_preferences", {})

    # 获取特定事件的偏好，如果不存在，则使用通用信息事件的偏好作为部分默认
    specific_event_prefs = feedback_prefs_all.get(event_type, {})
    # 通用事件的偏好用于填充特定事件偏好中缺失的部分
    generic_event_prefs = feedback_prefs_all.get(EVENT_GENERIC_INFO, {})

    # 合并偏好：特定事件的偏好优先，然后是通用事件的，最后是硬编码的兜底默认值
    final_prefs = {
        "enabled_modalities": specific_event_prefs.get("enabled_modalities", generic_event_prefs.get("enabled_modalities", ["text_display"])),
        "voice_detail_level": specific_event_prefs.get("voice_detail_level", generic_event_prefs.get("voice_detail_level", "normal")),
        "text_display_enabled": specific_event_prefs.get("text_display_enabled", generic_event_prefs.get("text_display_enabled", True)),
        # 获取通用设置
        "general_voice_volume": feedback_prefs_all.get("general_voice_volume", 70),
        "disable_all_audio_feedback": feedback_prefs_all.get("disable_all_audio_feedback", False)
        # 可以添加其他反馈相关的通用或特定偏好字段
    }
    return final_prefs

# --- 新增方法：更新用户个性化数据（从分析结果而来）---
def update_user_personalization_from_analysis(user_id: str, analysis_data: dict):
    """
    根据日志分析结果更新用户的个性化数据（常用指令、交互习惯等）。
    analysis_data 应该是一个字典，包含要更新的字段，例如：
    {
        "common_commands": {"打开空调": 15, "播放音乐": 10},
        "interaction_habits": {"warning_response_habit": {"确认": 8, "拒绝": 2}},
        "preferred_modality": "voice" # 偏好模态也可以作为一种习惯
    }
    """
    profiles = _load_all_profiles()
    if user_id not in profiles:
        print(f"警告：用户 '{user_id}' 不存在，无法更新个性化数据。")
        return

    user_profile = profiles[user_id]

    # 更新常用指令 (这里假设直接替换，如果需要合并或增量更新，逻辑会更复杂)
    if "common_commands" in analysis_data:
        user_profile["common_commands"] = analysis_data["common_commands"]

    # 更新交互习惯 (这里假设直接替换相应的子字段)
    if "interaction_habits" in analysis_data:
         # 确保 interaction_habits 字段存在
        if "interaction_habits" not in user_profile:
            user_profile["interaction_habits"] = {}
        # 合并或替换具体的习惯数据
        user_profile["interaction_habits"].update(analysis_data["interaction_habits"])

    # 更新偏好模态 (如果作为独立字段存储的话)
    if "preferred_modality" in analysis_data:
         # 确保 interaction_habits 字段存在 (或者在 profile 根目录)
        if "interaction_habits" not in user_profile:
            user_profile["interaction_habits"] = {} # 或者直接 user_profile['preferred_modality'] = ...
        user_profile["interaction_habits"]["preferred_modality"] = analysis_data["preferred_modality"]


    _save_all_profiles(profiles)
    print(f"用户 '{user_id}' 的个性化数据已更新（从分析结果）。")

def get_default_feedback_preferences() -> dict:
    """获取默认反馈偏好设置"""
    return {
        "enabled_modalities": [
            "voice",               # 语音反馈
            "text_display",        # 文本显示反馈
            "visual_dashboard_light", # 视觉指示灯反馈
            "visual_graphic_feedback" # 新增：图形视觉反馈 (图标、颜色变化、动画)
        ],
        # 语音反馈相关设置
        "voice_detail_level": "normal",  # 可选值: "brief", "normal", "detailed", "urgent"
        "general_voice_volume": 70,      # 0-100 音量
        "disable_all_audio_feedback": False,  # 是否完全禁用所有声音反馈
        
        # 文本显示反馈相关设置
        "text_display_enabled": True,    # 是否启用文本显示
        "text_display_duration": 3000,   # 文本显示持续时间 (毫秒)
        
        # 视觉反馈相关设置
        "visual_alert_intensity": "medium",  # 可选值: "low", "medium", "high"
        
        # 图形视觉反馈设置
        "visual_graphic_feedback_enabled": True, # 是否启用图形视觉反馈
        "visual_animation_enabled": True,        # 是否启用动画效果
        
        # 事件特定的设置可以添加在这里
        "event_specific": {
            # 驾驶员分心事件特殊处理
            "USER_DISTRACTED": {
                "voice_detail_level": "urgent",        # 使用更紧急的语音
                "general_voice_volume": 90,            # 更高音量
                "visual_alert_intensity": "high",      # 更高强度的视觉警报
                "text_display_duration": 5000,         # 更长的文本显示时间
            }
        }
    }

# 模块加载时，确保配置文件存在并包含默认用户
_load_all_profiles()

# 示例：模块初始化和一些基本操作（通常由主程序调用） - 移到 main.py 或独立的测试文件中
# if __name__ == '__main__':
#    ... (原有的测试代码) ...
