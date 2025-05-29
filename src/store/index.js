import axios from 'axios';
import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    isLoggedIn: false, // 用户登录状态
    userRole: null, // 用户角色
    username: null // 用户名
  },
  mutations: {
    setLogin(state, payload) {
      state.isLoggedIn = payload;
    },
    setUserRole(state, role) {
      state.userRole = role; // 设置用户角色
    },
    setUsername(state, name) {
      state.username = name; // 设置用户名
    }
  },
  actions: {
    async login({ commit }, { username, password }) {
      try {
        const response = await axios.post('http://localhost:5000/login', { username, password });
        commit('setLogin', true); // 登录成功
        commit('setUserRole', response.data.role); // 设置用户角色
        commit('setUsername', response.data.name); // 设置用户名
      } catch (error) {
        // 捕获错误并抛出以供前端处理
        if (error.response) {
          throw new Error(error.response.data.error || '登录失败');
        } else {
          throw new Error('登录请求失败');
        }
      }
    },
    logout({ commit }) {
      commit('setLogin', false); // 退出登录
      commit('setUserRole', null); // 清除用户角色
      commit('setUsername', null); // 清除用户名
    }
  },
  getters: {
    isLoggedIn: (state) => state.isLoggedIn,
    userRole: (state) => state.userRole,
    username: (state) => state.username // 新增 getter
  }
});
