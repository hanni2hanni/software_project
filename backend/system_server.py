from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import os
import csv
import json

app = Flask(__name__)
CORS(app)

USER_FILE = os.path.join(os.path.dirname(__file__), 'system_management', 'user_profiles.json')

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
        if user_info.get("name") == username:  # 用name字段比对
            user = user_info
            break

    if user is None:
        return jsonify({"error": "用户不存在"}), 404

    # 假设每个用户都存储一个"password"字段来进行验证
    if password != None:  # 替换为真实的密码验证逻辑
        return jsonify({
            "message": "登录成功",
            "role": user.get("role"),  # 返回用户角色
            "name": user.get("name")   # 返回用户名
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


if __name__ == "__main__":
    app.run(port=5000, debug=True)

