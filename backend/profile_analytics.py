import os
import json
import threading
from user_profile import UserProfile, PROFILE_DIR
from user_manager import USER_TYPES, USER_PERMISSIONS, UserManager
# 新增
import textwrap
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# 注册中文字体（Windows 示例）
pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))

# 系统常量定义
LOG_FILE = 'log.txt'
INTERACTION_TYPES = {
    '视觉交互': ['眼睛居中', '向左看', '向右看', '向下看', '未检测到眼动'],
    '手势交互': ['竖拇指', '挥手', '握拳', 'OK手势', '无手势'],
    '语音交互': ['已经注意道路', '语音命令'],
    '场景交互': ['自由多模态识别', '分心检测', '导航确认', '音乐状态']
}

class ProfileAnalytics:
    """
    用户个性化配置分析工具类
    提供用户习惯分析、推荐系统和用户体验优化功能
    """
    def __init__(self):
        self.profiles = {}
        self.user_manager = UserManager()
        self._lock = threading.Lock()
        self.load_all_profiles()

    def load_all_profiles(self):
        """加载所有用户配置文件"""
        print(f"ProfileAnalytics: 开始从 '{PROFILE_DIR}' 加载所有用户配置文件...")
        loaded_profile_usernames = []
        try:
            if not os.path.exists(PROFILE_DIR):
                print(f"ProfileAnalytics: 错误 - 配置文件目录 '{PROFILE_DIR}' 不存在。")
                return

            for filename in os.listdir(PROFILE_DIR):
                if filename.endswith('.json'):
                    username = filename[:-5]
                    with self._lock:
                        # 直接加载配置文件，不再强制要求用户必须在 UserManager 中预定义
                        self.profiles[username] = UserProfile(username)
                        loaded_profile_usernames.append(username)
                        print(f"ProfileAnalytics: 已加载配置文件 '{filename}' 为用户 '{username}'.")

            if not loaded_profile_usernames:
                print(f"ProfileAnalytics: 在 '{PROFILE_DIR}' 中没有找到任何 .json 配置文件。")
            else:
                print(f"ProfileAnalytics: 共加载了 {len(loaded_profile_usernames)} 个用户配置文件: {loaded_profile_usernames}")

            # 加载后，检查哪些用户未被 UserManager 管理，并发出警告
            managed_users = self.user_manager.get_usernames()
            for uname in loaded_profile_usernames:
                if uname not in managed_users:
                    print(f"ProfileAnalytics: 警告 - 用户配置文件 '{uname}.json' 已加载，但用户 '{uname}' 未在 UserManager 中定义。其用户类型和特定权限可能未知或受限。")

        except Exception as e:
            print(f"ProfileAnalytics: 加载用户配置文件时发生严重错误: {e}")
            import traceback
            traceback.print_exc()

    def get_user_type(self, username):
        """获取用户类型"""
        for user in self.user_manager.user_list:
            if user.username == username:
                return user.user_type
        return None

    def check_permission(self, username, operation):
        """检查用户权限"""
        user_type = self.get_user_type(username)
        if not user_type:
            return False

        # 管理人员拥有所有权限
        if user_type == '管理人员':
            return True

        # 驾驶员可以进行所有交互操作
        if user_type == '驾驶员':
            return True

        # 乘客只能查看，不能修改
        if user_type == '乘客' and operation == 'read':
            return True

        # 维护人员可以查看和分析
        if user_type == '维护人员' and operation in ['read', 'analyze']:
            return True

        return False

    def analyze_common_patterns(self):
        """分析所有用户的常用模式，找出共同点"""
        common_commands = {}
        common_gestures = {}
        common_preferences = {}

        for username, profile in self.profiles.items():
            for cmd in profile.get('常用语音指令', []):
                common_commands[cmd] = common_commands.get(cmd, 0) + 1
            for gesture in profile.get('常用手势', []):
                common_gestures[gesture] = common_gestures.get(gesture, 0) + 1

            # 分析交互偏好
            for pref_key, pref_val in profile.get('交互偏好', {}).items():
                if pref_key not in common_preferences:
                    common_preferences[pref_key] = {}

                pref_str = str(pref_val)  # 转换为字符串以支持各种类型的值
                common_preferences[pref_key][pref_str] = common_preferences[pref_key].get(pref_str, 0) + 1

        return {
            '常用语音指令': sorted(common_commands.items(), key=lambda x: x[1], reverse=True),
            '常用手势': sorted(common_gestures.items(), key=lambda x: x[1], reverse=True),
            '交互偏好': {k: sorted(v.items(), key=lambda x: x[1], reverse=True)
                      for k, v in common_preferences.items()}
        }

    def get_personalized_recommendations(self, username):
        """为特定用户提供个性化建议"""
        if username not in self.profiles:
            return {}

        profile = self.profiles[username]
        all_patterns = self.analyze_common_patterns()

        # 找出其他用户常用但该用户未使用的功能
        recommendations = {
            '推荐语音指令': [],
            '推荐手势': [],
            '推荐交互设置': {}
        }

        user_commands = set(profile.get('常用语音指令', []))
        user_gestures = set(profile.get('常用手势', []))
        user_prefs = profile.get('交互偏好', {})

        # 推荐常用命令
        for cmd, count in all_patterns['常用语音指令']:
            if cmd not in user_commands and count >= 1:
                recommendations['推荐语音指令'].append(cmd)

        # 推荐常用手势
        for gesture, count in all_patterns['常用手势']:
            if gesture not in user_gestures and count >= 1:
                recommendations['推荐手势'].append(gesture)

        # 推荐流行的交互设置
        for pref_key, pref_counts in all_patterns['交互偏好'].items():
            if pref_key not in user_prefs and len(pref_counts) > 0:
                most_common = pref_counts[0][0]  # 最常用的设置值
                recommendations['推荐交互设置'][pref_key] = most_common

        return recommendations

    def update_profile_from_log_analysis(self, username, log_analysis_data, top_n_commands=5, top_n_gestures=3):
        """
        根据 log_analyzer.py 的分析结果更新用户配置。

        参数:
        username - 用户名
        log_analysis_data - 来自 LogAnalyzer.analyze_user_behavior() 的分析字典
        top_n_commands - 保留最常用的N个语音指令
        top_n_gestures - 保留最常用的N个手势
        """
        print(f"ProfileAnalytics: 尝试从日志分析结果更新用户 '{username}' 的配置...")
        if not log_analysis_data:
            print(f"ProfileAnalytics: 用户 '{username}' 的日志分析数据为空，跳过更新。")
            return False

        with self._lock:
            profile = self.profiles.get(username)
            if not profile:
                print(f"ProfileAnalytics: 用户 '{username}' 的配置不存在，将创建一个新的。")
                profile = UserProfile(username)
                self.profiles[username] = profile

            updated = False

            # 1. 更新常用语音指令
            voice_analysis = log_analysis_data.get('语音识别', {})
            if voice_analysis:
                # voice_analysis 是 {'命令': 次数} 的字典
                sorted_commands = sorted(voice_analysis.items(), key=lambda item: item[1], reverse=True)
                top_commands_list = [cmd for cmd, count in sorted_commands[:top_n_commands]]
                if top_commands_list:
                    profile.set('常用语音指令', top_commands_list)
                    print(f"ProfileAnalytics: 用户 '{username}' 的常用语音指令已更新: {top_commands_list}")
                    updated = True

            # 2. 更新常用手势
            gesture_analysis = log_analysis_data.get('手势识别', {})
            if gesture_analysis:
                # gesture_analysis 是 {'手势': 次数} 的字典
                sorted_gestures = sorted(gesture_analysis.items(), key=lambda item: item[1], reverse=True)
                top_gestures_list = [gesture for gesture, count in sorted_gestures[:top_n_gestures]]
                if top_gestures_list:
                    profile.set('常用手势', top_gestures_list)
                    print(f"ProfileAnalytics: 用户 '{username}' 的常用手势已更新: {top_gestures_list}")
                    updated = True

            # 3. 更新交互偏好 (基于最常用模式)
            common_modes = log_analysis_data.get('常用模式', []) # 格式: [('模式', 次数), ...]
            if common_modes:
                preferences = profile.get('交互偏好', {})
                # 获取最常用的模式 (已排序)
                most_common_mode_name = common_modes[0][0]

                # 重置之前的优先设置，避免冲突
                preferences.pop('语音优先', None)
                preferences.pop('手势优先', None)
                # 可以根据需要添加更多模式的偏好设置

                if most_common_mode_name == '语音':
                    preferences['语音优先'] = True
                    print(f"ProfileAnalytics: 用户 '{username}' 的交互偏好已更新为 '语音优先'.")
                elif most_common_mode_name == '手势':
                    preferences['手势优先'] = True
                    print(f"ProfileAnalytics: 用户 '{username}' 的交互偏好已更新为 '手势优先'.")
                # 可根据需要扩展其他模式的偏好设置

                profile.set('交互偏好', preferences)
                updated = True

            # (可选) 更新其他信息，例如常用导航/音乐操作
            # nav_actions = log_analysis_data.get('导航操作', {})
            # music_actions = log_analysis_data.get('音乐操作', {})
            # if nav_actions:
            #     profile.set('常用导航操作', sorted(nav_actions.items(), key=lambda x: x[1], reverse=True))
            #     updated = True
            # if music_actions:
            #     profile.set('常用音乐操作', sorted(music_actions.items(), key=lambda x: x[1], reverse=True))
            #     updated = True

            if updated:
                profile.save()
                print(f"ProfileAnalytics: 用户 '{username}' 的配置文件已保存更新。")
            else:
                print(f"ProfileAnalytics: 用户 '{username}' 的配置没有需要从日志分析结果中更新的内容。")
            return updated

    def update_profile_based_on_interaction(self, username, interaction_type, content):
        """
        基于用户交互更新个性化配置

        参数:
        username - 用户名
        interaction_type - 交互类型（视觉/手势/语音/场景）
        content - 交互内容

        返回:
        bool - 是否更新成功
        """
        if username not in self.profiles:
            return False

        with self._lock:
            profile = self.profiles[username]
            updated = False

            # 根据交互类型更新配置
            if interaction_type.lower() == '语音':
                commands = profile.get('常用语音指令', [])
                if content not in commands:
                    commands.append(content)
                    profile.set('常用语音指令', commands)
                    updated = True

            elif interaction_type.lower() == '手势':
                gestures = profile.get('常用手势', [])
                if content not in gestures:
                    gestures.append(content)
                    profile.set('常用手势', gestures)
                    updated = True

            elif interaction_type.lower() in ['自由多模态识别', '分心检测', '导航确认', '音乐状态']:
                # 更新最近场景
                profile.set('最近场景', interaction_type)
                # 更新常用场景列表
                scenes = profile.get('常用场景', [])
                if interaction_type not in scenes:
                    scenes.append(interaction_type)
                    profile.set('常用场景', scenes)
                updated = True

            # 更新交互偏好
            preferences = profile.get('交互偏好', {})
            if interaction_type.lower() == '语音' and content:
                preferences['语音优先'] = True
            elif interaction_type.lower() == '手势' and content != '无手势':
                preferences['手势灵敏度'] = preferences.get('手势灵敏度', '中')
            profile.set('交互偏好', preferences)

            if updated:
                profile.save()

            return updated

    def get_user_preference(self, username, preference_key, default=None):
        """获取用户特定偏好设置"""
        if username not in self.profiles:
            return default

        profile = self.profiles[username]
        preferences = profile.get('交互偏好', {})
        return preferences.get(preference_key, default)

    def set_user_preference(self, username, preference_key, value):
        """设置用户特定偏好"""
        if username not in self.profiles:
            return False

        profile = self.profiles[username]
        preferences = profile.get('交互偏好', {})
        preferences[preference_key] = value
        profile.set('交互偏好', preferences)
        return True

    def generate_user_report(self, username):
        """生成用户使用报告"""
        if username not in self.profiles:
            return {}

        profile = self.profiles[username]
        recommendations = self.get_personalized_recommendations(username)

        report = {
            '用户名': username,
            '常用功能总结': {
                '语音指令': len(profile.get('常用语音指令', [])),
                '手势': len(profile.get('常用手势', [])),
                '自定义快捷操作': len(profile.get('自定义快捷操作', []))
            },
            '个性化推荐': recommendations,
            '最近使用场景': profile.get('最近场景', ''),
            '交互偏好': profile.get('交互偏好', {})
        }

        return report

# 使用示例
# if __name__ == '__main__':
#     import json # 确保导入 json 模块
#     analytics = ProfileAnalytics()

#     print("--- 开始分析所有用户的共同模式 ---")
#     patterns = analytics.analyze_common_patterns()
#     if patterns:
#         print("全局常用语音指令:")
#         print(json.dumps(patterns.get('常用语音指令', []), indent=2, ensure_ascii=False))
#         print("\n全局常用手势:")
#         print(json.dumps(patterns.get('常用手势', []), indent=2, ensure_ascii=False))
#         print("\n全局交互偏好统计:")
#         print(json.dumps(patterns.get('交互偏好', {}), indent=2, ensure_ascii=False))
#     else:
#         print("未能分析出共同模式，可能没有加载到任何用户配置。")
#     print("--- 所有用户共同模式分析完毕 ---")

#     # 获取所有已加载配置文件的用户
#     profile_usernames = list(analytics.profiles.keys())

#     if not profile_usernames:
#         print("\n未能从 'user_profiles' 目录加载任何有效的用户配置文件，无法为特定用户生成报告或推荐。")
#     else:
#         print(f"\n--- 开始为以下已加载配置文件的用户生成报告和推荐: {profile_usernames} ---")
#         for username in profile_usernames:
#             print(f"\n----- 用户: {username} -----")

#             # 检查用户是否存在于 UserManager 中 (可选，但良好实践)
#             if username not in analytics.user_manager.get_usernames():
#                 print(f"警告: 用户 '{username}' 存在配置文件，但在 UserManager 中未定义。跳过分析。")
#                 continue

#             # 获取并打印个性化推荐
#             print(f"\n  为用户 '{username}' 生成个性化推荐...")
#             recommendations = analytics.get_personalized_recommendations(username)
#             if recommendations:
#                 print(f"  给 '{username}' 的推荐:")
#                 print(json.dumps(recommendations, indent=2, ensure_ascii=False))
#             else:
#                 print(f"  未能为 '{username}' 生成推荐 (可能因为是新用户或数据不足)。")

#             # 获取并打印用户报告
#             print(f"\n  为用户 '{username}' 生成用户报告...")
#             user_report = analytics.generate_user_report(username)
#             if user_report:
#                 print(f"  用户 '{username}' 的报告:")
#                 print(json.dumps(user_report, indent=2, ensure_ascii=False))
#             else:
#                 print(f"  未能为 '{username}' 生成用户报告。")

#             print(f"----- 用户: {username} 分析完毕 -----")
#         print("--- 所有已加载配置文件的用户分析完毕 ---")

#     print("\nProfileAnalytics 示例运行完毕。")

# 新增
import os
import textwrap
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from profile_analytics import ProfileAnalytics

# 注册中文字体（Windows 示例）
pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))

def generate_profile_analysis_pdf(output_path="pdf_reports/profile_analysis.pdf"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
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

    def write_wrapped(text, indent=0, width_limit=90):
        lines = textwrap.wrap(str(text), width=width_limit)
        for line in lines:
            write_line(line, indent)

    analytics = ProfileAnalytics()

    write_line("多用户配置偏好分析报告", indent=0)
    write_line("-" * 80)

    # --- 全局偏好 ---
    write_line("【全局共同模式分析】", indent=0)

    patterns = analytics.analyze_common_patterns()
    if patterns:
        write_line("● 常用语音指令：", indent=10)
        for item in patterns.get("常用语音指令", []):
            write_wrapped(f"- {item}", indent=30)

        write_line("● 常用手势：", indent=10)
        for item in patterns.get("常用手势", []):
            write_wrapped(f"- {item}", indent=30)

        write_line("● 交互偏好：", indent=10)
        for k, v in patterns.get("交互偏好", {}).items():
            write_wrapped(f"{k}：{v}", indent=30)
    else:
        write_line("未能分析出全局共同偏好", indent=10)

    # --- 每位用户 ---
    profile_usernames = list(analytics.profiles.keys())
    if not profile_usernames:
        write_line("\n未能加载任何用户配置文件", indent=0)
    else:
        write_line("\n【用户个性化推荐与报告】", indent=0)
        for username in profile_usernames:
            write_line(f"\n◎ 用户：{username}", indent=10)

            if username not in analytics.user_manager.get_usernames():
                write_line("⚠️ 未在 UserManager 中定义，跳过。", indent=20)
                continue

            # 推荐
            recommendations = analytics.get_personalized_recommendations(username)
            write_line("• 个性化推荐：", indent=20)
            if recommendations:
                for idx, rec in enumerate(recommendations, 1):
                    if isinstance(rec, dict):
                        line = f"{idx}. {rec.get('类型', '无类型')}（优先级：{rec.get('优先级', '无')})"
                        write_line(line, indent=30)
                        wrapped = textwrap.wrap(rec.get("内容", ""), width=80)
                        for wline in wrapped:
                            write_line(wline, indent=50)
                    else:
                        write_wrapped(f"{idx}. {rec}", indent=30)
            else:
                write_line("无推荐建议", indent=30)

            # 报告
            user_report = analytics.generate_user_report(username)
            write_line("• 用户报告：", indent=20)
            if user_report:
                for key, value in user_report.items():
                    write_wrapped(f"{key}：{value}", indent=30)
            else:
                write_line("无报告生成", indent=30)

    c.save()
    print(f"[PDF] 偏好分析报告已生成：{output_path}")
if __name__ == '__main__':
    generate_profile_analysis_pdf()
