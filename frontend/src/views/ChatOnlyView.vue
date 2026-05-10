<script setup lang="ts">
import ChatWidget from '@/components/ChatWidget.vue'

</script>

<template>
  <main class="chat-only-view">
    <ChatWidget
      mode="inplace"
      title="Lovely Chat"
      placeholder="Escribe tu mensaje"
    />
  </main>
</template>

<style scoped lang="sass">
.chat-only-view
  min-height: 100vh
  padding: 1.5rem
  display: flex
  align-items: stretch
  justify-content: center
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)

  :deep(.chat-widget)
    width: min(100%, 720px)

  :deep(.chat-panel--inline)
    width: 100%
    min-height: calc(100vh - 3rem)

@media (max-width: 768px)
  .chat-only-view
    padding: 0

    :deep(.chat-widget)
      width: 100%

    :deep(.chat-panel--inline)
      min-height: 100vh
      border-radius: 0
</style>
