from flask import Flask, Response, request, jsonify, send_file
from flask_cors import CORS
import os
import csv
import json
import subprocess
import time

app = Flask(__name__)
CORS(app)

USER_FILE = os.path.join(os.path.dirname(__file__), 'system_management', 'user_profiles.json')

# 定义共享 PDF 文件路径
SHARED_PDF_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared/pdf_reports/profile_analysis.pdf"))
SHARED_PDF_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../car_system/backend/pdf_reports/profile_analysis.pdf"))

# 定义 profile_analytics.py 的相对路径
PROFILE_ANALYTICS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../car_system/backend/profile_analytics.py"))
PROFILE_ANALYTICS_DIR = os.path.dirname(PROFILE_ANALYTICS_PATH)

# --- 用户管理相关函数 ---
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

@app.route("/users", methods=["GET"])
def get_users():
    users = load_users()
    user_list = [
        {"id": uid, "name": profile.get("name", ""), "role": profile.get("role", "")}
        for uid, profile in users.items()
    ]
    return jsonify({"users": user_list})

@app.route("/user/<user_id>", methods=["GET"])
def get_user_detail(user_id):
    users = load_users()
    user = users.get(user_id)
    if user is None:
        return jsonify({"error": "用户不存在"}), 404
    return jsonify(user)

@app.route("/add_user", methods=["POST"])
def add_user():
    data = request.get_json()
    uid = data.get("id")
    name = data.get("name")
    role = data.get("role")

    if not uid or not name or not role:
        return jsonify({"error": "缺少必要字段"}), 400

    users = load_users()
    if uid in users:
        return jsonify({"error": "用户已存在"}), 409

    users[uid] = {
        "name": name,
        "role": role,
        "common_commands": {},
        "interaction_habits": {},
        "feedback_preferences": {
            "USER_DISTRACTED": {
                "enabled_modalities": ["voice", "text_display", "visual_dashboard_light", "visual_graphic_feedback"],
                "voice_detail_level": "normal"
            },
            "COMMAND_SUCCESS": {
                "enabled_modalities": ["voice_brief", "visual_graphic_feedback"],
                "text_display_enabled": False
            },
            "COMMAND_FAILURE": {
                "enabled_modalities": ["voice", "text_display", "visual_graphic_feedback", "visual_dashboard_light"],
                "voice_detail_level": "normal"
            },
            "PERMISSION_DENIED": {
                "enabled_modalities": ["voice", "text_display", "visual_graphic_feedback", "visual_dashboard_light"],
                "voice_detail_level": "brief"
            },
            "GENERIC_INFO": {
                "enabled_modalities": ["text_display", "visual_graphic_feedback"],
                "voice_detail_level": "normal"
            },
            "general_voice_volume": 70,
            "disable_all_audio_feedback": False,
            "visual_graphic_feedback_enabled": True,
            "visual_animation_enabled": True
        }
    }

    save_users(users)
    return jsonify({"message": "用户添加成功"})

@app.route("/delete_user", methods=["POST"])
def delete_user():
    data = request.get_json()
    uid = data.get("id")

    if not uid:
        return jsonify({"error": "缺少用户ID"}), 400

    users = load_users()
    if uid not in users:
        return jsonify({"error": "用户不存在"}), 404

    del users[uid]
    save_users(users)
    return jsonify({"message": "用户删除成功"})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    print(username, password)

    users = load_users()
    user = None
    for user_id, user_info in users.items():
        if user_info.get("name") == username:
            user = user_info
            break

    if user is None:
        return jsonify({"error": "用户不存在"}), 404

    if password != None:
        return jsonify({
            "message": "登录成功",
            "role": user.get("role"),
            "name": user.get("name")
        })
    else:
        return jsonify({"error": "密码错误"}), 401

# --- 日志接口 ---
@app.route('/api/logs', methods=['GET'])
def get_logs():
    log_path = os.path.join(os.path.dirname(__file__), 'system_management', 'log_output.csv')

    if not os.path.exists(log_path):
        return {"error": f"日志文件未找到: {log_path}"}, 404

    filtered_lines = []
    with open(log_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            filtered_lines.append(','.join(row[:4]))

    csv_data = '\n'.join(filtered_lines)
    return Response(csv_data, mimetype='text/csv')

# --- 用户偏好分析接口 ---
@app.route('/api/profile_analytics', methods=['GET'])
def get_profile_analytics():
    # 由于无法导入 ProfileAnalytics，使用模拟数据
    mock_data = {
        'common_patterns': {
            '常用语音指令': [('已经注意道路', 5), ('语音命令', 3)],
            '常用手势': [('竖拇指', 4), ('挥手', 2)],
            '交互偏好': {'语音优先': [('True', 6)]}
        },
        'user_reports': {
            'user1': {
                '用户名': 'user1',
                '常用功能总结': {'语音指令': 2, '手势': 1, '自定义快捷操作': 0},
                '个性化推荐': {'推荐语音指令': ['语音命令'], '推荐手势': ['挥手'], '推荐交互设置': {'语音优先': 'True'}},
                '最近使用场景': '导航确认',
                '交互偏好': {'语音优先': True}
            }
        }
    }
    return jsonify(mock_data)

# --- PDF 下载接口 ---
@app.route('/api/generate_profile_pdf', methods=['GET'])
def generate_profile_pdf():
    try:
        # 调试：打印路径
        print(f"检查 profile_analytics.py 路径: {PROFILE_ANALYTICS_PATH}")
        if not os.path.exists(PROFILE_ANALYTICS_PATH):
            return jsonify({"error": f"profile_analytics.py 文件未找到: {PROFILE_ANALYTICS_PATH}"}), 404

        # 触发 profile_analytics.py 运行以生成 PDF
        print(f"触发 profile_analytics.py 运行: {PROFILE_ANALYTICS_PATH}")
        result = subprocess.run(
            ["python", PROFILE_ANALYTICS_PATH],
            capture_output=True,
            text=True,
            timeout=30,  # 设置超时为 30 秒
            cwd=PROFILE_ANALYTICS_DIR  # 设置工作目录
        )
        print(f"脚本输出: {result.stdout}")
        if result.stderr:
            print(f"脚本错误: {result.stderr}")
            return jsonify({"error": f"生成 PDF 失败: {result.stderr}"}), 500

        # 等待片刻以确保文件生成
        time.sleep(1)

        # 检查共享 PDF 文件是否存在
        if not os.path.exists(SHARED_PDF_PATH):
            return jsonify({"error": f"PDF 文件未找到: {SHARED_PDF_PATH}"}), 404
        
        print(f"找到文件: {SHARED_PDF_PATH}")
        # 返回 PDF 文件流
        return send_file(
            SHARED_PDF_PATH,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='profile_analysis.pdf'
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": "生成 PDF 超时，请稍后重试"}), 500
    except Exception as e:
        return jsonify({"error": f"提供 PDF 失败: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)