<template>
  <div class="admin">
    <h1>系统管理员页面</h1>
    <p>欢迎，管理员！请管理系统设置和用户信息：</p>
    <div class="admin-features">
      <div class="admin-feature-item">
        <h2>用户管理</h2>
        <p>查看、添加或删除用户信息。</p>
        <router-link to="/user-management" class="admin-feature-link">管理用户</router-link>
      </div>
      <div class="admin-feature-item">
        <h2>系统设置</h2>
        <p>调整系统设置以优化性能。</p>
        <router-link to="/system-settings" class="admin-feature-link">进入设置</router-link>
      </div>
      <div class="admin-feature-item">
        <h2>监控日志</h2>
        <p>查看系统运行日志，确保系统正常运行。</p>
        <router-link to="/system-logs" class="admin-feature-link">查看日志</router-link>
      </div>
    </div>
    <div class="back-link-container">
      <router-link to="/" class="back-link">返回主页</router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Admin'
}
</script>

<style scoped>
.admin {
  text-align: center;
  padding: 20px;
  color: #ecf0f1; /* 文字颜色 */
  height: 100vh; /* 适配屏幕高度 */
  display: flex;
  flex-direction: column;
  justify-content: flex-start; /* 使内容上对齐 */
  background-color: transparent; /* 背景透明 */
}

h1{
  margin: 0; /* 去掉默认的间距 */
}

.admin-features {
  display: grid;
  grid-template-columns: repeat(3, 1fr); /* 三列布局 */
  gap: 20px; /* 卡片之间的间距 */
  margin-top: 20px;
}

.admin-feature-item {
  border: 2px solid #92cdf7; /* 蓝色边框 */
  border-radius: 10px;
  padding: 20px;
  background-color: rgba(52, 152, 219, 0.1); /* 半透明蓝色背景 */
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s, background-color 0.3s;
}

.admin-feature-item:hover {
  transform: translateY(-5px);
  background-color: rgba(52, 152, 219, 0.2); /* 悬停时加深蓝色背景 */
}

.admin-feature-link {
  display: inline-block;
  margin-top: 10px;
  padding: 10px 15px;
  color: white; /* 链接文本颜色 */
  background-color: #3498db; /* 蓝色按钮背景色 */
  border-radius: 5px;
  text-decoration: none;
  transition: background-color 0.3s;
}

.admin-feature-link:hover {
  background-color: #2980b9; /* 悬停时按钮颜色 */
}

.back-link-container {
  margin-top: 20px; /* 顶部间距 */
}

.back-link {
  display: inline-block;
  color: #ecf0f1; /* 链接文字颜色 */
  text-decoration: none;
  padding: 10px 15px;
  border: 1px solid #60aade; /* 蓝色边框 */
  border-radius: 5px;
  transition: background-color 0.3s, color 0.3s;
}

.back-link:hover {
  background-color: #60aade; /* 背景色 */
  color: #fff; /* 字体颜色 */
}
</style>
