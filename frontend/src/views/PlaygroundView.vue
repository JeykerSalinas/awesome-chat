<script setup lang="ts">
import { computed, ref } from 'vue'
import ChatWidget from '@/components/ChatWidget.vue'
import { followUps, mockConversation } from '@/mocks/chatData'

type ModeOption = {
  value: 'floating' | 'modal' | 'inplace' | 'assistant'
  label: string
  description: string
}

const modes: ModeOption[] = [
  {
    value: 'floating',
    label: 'Floating button',
    description:
      'Botón flotante que abre un chat emergente en la esquina inferior derecha.',
  },
  {
    value: 'modal',
    label: 'Modal',
    description: 'Botón flotante que despliega un modal centrado con overlay.',
  },
  {
    value: 'inplace',
    label: 'In place',
    description: 'Bloque embebido que se integra al flujo normal del contenido.',
  },
  {
    value: 'assistant',
    label: 'Assistant',
    description: 'Panel lateral fijo en el lado izquierdo del viewport.',
  },
]

const activeMode = ref<ModeOption['value']>('inplace')

const activeDescription = computed(() => {
  return modes.find((mode) => mode.value === activeMode.value)?.description ?? ''
})
</script>

<template>
  <main class="app-layout">
    <header class="hero">
      <h1>Lovely Chat playground</h1>
      <p>
        Selecciona una modalidad para previsualizar el componente de chat y simular una
        conversación con datos mockeados.
      </p>
    </header>

    <section class="controls">
      <label
        class="controls__label"
        for="chat-mode"
      >
        Modo de chat
      </label>
      <select
        id="chat-mode"
        v-model="activeMode"
        class="controls__select"
        data-testid="mode-select"
      >
        <option
          v-for="mode in modes"
          :key="mode.value"
          :value="mode.value"
        >
          {{ mode.label }}
        </option>
      </select>
      <p
        class="controls__description"
        data-testid="mode-description"
      >
        {{ activeDescription }}
      </p>
    </section>

    <section
      class="preview"
      data-testid="chat-preview"
    >
      <ChatWidget
        :key="activeMode"
        :mode="activeMode"
        title="Lovely Chat"
        :initial-messages="mockConversation"
        placeholder="Escribe tu mensaje"
      />
    </section>

    <section class="follow-ups">
      <h2>Respuestas sugeridas</h2>
      <ul>
        <li
          v-for="option in followUps"
          :key="option"
        >
          {{ option }}
        </li>
      </ul>
    </section>
  </main>
</template>

<style scoped lang="sass" src="../styles/app.sass"></style>
