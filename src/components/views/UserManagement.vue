<template>
  <div class="user-management">
    <h2>用户管理</h2>
    <table class="user-table">
      <thead>
        <tr>
          <th>用户名</th>
          <th>姓名</th>
          <th>角色</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.name }}</td>
          <td>{{ user.role }}</td>
          <td>
            <router-link :to="`/user-detail/${user.id}`" class="detail-btn">查看详情</router-link>
            <button @click="deleteUser(user.id)" class="delete-btn">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div class="back-link-container">
      <button @click="$router.back()" class="back-link">返回上一页</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'UserManagement',
  data() {
    return {
      users: [],
    };
  },
  methods: {
    fetchUsers() {
      axios.get('http://127.0.0.1:5000/users')
        .then(response => {
          this.users = response.data.users;
        })
        .catch(err => {
          console.error('加载用户失败:', err);
        });
    },
    deleteUser(id) {
      if (!confirm(`确定删除用户 "${id}" 吗？`)) return;
      axios.post('http://127.0.0.1:5000/delete_user', { id })
        .then(() => {
          this.fetchUsers();
        })
        .catch(err => {
          console.error('删除失败:', err);
        });
    }
  },
  mounted() {
    this.fetchUsers();
  }
};
</script>

<style scoped>
.user-management {
  padding: 20px;
  color: #ecf0f1;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
  background-color: rgba(255, 255, 255, 0.05);
}

.user-table th,
.user-table td {
  border: 1px solid #3498db;
  padding: 10px;
  text-align: center;
}

.detail-btn,
.delete-btn {
  display: inline-block;
  padding: 5px 12px;
  font-size: 14px;
  color: white;
  background-color: #3498db; /* 初始为蓝色 */
  border: none;
  border-radius: 5px;
  text-decoration: none;
  cursor: pointer;
  transition: background-color 0.3s ease;
  margin: 0 5px;
}

/* 悬浮“详情”按钮 */
.detail-btn:hover {
  background-color: #2980b9; /* 深蓝色悬浮态，参考admin样式 */
}

/* 悬浮“删除”按钮 */
.delete-btn:hover {
  background-color: #c0392b; /* 红色警示删除 */
}

.detail-btn,
.detail-btn:link,
.detail-btn:visited,
.detail-btn:hover,
.detail-btn:active {
  text-decoration: none;
}

.delete-btn,
.delete-btn:link,
.delete-btn:visited,
.delete-btn:hover,
.delete-btn:active {
  text-decoration: none;
}

.back-link-container {
  margin-top: 20px;
}
.back-link {
  display: inline-block;
  padding: 10px 15px;
  color: #ecf0f1;
  background-color: #3498db;
  border: 1px solid #60aade;
  border-radius: 5px;
  text-decoration: none;
  cursor: pointer;
  transition: background-color 0.3s, transform 0.2s, color 0.3s;
}

.back-link:hover {
  background-color: #60aade;
  color: #fff;
  transform: scale(1.05);
}
</style>
