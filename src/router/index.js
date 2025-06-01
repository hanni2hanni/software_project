import Vue from 'vue'
import Router from 'vue-router'
import Home from '../components/views/Home.vue'
import Login from '../components/views/Login.vue'
import Driver from '../components/views/Driver.vue'
import Admin from '../components/views/Admin.vue'
import Maintenance from '../components/views/Maintenance.vue'
import Navigation from '../components/views/Navigation.vue'
import VoiceAssistant from '../components/views/VoiceAssistant.vue'
import GestureRecognition from '../components/views/GestureRecognition.vue'
import EyeTracking from '../components/views/EyeTracking.vue'

import UserManagement from '../components/views/UserManagement.vue'
import UserDetail from '../components/views/UserDetail.vue'
import SystemLogs from '../components/views/SystemLogs.vue'
import SystemSettings from '../components/views/SystemSettings.vue'

import store from '../store'

Vue.use(Router)

const router = new Router({
  mode: 'history', // 使用 history 模式以去掉 URL 中的 hash (#)
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home
    },
    {
      path: '/driver',
      name: 'Driver',
      component: Driver,
      meta: { requiresRole: 'driver' } // 需要驾驶员角色
    },
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/admin',
      name: 'Admin',
      component: Admin,
      meta: { requiresRole: 'system_administrator' } // 需要管理员角色
    },
    {
      path: '/user-management',
      name: 'UserManagement',
      component: UserManagement
    },
    {
      path: '/user-detail/:id',
      name: 'UserDetail',
      component: UserDetail
    },
    {
      path: '/system-settings',
      name: 'SystemSettings',
      component: SystemSettings
    },
    {
      path: '/system-logs',
      name: 'SystemLogs',
      component: SystemLogs
    },
    {
      path: '/maintenance',
      name: 'Maintenance',
      component: Maintenance,
      meta: { requiresRole: 'vehicle_maintenance' } // 需要维护人员角色
    },
    {
      path: '/voice-assistant',
      name: 'VoiceAssistant',
      component: VoiceAssistant
    },
    {
      path: '/gesture-recognition',
      name: 'GestureRecognition',
      component: GestureRecognition
    },
    {
      path: '/eye-tracking',
      name: 'EyeTracking',
      component: EyeTracking
    },
    {
      path: '/navigation',
      name: 'Navigation',
      component: Navigation
    }
  ]
})

// 全局前置守卫
router.beforeEach((to, from, next) => {
  const isLoggedIn = store.getters.isLoggedIn // 获取登录状态
  const userRole = store.getters.userRole // 获取用户角色

  // 如果要访问的路由不是登录页且用户未登录
  if (to.name !== 'Login' && !isLoggedIn) {
    next({ name: 'Login' }) // 重定向到登录页
  } else if (to.meta.requiresRole && to.meta.requiresRole !== userRole) {
    next({ name: 'Home' }) // 如果角色不匹配，重定向到主页
  } else {
    next() // 继续路由
  }
})

export default router
