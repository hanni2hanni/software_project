# system_management/interaction_logger.py

import csv
import os
from datetime import datetime
# 从 config 中导入 INTERACTION_LOG_PATH 和 LOG_COLUMNS
# 我们在 config.py 中已经移除了冗余的 LOG_HEADERS，统一使用 LOG_COLUMNS
from .config import INTERACTION_LOG_PATH, LOG_COLUMNS

def _ensure_data_dir_exists():
    """确保 data 目录存在"""
    data_dir = os.path.dirname(INTERACTION_LOG_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

def initialize_log():
    """初始化日志文件：如果不存在则创建并写入表头。"""
    _ensure_data_dir_exists()
    write_header = not os.path.exists(INTERACTION_LOG_PATH)
    if write_header:
        with open(INTERACTION_LOG_PATH, 'w', newline='', encoding='utf-8-sig') as f: # utf-8-sig 确保Excel能正确打开中文CSV
            writer = csv.writer(f)
            # 使用 LOG_COLUMNS 作为表头写入
            writer.writerow(LOG_COLUMNS)
            print(f"创建日志文件并写入表头: {INTERACTION_LOG_PATH}")
    else: # 检查表头是否匹配 (可选但推荐)
        try:
            with open(INTERACTION_LOG_PATH, 'r', newline='', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                existing_headers = next(reader)
                # 检查现有表头是否与 LOG_COLUMNS 匹配
                if existing_headers != LOG_COLUMNS:
                    print(f"警告：日志文件 {INTERACTION_LOG_PATH} 的表头与配置不符。")
                    print(f"  期望表头: {LOG_COLUMNS}")
                    print(f"  实际表头: {existing_headers}")
                    # print("  请考虑备份并重新初始化日志文件，或更新 config.py 中的 LOG_COLUMNS。")
        except StopIteration: # 文件存在但是空的
             with open(INTERACTION_LOG_PATH, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # 文件为空，重新写入 LOG_COLUMNS 作为表头
                writer.writerow(LOG_COLUMNS)
                print(f"发现空日志文件，重新写入表头: {INTERACTION_LOG_PATH}")
        except FileNotFoundError:
             # 应该被 write_header = not os.path.exists() 捕获，但安全起见
             pass
        except Exception as e:
            print(f"检查日志表头时发生错误: {e}")


def log_interaction(log_data: dict):
    """
    记录一次交互到CSV文件。
    log_data: 一个字典，键应与 LOG_COLUMNS 中的值对应。
    """
    # initialize_log() # 每次记录都检查可能影响性能，但确保安全。可以移到模块加载时或启动时调用一次。
    # 假设 initialize_log 已经在模块导入时或系统启动时调用过了

    # 按 LOG_COLUMNS 定义的顺序获取字典中的数据
    row_to_write = [log_data.get(column, "") for column in LOG_COLUMNS]

    # 确保 timestamp 总是第一个且自动生成 (如果外部没提供)
    if 'timestamp' not in log_data or not log_data['timestamp']:
        try:
             # 使用 LOG_COLUMNS 查找 timestamp 的索引
             timestamp_index = LOG_COLUMNS.index('timestamp')
             row_to_write[timestamp_index] = datetime.now().isoformat(sep=' ', timespec='milliseconds')
        except ValueError:
            # 如果 LOG_COLUMNS 中没有 'timestamp'，则忽略自动生成
            pass


    try:
        with open(INTERACTION_LOG_PATH, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(row_to_write)
        # print(f"日志记录成功: {log_entry}") # 通常生产环境不会打印每条日志
    except Exception as e:
        print(f"错误：写入日志失败 - {e}")

# 模块导入时即初始化日志，确保文件和表头准备就绪
# initialize_log() # 在 main.py 中统一初始化
