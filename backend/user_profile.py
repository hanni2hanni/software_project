import json
import os

PROFILE_DIR = 'user_profiles'

# 确保配置目录存在
if not os.path.exists(PROFILE_DIR):
    os.makedirs(PROFILE_DIR)

class UserProfile:
    def __init__(self, username):
        self.username = username
        self.profile_path = os.path.join(PROFILE_DIR, f'{username}.json')
        self.data = {
            '常用语音指令': [],
            '常用手势': [],
            '交互偏好': {},
            '最近场景': '',
            '自定义快捷操作': []
        }
        self.load()

    def load(self):
        if os.path.exists(self.profile_path):
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

    def save(self):
        with open(self.profile_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def get(self, key, default=None):
        return self.data.get(key, default)

def generate_demo_profiles():
    demo_profiles = [
        {
            'username': 'driver1',
            '常用语音指令': ['打开空调', '播放音乐', '导航到公司', '拨打电话给张三', '关闭车窗'],
            '常用手势': ['竖拇指', '挥手', 'OK手势'],
            '交互偏好': {'语音优先': True, '手势灵敏度': '高', '界面主题': '深色'},
            '最近场景': '导航确认',
            '自定义快捷操作': ['一键回家', '一键静音']
        },
        {
            'username': 'driver2',
            '常用语音指令': ['导航到家', '暂停音乐', '打开天窗', '切换收音机', '开启座椅加热'],
            '常用手势': ['食指指向', '胜利手势'],
            '交互偏好': {'语音优先': False, '手势灵敏度': '中', '界面主题': '浅色'},
            '最近场景': '音乐状态',
            '自定义快捷操作': ['一键导航公司', '一键开启空调']
        },
        {
            'username': 'driver3',
            '常用语音指令': ['打开导航', '关闭音乐', '调高音量', '打开阅读灯'],
            '常用手势': ['OK手势', '挥手'],
            '交互偏好': {'语音优先': True, '手势灵敏度': '低', '界面主题': '蓝色'},
            '最近场景': '分心检测',
            '自定义快捷操作': ['一键报警', '一键求助']
        }
    ]
    for profile in demo_profiles:
        up = UserProfile(profile['username'])
        for k, v in profile.items():
            if k != 'username':
                up.set(k, v)

if __name__ == '__main__':
    generate_demo_profiles()
    print('驾驶员个性化配置文件，可在user_profiles目录下查看。') 