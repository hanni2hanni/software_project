# system_management/interaction_analyzer.py

import pandas as pd
import os
from collections import defaultdict
import json
import ast # 引入 ast 模块用于解析 Python 字面量
from . import config
from datetime import datetime

class InteractionAnalyzer:
    def __init__(self):
        self.log_path = config.INTERACTION_LOG_PATH
        self.report_path = config.ANALYSIS_REPORT_PATH
        # 确保报告目录存在
        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)

    def run_analysis(self, user_manager_instance):
        """
        执行日志分析并生成报告，然后根据分析结果更新用户配置。
        Args:
            user_manager_instance: UserManager 的实例，用于加载和保存用户配置。
        """
        if not os.path.exists(self.log_path) or os.path.getsize(self.log_path) == 0:
            print("日志文件不存在或为空，跳过分析。")
            return

        try:
            # 读取CSV文件
            # 使用 dtype=str 防止 pandas 自动推断 event_data 列的类型，确保它是字符串
            df = pd.read_csv(self.log_path, dtype=str)
            # 确保所有必要的列都存在，如果不存在则用默认值填充 NaN
            for col in config.LOG_COLUMNS:
                if col not in df.columns:
                    df[col] = pd.NA # 使用 pandas 的 NA 表示缺失值

            # 将 NaN 填充为空字符串，以便后续的字符串处理和解析不易出错
            # 只对可能包含数据的列进行填充，特别是 event_data
            df['event_data'] = df['event_data'].fillna('')
            df['recognized_intent'] = df['recognized_intent'].fillna('N/A') #填充意图列，方便后续处理
            df['input_modalities'] = df['input_modalities'].fillna('N/A') #填充模态列

        except pd.errors.EmptyDataError:
            print("日志文件为空，无法进行分析。")
            return
        except Exception as e:
            print(f"读取日志文件时发生错误: {e}")
            return

        print("--- 开始加载并分析交互日志 ---")
        # 将 DataFrame 传递给报告生成函数
        report_content = self._generate_analysis_report(df)

        with open(self.report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"分析报告已生成至: {self.report_path}")

        print("\n--- 根据日志分析结果更新用户个性化配置 ---")
        # 将 DataFrame 传递给用户配置更新函数
        self._update_user_personalization_from_analysis(df, user_manager_instance)
        print("--- 用户个性化配置更新完成 ---")


    def _generate_analysis_report(self, df: pd.DataFrame) -> str:
        """
        根据DataFrame生成分析报告的文本内容。
        Args:
            df (pd.DataFrame): 包含交互日志的 DataFrame。
        Returns:
            str: 分析报告的文本内容。
        """
        report_lines = []
        report_lines.append(f"车载多模态交互日志分析报告 - 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_lines.append(f"总日志条数: {len(df)}条\n")

        # 全局常用指令/意图
        report_lines.append("--- 全局常用指令/意图 ---")
        # 使用 .value_counts() 统计，这里包括了 'N/A' 意图
        global_commands = df['recognized_intent'].value_counts().to_dict()
        for cmd, count in global_commands.items():
            # 过滤掉计数为0的 'N/A'，但如果 'N/A' 有计数则保留
            if cmd == 'N/A' and count == 0:
                 continue
            report_lines.append(f"- {cmd}: {count}次")
        report_lines.append("\n")

        # 全局模态使用频率
        report_lines.append("--- 全局模态使用频率 ---")
        all_modalities = defaultdict(int)
        # 遍历 input_modalities 列，确保处理的是字符串
        for modalities_str in df['input_modalities']:
            if isinstance(modalities_str, str) and modalities_str.strip() != 'N/A': # 忽略 'N/A'
                 for mod in modalities_str.split(';'):
                     all_modalities[mod.strip()] += 1
        for mod, count in all_modalities.items():
            report_lines.append(f"- {mod}: {count}次")
        report_lines.append("\n")

        # 各用户详细分析
        report_lines.append("--- 各用户详细分析 ---\n")
        # 获取唯一的用户ID列表
        for user_id in df['user_id'].unique():
            user_logs = df[df['user_id'] == user_id]
            # 调用 _analyze_user_interactions 获取分析数据
            user_analysis_data = self._analyze_user_interactions(user_id, user_logs)

            # 尝试获取用户角色，如果用户日志为空或角色列是N/A，则显示未知
            user_role = '未知'
            if not user_logs.empty and 'user_role' in user_logs.columns:
                 # 获取第一个非空的 user_role 值
                 first_role = user_logs['user_role'].dropna().iloc[0] if not user_logs['user_role'].dropna().empty else 'N/A'
                 if first_role != 'N/A':
                      user_role = first_role


            report_lines.append(f"用户ID: {user_id} (角色: {user_role})")
            report_lines.append(f"  交互总次数: {len(user_logs)}")

            # 常用指令/意图
            report_lines.append("  常用指令/意图:")
            # 使用 .get() 安全访问字典键
            common_commands = user_analysis_data.get('common_commands', {})
            if common_commands:
                # 过滤掉计数为0的 'N/A'，只报告有计数的意图
                reportable_commands = {cmd: count for cmd, count in common_commands.items() if cmd != 'N/A' or count > 0}
                if reportable_commands:
                    for cmd, count in reportable_commands.items():
                        report_lines.append(f"    - {cmd}: {count}次")
                else:
                     report_lines.append("    无 (所有意图均为N/A或未记录)")
            else:
                report_lines.append("    无")


            # 偏好模态
            report_lines.append("  偏好模态:")
            preferred_modality_counts = user_analysis_data.get('preferred_modality_counts', {})
            if preferred_modality_counts:
                for mod, count in preferred_modality_counts.items():
                    report_lines.append(f"    - {mod}: {count}次")
                # preferred_modality 字段应该总是在 analyzed_data 中，即使是 'N/A'
                report_lines.append(f"    最常用模态: {user_analysis_data.get('preferred_modality', 'N/A')}")
            else:
                report_lines.append("    无")

            # 警告响应习惯
            report_lines.append("  警告响应习惯:")
            # 直接获取分析结果中的警告响应计数，使用 .get() 提供默认值
            warning_responses = user_analysis_data.get('warning_responses', {"确认": 0, "拒绝": 0, "无响应/其他": 0})
            report_lines.append(f"    - 确认: {warning_responses.get('确认', 0)}次")
            report_lines.append(f"    - 拒绝: {warning_responses.get('拒绝', 0)}次")
            report_lines.append(f"    - 无响应/其他: {warning_responses.get('无响应/其他', 0)}次")
            report_lines.append("\n")

        return "\n".join(report_lines)


    def _analyze_user_interactions(self, user_id: str, user_logs: pd.DataFrame) -> dict:
        """
        分析单个用户的交互数据，提取个性化信息。
        Args:
            user_id (str): 要分析的用户ID。
            user_logs (pd.DataFrame): 该用户的交互日志 DataFrame。
        Returns:
            dict: 该用户的分析结果，包括常用指令、偏好模态和警告响应习惯。
        """
        user_analysis_data = {}

        # 常用指令/意图
        # 统计所有 recognized_intent，包括 'N/A' 值
        common_commands = user_logs['recognized_intent'].value_counts().to_dict()
        user_analysis_data['common_commands'] = common_commands

        # 偏好模态
        modality_counts = defaultdict(int)
        # 遍历 input_modalities 列，确保处理的是字符串并忽略 'N/A'
        for modalities_str in user_logs['input_modalities']:
             if isinstance(modalities_str, str) and modalities_str.strip() != 'N/A':
                  for mod in modalities_str.split(';'):
                       modality_counts[mod.strip()] += 1

        user_analysis_data['preferred_modality_counts'] = modality_counts
        if modality_counts:
            preferred_modality = max(modality_counts, key=modality_counts.get)
            user_analysis_data['preferred_modality'] = preferred_modality
        else:
            user_analysis_data['preferred_modality'] = "N/A"


        # *** 修复核心：警告响应习惯计数逻辑 (基于常用指令) ***
        warning_responses_count = {"确认": 0, "拒绝": 0, "无响应/其他": 0} # 初始化计数

        # 直接从常用指令计数中获取 CONFIRM_ACTION 和 REJECT_ACTION 的次数
        # 假设在当前系统中，CONFIRM_ACTION 和 REJECT_ACTION 主要用作警告响应
        # 使用 .get() 安全地获取计数，即使意图不存在也返回 0
        confirm_count = common_commands.get('CONFIRM_ACTION', 0)
        reject_count = common_commands.get('REJECT_ACTION', 0)

        warning_responses_count['确认'] = confirm_count
        warning_responses_count['拒绝'] = reject_count

        # TODO: 如果 config 中定义了 EVENT_WARNING_UNRESPONSIVE 并且您的模拟会记录此事件，
        #       可以在这里添加 elif 来计数 '无响应/其他'。
        #       例如：
        # for index, log_entry in user_logs.iterrows():
        #      if log_entry['event_type'] == config.EVENT_WARNING_UNRESPONSIVE:
        #           warning_responses_count['无响应/其他'] += 1


        # 将最终的警告响应计数添加到分析结果中
        user_analysis_data['warning_responses'] = warning_responses_count
        # *** 修复核心结束 ***

        return user_analysis_data


    def _update_user_personalization_from_analysis(self, df: pd.DataFrame, user_manager_instance):
        """
        根据分析结果更新用户的个性化配置。
        Args:
            df (pd.DataFrame): 包含交互日志的 DataFrame。
            user_manager_instance: UserManager 的实例，用于加载和保存用户配置。
        """
        # 获取唯一的用户ID列表
        for user_id in df['user_id'].unique():
            user_logs = df[df['user_id'] == user_id]
            analyzed_data = self._analyze_user_interactions(user_id, user_logs)
            # 确保 user_manager_instance 被正确传递和使用来更新配置
            self.update_user_personalization(user_id, analyzed_data, user_manager_instance)


    def update_user_personalization(self, user_id: str, analyzed_data: dict, user_manager_instance):
        """
        根据分析结果更新用户的个性化配置。
        Args:
            user_id (str): 要更新的用户ID。
            analyzed_data (dict): 该用户的分析结果。
            user_manager_instance: UserManager 的实例，用于加载和保存用户配置。
        """
        print(f"正在分析用户: {user_id}")
        # 加载当前用户配置文件，以便与分析结果合并
        # user_manager.load_user_profile 会在用户不存在时返回默认配置，这是期望的行为
        user_profile = user_manager_instance.load_user_profile(user_id)

        # 更新常用指令
        if 'common_commands' in analyzed_data:
            # 简单地用最新的分析结果替换常用指令。
            # 过滤掉计数为0的 'N/A'，避免将无意义的统计存入用户配置
            user_profile['common_commands'] = {cmd: count for cmd, count in analyzed_data['common_commands'].items() if cmd != 'N/A' or count > 0}


        # 更新交互习惯
        # 确保 interaction_habits 键存在
        if 'interaction_habits' not in user_profile:
             user_profile['interaction_habits'] = {}

        # 更新偏好模态
        if 'preferred_modality' in analyzed_data:
            user_profile['interaction_habits']['preferred_modality'] = analyzed_data['preferred_modality']

        # 更新警告响应习惯 (根据分析结果直接更新)
        # 使用 .get() 安全访问 analyzed_data['warning_responses']，并提供默认值
        if 'warning_responses' in analyzed_data:
             # 确保写入的数据结构是预期的 {"确认": x, "拒绝": y, "无响应/其他": z}
             # analyzed_data['warning_responses'] 应该就是这个结构
             user_profile['interaction_habits']['warning_response_habit'] = analyzed_data['warning_responses']
        # else: # 如果 analyzed_data 里没有 warning_responses，保留或设置为默认值，这里选择保留初始化时的默认值


        # 保存更新后的配置文件
        user_manager_instance.save_user_profile(user_id, user_profile)
        print(f"用户 '{user_id}' 的个性化数据已更新（从分析结果）。")
