<template>
  <div class="maintenance">
    <h1>车辆维护页面</h1>
    <p>欢迎进入车辆维护人员管理界面。以下是可用的功能：</p>
    <div class="maintenance-features">
      <div class="maintenance-feature-item">
        <h2>检查车辆状态</h2>
        <p>实时监控车辆状态，确保安全行驶。</p>
      </div>
      <div class="maintenance-feature-item">
        <h2>维护记录管理</h2>
        <p>管理所有的维护记录，方便查阅和跟踪。</p>
      </div>
    </div>
    <h2>车辆状态</h2>
    <div class="vehicle-status">
      <p>发动机状态: 正常</p>
      <p>轮胎压力: 正常</p>
      <p>电池健康: 良好</p>
    </div>
    <div class="generate-report-container">
      <button @click="generateReport" class="generate-report-button">生成维护报告</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Maintenance',
  methods: {
    generateReport () {
      alert('维护报告已生成！')
    }
  }
}
</script>

<style scoped>
.maintenance {
  text-align: center;
  color: #ecf0f1; /* 文字颜色 */
  padding: 20px;
  height: 100vh; /* 适配屏幕高度 */
  display: flex;
  flex-direction: column;
  justify-content: flex-start; /* 使内容上对齐 */
  background-color: transparent; /* 背景透明 */
}

h1 {
  font-size: 2em;
  margin: 0;
}

h2 {
  margin-top: 20px;
}

.maintenance-features {
  display: grid;
  grid-template-columns: repeat(2, 1fr); /* 两列布局 */
  gap: 20px; /* 卡片之间的间距 */
  margin-top: 20px;
}

.maintenance-feature-item {
  border: 2px solid #92cdf7; /* 蓝色边框 */
  border-radius: 10px;
  padding: 20px;
  background-color: rgba(52, 152, 219, 0.1); /* 半透明蓝色背景 */
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s, background-color 0.3s;
}

.maintenance-feature-item:hover {
  transform: translateY(-5px);
  background-color: rgba(52, 152, 219, 0.2); /* 悬停时加深蓝色背景 */
}

.vehicle-status {
  margin-top: 20px;
  padding: 10px;
  background: rgba(52, 152, 219, 0.3); /* 半透明背景 */
  border-radius: 5px;
}

.generate-report-button {
  margin-top: 20px;
  padding: 10px 20px;
  background-color: #3498db; /* 蓝色按钮背景色 */
  color: #ecf0f1; /* 按钮文本颜色 */
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.generate-report-button:hover {
  background-color: #2980b9; /* 悬停时蓝色按钮颜色 */
}
</style>
