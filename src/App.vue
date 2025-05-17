<template>
  <div id="app">
    <div ref="vantaRef" class="vanta-background"></div>
    <div class="sidebar">
      <h2>智能交互系统</h2>
      <div class="gesture-display">
        <h2>当前手势: {{ currentGesture }}</h2>
      </div>
      <nav>
        <router-link to="/" class="nav-item">主页</router-link>
        <router-link to="/driver" class="nav-item">驾驶员功能</router-link>
        <router-link to="/admin" class="nav-item">系统管理</router-link>
        <router-link to="/maintenance" class="nav-item">车辆维护</router-link>
      </nav>
      <div class="status">
        <h3>系统状态</h3>
        <p>当前状态: <span class="status-active">在线</span></p>
        <p>电池电量: <span class="battery-level">75%</span></p>
      </div>
      <div class="voice-command">
        <h3>语音指令</h3>
        <p>说出 "帮助" 获取指令列表。</p>
      </div>
      <div class="music-player">
        <h3>音乐播放</h3>
        <audio ref="audio" :src="musicSrc" @ended="onEnded" preload="auto" />
        <button @click="playMusic">{{ isPlaying ? '暂停' : '播放' }}</button>
      </div>
    </div>
    <div class="content">
      <router-view />
    </div>
  </div>
</template>

<script>
import * as THREE from 'three';
import VANTA from 'vanta/src/vanta.net'; // 导入 Vanta
import axios from 'axios';
import music from '@/assets/music.mp3';

export default {
  name: 'App',
  data() {
    return {
      isPlaying: false,
      musicSrc: music,
      currentGesture: '无手势',
      vantaEffect: null // 存储 Vanta.js 实例
    };
  },
  mounted() {
    this.initVanta(); // 初始化 Vanta.js 背景效果
    this.fetchGesture();
    setInterval(this.fetchGesture, 2000);
  },
  beforeDestroy() {
    if (this.vantaEffect) {
      this.vantaEffect.destroy(); // 销毁 Vanta.js 实例以防内存泄漏
    }
  },
  methods: {
    initVanta() {
      this.vantaEffect = VANTA({
        el: this.$refs.vantaRef,
        THREE: THREE,
        mouseControls: true,
        touchControls: true,
        gyroControls: false,
        minHeight: 200.00,
        minWidth: 200.00,
        scale: 1.00,
        scaleMobile: 1.00,
        color: 0x3b7dae,
        backgroundColor: 0x1d1e44,
        spacing: 12.00
      });
    },
    playMusic() {
      const audio = this.$refs.audio;
      if (!audio) {
        console.error("Audio element not found");
        return;
      }
      
      if (this.isPlaying) {
        audio.pause();
      } else {
        audio.play().catch(error => {
          console.error("Error playing audio:", error);
        });
      }
      this.isPlaying = !this.isPlaying;
    },
    onEnded() {
      this.isPlaying = false;
    },
    async fetchGesture() {
      try {
        const response = await axios.get('http://localhost:5000/api/gesture');
        this.currentGesture = response.data.gesture;
        this.handleGesture(response.data.gesture);
      } catch (error) {
        console.error('Error fetching gesture:', error);
      }
    },
    handleGesture(gesture) {
      switch (gesture) {
        case '握拳':
          this.pauseMusic();
          break;
        case '竖拇指':
          // 处理竖拇指手势的逻辑
          break;
        case '挥手':
          // 处理挥手手势的逻辑
          break;
        default:
          console.log('无手势');
      }
    },
    pauseMusic() {
      const audio = this.$refs.audio;
      if (this.isPlaying) {
        audio.pause();
        this.isPlaying = false;
      }
    },
  },
};
</script>

<style>
#app {
  display: flex;
  height: 100vh;
  font-family: Arial, sans-serif;
  position: relative; /* 使绝对定位生效 */
}

h2 {
  text-align: center;
  margin-bottom: 20px; /* 标题底部间距 */
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

.status, .voice-command {
  margin-top: 20px; /* 顶部间距 */
}

.status-active {
  color: #2ecc71; /* 在线状态颜色 */
}

.battery-level {
  color: #f39c12; /* 电池电量颜色 */
}

.music-player {
  margin-top: 20px; /* 顶部间距 */
}

.music-player h3 {
  margin-bottom: 10px; /* 标题底部间距 */
}

.music-player button {
  background-color: #3498db; /* 按钮背景色 */
  color: #ffffff; /* 按钮文字颜色 */
  border: none; /* 去掉边框 */
  padding: 8px 16px; /* 内边距 */
  font-size: 14px; /* 字体大小 */
  border-radius: 5px; /* 圆角效果 */
  cursor: pointer; /* 鼠标悬停时显示手型 */
  transition: background-color 0.3s, transform 0.2s; /* 过渡效果 */
}

.music-player button:hover {
  background-color: #2980b9; /* 悬停时背景色 */
}

.music-player button:active {
  transform: scale(0.95); /* 点击时按钮缩小 */
}

.music-player button:focus {
  outline: none; /* 去掉焦点时的默认边框 */
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
