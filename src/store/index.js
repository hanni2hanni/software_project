import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    isLoggedIn: false, // 用户登录状态
    userRole: null // 用户角色
  },
  mutations: {
    setLogin (state, payload) {
      state.isLoggedIn = payload
    },
    setUserRole (state, role) {
      state.userRole = role // 设置用户角色
    }
  },
  actions: {
    async login ({ commit }, { username, password }) {
      // 模拟用户数据（实际项目中应该从后端获取）
      const mockUsers = [
        { username: 'admin', password: 'password', role: 'admin' },
        { username: 'driver', password: 'password', role: 'driver' },
        { username: 'maintenance', password: 'password', role: 'maintenance' },
        { username: 'passenger', password: 'password', role: 'passenger' }
      ]

      // 查找匹配的用户
      const user = mockUsers.find(
        (u) => u.username === username && u.password === password
      )

      if (user) {
        commit('setLogin', true) // 登录成功
        commit('setUserRole', user.role) // 设置用户角色
      } else {
        throw new Error('用户名或密码错误')
      }
    },
    logout ({ commit }) {
      commit('setLogin', false) // 退出登录
      commit('setUserRole', null) // 清除用户角色
    }
  },
  getters: {
    isLoggedIn: (state) => state.isLoggedIn, // 返回登录状态
    userRole: (state) => state.userRole // 返回用户角色
  }
})
