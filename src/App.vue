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
      </div>
      <div v-if="userRole === 'driver'" class="voice-command">
        <h3>语音指令</h3>
        <p>呼唤 “ 小贝 ” 开始语音指令识别</p>
      </div>
      <div v-if="userRole === 'driver'" class="recognition-results">
        <h3>识别结果</h3>
        <p>目光：<span>{{ recognitionData.gaze }}</span></p>
        <p>手势：<span>{{ recognitionData.gesture }}</span></p>
        <p>头部姿态：<span>{{ recognitionData.headpose }}</span></p>
        <p>语音状态：<span>{{ recognitionData.voice }}</span></p>
        <p v-if="isDistracted" style="color: red;">⚠️ 检测到驾驶员注意力不集中</p>
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
      recognitionInterval: null,
      isDistracted: false,
      distractedStartTime: null,
      alertAudio: null,
      musicAudio: null // ✅ 添加音乐播放器

    }
  },
  computed: {
    ...mapGetters(['isLoggedIn', 'userRole', 'recognitionData'])
  },
  watch: {
    isLoggedIn (newVal) {
      if (newVal && this.userRole === 'driver') {
        this.startRecognitionUpdate()
      } else {
        this.stopRecognitionUpdate()
      }
    },
    userRole (newVal) {
      if (this.isLoggedIn && newVal === 'driver') {
        this.startRecognitionUpdate()
      } else {
        this.stopRecognitionUpdate()
      }
    }
  },
  mounted () {
    this.initVanta()
    this.updateTime()
    setInterval(this.updateTime, 1000)

    // 初始化报警音频
    this.alertAudio = new Audio(require('@/assets/alert.wav'))
    this.alertAudio.loop = true;
    this.musicAudio = new Audio(require('@/assets/music.mp3')) // ← 请替换成你的音乐文件路径
    this.musicAudio.loop = true
  },
  beforeDestroy () {
    if (this.vantaEffect) {
      this.vantaEffect.destroy()
    }
    this.stopRecognitionUpdate()
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
    startRecognitionUpdate () {
      this.recognitionInterval = setInterval(() => {
        this.fetchRecognitionResults()
          .then(() => {
            this.checkGesture()
            this.checkDistraction()
            this.checkVoiceCommand() // ✅ 增加语音指令检测
          })
      }, 50)
    },
    stopRecognitionUpdate () {
      if (this.recognitionInterval) {
        clearInterval(this.recognitionInterval)
        this.recognitionInterval = null
      }
    },
    checkGesture () {
      const { gesture } = this.recognitionData || {}
      if (gesture === '挥手') {
        this.$router.push({ name: 'Navigation' })
        console.log('[手势控制] 检测到挥手，跳转导航页')
      }
      if (gesture === '握拳') {
        if (this.musicAudio && !this.musicAudio.paused) {
          this.musicAudio.pause()
          console.log('[音乐控制] 握拳检测到，暂停音乐')
        }
      }
    },

    checkVoiceCommand () {
      const { voice } = this.recognitionData || {}
      if (voice && voice.includes('播放音乐')) {
        if (this.musicAudio && this.musicAudio.paused) {
          this.musicAudio.play()
          console.log('[音乐控制] 语音指令触发，播放音乐')
        }
      }
    },
    checkDistraction () {
      const { gaze, gesture, voice } = this.recognitionData || {};
      const now = Date.now();

      // 检查目光是否偏离中心
      const isNotCenter = gaze !== '眼睛居中';

      if (isNotCenter) {
        // 如果目光偏离中心，开始计时
        if (!this.distractedStartTime) {
          this.distractedStartTime = now;
          console.log('[分心检测] 目光偏离中心，开始计时');
        } else if (now - this.distractedStartTime >= 5000 && !this.isDistracted) {
          // 累计时间超过 5 秒，触发警告
          console.log('[分心检测] 目光偏离超过 5 秒，触发分心警告');
          this.isDistracted = true;
          this.triggerDistractionWarning(); // 播放警告音频
        }
      } else {
        // 目光恢复居中，重置分心状态
        if (this.distractedStartTime) {
          console.log('[分心检测] 目光恢复居中，重置分心状态');
          this.clearDistraction();
        }
        this.distractedStartTime = null; // 清空计时器
      }

      // 检查用户是否确认已注意道路
      const acknowledged = (voice && (voice.includes('已注意道路') || voice.includes('注意道路'))) || gesture === '竖拇指';
      if (this.isDistracted && acknowledged) {
        console.log('[分心检测] 用户确认已注意道路，清除分心状态');
        this.clearDistraction();
      }

      // 确保警告音频在分心状态下循环播放
      if (this.isDistracted) {
        this.triggerDistractionWarning();
      }
    },

    triggerDistractionWarning () {
      console.warn('分心警告触发！');
      if (this.alertAudio && this.alertAudio.paused) {
        this.alertAudio.play(); // 播放音频
      }
    },

    clearDistraction () {
      console.log('用户已解除分心');
      this.isDistracted = false;
      this.distractedStartTime = null;
      if (this.alertAudio) {
        this.alertAudio.pause(); // 暂停播放音频
        this.alertAudio.currentTime = 0; // 重置音频播放位置
      }
    }
  }
}
</script>

<style>
/* 保持原有样式 */
#app {
  display: flex;
  height: 100vh;
  font-family: Arial, sans-serif;
  position: relative;
}

h2 {
  text-align: center;
  margin-bottom: 15px;
}

.nav-item {
  display: block;
  color: #ecf0f1;
  text-decoration: none;
  padding: 10px;
  margin: 5px 0;
  border-radius: 5px;
  transition: background 0.3s;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.status, .voice-command, .recognition-results {
  margin-top: 20px;
}

.status-active {
  color: #2ecc71;
}

.battery-level {
  color: #f39c12;
}

.current-time {
  font-weight: bold;
  color: #ecf0f1;
}

.vanta-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.sidebar {
  background-color: rgba(44, 62, 80, 0.8);
  color: #ecf0f1;
  padding: 20px;
  width: 250px;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.5);
  z-index: 2;
}

.content {
  flex: 1;
  padding: 20px;
  background-color: transparent;
  z-index: 2;
}
</style>
