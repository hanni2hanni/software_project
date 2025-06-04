import axios from 'axios'
import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    isLoggedIn: false, // 用户登录状态
    userRole: null, // 用户角色
    username: null, // 用户名
    recognitionData: null // 存储多模态识别数据
  },
  mutations: {
    setLogin (state, payload) {
      state.isLoggedIn = payload
    },
    setUserRole (state, role) {
      state.userRole = role // 设置用户角色
    },
    setUsername (state, name) {
      state.username = name // 设置用户名
    },
    setRecognitionData (state, data) {
      state.recognitionData = data // 设置多模态识别数据
    }
  },
  actions: {
    async login ({ commit }, { username, password }) {
      try {
        const response = await axios.post('http://localhost:5000/login', { username, password })
        commit('setLogin', true) // 登录成功
        commit('setUserRole', response.data.role) // 设置用户角色
        commit('setUsername', response.data.name) // 设置用户名
        // 如果需要在登录时获取多模态识别结果，可以在这里调用
        // await dispatch('fetchRecognitionResults'); // 可选
      } catch (error) {
        // 捕获错误并抛出以供前端处理
        if (error.response) {
          throw new Error(error.response.data.error || '登录失败')
        } else {
          throw new Error('登录请求失败')
        }
      }
    },
    logout ({ commit }) {
      commit('setLogin', false) // 退出登录
      commit('setUserRole', null) // 清除用户角色
      commit('setUsername', null) // 清除用户名
      commit('setRecognitionData', null); // 清除识别数据
    },
    async fetchRecognitionResults({ commit }) {
      try {
        const response = await axios.get('http://localhost:5002/api/recognition');
        commit('setRecognitionData', response.data); // 保存识别结果
      } catch (error) {
        console.error('获取识别结果时出错:', error);
      }
    }
  },
  getters: {
    isLoggedIn: (state) => state.isLoggedIn,
    userRole: (state) => state.userRole,
    username: (state) => state.username,
    recognitionData: (state) => state.recognitionData // 获取识别数据
  }
})
