<script setup lang="ts">
import { computed, ref } from 'vue'
import { useStream } from '@langchain/vue'
import { AIMessage, HumanMessage } from '@langchain/core/messages'

const PRESETS = [
  'Write a quick-start guide for building a REST API with Express.js',
  'Compare Python and Rust in a table with pros and cons',
  'Explain the merge sort algorithm with code examples',
]

const draft = ref('')
const threadId = ref<string | null>(null)

const stream = useStream({
  apiUrl: 'http://127.0.0.1:2024',
  assistantId: 'playground-agent',
  threadId,
  onThreadId: (id) => {
    threadId.value = id
  },
})

const messages = computed(() => stream.messages.value)
const hasMessages = computed(() => messages.value.length > 0)

async function handleSubmit(text: string) {
  const trimmed = text.trim()
  if (!trimmed || stream.isLoading.value) return

  draft.value = ''
  await stream.submit({
    messages: [{ type: 'human' as const, content: trimmed }],
  })
}

function sendMessage() {
  void handleSubmit(draft.value)
}

function resetThread() {
  threadId.value = null
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}
</script>

<template>
  <main class="playground-agent">
    <section class="playground-agent__hero">
      <h1>Playground Agent</h1>
      <p>
        Integración mínima con <code>useStream()</code> conectada a LangGraph Agent Server.
      </p>
      <pre><code>agent = create_agent(model=build_model())</code></pre>
    </section>

    <section class="playground-agent__panel">
      <div class="playground-agent__messages">
        <div
          v-if="!hasMessages"
          class="playground-agent__presets"
        >
          <button
            v-for="prompt in PRESETS"
            :key="prompt"
            type="button"
            class="playground-agent__preset"
            @click="handleSubmit(prompt)"
          >
            {{ prompt }}
          </button>
        </div>

        <article
          v-for="message in messages"
          :key="message.id ?? message.lc_id?.join('-') ?? message.text"
          class="playground-agent__message"
          :class="{
            'playground-agent__message--user': HumanMessage.isInstance(message),
            'playground-agent__message--assistant': AIMessage.isInstance(message),
          }"
        >
          <strong>{{ HumanMessage.isInstance(message) ? 'Tú' : 'Agente' }}</strong>
          <p>{{ message.text }}</p>
        </article>

        <article
          v-if="stream.isLoading.value"
          class="playground-agent__message playground-agent__message--assistant playground-agent__message--loading"
        >
          <strong>Agente</strong>
          <p>Cargando...</p>
        </article>
      </div>

      <div class="playground-agent__composer">
        <div class="playground-agent__toolbar">
          <span class="playground-agent__thread">
            {{ threadId ? `Thread: ${threadId}` : 'Sin thread todavía' }}
          </span>
          <button
            type="button"
            class="playground-agent__new-thread"
            :disabled="stream.isLoading.value"
            @click="resetThread"
          >
            Nuevo hilo
          </button>
        </div>
        <textarea
          v-model="draft"
          class="playground-agent__input"
          placeholder="Escribe un mensaje"
          rows="4"
          :disabled="stream.isLoading.value"
          @keydown="onKeydown"
        />
        <button
          type="button"
          class="playground-agent__send"
          :disabled="stream.isLoading.value"
          @click="sendMessage"
        >
          {{ stream.isLoading.value ? 'Enviando...' : 'Enviar' }}
        </button>
      </div>
    </section>
  </main>
</template>

<style scoped lang="sass">
.playground-agent
  min-height: 100vh
  padding: 2rem
  display: grid
  gap: 1.5rem
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)

.playground-agent__hero
  max-width: 960px
  margin: 0 auto
  width: 100%
  padding: 1.75rem
  border-radius: 1.5rem
  background: rgba(255, 255, 255, 0.9)
  border: 1px solid rgba(99, 102, 241, 0.12)

  h1
    margin: 0 0 0.75rem

  p
    margin: 0 0 1rem

  pre
    margin: 0
    padding: 1rem
    border-radius: 1rem
    background: #0f172a
    color: #e2e8f0
    overflow-x: auto

.playground-agent__panel
  max-width: 960px
  margin: 0 auto
  width: 100%
  min-height: 60vh
  display: grid
  grid-template-rows: 1fr auto
  border-radius: 1.5rem
  overflow: hidden
  border: 1px solid rgba(99, 102, 241, 0.12)
  background: rgba(255, 255, 255, 0.92)

.playground-agent__messages
  padding: 1.5rem
  display: flex
  flex-direction: column
  gap: 0.9rem
  overflow-y: auto

.playground-agent__presets
  display: grid
  gap: 0.75rem
  margin-bottom: 0.5rem

.playground-agent__preset
  text-align: left
  border: 1px solid rgba(99, 102, 241, 0.14)
  background: rgba(99, 102, 241, 0.05)
  border-radius: 1rem
  padding: 0.95rem 1rem
  font: inherit
  cursor: pointer

  &:hover
    border-color: rgba(99, 102, 241, 0.28)
    background: rgba(99, 102, 241, 0.09)

.playground-agent__message
  max-width: 80%
  padding: 0.9rem 1rem
  border-radius: 1rem
  display: grid
  gap: 0.35rem

  strong
    font-size: 0.85rem

  p
    margin: 0
    white-space: pre-wrap

  &--user
    justify-self: end
    background: linear-gradient(135deg, #6366f1, #4f46e5)
    color: white

  &--assistant
    justify-self: start
    background: rgba(15, 23, 42, 0.06)
    color: #0f172a

  &--loading
    opacity: 0.75

.playground-agent__composer
  padding: 1rem
  display: grid
  gap: 0.75rem
  border-top: 1px solid rgba(99, 102, 241, 0.08)

.playground-agent__toolbar
  display: flex
  align-items: center
  justify-content: space-between
  gap: 1rem

.playground-agent__thread
  font-size: 0.85rem
  color: #475569
  overflow: hidden
  text-overflow: ellipsis
  white-space: nowrap

.playground-agent__new-thread
  border: 1px solid rgba(99, 102, 241, 0.15)
  background: white
  color: #334155
  border-radius: 0.85rem
  padding: 0.65rem 0.9rem
  font: inherit
  font-weight: 600
  cursor: pointer

  &:disabled
    opacity: 0.6
    cursor: wait

.playground-agent__input
  width: 100%
  border: 1px solid rgba(99, 102, 241, 0.18)
  border-radius: 1rem
  padding: 0.9rem 1rem
  font: inherit
  resize: vertical

.playground-agent__send
  justify-self: end
  border: none
  border-radius: 0.9rem
  padding: 0.8rem 1.1rem
  background: linear-gradient(135deg, #6366f1, #4f46e5)
  color: white
  font-weight: 600
  cursor: pointer

  &:disabled
    opacity: 0.7
    cursor: wait

@media (max-width: 768px)
  .playground-agent
    padding: 1rem

  .playground-agent__message
    max-width: 100%
</style>
