<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';

type ChatRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  author: ChatRole;
  content: string;
  timestamp: string;
}

const props = defineProps<{
  mode?: 'floating' | 'modal' | 'inplace' | 'assistant';
  title?: string;
  initialMessages?: ChatMessage[];
  placeholder?: string;
}>();

const mode = computed(() => props.mode ?? 'inplace');
const title = computed(() => props.title ?? 'Lovely Chat');
const placeholder = computed(() => props.placeholder ?? 'Escribe un mensaje');

type ChatWidgetMode = 'floating' | 'modal' | 'inplace' | 'assistant';
const autoOpenModes = new Set<ChatWidgetMode>(['inplace', 'assistant']);

const isOpen = ref(autoOpenModes.has(mode.value));
const draft = ref('');

const messages = ref<ChatMessage[]>(props.initialMessages ? [...props.initialMessages] : []);

const isPersistent = computed(() => mode.value === 'inplace');
const isFloating = computed(() => mode.value === 'floating');
const isModal = computed(() => mode.value === 'modal');
const isAssistant = computed(() => mode.value === 'assistant');
const showLauncher = computed(() => !isPersistent.value);

const panelTestId = computed(() => {
  switch (mode.value) {
    case 'floating':
      return 'chat-panel-floating';
    case 'modal':
      return 'chat-panel-modal';
    case 'assistant':
      return 'chat-panel-assistant';
    default:
      return 'chat-panel-inline';
  }
});

watch(mode, (newMode) => {
  isOpen.value = autoOpenModes.has(newMode);
});

function toggleChat() {
  isOpen.value = !isOpen.value;
}

function closeChat() {
  if (!isPersistent.value) {
    isOpen.value = false;
  }
}

function sendMessage() {
  const trimmed = draft.value.trim();
  if (!trimmed) return;

  const now = new Date().toISOString();
  messages.value.push({
    id: `${now}-${messages.value.length}`,
    author: 'user',
    content: trimmed,
    timestamp: now,
  });
  draft.value = '';
}

function setDraft(value: string) {
  draft.value = value;
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

function lockBodyScroll() {
  document.body.style.overflow = isModal.value && isOpen.value ? 'hidden' : '';
}

const ASSISTANT_CLASS = 'has-assistant-chat';
const assistantWidth = computed(() => 360);

function syncAssistantLayout() {
  const root = document.documentElement;
  if (isAssistant.value && isOpen.value) {
    document.body.classList.add(ASSISTANT_CLASS);
    root.style.setProperty('--assistant-chat-width', `${assistantWidth.value}px`);
  } else {
    document.body.classList.remove(ASSISTANT_CLASS);
    root.style.removeProperty('--assistant-chat-width');
  }
}

watch(isOpen, lockBodyScroll);

watch(mode, lockBodyScroll);

watch([isOpen, mode], () => {
  syncAssistantLayout();
}, { immediate: true });

watch(
  () => props.initialMessages,
  (next) => {
    messages.value = next ? [...next] : [];
  }
);

onMounted(() => {
  lockBodyScroll();
});

onBeforeUnmount(() => {
  document.body.style.overflow = '';
  document.body.classList.remove(ASSISTANT_CLASS);
  document.documentElement.style.removeProperty('--assistant-chat-width');
});
</script>

<template>
  <div class="chat-widget" :data-mode="mode">
    <div v-if="showLauncher" class="chat-launcher__wrapper">
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

    <Teleport to="body" v-if="isFloating">
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
              <div class="chat-panel__messages" data-testid="chat-messages">
                <template v-for="message in messages" :key="message.id">
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
                      <time class="chat-message__time">{{ new Date(message.timestamp).toLocaleTimeString() }}</time>
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
                <button type="button" class="chat-send" data-testid="chat-send" @click="sendMessage">Enviar</button>
              </footer>
            </slot>
          </section>
        </transition>
      </div>
    </Teleport>

    <Teleport to="body" v-else-if="isModal">
      <transition name="chat-fade">
        <div
          v-if="isOpen"
          class="chat-overlay"
          data-testid="chat-overlay"
          @click.self="closeChat"
        >
          <section class="chat-panel chat-panel--modal" :data-testid="panelTestId">
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
              <div class="chat-panel__messages" data-testid="chat-messages">
                <template v-for="message in messages" :key="message.id">
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
                      <time class="chat-message__time">{{ new Date(message.timestamp).toLocaleTimeString() }}</time>
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
                <button type="button" class="chat-send" data-testid="chat-send" @click="sendMessage">Enviar</button>
              </footer>
            </slot>
          </section>
        </div>
      </transition>
    </Teleport>

    <Teleport to="body" v-else-if="isAssistant">
      <div class="chat-assistant" :class="{ 'chat-assistant--open': isOpen }" :aria-hidden="(!isOpen).toString()">
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
                  <span class="chat-panel__badge chat-panel__badge--assistant">Assistant</span>
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
              <div class="chat-panel__messages" data-testid="chat-messages">
                <template v-for="message in messages" :key="message.id">
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
                      <time class="chat-message__time">{{ new Date(message.timestamp).toLocaleTimeString() }}</time>
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
                <button type="button" class="chat-send" data-testid="chat-send" @click="sendMessage">Enviar</button>
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
        <div class="chat-panel__messages" data-testid="chat-messages">
          <template v-for="message in messages" :key="message.id">
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
                <time class="chat-message__time">{{ new Date(message.timestamp).toLocaleTimeString() }}</time>
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
          <button type="button" class="chat-send" data-testid="chat-send" @click="sendMessage">Enviar</button>
        </footer>
      </slot>
    </section>
  </div>
</template>

<style scoped lang="sass" src="../styles/chat-widget.sass"></style>
