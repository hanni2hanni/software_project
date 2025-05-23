import Vue from 'vue'
import Router from 'vue-router'
import Home from '../components/views/Home.vue';
import Driver from '../components/views/Driver.vue';
import Admin from '../components/views/Admin.vue';
import Maintenance from '../components/views/Maintenance.vue';
import VoiceAssistant from '../components/views/VoiceAssistant.vue'
import GestureRecognition from '../components/views/GestureRecognition.vue'
import EyeTracking from '../components/views/EyeTracking.vue'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home,
    },
    {
      path: '/driver',
      name: 'Driver',
      component: Driver,
    },
    {
      path: '/admin',
      name: 'Admin',
      component: Admin,
    },
    {
      path: '/maintenance',
      name: 'Maintenance',
      component: Maintenance,
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
    }
  ],
});
