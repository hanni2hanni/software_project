<template>
  <div class="login-wrapper">
    <div class="login-container">
      <h2>系统登录</h2>
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input type="text" v-model="username" required placeholder="请输入用户名" />
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input type="password" v-model="password" required placeholder="请输入密码" />
        </div>
        <button type="submit" class="login-button">登 录</button>
      </form>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'

export default {
  data () {
    return {
      username: '',
      password: '',
      errorMessage: ''
    }
  },
  methods: {
    ...mapActions(['login']),
    async handleLogin () {
      try {
        await this.login({ username: this.username, password: this.password })
        this.$router.push({ name: 'Home' }) // 登录成功后跳转
      } catch (error) {
        this.errorMessage = error.message || '登录失败，请检查用户名和密码。'
      }
    }
  }
}
</script>

<style scoped>
.login-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100%;
  position: relative;
  z-index: 2;
}

.login-container {
  width: 360px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

h2 {
  color: #fff;
  margin-bottom: 30px;
  font-size: 24px;
  font-weight: 500;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  text-align: left;
}

label {
  display: block;
  margin-bottom: 8px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

input {
  width: calc(100% - 30px);
  padding: 12px 15px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 14px;
  transition: all 0.3s;
}

input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.login-button {
  width: 30%; /* 保持按钮宽度 */
  padding: 12px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  margin: 10px auto 0; /* 修改这里：auto实现水平居中 */
  display: block; /* 添加这个使margin auto生效 */
}

.login-button:hover {
  background: #2980b9;
  transform: translateY(-2px);
}

.error {
  color: #e74c3c;
  margin-top: 15px;
  font-size: 14px;
  animation: shake 0.5s;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-5px); }
  40%, 80% { transform: translateX(5px); }
}
</style>
