<template>
  <div class="gesture">
    <h1>手势识别页面</h1>
    <p>你好，我是你的车载手势识别助手。你可以通过手势控制车辆功能。</p>
    <div class="assistant-panel">
      <div class="gesture-indications">
        <div class="gesture-box">
          <strong>握拳：</strong>停止音乐
        </div>
        <div class="gesture-box">
          <strong>竖拇指：</strong>开始音乐
        </div>
        <div class="gesture-box">
          <strong>挥手：</strong>返回驾驶员页面
        </div>
      </div>
      <h2>当前手势状态：</h2>
      <p class="status">{{ gestureStatus }}</p>
      <p class="instruction">请确保您的摄像头正常工作，并注意观察系统的反馈。</p>
    </div>
    <div class="back-link-container">
      <router-link to="/driver" class="back-link">返回驾驶员页面</router-link>
    </div>
    <audio ref="audio" :src="musicSource" preload="auto"></audio>
  </div>
</template>

<script>
import axios from 'axios'
import music from '@/assets/music.mp3'

export default {
  name: 'GestureRecognition',
  data () {
    return {
      gestureStatus: '加载中...',
      musicSource: music
    }
  },
  mounted () {
    this.fetchGestureStatus() // 初始化获取手势状态
    setInterval(this.fetchGestureStatus, 2000) // 每2秒获取一次手势状态
  },
  methods: {
    async fetchGestureStatus () {
      try {
        const response = await axios.get('http://localhost:5000/api/gesture') // 假设后端提供手势识别的 API
        this.gestureStatus = response.data['gesture']

        // 根据手势状态控制音乐
        this.controlMusic(this.gestureStatus)
      } catch (error) {
        console.error('Error fetching gesture data:', error)
      }
    },
    controlMusic (gesture) {
      const audio = this.$refs.audio
      switch (gesture) {
        case '握拳':
          audio.pause() // 停止音乐
          break
        case '竖拇指':
          audio.play() // 开始音乐
          break
        case '挥手':
          this.$router.push('/driver') // 返回驾驶员主页
          break
        default:
          break
      }
    }
  }
}
</script>

<style scoped>
.gesture {
  text-align: center;
  padding: 20px;
  color: #ecf0f1;
}

.assistant-panel {
  margin-top: 20px;
  border: 2px solid #92cdf7;
  border-radius: 10px;
  padding: 20px;
  background-color: rgba(52, 152, 219, 0.1);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}

.gesture-indications {
  display: flex; /* 使用 Flexbox 来并排显示 */
  justify-content: center; /* 居中对齐 */
  margin-top: 15px;
}

.gesture-box {
  background-color: rgba(52, 152, 219, 0.2);
  border: 1px solid #3498db;
  border-radius: 8px;
  padding: 10px;
  margin: 0 10px; /* 添加左右间隔 */
  flex: 1; /* 使每个框大小相等 */
  max-width: 200px; /* 限制最大宽度 */
  text-align: center; /* 文本居中 */
  transition: background-color 0.3s; /* 添加过渡效果 */
}

.gesture-box:hover {
  background-color: rgba(52, 152, 219, 0.3); /* 悬停时改变背景颜色 */
}

.status {
  margin-top: 15px;
  font-style: italic;
  color: #f1c40f;
}

.instruction {
  font-style: italic;
  color: #f39c12;
}

.back-link-container {
  margin-top: 30px;
}

.back-link {
  color: #ecf0f1;
  text-decoration: none;
  padding: 10px 15px;
  border: 1px solid #60aade;
  border-radius: 5px;
  transition: background-color 0.3s;
}

.back-link:hover {
  background-color: #60aade;
  color: #fff;
}
</style>
