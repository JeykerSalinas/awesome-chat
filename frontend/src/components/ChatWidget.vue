<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ChatOllama } from '@langchain/ollama'
import { TavilySearch } from '@langchain/tavily'
import { createAgent, tool } from 'langchain'
import * as z from 'zod'
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

const isOpen = ref(autoOpenModes.has(mode.value))
const draft = ref('')
const isSending = ref(false)

const messages = ref<ChatMessage[]>(
  props.initialMessages ? [...props.initialMessages] : []
)

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

function toggleChat() {
  isOpen.value = !isOpen.value
}

function closeChat() {
  if (!isPersistent.value) {
    isOpen.value = false
  }
}

function appendMessage(author: ChatRole, content: string, searchResult?: TavilySearchPayload) {
  messages.value.push({
    id: `${new Date().toISOString()}-${messages.value.length}`,
    author,
    content,
    timestamp: new Date().toISOString(),
    searchResult,
  })
}

function toAgentMessages(history: ChatMessage[]) {
  return history.map((message) => ({
    role: message.author,
    content: message.content,
  }))
}

function normalizeAgentContent(
  content: string | Array<{ type?: string; text?: string }>
) {
  if (typeof content === 'string') {
    return content
  }

  return content
    .map((block) => {
      if (typeof block === 'string') {
        return block
      }

      return block.type === 'text' ? (block.text ?? '') : ''
    })
    .join('')
    .trim()
}

function tryParseJson<T>(value: string) {
  try {
    return JSON.parse(value) as T
  } catch {
    return null
  }
}

function isTavilySearchPayload(value: unknown): value is TavilySearchPayload {
  if (!value || typeof value !== 'object') {
    return false
  }

  const payload = value as Partial<TavilySearchPayload>

  return (
    typeof payload.query === 'string' &&
    Array.isArray(payload.results) &&
    payload.results.every((result) => {
      return (
        !!result &&
        typeof result === 'object' &&
        typeof (result as TavilySearchResultItem).url === 'string' &&
        typeof (result as TavilySearchResultItem).title === 'string'
      )
    })
  )
}

function extractTavilySearchPayload(agentMessages: Array<{ type?: string; name?: string; content?: unknown }>) {
  for (let index = agentMessages.length - 1; index >= 0; index -= 1) {
    const message = agentMessages[index]

    if (message?.type !== 'tool' || message?.name !== 'tavily_search') {
      continue
    }

    if (typeof message.content === 'string') {
      const parsedPayload = tryParseJson<TavilySearchPayload>(message.content)
      if (parsedPayload && isTavilySearchPayload(parsedPayload)) {
        return parsedPayload
      }
    }

    if (Array.isArray(message.content)) {
      const parsedPayload = tryParseJson<TavilySearchPayload>(normalizeAgentContent(message.content))
      if (parsedPayload && isTavilySearchPayload(parsedPayload)) {
        return parsedPayload
      }
    }
  }

  return null
}

async function sendMessage() {
  const trimmed = draft.value.trim()
  if (!trimmed || isSending.value) return

  appendMessage('user', trimmed)
  draft.value = ''

  // Enviamos el historial completo para que el agente pueda decidir si usa tools.
  isSending.value = true

  try {
    const result = await agent.invoke({
      messages: toAgentMessages(messages.value),
    })

    const searchResult = extractTavilySearchPayload(result.messages)
    const lastMessage = result.messages[result.messages.length - 1]
    const assistantReply = lastMessage
      ? normalizeAgentContent(lastMessage.content)
      : (searchResult?.answer ?? '')

    if (assistantReply) {
      appendMessage('assistant', assistantReply, searchResult ?? undefined)
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'No se pudo completar la solicitud.'
    appendMessage('assistant', `Error al consultar el agente: ${message}`)
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
    messages.value = next ? [...next] : []
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

const populationByLocation: Record<string, number> = {
  'caracas, venezuela': 2945000,
  'madrid, spain': 3335000,
  'madrid, españa': 3335000,
  madrid: 3335000,
  caracas: 2945000,
}

// Tools ejecutables: el agente puede llamarlas y LangChain resuelve el ciclo.
const getWeather = tool(
  async ({ city }) => `No tengo acceso a clima en tiempo real. Respuesta mock para ${city}: 22°C y soleado.`,
  {
    name: 'get_weather',
    description: 'Get the weather for a given city',
    schema: z.object({
      city: z.string().describe('The city to get the weather for'),
    }),
  }
)

const getPopulation = tool(
  async ({ location }) => {
    const normalizedLocation = location.trim().toLowerCase()
    const population = populationByLocation[normalizedLocation]

    if (!population) {
      return `No tengo población registrada para ${location}.`
    }

    return `La población estimada de ${location} es ${population.toLocaleString('es-ES')} habitantes.`
  },
  {
    name: 'GetPopulation',
    description: 'Get the current population in a given location',
    schema: z.object({
      location: z.string().describe('The city and country, e.g. Caracas, Venezuela'),
    }),
  }
)

const model = new ChatOllama({
  model: 'qwen2.5:7b',
  baseUrl: 'http://127.0.0.1:11434',
})

// En Vite, las variables del frontend deben publicarse con prefijo VITE_.
const tavilyApiKey = import.meta.env.VITE_TAVILY_API_KEY

const tavilySearch = tavilyApiKey
  ? new TavilySearch({
      tavilyApiKey,
      maxResults: 3,
      searchDepth: 'basic',
      topic: 'general',
      includeAnswer: true,
      includeRawContent: 'markdown',
    })
  : null

const agentTools = [getWeather, getPopulation, ...(tavilySearch ? [tavilySearch] : [])]

const agent = createAgent({
  model,
  tools: agentTools,
  systemPrompt:
    'Eres un asistente útil. Usa las tools cuando la pregunta requiera datos de clima, población o información actual de la web.',
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
                <button
                  v-if="!isPersistent"
                  type="button"
                  class="chat-close"
                  aria-label="Cerrar chat"
                  @click="closeChat"
                >
                  ×
                </button>
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
                    @keydown="onKeydown"
                  />
                </div>
                <button
                  type="button"
                  class="chat-send"
                  data-testid="chat-send"
                  @click="sendMessage"
                >
                  Enviar
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
                <button
                  v-if="!isPersistent"
                  type="button"
                  class="chat-close"
                  aria-label="Cerrar chat"
                  @click="closeChat"
                >
                  ×
                </button>
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
                    @keydown="onKeydown"
                  />
                </div>
                <button
                  type="button"
                  class="chat-send"
                  data-testid="chat-send"
                  @click="sendMessage"
                >
                  Enviar
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
                <button
                  v-if="!isPersistent"
                  type="button"
                  class="chat-close"
                  aria-label="Cerrar chat"
                  @click="closeChat"
                >
                  ×
                </button>
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
                    @keydown="onKeydown"
                  />
                </div>
                <button
                  type="button"
                  class="chat-send"
                  data-testid="chat-send"
                  @click="sendMessage"
                >
                  Enviar
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
              @keydown="onKeydown"
            />
          </div>
          <button
            type="button"
            class="chat-send"
            data-testid="chat-send"
            @click="sendMessage"
          >
            Enviar
          </button>
        </footer>
      </slot>
    </section>
  </div>
</template>

<style scoped lang="sass" src="../styles/chat-widget.sass"></style>
