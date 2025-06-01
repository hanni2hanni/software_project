<template>
  <div class="detail-container" v-if="userData">
    <h1>用户详情: {{ userId }}</h1>

    <div class="features">
      <div class="feature-item small-item">
        <h2 class="section-title">基本信息</h2>
        <div class="section-content">
          <p><strong class="label">姓名:</strong> <span class="content">{{ userData.name }}</span></p>
          <p><strong class="label">角色:</strong> <span class="content">{{ userData.role }}</span></p>
        </div>
      </div>

      <div class="feature-item small-item">
        <h2 class="section-title">常用指令</h2>
        <div class="section-content">
          <template v-if="userData.common_commands && Object.keys(userData.common_commands).length > 0">
            <ul>
              <li v-for="(cmd, key) in userData.common_commands" :key="key">
                <strong class="label">{{ key }}:</strong> <span class="content">{{ cmd }}</span>
              </li>
            </ul>
          </template>
          <template v-else><span class="no-content">无</span></template>
        </div>
      </div>

      <div class="feature-item small-item">
        <h2 class="section-title">交互习惯</h2>
        <div class="section-content">
          <template v-if="userData.interaction_habits && Object.keys(userData.interaction_habits).length > 0">
            <ul>
              <li v-for="(habit, key) in userData.interaction_habits" :key="key">
                <strong class="label">{{ key }}:</strong> <span class="content">{{ habit }}</span>
              </li>
            </ul>
          </template>
          <template v-else><span class="no-content">无</span></template>
        </div>
      </div>

      <div class="feature-item feedback-item">
        <h2 @click="toggleFeedback" class="section-title toggle-header">
          反馈偏好
          <span class="arrow">{{ isFeedbackExpanded ? '▲' : '▼' }}</span>
        </h2>
        <transition name="fade">
          <div v-show="isFeedbackExpanded" class="feedback-content">
            <template v-if="userData.feedback_preferences">
              <div class="feedback-grid">
                <div v-for="(pref, key) in userData.feedback_preferences" :key="key" class="feedback-subitem">
                  <h3 class="sub-section-title">{{ translateFeedbackKey(key) }}</h3>
                  <ul v-if="typeof pref === 'object'">
                    <li v-for="(val, subKey) in pref" :key="subKey">
                      <strong class="label">{{ translateFeedbackSubKey(subKey) }}:</strong>
                      <span class="content" v-if="Array.isArray(val)">{{ val.join('，') }}</span>
                      <span class="content" v-else>{{ val.toString() }}</span>
                    </li>
                  </ul>
                  <p v-else class="content">{{ pref.toString() }}</p>
                </div>
              </div>
            </template>
            <template v-else><span class="no-content">无</span></template>
          </div>
        </transition>
      </div>
    </div>
    <div class="back-link-container">
      <button @click="$router.back()" class="back-link">返回上一页</button>
    </div>
  </div>

  <div v-else class="loading">
    <p>加载用户数据中...</p>
  </div>

</template>

<script>
export default {
  name: 'UserDetail',
  data () {
    return {
      userData: null,
      userId: this.$route.params.id,
      isFeedbackExpanded: false
    }
  },
  mounted () {
    this.fetchUserData()
  },
  methods: {
    fetchUserData () {
      fetch(`http://localhost:5000/user/${this.userId}`)
        .then(response => {
          if (!response.ok) throw new Error('用户不存在或请求失败')
          return response.json()
        })
        .then(data => {
          this.userData = data
        })
        .catch(err => {
          console.error(err)
          this.userData = null
        })
    },
    toggleFeedback () {
      this.isFeedbackExpanded = !this.isFeedbackExpanded
    },
    translateFeedbackKey (key) {
      const map = {
        COMMAND_FAILURE: '命令失败',
        COMMAND_SUCCESS: '命令成功',
        GENERIC_INFO: '通用信息',
        PERMISSION_DENIED: '权限拒绝',
        USER_DISTRACTED: '用户分心',
        disable_all_audio_feedback: '禁用所有音频反馈',
        general_voice_volume: '语音音量',
        visual_animation_enabled: '视觉动画启用',
        visual_graphic_feedback_enabled: '视觉图形反馈启用'
      }
      return map[key] || key
    },
    translateFeedbackSubKey (subKey) {
      const map = {
        enabled_modalities: '启用的模态',
        voice_detail_level: '语音详细等级',
        text_display_enabled: '文本显示启用'
      }
      return map[subKey] || subKey
    }
  }
}
</script>

<style scoped>
.detail-container {
  text-align: center;
  padding: 20px;
  color: #ecf0f1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  background-color: transparent;
}

h1 {
  margin: 0;
  font-size: 24px;
}

.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 20px;
  align-items: stretch; /* 确保卡片高度一致 */
}

.feature-item {
  border: 2px solid #92cdf7;
  border-radius: 10px;
  padding: 20px;
  background-color: rgba(52, 152, 219, 0.1);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s, background-color 0.3s;
  display: flex;
  flex-direction: column;
}

.feature-item:hover {
  transform: translateY(-5px);
  background-color: rgba(255, 255, 255, 0.1);
}

.small-item {
  min-height: 150px; /* 确保卡片高度一致 */
}

.feedback-item {
  grid-column: 1 / 4; /* 占据整个网格宽度 */
  width: 100%; /* 确保与上面三个卡片总宽度对齐 */
}

.section-title {
  margin: 0 0 10px;
  font-size: 18px;
  font-weight: bold;
  color: #ffffff;
  background-color: rgba(41, 128, 185, 0.4);
  padding: 8px 12px;
  border-radius: 5px;
}

.sub-section-title {
  font-size: 16px;
  font-weight: bold;
  color: #ffffff;
  background-color: rgba(41, 128, 185, 0.3);
  padding: 6px 10px;
  border-radius: 5px;
  margin-bottom: 8px;
}

.section-content {
  text-align: left;
  flex-grow: 1; /* 确保内容填充卡片 */
}

.feedback-content {
  text-align: left;
}

.feedback-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); /* 自动调整为2-3列 */
  gap: 15px;
}

.feedback-subitem {
  background-color: rgba(255, 255, 255, 0.05);
  padding: 10px;
  border-radius: 5px;
}

.label {
  color: #92cdf7;
  font-weight: bold;
}

.content {
  color: #ecf0f1;
  font-weight: normal;
  background-color: rgba(255, 255, 255, 0.05);
  padding: 2px 5px;
  border-radius: 3px;
}

.no-content {
  color: #b0bec5;
  font-style: italic;
  background-color: rgba(255, 255, 255, 0.03);
  padding: 2px 5px;
  border-radius: 3px;
  display: inline-block;
}

.toggle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.arrow {
  font-size: 18px;
  color: #ecf0f1;
}

ul {
  list-style-type: none;
  padding-left: 0;
  margin: 0;
}

li {
  margin-bottom: 6px;
}

.back-link-container {
  margin-top: 20px;
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

.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

.loading {
  color: #ecf0f1;
  text-align: center;
  margin-top: 100px;
  font-size: 18px;
}
</style>
