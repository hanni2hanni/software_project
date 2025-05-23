<template>
  <div class="driver">
    <h1>驾驶员页面</h1>
    <p>欢迎回来，驾驶员！请查看以下功能：</p>
    <div class="features">
      <div class="feature-item large-item">
        <h2>实时导航</h2>
        <p>获取实时导航信息，帮助您安全到达目的地。</p>
        <router-link to="/navigation" class="feature-link">开始导航</router-link>
      </div>
      <div class="feature-item small-item">
        <h2>车辆状态监控</h2>
        <p>随时查看车辆的状态，包括油量、温度和电池健康。</p>
        <router-link to="/vehicle-status" class="feature-link">查看状态</router-link>
      </div>
      <div class="feature-item small-item">
        <h2>语音助手</h2>
        <p>使用语音助手发出指令，控制车载系统。</p>
        <router-link to="/voice-assistant" class="feature-link">启动助手</router-link>
      </div>
      <div class="feature-item small-item">
        <h2>智能手势识别</h2>
        <p>通过手势与系统实现快速交互，自动完成任务。</p>
        <router-link to="/gesture-recognition" class="feature-link">体验功能</router-link>
      </div>
      <div class="feature-item small-item">
        <h2>视觉识别</h2>
        <p>实时监测驾驶员头部姿态和目光集中区域，给予安全驾驶提示。</p>
        <router-link to="/eye-tracking" class="feature-link">开启识别</router-link>
      </div>
    </div>
    <div class="back-link-container">
      <router-link to="/" class="back-link">返回主页</router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Driver',
};
</script>

<style scoped>
.driver {
  text-align: center;
  padding: 20px;
  color: #ecf0f1; /* 文字颜色 */
  height: 0vh; /* 适配屏幕高度 */
  display: flex;
  flex-direction: column;
  justify-content: flex-start; /* 使内容上对齐 */
  background-color: transparent; /* 背景透明 */
}

h1 {
  margin: 0; /* 去掉默认的间距 */
}

.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr); /* 三列布局 */
  gap: 20px; /* 卡片之间的间距 */
  margin-top: 20px;
}

.feature-item {
  border: 2px solid #92cdf7; /* 与 App.vue 风格一致 */
  border-radius: 10px;
  padding: 20px;
  background-color: rgba(52, 152, 219, 0.1); /* 半透明背景 */
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s, background-color 0.3s;
}

.large-item {
  grid-column: span 2; /* 大卡片占用两列 */
}

.feature-item:hover {
  transform: translateY(-5px);
  background-color: rgba(255, 255, 255, 0.1); /* 悬停时加深背景 */
}

.feature-link {
  display: inline-block;
  margin-top: 10px;
  padding: 10px 15px;
  color: #fff;
  background-color: #3498db; /* 按钮背景色 */
  border-radius: 5px;
  text-decoration: none;
  transition: background-color 0.3s, transform 0.2s;
}

.feature-link:hover {
  background-color: #2780ba; /* 悬停时按钮颜色 */
  transform: scale(1.05); /* 悬停时放大按钮 */
}

.back-link-container {
  margin-top: 20px; /* 顶部间距 */
}

.back-link {
  display: inline-block;
  margin-top: 20px;
  color: #ecf0f1;
  text-decoration: none;
  padding: 10px 15px;
  border: 1px solid #60aade;
  border-radius: 5px;
  transition: background-color 0.3s, color 0.3s;
}

.back-link:hover {
  background-color: #60aade; /* 背景色 */
  color: #fff; /* 字体颜色 */
}
</style>
