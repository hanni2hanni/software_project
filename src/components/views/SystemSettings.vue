<template>
  <div class="system-settings">
    <h1>系统设置</h1>
    <p>调整系统参数以优化车载多模态交互体验。</p>

    <div class="settings-grid">
      <div class="setting-item">
        <h2>性能模式</h2>
        <select v-model="settings.performanceMode">
          <option value="normal">正常</option>
          <option value="power-saving">节能</option>
          <option value="high-performance">高性能</option>
        </select>
      </div>

      <div class="setting-item">
        <h2>语音识别灵敏度</h2>
        <input type="range" min="1" max="10" v-model="settings.voiceSensitivity" />
        <span>{{ settings.voiceSensitivity }}</span>
      </div>

      <div class="setting-item">
        <h2>手势识别开关</h2>
        <input type="checkbox" v-model="settings.gestureRecognitionEnabled" />
      </div>

      <div class="setting-item">
        <h2>视觉识别开关</h2>
        <input type="checkbox" v-model="settings.visualRecognitionEnabled" />
      </div>

      <div class="setting-item">
        <h2>通知提醒</h2>
        <input type="checkbox" v-model="settings.notificationsEnabled" />
      </div>

      <div class="setting-item">
        <h2>音量调节</h2>
        <input type="range" min="0" max="100" v-model="settings.volumeLevel" />
        <span>{{ settings.volumeLevel }}%</span>
      </div>

      <div class="setting-item">
        <h2>驾驶模式定制</h2>
        <div class="checkbox-group">
          <label><input type="checkbox" v-model="settings.customModes.voiceFeedback" /> 语音反馈</label>
          <label><input type="checkbox" v-model="settings.customModes.visualFeedback" /> 视觉反馈</label>
          <label><input type="checkbox" v-model="settings.customModes.hapticFeedback" /> 手势反馈</label>
        </div>
      </div>

      <div class="setting-item">
        <h2>自动更新开关</h2>
        <input type="checkbox" v-model="settings.autoUpdateEnabled" />
      </div>
    </div>

    <button @click="saveSettings">保存设置</button>
    <button @click="analyzePreferences" class="analysis-button">用户偏好分析</button>
    <div class="back-link-container">
      <router-link to="/admin" class="back-link">返回上一页</router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SystemSettings',
  data () {
    return {
      settings: {
        performanceMode: 'normal',
        voiceSensitivity: 5,
        gestureRecognitionEnabled: true,
        visualRecognitionEnabled: true,
        notificationsEnabled: true,
        volumeLevel: 50,
        customModes: {
          voiceFeedback: true,
          visualFeedback: true,
          hapticFeedback: false
        },
        autoUpdateEnabled: false
      }
    }
  },
  methods: {
    saveSettings () {
      this.$message({
        message: '设置已保存！',
        type: 'success',
        duration: 2000
      })
    },
    analyzePreferences () {
      this.$message({
        message: '正在分析用户偏好，请稍候...',
        type: 'info',
        duration: 2000
      })

      setTimeout(() => {
        this.$message({
          message: '用户偏好分析报告已生成！',
          type: 'success',
          duration: 3000
        })
      }, 2000)
    }
  }
}
</script>

<style scoped>
.system-settings {
  text-align: center;
  padding: 15px;
  color: #ecf0f1;
  background-color: transparent;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

h1 {
  margin-bottom: 10px;
  font-size: 24px;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 20px 0;
}

.setting-item {
  border: 1.5px solid #92cdf7;
  border-radius: 8px;
  padding: 12px 10px;
  background-color: rgba(52, 152, 219, 0.12);
  box-shadow: 0 3px 7px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s, background-color 0.2s;
  color: #ecf0f1;
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 110px;
}

.setting-item:hover {
  transform: translateY(-3px);
  background-color: rgba(255, 255, 255, 0.1);
}

.setting-item h2 {
  margin: 0 0 8px 0;
  font-size: 16px;
}

select,
input[type="range"] {
  width: 80%;
  border-radius: 4px;
  border: 1px solid #60aade;
  background-color: #1e3a5f;
  color: #ecf0f1;
  padding: 4px;
  margin-bottom: 6px;
  cursor: pointer;
}

input[type="checkbox"] {
  transform: scale(1.2);
  margin-left: 8px;
  cursor: pointer;
}

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
}

.checkbox-group label {
  cursor: pointer;
  user-select: none;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
}

button {
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 10px 28px;
  font-size: 15px;
  cursor: pointer;
  transition: background-color 0.3s;
  align-self: center;
  margin-top: 15px;
  width: 180px;
}

button:hover {
  background-color: #2780ba;
}

.analysis-button {
  padding: 10px 20px;
  background-color: #3498db;
  border: none;
  border-radius: 5px;
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.analysis-button:hover {
  background-color: #2780ba;
}

.back-link-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;  /* 居中对齐 */
  width: 100%;
  padding-left: 0; /* 去掉多余的左内边距 */
}

.back-link {
  display: inline-block;
  padding: 10px 15px;
  color: #ecf0f1;
  background-color: #3498db;
  border: 1px solid #60aade;
  border-radius: 5px;
  text-decoration: none;
  cursor: pointer;
  transition: background-color 0.3s, transform 0.2s, color 0.3s;
}

.back-link:hover {
  background-color: #60aade;
  color: #fff;
  transform: scale(1.05);
}
</style>
