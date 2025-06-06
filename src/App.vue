<template>
  <div id="app">
    <div ref="vantaRef" class="vanta-background"></div>
    <div v-if="isLoggedIn" class="sidebar">
      <h2>车载多模态</h2>
      <h2>智能交互系统</h2>
      <nav>
        <router-link to="/" class="nav-item">主页</router-link>
        <router-link v-if="userRole === 'driver'" to="/driver" class="nav-item">驾驶员功能</router-link>
        <router-link v-if="userRole === 'system_administrator'" to="/admin" class="nav-item">系统管理</router-link>
        <router-link v-if="userRole === 'vehicle_maintenance'" to="/maintenance" class="nav-item">车辆维护</router-link>
      </nav>
      <div class="status">
        <h3>系统状态</h3>
        <p>当前时间: <span class="current-time">{{ currentTime }}</span></p>
        <p>当前状态: <span class="status-active">在线</span></p>
        <p>电池电量: <span class="battery-level">75%</span></p>
        <p>空调状态: <span class="ac-status">{{ acStatus }}</span></p>
      </div>
      <div class="voice-command">
        <h3>语音指令</h3>
        <p>说出 “开始录音” 开始进行语音识别。</p>
      </div>
      <div v-if="userRole === 'driver'" class="recognition-results">
        <h3>识别结果</h3>
        <p>目光：<span>{{ recognitionData.gaze }}</span></p>
        <p>手势：<span>{{ recognitionData.gesture }}</span></p>
        <p>头部姿态：<span>{{ recognitionData.headpose }}</span></p>
        <p>语音状态：<span>{{ recognitionData.voice }}</span></p>
      </div>
    </div>
    <div class="content">
      <router-view />
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import * as THREE from 'three'
import VANTA from 'vanta/src/vanta.net'

export default {
  name: 'App',
  data () {
    return {
      vantaEffect: null,
      currentTime: '',
      acStatus: '关闭',
      recognitionInterval: null // 定时器 ID
    }
  },
  computed: {
    ...mapGetters(['isLoggedIn', 'userRole', 'recognitionData'])
  },
  watch: {
    isLoggedIn(newVal) {
      if (newVal) {
        this.startRecognitionUpdate(); // 启动更新定时器
      } else {
        this.stopRecognitionUpdate(); // 停止更新
      }
    },
    userRole(newVal) {
      if (newVal === 'driver') {
        this.startRecognitionUpdate(); // 启动更新定时器
      } else {
        this.stopRecognitionUpdate(); // 停止更新
      }
    }
  },
  mounted () {
    this.initVanta()
    this.updateTime()
    setInterval(this.updateTime, 1000) // 每秒更新一次时间
  },
  beforeDestroy () {
    if (this.vantaEffect) {
      this.vantaEffect.destroy()
    }
    this.stopRecognitionUpdate(); // 清除定时器
  },
  methods: {
    ...mapActions(['fetchRecognitionResults']),
    
    initVanta () {
      this.vantaEffect = VANTA({
        el: this.$refs.vantaRef,
        THREE: THREE,
        mouseControls: true,
        touchControls: true,
        gyroControls: false,
        minHeight: 200.0,
        minWidth: 200.0,
        scale: 1.0,
        scaleMobile: 1.0,
        color: 0x3b7dae,
        backgroundColor: 0x1d1e44,
        spacing: 12.0
      })
    },
    updateTime () {
      const now = new Date()
      this.currentTime = now.toLocaleTimeString()
    },
    startRecognitionUpdate() {
      // 每50毫秒更新识别结果
      this.recognitionInterval = setInterval(() => {
        this.fetchRecognitionResults()
          .then(() => {
            // 检查手势是否为挥手
            this.checkGesture();
          });
      }, 50);
    },
    stopRecognitionUpdate() {
      // 清除定时器
      if (this.recognitionInterval) {
        clearInterval(this.recognitionInterval);
        this.recognitionInterval = null;
      }
    },
    checkGesture() {
      // 检查手势状态
      const { gesture } = this.recognitionData || {};

      // 假设 "waving" 表示挥手
      if (gesture === '挥手') {
        this.$router.push({ name: 'Navigation' }); // 跳转到 Navigation
      }
    }
  }
}
</script>

<style>
/* 样式保持不变 */
#app {
  display: flex;
  height: 100vh;
  font-family: Arial, sans-serif;
  position: relative; /* 使绝对定位生效 */
}

h2 {
  text-align: center;
  margin-bottom: 15px; /* 标题底部间距 */
}

.nav-item {
  display: block;
  color: #ecf0f1; /* 链接颜色 */
  text-decoration: none; /* 去掉下划线 */
  padding: 10px;
  margin: 5px 0; /* 链接间距 */
  border-radius: 5px; /* 圆角效果 */
  transition: background 0.3s;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1); /* 悬停效果 */
}

.status, .voice-command, .recognition-results {
  margin-top: 20px; /* 顶部间距 */
}

.status-active {
  color: #2ecc71; /* 在线状态颜色 */
}

.battery-level {
  color: #f39c12; /* 电池电量颜色 */
}

.current-time {
  font-weight: bold; /* 加粗时间显示 */
  color: #ecf0f1; /* 时间颜色 */
}

.ac-status {
  color: #3498db; /* 空调状态颜色 */
}

.vanta-background {
  position: absolute; /* 绝对定位 */
  top: 0;
  left: 0;
  width: 100%; /* 填充全屏 */
  height: 100%; /* 填充全屏 */
  z-index: 1; /* 置于底层 */
}

.sidebar {
  background-color: rgba(44, 62, 80, 0.8); /* 半透明深色背景 */
  color: #ecf0f1;
  padding: 20px;
  width: 250px;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.5);
  z-index: 2; /* 置于上层 */
}

.content {
  flex: 1;
  padding: 20px;
  background-color: transparent; /* 设置为透明背景 */
  z-index: 2; /* 置于上层 */
}
</style>
