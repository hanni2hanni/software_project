import re
import csv
import os

LOG_FILE_PATH = 'log.txt'
CSV_OUTPUT_PATH = 'log_output.csv'

def parse_log_line(line):
    """
    解析单行日志，提取关键信息。
    返回一个包含提取字段的字典，如果无法解析则返回 None。
    """
    line = line.strip()
    if not line:
        return None

    # 模式1: [时间戳] [用户名] 模式: 内容
    match_with_user = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(.*?)\] (.*?): (.*)', line)
    if match_with_user:
        timestamp_str, username, mode, action = match_with_user.groups()
        return {
            'Timestamp': timestamp_str,
            'Username': username,
            'Mode': mode,
            'Action': action,
            'RawLog': line
        }

    # 模式2: [时间戳] 模式: 内容
    match_without_user = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (.*?): (.*)', line)
    if match_without_user:
        timestamp_str, mode, action = match_without_user.groups()
        return {
            'Timestamp': timestamp_str,
            'Username': 'unknown',  # 用户名未知
            'Mode': mode,
            'Action': action,
            'RawLog': line
        }
    
    # 如果两种模式都不匹配
    print(f"警告: 无法解析日志行: '{line[:100]}...'")
    return { # 仍然保存原始日志，但标记其他字段为解析失败
            'Timestamp': 'PARSE_ERROR',
            'Username': 'PARSE_ERROR',
            'Mode': 'PARSE_ERROR',
            'Action': 'PARSE_ERROR',
            'RawLog': line
        }


def convert_log_to_csv(log_file, csv_file):
    """
    读取日志文件，解析每一行，并将结果写入 CSV 文件。
    """
    print(f"开始转换日志文件 '{log_file}' 到 CSV 文件 '{csv_file}'...")
    
    # 检查日志文件是否存在
    if not os.path.exists(log_file):
        print(f"错误: 日志文件 '{log_file}' 未找到。转换中止。")
        return

    parsed_count = 0
    error_count = 0
    
    try:
        with open(log_file, 'r', encoding='utf-8') as infile, \
             open(csv_file, 'w', newline='', encoding='utf-8') as outfile:
            
            # 定义 CSV 列名
            fieldnames = ['Timestamp', 'Username', 'Mode', 'Action', 'RawLog']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            
            # 写入表头
            writer.writeheader()
            
            for i, line_content in enumerate(infile):
                parsed_data = parse_log_line(line_content)
                if parsed_data:
                    writer.writerow(parsed_data)
                    if parsed_data['Timestamp'] == 'PARSE_ERROR':
                        error_count +=1
                    else:
                        parsed_count += 1
                
                if (i + 1) % 100 == 0:
                    print(f"已处理 {i + 1} 行...")
            
        print(f"\n转换完成。")
        print(f"成功解析并写入 {parsed_count} 条日志。")
        if error_count > 0:
            print(f"有 {error_count} 条日志行未能完全解析 (已标记为 PARSE_ERROR 并写入 RawLog)。")
        print(f"CSV 文件已保存到: '{csv_file}'")

    except IOError as e:
        print(f"读写文件时发生错误: {e}")
    except Exception as e:
        print(f"转换过程中发生未知错误: {e}")

if __name__ == '__main__':
    convert_log_to_csv(LOG_FILE_PATH, CSV_OUTPUT_PATH) 