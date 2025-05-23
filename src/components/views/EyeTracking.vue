<template>
  <div class="gaze-tracking">
    <h1>视觉识别页面</h1>
    <p>你好，我是你的车载视觉识别助手。你可以通过目光和头部动作控制车辆功能。</p>
    <div class="assistant-panel">
      <h2>当前目光状态：</h2>
      <p class="gaze-status">{{ gazeStatus }}</p>
    </div>
    <div class="head-movement-panel">
      <h2>当前头部运动状态：</h2>
      <p class="head-movement-status">{{ headMovementStatus }}</p>
    </div>
    <p class="instruction">请确保您的摄像头正常工作，并注意观察系统的反馈。</p>
    <div class="back-link-container">
      <router-link to="/driver" class="back-link">返回驾驶员页面</router-link>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'GazeTracking',
  data() {
    return {
      gazeStatus: '加载中...',          // 更新目光状态
      headMovementStatus: '加载中...'   // 新增头部运动状态
    };
  },
  mounted() {
    this.fetchEyeTracking();           // 初始化获取目光追踪状态
    this.fetchHeadMovement();          // 初始化获取头部运动状态
    setInterval(this.fetchEyeTracking, 500);  // 每0.5秒获取一次目光状态
    setInterval(this.fetchHeadMovement, 500); // 每0.5秒获取一次头部运动状态
  },
  methods: {
    async fetchEyeTracking() {
      try {
        const response = await axios.get('http://localhost:5000/api/eye-tracking');
        this.gazeStatus = response.data['eye-tracking']; // 更新目光状态
        console.log('Gaze tracking data:', response.data);
      } catch (error) {
        console.error('Error fetching gaze tracking data:', error);
      }
    },
    async fetchHeadMovement() {
      try {
        const response = await axios.get('http://localhost:5000/api/head-movement');
        this.headMovementStatus = response.data['head_movement']; // 更新头部运动状态
        console.log('Head movement data:', response.data);
      } catch (error) {
        console.error('Error fetching head movement data:', error);
      }
    },
  },
};
</script>

<style scoped>
.gaze-tracking {
  text-align: center;
  padding: 20px;
  color: #ecf0f1;
}

.assistant-panel, .head-movement-panel {
  margin-top: 20px;
  border: 2px solid #92cdf7;
  border-radius: 10px;
  padding: 20px;
  background-color: rgba(52, 152, 219, 0.1);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}

.gaze-status, .head-movement-status {
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
