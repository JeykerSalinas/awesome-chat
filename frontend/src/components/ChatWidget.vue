<script setup lang="ts">
import axios from 'axios'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import SearchSourcesCard from '@/components/SearchSourcesCard.vue'

type ChatRole = 'user' | 'assistant'

interface TavilySearchResultItem {
  url: string
  title: string
  content: string
  score?: number
  raw_content?: string
}

interface TavilySearchPayload {
  query: string
  answer?: string | null
  response_time?: number
  request_id?: string
  results: TavilySearchResultItem[]
  follow_up_questions?: string[] | null
  images?: string[]
}

export interface ChatMessage {
  id: string
  author: ChatRole
  content: string
  timestamp: string
  isLocalError?: boolean
  searchResult?: TavilySearchPayload
}

const props = defineProps<{
  mode?: 'floating' | 'modal' | 'inplace' | 'assistant'
  title?: string
  initialMessages?: ChatMessage[]
  placeholder?: string
}>()

const mode = computed(() => props.mode ?? 'inplace')
const title = computed(() => props.title ?? 'Lovely Chat')
const placeholder = computed(() => props.placeholder ?? 'Escribe un mensaje')

type ChatWidgetMode = 'floating' | 'modal' | 'inplace' | 'assistant'
const autoOpenModes = new Set<ChatWidgetMode>(['inplace', 'assistant'])
const THREAD_STORAGE_KEY = 'lovely-chat-thread-id'
const MESSAGES_STORAGE_KEY = 'lovely-chat-messages'

function createThreadId() {
  return `chat-${crypto.randomUUID()}`
}

function getInitialThreadId() {
  if (typeof window === 'undefined') {
    return createThreadId()
  }

  return window.localStorage.getItem(THREAD_STORAGE_KEY) || createThreadId()
}

function getInitialMessages() {
  if (typeof window === 'undefined') {
    return props.initialMessages ? [...props.initialMessages] : []
  }

  const storedMessages = window.localStorage.getItem(MESSAGES_STORAGE_KEY)
  if (!storedMessages) {
    return props.initialMessages ? [...props.initialMessages] : []
  }

  try {
    return JSON.parse(storedMessages) as ChatMessage[]
  } catch {
    return props.initialMessages ? [...props.initialMessages] : []
  }
}

const isOpen = ref(autoOpenModes.has(mode.value))
const draft = ref('')
const isSending = ref(false)

const messages = ref<ChatMessage[]>(getInitialMessages())
const threadId = ref(getInitialThreadId())

const isPersistent = computed(() => mode.value === 'inplace')
const isFloating = computed(() => mode.value === 'floating')
const isModal = computed(() => mode.value === 'modal')
const isAssistant = computed(() => mode.value === 'assistant')
const showLauncher = computed(() => !isPersistent.value)

const panelTestId = computed(() => {
  switch (mode.value) {
    case 'floating':
      return 'chat-panel-floating'
    case 'modal':
      return 'chat-panel-modal'
    case 'assistant':
      return 'chat-panel-assistant'
    default:
      return 'chat-panel-inline'
  }
})

watch(mode, (newMode) => {
  isOpen.value = autoOpenModes.has(newMode)
})

watch(threadId, (nextThreadId) => {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(THREAD_STORAGE_KEY, nextThreadId)
  }
}, { immediate: true })

watch(messages, (nextMessages) => {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(MESSAGES_STORAGE_KEY, JSON.stringify(nextMessages))
  }
}, { deep: true, immediate: true })

function toggleChat() {
  isOpen.value = !isOpen.value
}

function closeChat() {
  if (!isPersistent.value) {
    isOpen.value = false
  }
}

function appendMessage(
  author: ChatRole,
  content: string,
  searchResult?: TavilySearchPayload,
  isLocalError = false,
) {
  messages.value.push({
    id: `${new Date().toISOString()}-${messages.value.length}`,
    author,
    content,
    timestamp: new Date().toISOString(),
    isLocalError,
    searchResult,
  })
}

function resetConversation() {
  messages.value = []
  draft.value = ''
  threadId.value = createThreadId()
}

const apiBaseUrl = import.meta.env.VITE_APP_BACKEND_URL ?? 'http://127.0.0.1:8000'

async function sendMessage() {
  const trimmed = draft.value.trim()
  if (!trimmed || isSending.value) return

  appendMessage('user', trimmed)
  draft.value = ''

  // El backend recupera la memoria usando `threadId`, así que aquí solo enviamos
  // el nuevo mensaje del usuario.
  isSending.value = true

  try {
    const { data } = await axios.post<{
      content: string
      searchResult?: TavilySearchPayload | null
      structuredResponse?: unknown
    }>(`${apiBaseUrl}/chat`, {
        threadId: threadId.value,
        message: trimmed,
    })

    const assistantReply = data.content.trim() || data.searchResult?.answer?.trim() || ''

    if (assistantReply) {
      appendMessage('assistant', assistantReply, data.searchResult ?? undefined)
    }
  } catch (error) {
    const readableMessage = axios.isAxiosError(error)
      ? error.response?.status
        ? `Backend respondió con ${error.response.status}`
        : `Could not reach the backend at ${apiBaseUrl}. Check that it is running and that CORS allows the current frontend origin.`
      : error instanceof Error
        ? error.message
        : 'Could not complete the request.'
    appendMessage('assistant', `Agent request error: ${readableMessage}`, undefined, true)
  } finally {
    isSending.value = false
  }
}

function setDraft(value: string) {
  draft.value = value
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

function lockBodyScroll() {
  document.body.style.overflow = isModal.value && isOpen.value ? 'hidden' : ''
}

const ASSISTANT_CLASS = 'has-assistant-chat'
const assistantWidth = computed(() => 360)

function syncAssistantLayout() {
  const root = document.documentElement
  if (isAssistant.value && isOpen.value) {
    document.body.classList.add(ASSISTANT_CLASS)
    root.style.setProperty('--assistant-chat-width', `${assistantWidth.value}px`)
  } else {
    document.body.classList.remove(ASSISTANT_CLASS)
    root.style.removeProperty('--assistant-chat-width')
  }
}

watch(isOpen, lockBodyScroll)

watch(mode, lockBodyScroll)

watch(
  [isOpen, mode],
  () => {
    syncAssistantLayout()
  },
  { immediate: true }
)

watch(
  () => props.initialMessages,
  (next) => {
    if (typeof window === 'undefined') {
      messages.value = next ? [...next] : []
    }
  }
)

onMounted(() => {
  lockBodyScroll()
})

onBeforeUnmount(() => {
  document.body.style.overflow = ''
  document.body.classList.remove(ASSISTANT_CLASS)
  document.documentElement.style.removeProperty('--assistant-chat-width')
})
</script>

<template>
  <div
    class="chat-widget"
    :data-mode="mode"
  >
    <div
      v-if="showLauncher"
      class="chat-launcher__wrapper"
    >
      <slot
        name="launcher"
        :is-open="isOpen"
        :toggle="toggleChat"
        :mode="mode"
      >
        <button
          type="button"
          class="chat-launcher"
          :class="`chat-launcher--${mode}`"
          data-testid="chat-launcher"
          :aria-expanded="isOpen"
          @click="toggleChat"
        >
          <span v-if="!isOpen">Abrir chat</span>
          <span v-else>Cerrar chat</span>
        </button>
      </slot>
    </div>

    <Teleport
      to="body"
      v-if="isFloating"
    >
      <div class="chat-floating">
        <transition name="chat-pop">
          <section
            v-if="isOpen"
            class="chat-panel chat-panel--floating"
            :data-testid="panelTestId"
          >
            <slot
              name="header"
              :title="title"
              :close="closeChat"
              :is-open="isOpen"
              :mode="mode"
            >
              <header class="chat-panel__header">
                <div class="chat-panel__title">
                  <span class="chat-panel__badge">Live</span>
                  <h2>{{ title }}</h2>
                </div>
                <div class="chat-panel__actions">
                  <button
                    type="button"
                    class="chat-reset"
                    @click="resetConversation"
                  >
                    Reset
                  </button>
                  <button
                    v-if="!isPersistent"
                    type="button"
                    class="chat-close"
                    aria-label="Cerrar chat"
                    @click="closeChat"
                  >
                    ×
                  </button>
                </div>
              </header>
            </slot>

            <slot
              name="messages"
              :messages="messages"
              :mode="mode"
            >
              <div
                class="chat-panel__messages"
                data-testid="chat-messages"
              >
                <template
                  v-for="message in messages"
                  :key="message.id"
                >
                  <slot
                    name="message"
                    :message="message"
                    :mode="mode"
                  >
                    <article
                      class="chat-message"
                      :class="`chat-message--${message.author}`"
                    >
                      <p>{{ message.content }}</p>
                      <SearchSourcesCard
                        v-if="message.searchResult"
                        :payload="message.searchResult"
                      />
                      <time class="chat-message__time">
                        {{ new Date(message.timestamp).toLocaleTimeString() }}
                      </time>
                    </article>
                  </slot>
                </template>
                <article
                  v-if="isSending"
                  class="chat-message chat-message--assistant chat-message--loading"
                >
                  <div class="chat-spinner">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <p>Pensando...</p>
                </article>
              </div>
            </slot>

            <slot
              name="composer"
              :draft="draft"
              :send="sendMessage"
              :set-draft="setDraft"
              :placeholder="placeholder"
              :mode="mode"
              :on-keydown="onKeydown"
            >
              <footer class="chat-panel__composer">
                <div class="chat-input__wrapper">
                  <textarea
                    v-model="draft"
                    class="chat-input"
                    :placeholder="placeholder"
                    data-testid="chat-input"
                    rows="2"
                    :disabled="isSending"
                    @keydown="onKeydown"
                  />
                </div>
                <button
                  type="button"
                  class="chat-send"
                  data-testid="chat-send"
                  :disabled="isSending"
                  @click="sendMessage"
                >
                  <span
                    v-if="isSending"
                    class="chat-send__content"
                  >
                    <span class="chat-send__spinner"></span>
                    Enviando
                  </span>
                  <span v-else>Enviar</span>
                </button>
              </footer>
            </slot>
          </section>
        </transition>
      </div>
    </Teleport>

    <Teleport
      to="body"
      v-else-if="isModal"
    >
      <transition name="chat-fade">
        <div
          v-if="isOpen"
          class="chat-overlay"
          data-testid="chat-overlay"
          @click.self="closeChat"
        >
          <section
            class="chat-panel chat-panel--modal"
            :data-testid="panelTestId"
          >
            <slot
              name="header"
              :title="title"
              :close="closeChat"
              :is-open="isOpen"
              :mode="mode"
            >
              <header class="chat-panel__header">
                <div class="chat-panel__title">
                  <span class="chat-panel__badge">En línea</span>
                  <h2>{{ title }}</h2>
                </div>
                <div class="chat-panel__actions">
                  <button
                    type="button"
                    class="chat-reset"
                    @click="resetConversation"
                  >
                    Reset
                  </button>
                  <button
                    v-if="!isPersistent"
                    type="button"
                    class="chat-close"
                    aria-label="Cerrar chat"
                    @click="closeChat"
                  >
                    ×
                  </button>
                </div>
              </header>
            </slot>

            <slot
              name="messages"
              :messages="messages"
              :mode="mode"
            >
              <div
                class="chat-panel__messages"
                data-testid="chat-messages"
              >
                <template
                  v-for="message in messages"
                  :key="message.id"
                >
                  <slot
                    name="message"
                    :message="message"
                    :mode="mode"
                  >
                    <article
                      class="chat-message"
                      :class="`chat-message--${message.author}`"
                    >
                      <p>{{ message.content }}</p>
                      <SearchSourcesCard
                        v-if="message.searchResult"
                        :payload="message.searchResult"
                      />
                      <time class="chat-message__time">
                        {{ new Date(message.timestamp).toLocaleTimeString() }}
                      </time>
                    </article>
                  </slot>
                </template>
                <article
                  v-if="isSending"
                  class="chat-message chat-message--assistant chat-message--loading"
                >
                  <div class="chat-spinner">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <p>Pensando...</p>
                </article>
              </div>
            </slot>

            <slot
              name="composer"
              :draft="draft"
              :send="sendMessage"
              :set-draft="setDraft"
              :placeholder="placeholder"
              :mode="mode"
              :on-keydown="onKeydown"
            >
              <footer class="chat-panel__composer">
                <div class="chat-input__wrapper">
                  <textarea
                    v-model="draft"
                    class="chat-input"
                    :placeholder="placeholder"
                    data-testid="chat-input"
                    rows="3"
                    :disabled="isSending"
                    @keydown="onKeydown"
                  />
                </div>
                <button
                  type="button"
                  class="chat-send"
                  data-testid="chat-send"
                  :disabled="isSending"
                  @click="sendMessage"
                >
                  <span
                    v-if="isSending"
                    class="chat-send__content"
                  >
                    <span class="chat-send__spinner"></span>
                    Enviando
                  </span>
                  <span v-else>Enviar</span>
                </button>
              </footer>
            </slot>
          </section>
        </div>
      </transition>
    </Teleport>

    <Teleport
      to="body"
      v-else-if="isAssistant"
    >
      <div
        class="chat-assistant"
        :class="{ 'chat-assistant--open': isOpen }"
        :aria-hidden="!isOpen"
      >
        <transition name="chat-slide-in">
          <section
            v-if="isOpen"
            class="chat-panel chat-panel--assistant"
            :data-testid="panelTestId"
          >
            <slot
              name="header"
              :title="title"
              :close="closeChat"
              :is-open="isOpen"
              :mode="mode"
            >
              <header class="chat-panel__header">
                <div class="chat-panel__title">
                  <span class="chat-panel__badge chat-panel__badge--assistant">
                    Assistant
                  </span>
                  <h2>{{ title }}</h2>
                </div>
                <div class="chat-panel__actions">
                  <button
                    type="button"
                    class="chat-reset"
                    @click="resetConversation"
                  >
                    Reset
                  </button>
                  <button
                    v-if="!isPersistent"
                    type="button"
                    class="chat-close"
                    aria-label="Cerrar chat"
                    @click="closeChat"
                  >
                    ×
                  </button>
                </div>
              </header>
            </slot>

            <slot
              name="messages"
              :messages="messages"
              :mode="mode"
            >
              <div
                class="chat-panel__messages"
                data-testid="chat-messages"
              >
                <template
                  v-for="message in messages"
                  :key="message.id"
                >
                  <slot
                    name="message"
                    :message="message"
                    :mode="mode"
                  >
                    <article
                      class="chat-message"
                      :class="`chat-message--${message.author}`"
                    >
                      <p>{{ message.content }}</p>
                      <SearchSourcesCard
                        v-if="message.searchResult"
                        :payload="message.searchResult"
                      />
                      <time class="chat-message__time">
                        {{ new Date(message.timestamp).toLocaleTimeString() }}
                      </time>
                    </article>
                  </slot>
                </template>
                <article
                  v-if="isSending"
                  class="chat-message chat-message--assistant chat-message--loading"
                >
                  <div class="chat-spinner">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <p>Pensando...</p>
                </article>
              </div>
            </slot>

            <slot
              name="composer"
              :draft="draft"
              :send="sendMessage"
              :set-draft="setDraft"
              :placeholder="placeholder"
              :mode="mode"
              :on-keydown="onKeydown"
            >
              <footer class="chat-panel__composer">
                <div class="chat-input__wrapper">
                  <textarea
                    v-model="draft"
                    class="chat-input"
                    :placeholder="placeholder"
                    data-testid="chat-input"
                    rows="3"
                    :disabled="isSending"
                    @keydown="onKeydown"
                  />
                </div>
                <button
                  type="button"
                  class="chat-send"
                  data-testid="chat-send"
                  :disabled="isSending"
                  @click="sendMessage"
                >
                  <span
                    v-if="isSending"
                    class="chat-send__content"
                  >
                    <span class="chat-send__spinner"></span>
                    Enviando
                  </span>
                  <span v-else>Enviar</span>
                </button>
              </footer>
            </slot>
          </section>
        </transition>
      </div>
    </Teleport>

    <section
      v-else
      class="chat-panel chat-panel--inline"
      :data-testid="panelTestId"
    >
      <slot
        name="header"
        :title="title"
        :close="closeChat"
        :is-open="isOpen"
        :mode="mode"
      >
        <header class="chat-panel__header">
          <div class="chat-panel__title">
            <span class="chat-panel__badge chat-panel__badge--inline">Embebido</span>
            <h2>{{ title }}</h2>
          </div>
          <div class="chat-panel__actions">
            <button
              type="button"
              class="chat-reset"
              @click="resetConversation"
            >
              Reset
            </button>
          </div>
        </header>
      </slot>

      <slot
        name="messages"
        :messages="messages"
        :mode="mode"
      >
        <div
          class="chat-panel__messages"
          data-testid="chat-messages"
        >
          <template
            v-for="message in messages"
            :key="message.id"
          >
            <slot
              name="message"
              :message="message"
              :mode="mode"
            >
              <article
                class="chat-message"
                :class="`chat-message--${message.author}`"
              >
                <p>{{ message.content }}</p>
                <SearchSourcesCard
                  v-if="message.searchResult"
                  :payload="message.searchResult"
                />
                <time class="chat-message__time">
                  {{ new Date(message.timestamp).toLocaleTimeString() }}
                </time>
              </article>
            </slot>
          </template>
          <article
            v-if="isSending"
            class="chat-message chat-message--assistant chat-message--loading"
          >
            <div class="chat-spinner">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <p>Pensando...</p>
          </article>
        </div>
      </slot>

      <slot
        name="composer"
        :draft="draft"
        :send="sendMessage"
        :set-draft="setDraft"
        :placeholder="placeholder"
        :mode="mode"
        :on-keydown="onKeydown"
      >
        <footer class="chat-panel__composer">
          <div class="chat-input__wrapper">
            <textarea
              v-model="draft"
              class="chat-input"
              :placeholder="placeholder"
              data-testid="chat-input"
              rows="3"
              :disabled="isSending"
              @keydown="onKeydown"
            />
          </div>
          <button
            type="button"
            class="chat-send"
            data-testid="chat-send"
            :disabled="isSending"
            @click="sendMessage"
          >
            <span
              v-if="isSending"
              class="chat-send__content"
            >
              <span class="chat-send__spinner"></span>
              Enviando
            </span>
            <span v-else>Enviar</span>
          </button>
        </footer>
      </slot>
    </section>
  </div>
</template>

<style scoped lang="sass" src="../styles/chat-widget.sass"></style>
