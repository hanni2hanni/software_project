<template>
  <div class="home">
    <div class="big-time">{{ currentTime }}</div> <!-- 显示当前时间 -->
    <p>欢迎，{{ username || '用户' }} {{ userRole || '未定义' }}！</p> <!-- 显示用户名 -->
    <p>请根据需要选择相应的功能：</p>
    <ul>
      <li>✓ 语音控制</li>
      <li>✓ 手势交互</li>
      <li>✓ 视觉交互</li>
      <li>✓ 系统管理</li>
    </ul>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  data () {
    return {
      currentTime: '' // 用于存储当前时间
    }
  },
  computed: {
    ...mapGetters(['username', 'userRole']) // 从 Vuex 获取用户名和用户角色
  },
  mounted () {
    this.updateTime() // 初始化时间
    setInterval(this.updateTime, 1000) // 每秒更新一次时间
  },
  methods: {
    updateTime () {
      const now = new Date()
      this.currentTime = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  }
}
</script>

<style scoped>
.home {
  text-align: center;
}

.big-time {
  font-size: 5em; /* 设置时间显示的字体大小 */
  color: #eef7fe; /* 设置时间颜色 */
  margin: 20px 0; /* 上下间距 */
}

p {
  font-size: 1.2em; /* 段落文字大小 */
  color: #eef7fe; /* 段落文字颜色 */
}

ul {
  list-style-type: none; /* 去掉列表标记 */
  padding: 0; /* 去掉内边距 */
}

li {
  font-size: 1.1em; /* 列表项大小 */
  color: #eef7fe; /* 列表项颜色 */
}

li:not(:last-child) {
  margin-bottom: 10px; /* 列表项间距 */
}
</style>
