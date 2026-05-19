import { createRouter, createWebHistory } from 'vue-router'
import ChatOnlyView from '@/views/ChatOnlyView.vue'
import ChatView from '@/views/ChatView.vue'
import CvAssistantView from '@/views/CvAssistantView.vue'
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
    {
      path: '/superchat',
      name: 'super-chat',
      component: ChatView,
    },
    {
      path: '/cv-assistant',
      name: 'cv-assistant',
      component: CvAssistantView,
    },
  ],
})

export default router
