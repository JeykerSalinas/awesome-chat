import type { ChatMessage } from '@/components/ChatWidget.vue';

export const mockConversation: ChatMessage[] = [
  {
    id: '1',
    author: 'assistant',
    content: '¡Hola! Soy Lovely Chat. ¿En qué puedo ayudarte hoy?',
    timestamp: '2024-05-14T12:00:00.000Z',
  },
  {
    id: '2',
    author: 'user',
    content: 'Necesito más información sobre su plan premium.',
    timestamp: '2024-05-14T12:00:10.000Z',
  },
  {
    id: '3',
    author: 'assistant',
    content: 'El plan premium incluye soporte prioritario y analíticas avanzadas.',
    timestamp: '2024-05-14T12:00:20.000Z',
  },
  {
    id: '4',
    author: 'assistant',
    content: '¿Quieres que te envíe un resumen por correo?',
    timestamp: '2024-05-14T12:00:25.000Z',
  },
];

export const followUps = [
  'Sí, por favor envíalo a mi correo.',
  '¿Cuál es el tiempo de respuesta promedio?',
  'Quiero hablar con un agente humano.',
];
