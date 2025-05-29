USER_TYPES = ['驾驶员', '乘客', '维护人员', '管理人员']
USER_PERMISSIONS = {
    '驾驶员': '可操作驾驶相关功能，查看多模态识别结果',
    '乘客': '仅可查看多模态识别结果，部分操作受限',
    '维护人员': '可查看系统日志，维护系统',
    '管理人员': '可管理所有用户和系统设置，拥有全部权限'
}

class User:
    def __init__(self, username, user_type):
        self.username = username
        self.user_type = user_type
        self.permissions = USER_PERMISSIONS.get(user_type, '')

class UserManager:
    def __init__(self):
        self.user_list = [
            User('driver1', '驾驶员'),
            User('passenger1', '乘客'),
            User('maintainer1', '维护人员'),
            User('admin1', '管理人员')
        ]
        self.current_user = self.user_list[0]

    def get_usernames(self):
        return [user.username for user in self.user_list]

    def set_current_user(self, username):
        for user in self.user_list:
            if user.username == username:
                self.current_user = user
                break

    def get_current_user(self):
        return self.current_user 