import re
import datetime
import json
import threading
from collections import defaultdict, Counter
from user_manager import UserManager

# 新增
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
# 注册中文字体（仅需一次）
pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))  # Windows 系统常有该字体

# 系统常量定义
LOG_FILE = 'log.txt'
INTERACTION_MODES = {
    '视觉': ['眼睛居中', '向左看', '向右看', '向下看', '未检测到眼动'],
    '手势': ['竖拇指', '挥手', '握拳', 'OK手势', '无手势'],
    '语音': ['已经注意道路', '语音命令'],
    '警告': ['请目视前方'],
    '确认': ['安全已确认'],
    '拒绝': ['警告未解除'],
    '导航': ['导航路线已确认', '请重新选择导航路线'],
    '音乐': ['音乐正在播放', '音乐已暂停'],
    '场景': ['自由多模态识别', '分心检测', '导航确认', '音乐状态']
}

class LogAnalyzer:
    """
    多模态交互日志分析工具
    用于分析用户交互行为、识别模式和提供系统改进建议
    """
    def __init__(self, log_file=None):
        print("LogAnalyzer: 初始化开始...")
        self.log_file = log_file or LOG_FILE
        self.log_data = []
        self.user_sessions = defaultdict(list)

        print("LogAnalyzer: 正在初始化 UserManager...")
        self.user_manager = UserManager()
        print("LogAnalyzer: UserManager 初始化完成.")

        # self._lock = threading.Lock() # 暂时注释掉锁的初始化, FOR DEBUGGING

        print("LogAnalyzer: 开始加载日志...")
        start_time_load_logs = datetime.datetime.now()
        self.load_logs()
        end_time_load_logs = datetime.datetime.now()
        print(f"LogAnalyzer: 日志加载完成。耗时: {end_time_load_logs - start_time_load_logs}")
        print("LogAnalyzer: 初始化完成.")

    def check_permission(self, username):
        """检查用户是否有权限查看日志"""
        user_type = None
        for user in self.user_manager.user_list:
            if user.username == username:
                user_type = user.user_type
                break

        if not user_type:
            return False

        # 管理人员拥有所有权限
        if user_type == '管理人员':
            return True

        # 维护人员可以查看所有日志
        if user_type == '维护人员':
            return True

        # 驾驶员只能查看自己的日志
        if user_type == '驾驶员':
            return True  # 在analyze_user_behavior中会进一步过滤只显示自己的日志

        return False

    def load_logs(self):
        """加载并解析日志文件"""
        print("  load_logs: 开始执行...")
        processed_lines = 0
        start_time = datetime.datetime.now()
        # with self._lock:  # 使用线程锁保护日志加载 - FOR DEBUGGING, lock is commented out in __init__
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                print(f"  load_logs: 打开文件 {self.log_file} 成功.")
                for i, line in enumerate(f):
                    line_content = line.strip()
                    print(f"  load_logs: 正在处理行 #{i+1}, 内容: '{line_content[:100]}'...") # 打印行号和部分内容，避免过长
                    if line_content:
                        self._parse_log_line(line_content) # 传递 strip 后的内容
                        processed_lines += 1
                    if (i + 1) % 200 == 0: # 每处理200行打印一次进度
                        now = datetime.datetime.now()
                        print(f"  load_logs: 已处理 {i + 1} 行... 当前耗时: {now - start_time}")
        except FileNotFoundError:
            print(f"  load_logs: 错误 - 日志文件 {self.log_file} 未找到。")
            return # 如果文件未找到，提前返回
        except Exception as e:
            print(f"  load_logs: 日志加载时发生错误: {e}")

        end_time = datetime.datetime.now()
        print(f"  load_logs: 执行完毕。共处理有效日志行: {processed_lines}。总耗时: {end_time - start_time}")

    def _parse_log_line(self, line):
        """
        解析单行日志
        支持的格式:
        1. [时间戳] [用户名] 模式: 内容
        2. [时间戳] 模式: 内容
        """
        # 注意：这里接收的 line 已经是 strip() 过的
        print(f"    _parse_log_line: 开始解析行: '{line[:100]}'")
        try:
            # 使用正则表达式匹配日志格式
            # 修正正则表达式以正确捕获完整时间戳 YYYY-MM-DD HH:MM:SS

            print(f"    _parse_log_line: 尝试匹配 'match_with_user'...")
            match_with_user = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(.*?)\] (.*?): (.*)', line) # 用户名后有方括号

            if match_with_user:
                print(f"    _parse_log_line: 'match_with_user' 匹配成功.")
                timestamp_str, username, mode, content = match_with_user.groups()

                print(f"    _parse_log_line: 尝试解析时间戳: '{timestamp_str}'...")
                timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                print(f"    _parse_log_line: 时间戳解析成功.")

                # 验证交互模式的有效性
                print(f"    _parse_log_line: 检查交互模式 '{mode}'...")
                if mode not in INTERACTION_MODES:
                    print(f"警告: 未知的交互模式 {mode} 在行: '{line[:100]}'")
                print(f"    _parse_log_line: 交互模式检查完毕.")

                log_entry = {
                    'timestamp': timestamp,
                    'content': line, # 使用传入的 stripped line
                    'user': username,
                    'mode': mode,
                    'action': content
                }
                print(f"    _parse_log_line: log_entry 创建完毕: user='{log_entry['user']}', mode='{log_entry['mode']}'")

                print(f"    _parse_log_line: 开始追加到 log_data (无锁)...")
                self.log_data.append(log_entry)
                print(f"    _parse_log_line: 追加到 log_data 完成.")
                print(f"    _parse_log_line: 开始追加到 user_sessions for user '{log_entry['user']}' (无锁)...")
                self.user_sessions[log_entry['user']].append(log_entry)
                print(f"    _parse_log_line: 追加到 user_sessions 完成.")
                print(f"    _parse_log_line: 'match_with_user' 处理完毕.")
                return # 成功解析一种格式后即返回
            else:
                print(f"    _parse_log_line: 'match_with_user' 匹配失败.")

            print(f"    _parse_log_line: 尝试匹配 'match_without_user'...")
            # 修正正则表达式以正确捕获完整时间戳 YYYY-MM-DD HH:MM:SS
            match_without_user = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (.*?): (.*)', line)

            if match_without_user:
                print(f"    _parse_log_line: 'match_without_user' 匹配成功.")
                timestamp_str, mode, content = match_without_user.groups()

                print(f"    _parse_log_line: 尝试解析时间戳: '{timestamp_str}'...")
                timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                print(f"    _parse_log_line: 时间戳解析成功.")

                # 验证交互模式的有效性
                print(f"    _parse_log_line: 检查交互模式 '{mode}'...")
                if mode not in INTERACTION_MODES:
                    print(f"警告: 未知的交互模式 {mode} 在行: '{line[:100]}'")
                print(f"    _parse_log_line: 交互模式检查完毕.")

                log_entry = {
                    'timestamp': timestamp,
                    'content': line, # 使用传入的 stripped line
                    'user': 'unknown',
                    'mode': mode,
                    'action': content
                }
                print(f"    _parse_log_line: log_entry 创建完毕: user='{log_entry['user']}', mode='{log_entry['mode']}'")

                # print(f"    _parse_log_line: 尝试获取锁...") # 锁相关的打印也注释掉
                # with self._lock: # 移除 with 块 FOR DEBUGGING
                # print(f"    _parse_log_line: 成功获取锁. 开始追加到 log_data...") # 调整打印，因为没有锁了
                print(f"    _parse_log_line: 开始追加到 log_data (无锁)...")
                self.log_data.append(log_entry)
                print(f"    _parse_log_line: 追加到 log_data 完成.")
                print(f"    _parse_log_line: 开始追加到 user_sessions for user '{log_entry['user']}' (无锁)...")
                self.user_sessions[log_entry['user']].append(log_entry)
                print(f"    _parse_log_line: 追加到 user_sessions 完成.")
                print(f"    _parse_log_line: 'match_without_user' 处理完毕.")
                return # 成功解析一种格式后即返回
            else:
                print(f"    _parse_log_line: 'match_without_user' 匹配失败.")
                print(f"    _parse_log_line: 无法解析日志行: '{line[:100]}'") # 两种格式都匹配失败

        except Exception as e:
            print(f"    _parse_log_line: 解析行 '{line[:100]}' 时发生严重错误: {e}")

    def analyze_user_behavior(self, username, time_period=24):
        """
        分析特定用户在指定时间段内的行为模式

        参数:
        username - 用户名
        time_period - 时间范围（小时），默认24小时

        返回:
        包含用户行为分析的字典
        """
        if not self.check_permission(username):
            return {'error': '没有权限查看日志分析'}

        user_type = None
        for user in self.user_manager.user_list:
            if user.username == username:
                user_type = user.user_type
                break

        if user_type == '驾驶员' and username not in self.user_sessions:
            # This check might be slightly off if a driver has NO logs,
            # but the original check was like this.
            # A better check might be if self.user_sessions.get(username) is empty.
            # For now, sticking to the structure.
             return {'error': '只能查看自己的日志'} # Or "没有找到该驾驶员的日志"

        if username not in self.user_sessions or not self.user_sessions[username]:
            return {} # No logs for this user in the period or at all

        now = datetime.datetime.now()
        cutoff_time = now - datetime.timedelta(hours=time_period)

        recent_logs = [log for log in self.user_sessions[username]
                      if log['timestamp'] > cutoff_time]

        if not recent_logs:
            return {}

        # 初始化分析结果
        result = {
            '视觉识别': defaultdict(int),
            '手势识别': defaultdict(int),
            '语音识别': defaultdict(int),
            '场景交互': defaultdict(int),
            '导航操作': defaultdict(int), # Added
            '音乐操作': defaultdict(int), # Added
            '警告与确认': defaultdict(lambda: defaultdict(int)), # Added
            '交互频率': {
                '总次数': len(recent_logs),
                '平均每小时': len(recent_logs) / time_period if time_period > 0 else 0
            },
            '常用模式': [],
            '错误率': {},
            '用户活跃时段': defaultdict(int) # Added
        }

        # 分析日志内容
        for log in recent_logs:
            content = log['content'].lower()
            mode = log['mode'] # Using original case from parsing, can be .lower() if needed for consistency
            action = log['action']

            # 分析用户活跃时段
            result['用户活跃时段'][log['timestamp'].hour] += 1

            # 分析视觉识别
            if mode == '视觉':
                if '注视前方' in content or '眼睛居中' in content:
                    result['视觉识别']['注视前方'] += 1
                elif '注视左侧' in content or '向左看' in content:
                    result['视觉识别']['注视左侧'] += 1
                elif '注视右侧' in content or '向右看' in content:
                    result['视觉识别']['注视右侧'] += 1
                elif '注视下方' in content or '向下看' in content:
                    result['视觉识别']['注视下方'] += 1
                elif '分心' in content or '警告' in content: # Assuming '警告' in content for visual mode means distraction
                    result['视觉识别']['分心'] += 1
                elif '点头' in content:
                    result['视觉识别']['点头'] += 1
                elif '摇头' in content:
                    result['视觉识别']['摇头'] += 1

            # 分析手势识别
            elif mode == '手势':
                if '拇指' in content:
                    result['手势识别']['拇指'] += 1
                elif '挥手' in content:
                    result['手势识别']['挥手'] += 1
                elif 'ok' in content or 'OK' in content:
                    result['手势识别']['OK手势'] += 1
                elif '握拳' in content:
                    result['手势识别']['握拳'] += 1

            # 分析语音识别
            elif mode == '语音':
                voice_commands = re.findall(r'"(.*?)"', content)
                if voice_commands:
                    for cmd in voice_commands:
                        result['语音识别'][cmd] += 1
                else:
                    text_parts = content.split('语音: ') # Original log format might be "语音: command"
                    if len(text_parts) > 1:
                         # Use action field if it's cleaner and already parsed
                        result['语音识别'][action or text_parts[1]] += 1
                    elif action: # If action is populated from parsing
                        result['语音识别'][action] += 1

            # 分析场景交互及细分操作
            elif mode in ['导航', '音乐', '警告', '确认']:
                result['场景交互'][mode] += 1

                if mode == '导航':
                    if '导航路线已确认' in action:
                        result['导航操作']['路线已确认'] += 1
                    elif '请重新选择导航路线' in action:
                        result['导航操作']['重新选择路线'] += 1
                elif mode == '音乐':
                    if '音乐正在播放' in action:
                        result['音乐操作']['播放'] += 1
                    elif '音乐已暂停' in action:
                        result['音乐操作']['暂停'] += 1
                elif mode == '警告':
                    result['警告与确认']['警告'][action] += 1
                elif mode == '确认':
                    result['警告与确认']['确认'][action] += 1

        # 分析常用模式
        mode_counter = Counter([log['mode'] for log in recent_logs])
        result['常用模式'] = mode_counter.most_common()

        # 计算错误率
        total_interactions = len(recent_logs)
        # Assuming '错误', '失败', '异常' in the raw log content indicate an error for that entry
        error_logs = [log for log in recent_logs if any(err_kw in log['content'].lower() for err_kw in ['错误', '失败', '异常'])]
        error_rate = len(error_logs) / total_interactions if total_interactions > 0 else 0
        result['错误率'] = {
            '总体': error_rate,
            '详细': {
                '视觉识别': self._calculate_error_rate(recent_logs, error_logs, '视觉'),
                '手势识别': self._calculate_error_rate(recent_logs, error_logs, '手势'),
                '语音识别': self._calculate_error_rate(recent_logs, error_logs, '语音'),
            }
        }

        # 转换defaultdict为普通dict并排序活跃时段
        for key in result:
            if isinstance(result[key], defaultdict):
                if key == '警告与确认':
                    result[key] = {k: dict(v) for k, v in result[key].items()}
                else:
                    result[key] = dict(result[key])

        if '用户活跃时段' in result and isinstance(result['用户活跃时段'], dict):
            result['用户活跃时段'] = dict(sorted(result['用户活跃时段'].items()))

        return result

    def _calculate_error_rate(self, all_logs, error_logs, mode_filter):
        """计算特定类型交互的错误率 (helper method)"""
        mode_logs = [log for log in all_logs if log['mode'].lower() == mode_filter.lower()]
        mode_errors = [log for log in error_logs if log['mode'].lower() == mode_filter.lower()]
        return len(mode_errors) / len(mode_logs) if len(mode_logs) > 0 else 0

    def get_improvement_suggestions(self, username):
        """基于用户行为分析提供系统改进建议"""
        analysis = self.analyze_user_behavior(username)
        if not analysis or 'error' in analysis:
            return []

        suggestions = []

        # 分心检测相关建议 (from existing visual analysis)
        if analysis.get('视觉识别', {}).get('分心', 0) > 5:
            suggestions.append({
                '类型': '安全建议',
                '内容': '用户驾驶时注意力分散较多，建议增强分心提醒频率，提高警告声音',
                '优先级': '高'
            })

        # 导航操作建议 (new)
        nav_ops = analysis.get('导航操作', {})
        # Example: if re-selects are more than 50% of confirmed, and total re-selects > 3
        if nav_ops.get('重新选择路线', 0) > nav_ops.get('路线已确认', 0) * 0.5 and nav_ops.get('重新选择路线', 0) > 3:
            suggestions.append({
                '类型': '导航优化',
                '内容': '用户频繁请求重新选择导航路线，可能表示对当前路线不满意或指令不清晰，建议优化路线规划算法或语音指令识别。',
                '优先级': '中'
            })

        # 音乐操作建议 (new)
        music_ops = analysis.get('音乐操作', {})
        total_music_ops = music_ops.get('播放', 0) + music_ops.get('暂停', 0)
        if total_music_ops > 10: # Example: if user interacts with music controls frequently
            suggestions.append({
                '类型': '交互便捷性',
                '内容': '用户频繁操作音乐播放/暂停，可以考虑优化音乐控制的便捷性，如增加方向盘快捷键或更智能的语音控制。',
                '优先级': '低' # Lower priority unless errors are high
            })

        # 警告与确认分析 (new)
        warn_confirm_analysis = analysis.get('警告与确认', {})
        total_warnings = sum(warn_confirm_analysis.get('警告', {}).values())
        total_confirmations = sum(warn_confirm_analysis.get('确认', {}).values())
        if total_warnings > 5 and total_confirmations < total_warnings * 0.3: # Example: many warnings, few confirmations
            suggestions.append({
                '类型': '系统有效性',
                '内容': '系统发出了较多警告，但用户确认比例较低，建议评估警告的准确性和用户的接受度，优化警告触发条件或形式。',
                '优先级': '中'
            })

        # 视觉交互建议 (existing)
        vision_analysis = analysis.get('视觉识别', {})
        vision_total = sum(vision_analysis.values())
        if vision_total > 0:
            if vision_analysis.get('注视左侧', 0) / vision_total > 0.4:
                suggestions.append({
                    '类型': '界面优化',
                    '内容': '用户频繁注视左侧，建议将重要信息/控件调整到左侧区域',
                    '优先级': '中'
                })

        # 手势识别建议 (existing)
        if analysis.get('手势识别', {}).get('拇指', 0) > 10:
            suggestions.append({
                '类型': '交互优化',
                '内容': '用户常用拇指手势，建议扩展该手势的功能映射',
                '优先级': '中'
            })

        # 语音识别建议 (existing, slight enhancement for clarity)
        voice_commands = analysis.get('语音识别', {})
        if voice_commands:
            # Find the most common voice command if there are any
            # Ensure voice_commands is not empty and items are tuples for max()
            if isinstance(voice_commands, dict) and voice_commands:
                # Sort by count, then by command string if counts are equal
                sorted_commands = sorted(voice_commands.items(), key=lambda x: (-x[1], x[0]))
                if sorted_commands:
                    common_cmd = sorted_commands[0][0]
                    suggestions.append({
                        '类型': '语音优化',
                        '内容': f'用户常用 "{common_cmd}" 语音命令，建议添加快捷方式或进一步优化其识别率。',
                        '优先级': '中'
                    })

        # 错误率相关建议 (existing)
        error_rate_info = analysis.get('错误率', {})
        if error_rate_info.get('总体', 0) > 0.2:
            error_rates_detail = error_rate_info.get('详细', {})
            if error_rates_detail:
                valid_error_rates = {k: v for k, v in error_rates_detail.items() if isinstance(v, (int, float))}
                if valid_error_rates:
                    highest_error_mode = max(valid_error_rates.items(), key=lambda x: x[1])
                    suggestions.append({
                        '类型': '可靠性优化',
                        '内容': f'{highest_error_mode[0]}错误率较高({highest_error_mode[1]:.0%})，建议优化识别算法',
                        '优先级': '高'
                    })

        # 用户活跃时段建议 (new)
        active_hours = analysis.get('用户活跃时段', {})
        total_interactions_in_analysis = analysis.get('交互频率', {}).get('总次数', 1) # Avoid division by zero

        if active_hours and total_interactions_in_analysis > 0:
            # Example: if more than 60% of interactions happen in a 2-hour window or less
            # This is a simple heuristic, could be more sophisticated
            sorted_active_hours = sorted(active_hours.items(), key=lambda item: -item[1]) # Sort by count desc

            # Check concentration in peak hours
            # For instance, if top 1 hour has > 40% or top 2 hours have > 60%
            if sorted_active_hours:
                peak_1_hour_interactions = sorted_active_hours[0][1]
                peak_1_hour = sorted_active_hours[0][0]
                if peak_1_hour_interactions / total_interactions_in_analysis > 0.40:
                    suggestions.append({
                        '类型': '系统表现关注',
                        '内容': f'用户在 {peak_1_hour}点 时段交互次数非常集中 ({peak_1_hour_interactions / total_interactions_in_analysis:.0%})，可能表示该时段驾驶任务繁重或系统在该时段表现不稳定，建议关注。',
                        '优先级': '中'
                    })
                elif len(sorted_active_hours) > 1:
                    peak_2_hours_interactions = peak_1_hour_interactions + sorted_active_hours[1][1]
                    peak_2_hour_list = [sorted_active_hours[0][0], sorted_active_hours[1][0]]
                    if peak_2_hours_interactions / total_interactions_in_analysis > 0.60:
                         suggestions.append({
                            '类型': '系统表现关注',
                            '内容': f'用户在 {peak_2_hour_list[0]}点 及 {peak_2_hour_list[1]}点 时段交互次数非常集中 ({peak_2_hours_interactions / total_interactions_in_analysis:.0%})，建议关注系统表现或用户状态。',
                            '优先级': '中'
                        })

        return suggestions

    def generate_system_report(self, num_recent_logs=2000):
        """生成系统整体报告，分析最近 N 条日志"""
        print(f"  DEBUG generate_system_report: 开始执行，分析最多 {num_recent_logs} 条最近日志")

        if not self.log_data:
            print("  DEBUG generate_system_report: self.log_data 为空，无法生成报告。")
            return {}

        try:
            first_log_ts = self.log_data[0]['timestamp']
            last_log_ts = self.log_data[-1]['timestamp']
            print(f"  DEBUG generate_system_report: 日志中第一条时间戳: {first_log_ts.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  DEBUG generate_system_report: 日志中最后一条时间戳: {last_log_ts.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  DEBUG generate_system_report: 总日志条数: {len(self.log_data)}")
        except (IndexError, KeyError, AttributeError) as e:
            print(f"  DEBUG generate_system_report: 无法获取首尾日志时间戳或总条数: {e}")

        start_index = max(0, len(self.log_data) - num_recent_logs)
        recent_logs = self.log_data[start_index:]

        print(f"  DEBUG generate_system_report: 筛选后 recent_logs 数量: {len(recent_logs)}")

        if not recent_logs:
            print("  DEBUG generate_system_report: recent_logs 为空，因此返回空报告。")
            return {}

        active_users = set(log['user'] for log in recent_logs if log['user'] != 'unknown')

        # 初始化全局分析统计
        global_mode_distribution = defaultdict(int)
        global_navigation_actions = defaultdict(int)
        global_music_actions = defaultdict(int)
        global_warning_confirmation_actions = defaultdict(lambda: defaultdict(int))
        global_mode_most_common_actions = defaultdict(lambda: defaultdict(int))
        error_logs_by_mode = defaultdict(list)
        total_logs_by_mode = defaultdict(int)
        error_log_keywords = ['错误', '失败', '异常']

        for log in recent_logs:
            mode = log.get('mode')
            action = log.get('action', '')
            content = log.get('content', '').lower()

            if mode:
                global_mode_distribution[mode] += 1
                total_logs_by_mode[mode] += 1

                # 填充全局各模式最常用操作
                if action: # 确保 action 存在
                    global_mode_most_common_actions[mode][action] += 1

                if mode == '导航':
                    if '导航路线已确认' in action:
                        global_navigation_actions['路线已确认'] += 1
                    elif '请重新选择导航路线' in action:
                        global_navigation_actions['重新选择路线'] += 1
                elif mode == '音乐':
                    if '音乐正在播放' in action:
                        global_music_actions['播放'] += 1
                    elif '音乐已暂停' in action:
                        global_music_actions['暂停'] += 1
                elif mode == '警告':
                    global_warning_confirmation_actions[mode][action] += 1
                elif mode == '确认':
                    global_warning_confirmation_actions[mode][action] += 1

            is_error = any(keyword in content for keyword in error_log_keywords)
            if is_error and mode:
                error_logs_by_mode[mode].append(log)

        global_error_rates_by_mode = {}
        for mode_key, errors in error_logs_by_mode.items():
            if total_logs_by_mode[mode_key] > 0:
                global_error_rates_by_mode[mode_key] = len(errors) / total_logs_by_mode[mode_key]
            else:
                global_error_rates_by_mode[mode_key] = 0

        scene_usage = defaultdict(int)
        for log_entry in recent_logs: # Renamed log to log_entry to avoid conflict with outer scope log var if any
            if isinstance(log_entry.get('content'), str) and '场景' in log_entry['content']:
                # 此处场景使用的逻辑暂时保留，但不在报告中输出
                for scene in INTERACTION_MODES.get('场景', []):
                    if scene in log_entry['content']:
                        scene_usage[scene] += 1 # 仍然计算，但不显示

        total_error_logs_count = sum(len(logs) for logs in error_logs_by_mode.values())

        report = {
            '分析范围': f'最近 {len(recent_logs)} 条日志 (请求分析最多 {num_recent_logs} 条)',
            '总交互次数': len(recent_logs),
            '活跃用户数': len(active_users),
            '日志中所有用户活动统计': dict(Counter(log_entry['user'] for log_entry in recent_logs)),
            '全局交互模式分布': dict(global_mode_distribution),
            '全局导航操作统计': dict(global_navigation_actions),
            '全局音乐操作统计': dict(global_music_actions),
            '全局警告与确认统计': {k: dict(v) for k, v in global_warning_confirmation_actions.items()},
            '全局各模式最常用操作': {mode: dict(actions) for mode, actions in global_mode_most_common_actions.items()},
            '总错误数': total_error_logs_count,
            '总体错误率': total_error_logs_count / len(recent_logs) if recent_logs else 0,
            '各交互模式错误率': global_error_rates_by_mode,
            '活跃时段': self._analyze_active_periods(recent_logs)
        }
        print(f"  DEBUG generate_system_report: 报告生成完毕，准备返回。")
        return report

    def _analyze_active_periods(self, logs):
        """分析系统活跃时段"""
        hour_counts = defaultdict(int)
        for log in logs:
            hour = log['timestamp'].hour
            hour_counts[hour] += 1

        return dict(sorted(hour_counts.items()))

    def export_analysis(self, username, filepath=None):
        """导出用户分析结果到JSON文件"""
        analysis = self.analyze_user_behavior(username)
        suggestions = self.get_improvement_suggestions(username)

        export_data = {
            '用户': username,
            '分析时间': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '行为分析': analysis,
            '改进建议': suggestions
        }

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

        return export_data

# 新增
import textwrap


def generate_user_report_pdf(username, analysis_result, suggestions, output_dir="pdf_reports"):
    import os
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    import textwrap

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{username}_行为报告.pdf")

    c = canvas.Canvas(filepath, pagesize=A4)
    c.setFont("SimSun", 12)
    width, height = A4
    y = height - 50

    def write_line(text, indent=0):
        nonlocal y
        if y < 50:
            c.showPage()
            c.setFont("SimSun", 12)
            y = height - 50
        c.drawString(50 + indent, y, text)
        y -= 20

    def write_wrapped_line(label, value, indent=20, width=70):
        wrapped_lines = textwrap.wrap(str(value), width=width)
        write_line(f"{label}：", indent=indent)
        for line in wrapped_lines:
            write_line(line, indent=indent + 20)

    # 生成报告内容
    write_line(f"用户行为分析报告：{username}")
    write_line("-" * 80)

    write_line("【行为分析结果】")
    for key, value in analysis_result.items():
        write_wrapped_line(key, value)

    write_line("")
    write_line("【改进建议】")
    for idx, sug in enumerate(suggestions, 1):
        if isinstance(sug, dict):
            type_str = sug.get("类型", "无类型")
            level_str = sug.get("优先级", "无优先级")
            content_str = sug.get("内容", "")

            # 标题行：1. 导航优化（优先级：中）
            write_line(f"{idx}. {type_str}（优先级：{level_str}）", indent=20)

            # 内容自动换行
            wrapped = textwrap.wrap(content_str, width=60)
            for line in wrapped:
                write_line(line, indent=40)
        else:
            # 若建议是字符串
            write_line(f"{idx}.", indent=20)
            wrapped = textwrap.wrap(str(sug), width=60)
            for line in wrapped:
                write_line(line, indent=40)

        write_line("")  # 空行分隔建议

    c.save()
    print(f"[PDF] 用户报告已保存至：{filepath}")
# 新增
def generate_system_report_pdf(system_report, output_path="pdf_reports/系统总览报告.pdf"):
    c = canvas.Canvas(output_path, pagesize=A4)
    c.setFont("SimSun", 12)
    width, height = A4
    y = height - 50

    def write_line(text, indent=0):
        nonlocal y
        if y < 50:
            c.showPage()
            c.setFont("SimSun", 12)
            y = height - 50
        c.drawString(50 + indent, y, text)
        y -= 20

    def write_wrapped_line(label, value, indent=20, width=90):
        wrapped_lines = textwrap.wrap(str(value), width=width)
        write_line(f"{label}：", indent=indent)
        for line in wrapped_lines:
            write_line(line, indent=indent + 20)

    write_line("系统行为分析报告总览")
    write_line("-" * 80)
    # for key, value in system_report.items():
    #     write_line(f"{key}：{value}", indent=20)
    for key, value in system_report.items():
        write_wrapped_line(key, value)


    c.save()
    print(f"[PDF] 系统总报告已保存至：{output_path}")


# 使用示例
# if __name__ == '__main__':
#     print("开始测试 LogAnalyzer (分析所有涉及的用户)...")
#     analyzer = LogAnalyzer()

#     if not analyzer.log_data:
#         print("未能加载任何日志数据，无法进行分析。请检查日志文件是否存在且包含数据。")
#     else:
#         print(f"成功加载 {len(analyzer.log_data)} 条日志记录。")

#         # 获取所有在日志中出现过的用户 (排除 'unknown')
#         all_users = [user for user in analyzer.user_sessions.keys() if user and user != 'unknown']

#         if not all_users:
#             print("日志中未找到有效的用户条目 (排除了 'unknown' 用户)。")
#         else:
#             print(f"在日志中找到以下用户将进行分析: {(', '.join(all_users)) if all_users else '无'}")

#             for username in all_users:
#                 print(f"\n--- 开始分析用户: {username} ---")

#                 # --- 获取并打印特定用户的行为分析 ---
#                 #print(f"正在为用户 '{username}' 生成行为分析报告...")
#                 user_analysis = analyzer.analyze_user_behavior(username)

#                 if user_analysis:
#                     if 'error' in user_analysis:
#                         print(f"分析用户 '{username}' 时出错: {user_analysis['error']}")
#                     else:
#                         print(f"用户 '{username}' 的行为分析结果:")
#                         try:
#                             print(json.dumps(user_analysis, indent=2, ensure_ascii=False))
#                         except Exception as e:
#                             print(f"(直接打印用户分析，json格式化失败: {e})")
#                             print(user_analysis)
#                 else:
#                     print(f"未能为用户 '{username}' 生成有效的行为分析 (可能该用户在默认时间段内无日志，或权限问题)。")

#                 # --- 获取并打印特定用户的改进建议 ---
#                 print(f"\n正在为用户 '{username}' 生成改进建议...")
#                 user_suggestions = analyzer.get_improvement_suggestions(username)

#                 if user_suggestions:
#                     print(f"针对用户 '{username}' 的改进建议:")
#                     try:
#                         print(json.dumps(user_suggestions, indent=2, ensure_ascii=False))
#                     except Exception as e:
#                         print(f"(直接打印用户建议，json格式化失败: {e})")
#                         print(user_suggestions)
#                 elif isinstance(user_analysis, dict) and 'error' in user_analysis :
#                      print(f"由于 '{username}' 的行为分析出错，无法生成改进建议。")
#                 else:
#                     print(f"未能为用户 '{username}' 生成改进建议 (通常因为分析数据不足以产生建议)。")

#                 print(f"--- 用户: {username} 分析完毕 ---")

#     # --- 系统整体报告部分 ---
#     logs_to_analyze_count = 2000
#     print(f"\n生成系统整体报告 (分析最近 {logs_to_analyze_count} 条日志)...")
#     system_report = analyzer.generate_system_report(num_recent_logs=logs_to_analyze_count)

#     if system_report:
#         print("\n系统报告内容:")
#         try:
#             print(json.dumps(system_report, indent=2, ensure_ascii=False))
#         except Exception as e:
#             print(f"(直接打印系统报告，json格式化失败: {e})")
#             print(system_report)
#     else:
#         print(f"未能生成系统报告 (可能是因为没有任何日志数据)。")

#     print("\nLogAnalyzer 测试脚本 (全用户分析模式) 运行完毕。")
if __name__ == '__main__':
    print("开始生成多用户日志分析 PDF 报告...")
    analyzer = LogAnalyzer()

    if not analyzer.log_data:
        print("❌ 未加载任何日志数据，无法分析。请检查日志文件。")
    else:
        print(f"✅ 已加载 {len(analyzer.log_data)} 条日志记录。")

        # 获取所有有效用户
        all_users = [user for user in analyzer.user_sessions.keys() if user and user != 'unknown']

        if not all_users:
            print("⚠️ 日志中未找到有效用户（已排除 'unknown'）。")
        else:
            print(f"🔍 分析以下用户：{', '.join(all_users)}")

            for username in all_users:
                print(f"📄 正在生成用户 [{username}] 的报告...")

                user_analysis = analyzer.analyze_user_behavior(username)
                user_suggestions = analyzer.get_improvement_suggestions(username) or []

                if not user_analysis or 'error' in user_analysis:
                    print(f"⚠️ 用户 {username} 的行为分析失败，跳过报告生成。")
                    continue

                try:
                    generate_user_report_pdf(username, user_analysis, user_suggestions)
                except Exception as e:
                    print(f"❌ 无法生成用户 {username} 的 PDF 报告: {e}")
                else:
                    print(f"✅ 已生成用户 {username} 的报告。")

    # 生成系统整体报告
    logs_to_analyze_count = 2000
    print(f"\n📊 正在生成系统整体报告（最近 {logs_to_analyze_count} 条日志）...")
    system_report = analyzer.generate_system_report(num_recent_logs=logs_to_analyze_count)

    if system_report:
        try:
            generate_system_report_pdf(system_report)
        except Exception as e:
            print(f"❌ 系统报告生成失败: {e}")
        else:
            print("✅ 系统报告生成成功。")
    else:
        print("⚠️ 无法生成系统报告（日志不足或为空）。")

    print("\n📚 全部报告生成完毕。请查看 pdf_reports 文件夹。")