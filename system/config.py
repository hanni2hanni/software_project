# config.py

import os

# system_management 模块的根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# data 目录的路径 (在 system_management 上一级，然后进入 data)
# 假设 system_management 模块在一个名为 system_management 的子目录里
# 如果你的项目结构不同，需要调整这个路径
PROJECT_ROOT = os.path.dirname(BASE_DIR) # 项目根目录
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


# 数据文件路径
USER_PROFILES_PATH = os.path.join(DATA_DIR, "user_profiles.json")
INTERACTION_LOG_PATH = os.path.join(DATA_DIR, "interaction_log.csv")

# 默认用户和角色
DEFAULT_USER_ID = "guest_user" # 访客用户ID
DEFAULT_ROLE = "passenger"     # 访客用户的默认角色

# 事件类型常量 (用于反馈编排和日志记录)
EVENT_USER_DISTRACTED = "USER_DISTRACTED"
EVENT_COMMAND_SUCCESS = "COMMAND_SUCCESS"
EVENT_COMMAND_FAILURE = "COMMAND_FAILURE"
EVENT_PERMISSION_DENIED = "PERMISSION_DENIED"
EVENT_GENERIC_INFO = "GENERIC_INFO" # 通用信息事件，例如视觉检测到的状态
EVENT_EYES_CLOSED = "EYES_CLOSED"   # 新增：检测到用户闭眼超过一定时间的事件类型


# 添加警告相关的事件类型常量
EVENT_WARNING_CONFIRMED = "WARNING_CONFIRMED"
EVENT_WARNING_REJECTED = "WARNING_REJECTED"
EVENT_WARNING_UNRESPONSIVE = "WARNING_UNRESPONSIVE" # 新增：用户对警告无响应的事件类型
# 如果还有其他警告相关的事件，例如超时未响应，也可以在这里定义
# EVENT_WARNING_TIMEOUT = "WARNING_TIMEOUT" # 这个可能和 UNRESPONSIVE 是同一个概念，根据你的实际逻辑来决定


# 定义交互日志的列名，用于CSV文件的表头和解析
# CSV 日志文件的表头 - 请确保与 interaction_logger.py 中的写入顺序一致
LOG_COLUMNS = [
    "timestamp",
    "user_id",
    "user_role",
    # "session_id", # 如果有session_id，可以添加
    "event_type",
    "event_details", # 存储事件的具体信息，例如警告类型、系统提示内容等
    "input_modalities",
    "input_data_summary",
    "recognized_intent",
    "system_action_taken",
    "action_result",
    "feedback_modalities_triggered",
    "feedback_content_summary",
    # "system_state", # 如果有系统状态信息，可以添加
    # "environment_data", # 如果有环境数据，可以添加
    "notes",
    # >>> 添加 event_data 列 <<<
    "event_data"
]


# 日志分析报告输出路径 (可选，可以放在 logs 子目录下)
ANALYSIS_REPORT_PATH = os.path.join(DATA_DIR, "reports", "analysis_report.txt")

# 确保 data 和 reports 目录存在 (虽然 interaction_logger 和 analyzer 也会检查，但在这里提前确保)
# os.makedirs(os.path.dirname(USER_PROFILES_PATH), exist_ok=True)
# os.makedirs(os.path.dirname(INTERACTION_LOG_PATH), exist_ok=True)
# os.makedirs(os.path.dirname(ANALYSIS_REPORT_PATH), exist_ok=True)
