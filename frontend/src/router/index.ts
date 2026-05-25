import { createRouter, createWebHistory } from 'vue-router'
import ChatOnlyView from '@/views/ChatOnlyView.vue'
import ChatView from '@/views/ChatView.vue'
import CvAssistantView from '@/views/CvAssistantView.vue'
import PlaygroundView from '@/views/PlaygroundView.vue'
import RagSystemManagement from '@/views/RagSystemManagement.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'playground',
      component: PlaygroundView,
      meta: {
        menuLabel: 'Playground',
        visibleInMenu: true,
        menuOrder: 1,
      },
    },
    {
      path: '/chat',
      name: 'chat-only',
      component: ChatOnlyView,
      meta: {
        menuLabel: 'Chat',
        visibleInMenu: true,
        menuOrder: 2,
      },
    },
    {
      path: '/superchat',
      name: 'super-chat',
      component: ChatView,
      meta: {
        menuLabel: 'Super Chat',
        visibleInMenu: true,
        menuOrder: 3,
      },
    },
    {
      path: '/cv-assistant',
      name: 'cv-assistant',
      component: CvAssistantView,
      meta: {
        menuLabel: 'CV Assistant',
        visibleInMenu: true,
        menuOrder: 4,
      },
    },
    {
      path: '/rag-system',
      name: 'rag-system',
      component: RagSystemManagement,
      meta: {
        menuLabel: 'RAG Management',
        visibleInMenu: true,
        menuOrder: 5,
      },
    },
  ],
})

export default router
