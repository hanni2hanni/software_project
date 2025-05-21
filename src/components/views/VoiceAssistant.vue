<template>
  <div class="driver">
    <h1>语音助手页面</h1>
    <p>你好，我是你的车载语音助手。你可以通过说出“帮助”来获取指令列表。</p>
    <div class="assistant-panel">
      <h2>支持的语音指令：</h2>
      <ul class="command-list">
        <li>打开音乐</li>
        <li>打开导航</li>
        <li>已经注意道路</li>
      </ul>
      <button class="start-button" @click="toggleVoiceAssistant">
        {{ eventSource ? '停止语音识别' : '启动语音识别' }}
      </button>
      <p v-if="statusMessage" class="status">{{ statusMessage }}</p>
    </div>
    <div class="back-link-container">
      <router-link to="/" class="back-link">返回主页</router-link>
    </div>
  </div>
</template>


<script>
import axios from 'axios'

export default {
  name: 'VoiceAssistant',
  data () {
    return {
      statusMessage: '',
      eventSource: null
    }
  },
  methods: {
    async toggleVoiceAssistant () {
      if (this.eventSource) {
        // 如果正在运行，就停止
        await this.stopVoiceAssistant()
      } else {
        // 否则就启动
        await this.startVoiceAssistant()
      }
    },

    async startVoiceAssistant () {
      this.statusMessage = '正在启动语音助手...'
      try {
        const response = await axios.get('http://localhost:5000/api/start-voice')
        this.statusMessage = response.data.message || '语音助手已启动'

        this.eventSource = new EventSource('http://localhost:5000/api/stream')
        this.eventSource.onmessage = (event) => {
          this.statusMessage = event.data
          console.log('SSE:', event.data)
        }

        this.eventSource.onerror = (err) => {
          console.error('SSE连接错误:', err)
          this.statusMessage = '连接语音状态服务失败'
          this.eventSource.close()
          this.eventSource = null
        }
      } catch (error) {
        console.error('语音助手启动失败:', error)
        this.statusMessage = '启动语音助手失败，请检查连接。'
      }
    },

    async stopVoiceAssistant () {
      this.statusMessage = '正在停止语音助手...'
      try {
        await axios.get('http://localhost:5000/api/stop-voice')
        this.statusMessage = '语音助手已停止'
      } catch (error) {
        console.error('停止失败:', error)
        this.statusMessage = '停止语音助手失败'
      }

      if (this.eventSource) {
        this.eventSource.close()
        this.eventSource = null
      }
    }
  },
  beforeDestroy () {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
  }
}
</script>


<style scoped>
.driver {
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

.command-list {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 0;
  margin: 20px 0;
  list-style: none;
}

.command-list li {
  padding: 10px 20px;
  border: 2px solid #60aade;
  border-radius: 8px;
  background-color: rgba(96, 173, 222, 0.15);
  color: #ecf0f1;
  font-weight: bold;
  transition: background-color 0.3s, transform 0.2s;
}

.command-list li:hover {
  background-color: #60aade;
  transform: translateY(-3px);
  color: #fff;
}

.start-button {
  padding: 10px 20px;
  background-color: #3498db;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.start-button:hover {
  background-color: #2780ba;
}

.status {
  margin-top: 15px;
  font-style: italic;
  color: #f1c40f;
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
