import { createRouter, createWebHistory } from 'vue-router'
import ChatOnlyView from '@/views/ChatOnlyView.vue'
import PlaygroundView from '@/views/PlaygroundView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'playground',
      component: PlaygroundView,
    },
    {
      path: '/chat',
      name: 'chat-only',
      component: ChatOnlyView,
    },
  ],
})

export default router
