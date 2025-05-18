# 系统管理算法

本项目实现了一个基于多模态交互的车载系统，支持语音指令、视觉算法和手势控制等多种交互方式，并提供完善的用户管理、权限控制和反馈机制。


## 安装和环境配置

在使用系统前，请确保安装所有必要的依赖库：

```bash
# 安装依赖
pip install pandas pyttsx3 pywin32
```

为确保系统正常运行，请确认已安装以下Python库：
- pandas：用于数据分析
- pyttsx3：用于文本到语音转换
- pywin32：Windows平台下TTS支持（仅Windows系统需要）

系统要求Python 3.6+版本。

## 测试系统

系统提供了多种测试函数，可以通过运行`main.py`来测试系统功能：

### 运行系统

在项目根目录下使用以下命令启动系统：

```bash
# Windows系统
python -m system_management.main

# Linux/Mac系统
python3 -m system_management.main
```

使用模块导入方式(`-m`)启动可以确保所有相对导入正常工作，不会出现导入错误。
**不会出现任何报错信息**，并且可以听到语音播报(**请打开电脑扬声器**)和视觉反馈（**会弹出一个窗口**），则运行结果符合预期。

### 测试功能

系统内部包含以下测试函数，可以在`main.py`中调用：

```python
# 测试视觉反馈
test_visual_feedback()

# 测试模拟用户交互
simulate_user_interaction("driver_1")

# 测试闭眼警告响应
simulate_eyes_closed_warning_and_response("driver_1")
```

## 扩展系统

系统设计遵循模块化原则，便于扩展：

1. 添加新的输入模态：创建新的输入模拟器类，遵循现有的`get_input()`接口
2. 添加新的反馈类型：在`feedback_orchestrator.py`中添加新的反馈函数
3. 添加新的用户角色：在`ROLES_PERMISSIONS`中定义新角色及其权限

## 文件存储位置

系统使用的数据文件存储在`data`目录下：

- 用户配置：`data/user_profiles.json`
- 交互日志：`data/interaction_log.csv`
- 分析报告：`data/reports/analysis_report.txt`

## 正常运行状态

运行系统后，以下现象表明系统正常工作：

### 启动过程验证

1. **初始化输出**
   - 在命令行窗口中应看到以下内容：
     ```
     --- 开始系统管理模块初始化 ---
     视觉反馈管理器已成功初始化。
     语音引擎已成功初始化。
     系统管理模块已初始化。当前活动用户: 'guest_user' (passenger)。
     ```
   - 系统会创建并初始化`data`目录，包含必要的子目录

2. **视觉反馈窗口**
   - 系统启动时会自动弹出"系统视觉反馈"窗口
   - 窗口中应显示绿色状态指示灯和"系统初始化完成"消息
   - 窗口应保持在最前端，直到测试完成

### 功能测试验证

运行后系统会自动进行以下测试，观察相应输出可验证功能正常：

1. **用户操作模拟**
   - 命令行中将显示多轮交互测试信息：
     ```
     --- 开始模拟多轮用户随机交互以生成日志数据 ---
     [模拟用户交互] 用户ID: driver_1, 角色: driver
     检测到输入模态: voice
     识别指令: "播放音乐", 对应意图: PLAY_MUSIC
     执行权限检查: 允许操作
     ```

2. **分心警告测试**
   - 系统会模拟驾驶员分心场景：
     ```
     === 模拟驾驶员分心警告情景 ===
     1. 模拟检测到驾驶员目光集中在手机
     2. 系统警告驾驶员分心
     ```
   - 视觉反馈窗口会显示红色或橙色警告状态

3. **闭眼检测测试**
   - 系统会模拟驾驶员闭眼场景：
     ```
     === 模拟驾驶员闭眼警告情景 ===
     1. 模拟检测到驾驶员闭眼超过警戒时间
     2. 系统警告驾驶员保持清醒
     ```

4. **日志分析测试**
   - 分析测试会显示：
     ```
     --- 开始加载并分析交互日志 ---
     分析报告已生成至: data/reports/analysis_report.txt
     --- 根据日志分析结果更新用户个性化配置 ---
     正在分析用户: driver_1
     ```

### 文件验证

测试完成后，以下文件应存在且包含数据（注：这些文件是运行后才生成的）：

1. **用户配置文件**：`data/user_profiles.json`
   - 文件应包含多个用户配置，格式正确的JSON
   - 示例验证命令：`type data\user_profiles.json | findstr "common_commands"`

2. **交互日志**：`data/interaction_log.csv`
   - 应包含多行交互记录，CSV格式
   - 示例验证命令：`type data\interaction_log.csv | find /c /v ""`（显示行数）

3. **分析报告**：`data/reports/analysis_report.txt`
   - 包含用户交互分析结果
   - 示例验证命令：`type data\reports\analysis_report.txt`


## 项目结构

```
teamwork/
├── system_management/        # 系统管理模块
│   ├── __init__.py           # 包初始化文件
│   ├── main.py               # 主程序和模拟器实现
│   ├── config.py             # 系统配置和常量
│   ├── user_manager.py       # 用户管理和权限控制
│   ├── interaction_logger.py # 交互日志记录
│   ├── interaction_analyzer.py # 交互日志分析
│   └── feedback_orchestrator.py # 多模态反馈协调
├── data/                     # 数据目录
│   ├── user_profiles.json    # 用户配置文件
│   ├── interaction_log.csv   # 交互日志
│   └── reports/              # 分析报告目录
│       └── analysis_report.txt # 分析报告文件
└── README.md                 # 项目说明文档
``` 

## 系统功能概述

### 模拟多模态输入

1. **语音算法**
   - 实现基本语音指令识别，如"打开空调"、"播放音乐"等
   - 支持不同用户偏好和权限控制

2. **视觉算法**
   - 目光集中区域识别：能检测用户视线焦点
   - 闭眼检测：监测用户闭眼并在超过安全时间时触发警报
   - 头部姿态识别：识别点头(确认)和摇头(拒绝)等动作

3. **手势控制**
   - 握拳：暂停音乐
   - 竖起大拇指：确认操作
   - 摇手：拒绝操作
   - 其他手势控制

### 系统管理功能

1. **用户个性化配置**
   - 保存驾驶员常用指令和交互习惯
   - 个性化反馈偏好设置

2. **交互日志记录与分析**
   - 多模态交互日志记录
   - 日志分析改进用户体验

3. **权限管理**
   - 区分驾驶员、乘客、管理员等不同角色权限
   - 确保系统操作安全

### 多模态输出

1. **文本反馈**
   - 状态提示
   - 警告信息

2. **语音反馈**
   - 语音提示和确认
   - 可自定义音量和详细程度

3. **视觉提示**
   - 状态指示灯
   - 图形化反馈
   - 动画效果

## 系统实现详解

### 1. 模块结构

系统主要由以下模块组成：

- `main.py`: 系统入口和模拟测试
- `user_manager.py`: 用户管理和权限控制
- `interaction_logger.py`: 交互日志记录
- `interaction_analyzer.py`: 交互日志分析
- `feedback_orchestrator.py`: 多模态反馈协调管理
- `config.py`: 系统配置和常量定义

### 2. 语音指令识别实现

语音指令识别通过`VoiceInputSimulator`类实现：

```python
# system_management/main.py
class VoiceInputSimulator:
    def get_input(self):
        commands = [
            ("打开空调", "CONTROL_AC"),
            ("播放音乐", "PLAY_MUSIC"),
            ("暂停音乐", "PAUSE_MUSIC"),
            ("停止音乐", "STOP_MUSIC"),
            ("上一首", "PREVIOUS_SONG"),
            ("下一首", "NEXT_SONG"),
            ("音量调高", "SET_VOLUME_HIGH"),
            ("音量调低", "SET_VOLUME_LOW"),
            ("开始导航", "START_NAVIGATION"),
            ("接听电话", "ANSWER_CALL"),
            ("获取天气", "GET_WEATHER"),
            ("讲个笑话", "TELL_JOKE"),
            ("发送消息", "SEND_MESSAGE"),
            ("查看系统状态", "VIEW_DIAGNOSTICS"),
            ("重置系统", "RESET_SYSTEM"),
        ]
        # 随机选择指令和对应的意图
        # 实际系统会进行语音识别
```

### 3. 视觉算法实现

视觉功能通过`VisionInputSimulator`类实现：

```python
# system_management/main.py
class VisionInputSimulator:
    def get_input(self):
        # 目光集中区域识别
        gaze_areas = ["道路", "仪表盘", "手机", "乘客", "导航屏", "车外"]
        
        # 头部姿态识别
        head_poses = [("点头", "CONFIRM_ACTION"), ("摇头", "REJECT_ACTION"), ...]
        
        # 闭眼检测
        eye_states = ["睁眼", "闭眼"]
        
        # 随机生成模拟数据并返回对应事件
        # 实际系统会使用计算机视觉算法进行检测
```

### 4. 手势控制实现

手势控制通过`GestureInputSimulator`类实现：

```python
# system_management/main.py
class GestureInputSimulator:
    def get_input(self):
        gestures = [
            ("握拳", "PAUSE_MUSIC"),            # 握拳暂停音乐
            ("竖起大拇指", "CONFIRM_ACTION"),   # 竖起大拇指确认
            ("摇手", "REJECT_ACTION"),          # 摇手表示拒绝
            ("放大手势", "ZOOM_IN_MAP"),
            ("缩小手势", "ZOOM_OUT_MAP"),
            ("滑动", "SCROLL_DISPLAY"),
            ("挥手", "NEXT_ITEM"),
        ]
        # 随机选择手势和对应的意图
        # 实际系统会使用计算机视觉算法进行手势识别
```

### 5. 用户管理和权限控制

用户管理系统在`user_manager.py`中实现：

```python
# system_management/user_manager.py
# 角色及其权限定义
ROLES_PERMISSIONS = {
    "driver": [
        "CONTROL_AC", "PLAY_MUSIC", "PAUSE_MUSIC", "STOP_MUSIC", "PREVIOUS_SONG", ...
    ],
    "passenger": [
        "PLAY_MUSIC", "PAUSE_MUSIC", "STOP_MUSIC", "PREVIOUS_SONG", ...
    ],
    "vehicle_maintenance": [
        "VIEW_SYSTEM_DIAGNOSTICS", "RESET_SYSTEM_SETTINGS", ...
    ],
    "system_administrator": ["ALL_PERMISSIONS"],
    DEFAULT_ROLE: [
        "PLAY_GUEST_PLAYLIST", "PLAY_MUSIC", "PAUSE_MUSIC", ...
    ]
}
```

权限检查通过`check_permission`函数实现：

```python
def check_permission(user_id: str, action_tag: str) -> bool:
    """检查用户是否有权限执行某个动作"""
    role = get_user_role(user_id)
    permissions = ROLES_PERMISSIONS.get(role, [])
    if "ALL_PERMISSIONS" in permissions:
        return True
    return action_tag in permissions
```

### 6. 反馈机制实现

多模态反馈通过`feedback_orchestrator.py`实现：

#### 视觉反馈

```python
# system_management/feedback_orchestrator.py
class VisualFeedbackManager:
    """
    提供图形化视觉反馈的管理器类，使用tkinter创建可视化的状态提示和警告。
    支持多种视觉反馈元素，包括状态图标、颜色变化和动画效果。
    """
    # 实现方法：update_status, _start_blink_animation等
```

#### 语音反馈

```python
# system_management/feedback_orchestrator.py
def speak_text(text, volume=100, lang="zh-CN"):
    """使用TTS引擎播放文本"""
    engine = _get_tts_engine()
    if engine:
        if volume != 100:  # 如果需要调整音量
            engine.setProperty('volume', volume/100)
        engine.say(text)
        engine.runAndWait()
```

#### 反馈协调

```python
# system_management/feedback_orchestrator.py
def trigger_feedback(user_id: str, event_type: str, event_data: dict = None) -> dict:
    """
    根据事件类型和用户偏好触发适当的反馈。
    返回触发的反馈摘要，可用于日志记录。
    """
    # 获取用户对此事件类型的反馈偏好
    # 根据偏好触发不同模态的反馈
```

### 7. 交互日志与分析

交互日志记录在`interaction_logger.py`中实现：

```python
# system_management/interaction_logger.py
def log_interaction(log_data: dict):
    """
    记录一次交互到CSV文件。
    log_data: 一个字典，键应与 LOG_COLUMNS 中的值对应。
    """
    # 按LOG_COLUMNS定义的顺序获取字典中的数据
    # 写入CSV文件
```

交互分析在`interaction_analyzer.py`中实现：

```python
# system_management/interaction_analyzer.py
class InteractionAnalyzer:
    def run_analysis(self, user_manager_instance):
        """
        执行日志分析并生成报告，然后根据分析结果更新用户配置。
        """
        # 读取CSV文件
        # 分析用户交互习惯
        # 更新用户个性化配置
```

## 重要接口说明

### 1. 修改权限配置

如需修改不同角色的权限，请编辑`user_manager.py`中的`ROLES_PERMISSIONS`字典：

```python
# system_management/user_manager.py
ROLES_PERMISSIONS = {
    "driver": [
        # 在此添加或删除驾驶员权限
    ],
    "passenger": [
        # 在此添加或删除乘客权限
    ],
    # 其他角色权限...
}
```

### 2. 添加新用户

通过`add_new_user`函数添加新用户：

```python
# 在主程序中
from system_management.main import add_new_user

# 添加驾驶员
add_new_user("driver_3", "驾驶员3", "driver")

# 添加乘客
add_new_user("passenger_3", "乘客3", "passenger")
```

### 3. 修改用户反馈偏好

用户反馈偏好存储在用户配置中，可通过以下方式修改：

```python
# 在主程序中
from system_management.main import get_user_profile, update_user_profile

# 获取用户配置
profile = get_user_profile("driver_1")

# 修改反馈偏好
profile["feedback_preferences"]["general_voice_volume"] = 80
profile["feedback_preferences"]["visual_animation_enabled"] = True

# 更新用户配置
update_user_profile(profile, "driver_1")
```

### 4. 添加新的语音指令

要添加新的语音指令，修改`VoiceInputSimulator`类中的`commands`列表：

```python
# system_management/main.py 中的 VoiceInputSimulator 类
commands = [
    # 现有指令...
    ("新指令名称", "对应的意图标签"),  # 添加新指令
]
```

同时确保在`user_manager.py`的`ROLES_PERMISSIONS`中为相应角色添加对应的权限标签。

### 5. 添加新的手势控制

要添加新的手势控制，修改`GestureInputSimulator`类中的`gestures`列表：

```python
# system_management/main.py 中的 GestureInputSimulator 类
gestures = [
    # 现有手势...
    ("新手势名称", "对应的意图标签"),  # 添加新手势
]
```

同样需要在`ROLES_PERMISSIONS`中为相应角色添加对应的权限标签。

### 6. 添加新的事件类型

要添加新的事件类型，修改`config.py`：

```python
# system_management/config.py
# 事件类型常量
EVENT_USER_DISTRACTED = "USER_DISTRACTED"
# 其他现有事件...
EVENT_NEW_EVENT = "NEW_EVENT"  # 添加新事件
```

然后在`feedback_orchestrator.py`的`_generate_feedback_message`函数中添加对应事件的反馈消息生成逻辑。

## 用户管理与个性化配置详解

### 角色与权限分配

系统实现了完善的角色权限管理机制，主要包括以下角色：

1. **驾驶员(driver)**
   - 拥有最高级别的车内操作权限
   - 可以控制所有车载功能：空调、音乐、导航等
   - 可以查看系统诊断信息和接收关键警告
   - 可以执行系统重置操作
   - 权限标签包括：CONTROL_AC, PLAY_MUSIC, PAUSE_MUSIC, RESET_SYSTEM等

2. **乘客(passenger)**
   - 拥有有限的娱乐系统权限
   - 可以控制音乐播放但音量调整受限
   - 可以请求导航目的地但不能直接设置
   - 无权查看系统诊断或执行系统维护
   - 权限标签包括：PLAY_MUSIC, PAUSE_MUSIC, SET_VOLUME_MEDIUM等

3. **车辆维护人员(vehicle_maintenance)**
   - 拥有系统诊断和维护权限
   - 可以查看详细系统状态和执行系统测试
   - 有限的车载功能控制权
   - 权限标签包括：VIEW_SYSTEM_DIAGNOSTICS, RESET_SYSTEM_SETTINGS等

4. **系统管理员(system_administrator)**
   - 拥有所有系统权限(ALL_PERMISSIONS)
   - 可以配置系统设置和进行用户管理

5. **访客(DEFAULT_ROLE=passenger)**
   - 基本的娱乐功能权限
   - 严格限制对车辆关键系统的访问
   - 权限标签包括：PLAY_GUEST_PLAYLIST, PAUSE_MUSIC等

权限定义位于`user_manager.py`中的`ROLES_PERMISSIONS`字典，示例：

```python
ROLES_PERMISSIONS = {
    "driver": [
        "CONTROL_AC", "PLAY_MUSIC", "PAUSE_MUSIC", "STOP_MUSIC", "PREVIOUS_SONG", "NEXT_SONG", 
        "CONFIRM_ACTION", "REJECT_ACTION", "CONTROL_MUSIC", "SET_VOLUME", "SET_VOLUME_HIGH",
        "START_NAVIGATION", "NAVIGATE", "ANSWER_CALL", "VIEW_CRITICAL_ALERTS", "EXECUTE_COMMAND",
        "GET_WEATHER", "TELL_JOKE", "SEND_MESSAGE", "VIEW_DIAGNOSTICS", "RESET_SYSTEM"
    ],
    "passenger": [
        "PLAY_MUSIC", "PAUSE_MUSIC", "STOP_MUSIC", "PREVIOUS_SONG", "NEXT_SONG", 
        "CONTROL_MUSIC", "SET_VOLUME", "SET_VOLUME_MEDIUM", "CONFIRM_ACTION", "REJECT_ACTION",
        "REQUEST_NAVIGATION_DESTINATION", "EXECUTE_PASSENGER_COMMAND", "GET_WEATHER", "TELL_JOKE",
        "SEND_MESSAGE", "ZOOM_OUT_MAP"
    ],
    // 其他角色权限...
}
```

### 用户个性化配置详情

系统为每位用户存储以下个性化配置数据：

1. **用户基本信息**
   - 用户ID：唯一标识符，如"driver_1"
   - 用户姓名：用户显示名称
   - 用户角色：决定用户权限范围

2. **常用指令(common_commands)**
   - 系统自动记录用户最常使用的指令及使用频率
   - 格式: `{"指令意图": 使用次数}`
   - 示例: `{"PLAY_MUSIC": 15, "CONTROL_AC": 8}`
   - 位置: `user_profiles.json` 中每个用户配置的 `common_commands` 字段

3. **交互习惯(interaction_habits)**
   - 偏好模态：用户偏好的交互方式(语音/手势/视觉)
   - 警告响应习惯：用户对警告的典型响应方式(确认/拒绝/无响应)
   - 时间模式：用户在不同时间的交互偏好
   - 位置: `user_profiles.json` 中每个用户配置的 `interaction_habits` 字段

4. **反馈偏好(feedback_preferences)**
   - 语音反馈音量和详细程度设置
   - 视觉反馈样式和启用设置
   - 特定事件的反馈偏好(分心警告、指令成功等)
   - 示例:
     ```json
     "feedback_preferences": {
       "USER_DISTRACTED": {
         "enabled_modalities": ["voice", "visual_dashboard_light"],
         "voice_detail_level": "normal"
       },
       "general_voice_volume": 70,
       "visual_animation_enabled": true
     }
     ```

### 交互日志记录与分析机制

系统实现了完善的交互日志记录和分析功能：

1. **日志记录内容(interaction_log.csv)**
   - 时间戳：记录交互发生的精确时间
   - 用户信息：包括用户ID和角色
   - 事件类型：如指令执行、警告触发等
   - 输入模态：记录用户使用的交互方式
   - 输入数据摘要：用户输入的内容概述
   - 识别意图：系统理解的用户意图
   - 系统动作和结果：系统响应及执行结果
   - 反馈内容：系统提供的反馈摘要

2. **日志分析器(`interaction_analyzer.py`)**
   - 功能：定期分析用户交互日志，提取个性化配置信息
   - 分析项目：
     - 用户常用指令频率统计
     - 偏好交互模态识别
     - 警告响应模式分析
     - 使用情境分析(时间/位置模式)

3. **个性化配置更新机制**
   - 基于分析结果自动更新用户配置文件
   - 调用 `update_user_personalization_from_analysis` 函数更新
   - 示例结果：
     ```
     用户 'driver_1' 的分析:
     - 常用指令: {"PLAY_MUSIC": 23, "SET_VOLUME": 15, ...}
     - 偏好模态: "voice" (使用率75%)
     - 警告响应: {"确认": 12, "拒绝": 3, "无响应": 1}
     ```

4. **分析报告生成**
   - 系统生成人类可读的分析报告
   - 位置：`data/reports/analysis_report.txt`
   - 包含全局统计和各用户详细分析

## 系统接口与代码结构说明

系统的主要接口和功能分布在各个模块文件中，但大部分面向用户的接口集中在`main.py`中。下面对系统接口和main.py结构进行说明：

### 核心接口说明

系统的主要接口位于`system_management/main.py`，提供以下功能：

#### 1. 用户管理接口
```python
# 添加新用户
def add_new_user(user_id: str, name: str, role: str, initial_preferences: dict = None) -> tuple[bool, str]

# 删除现有用户
def delete_existing_user(user_id: str) -> tuple[bool, str]

# 修改用户角色
def modify_user_role(user_id: str, new_role: str) -> tuple[bool, str]

# 获取用户配置
def get_user_profile(user_id: str = None) -> dict

# 更新用户配置
def update_user_profile(profile_data: dict, user_id: str = None)

# 设置活动用户
def set_active_user(user_id: str) -> bool

# 获取当前活动用户
def get_active_user_id() -> str
```

#### 2. 权限检查接口
```python
# 检查操作权限
def is_action_permitted(action_tag: str, user_id: str = None) -> bool
```

#### 3. 事件处理与反馈接口
```python
# 处理事件并触发反馈
def process_event_and_trigger_feedback(event_type: str, event_data: dict = None, ...) -> dict
```

#### 4. 日志分析接口
```python
# 运行日志分析并更新用户个性化
def run_log_analysis_and_update_personalization()
```

### main.py 文件结构分析

`system_management/main.py`文件可分为以下几个部分：

#### 1. 核心功能部分（可直接调用的API）
- **初始化函数**（第50-80行）：`initialize_system_management()` - 系统初始化
- **用户管理函数**（第86-158行）：添加、删除、修改用户等
- **权限检查函数**（第161-163行）：`is_action_permitted()`
- **事件处理函数**（第166-236行）：`process_event_and_trigger_feedback()`
- **日志分析函数**（第283-296行）：`run_log_analysis_and_update_personalization()`

#### 2. 模拟器类（用于系统测试）
- **VoiceInputSimulator**（第298-314行）：语音输入模拟器
- **GestureInputSimulator**（第316-328行）：手势输入模拟器
- **VisionInputSimulator**（第330-372行）：视觉输入模拟器

#### 3. 测试/示例代码（仅用于展示系统功能）
- **simulate_user_interaction**（第413-527行）：模拟用户交互
- **simulate_distraction_warning_and_response**（第530-625行）：模拟分心警告场景
- **simulate_eyes_closed_warning_and_response**（第626-689行）：模拟闭眼警告场景
- **if __name__ == "__main__"部分**（第960-1136行）：主程序入口和测试场景
  - 系统初始化
  - 测试用户创建
  - 模拟用户交互
  - 特定场景测试
  - 日志分析运行

### 使用系统核心接口的示例

如果您希望将系统集成到自己的应用中，可以这样使用核心接口：

```python
from system_management.main import initialize_system_management, add_new_user, is_action_permitted

# 1. 初始化系统
initialize_system_management()

# 2. 添加用户
success, message = add_new_user("new_driver", "新司机", "driver")
print(message)  # 输出: 用户 'new_driver' 添加成功。

# 3. 检查操作权限
if is_action_permitted("CONTROL_AC", "new_driver"):
    print("新司机有权控制空调")
else:
    print("新司机无权控制空调")
```

### 扩展系统时应修改的文件

如需扩展系统功能，应该修改以下文件：

1. **添加新的权限**：修改`user_manager.py`中的`ROLES_PERMISSIONS`字典
2. **添加新的事件类型**：修改`config.py`中的事件类型常量
3. **添加新的输入模态**：在`main.py`中创建新的输入模拟器类
4. **修改反馈生成逻辑**：修改`feedback_orchestrator.py`中的反馈函数

