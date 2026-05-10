<script setup lang="ts">
type SearchResultItem = {
  url: string
  title: string
  content: string
  score?: number
}

type SearchPayload = {
  query: string
  answer?: string | null
  response_time?: number
  request_id?: string
  results: SearchResultItem[]
}

defineProps<{
  payload: SearchPayload
}>()
</script>

<template>
  <section class="search-sources">
    <header class="search-sources__header">
      <span class="search-sources__badge">Web Search</span>
      <p class="search-sources__query">{{ payload.query }}</p>
      <p
        v-if="payload.response_time"
        class="search-sources__meta"
      >
        {{ payload.results.length }} fuentes · {{ payload.response_time.toFixed(2) }}s
      </p>
    </header>

    <p
      v-if="payload.answer"
      class="search-sources__answer"
    >
      {{ payload.answer }}
    </p>

    <ul class="search-sources__list">
      <li
        v-for="result in payload.results"
        :key="result.url"
        class="search-sources__item"
      >
        <a
          class="search-sources__link"
          :href="result.url"
          target="_blank"
          rel="noreferrer"
        >
          {{ result.title }}
        </a>
        <p class="search-sources__snippet">
          {{ result.content }}
        </p>
      </li>
    </ul>
  </section>
</template>

<style scoped lang="sass">
.search-sources
  margin-top: 0.5rem
  padding: 0.9rem
  border-radius: 0.95rem
  background: rgba(255, 255, 255, 0.72)
  border: 1px solid rgba(99, 102, 241, 0.14)

.search-sources__header
  display: grid
  gap: 0.2rem
  margin-bottom: 0.75rem

.search-sources__badge
  font-size: 0.66rem
  font-weight: 700
  letter-spacing: 0.08em
  text-transform: uppercase
  color: #4f46e5

.search-sources__query
  margin: 0
  font-weight: 600
  color: #0f172a

.search-sources__meta
  margin: 0
  font-size: 0.75rem
  color: #64748b

.search-sources__answer
  margin: 0 0 0.85rem
  font-size: 0.88rem
  color: #334155

.search-sources__list
  list-style: none
  margin: 0
  padding: 0
  display: grid
  gap: 0.75rem

.search-sources__item
  display: grid
  gap: 0.25rem

.search-sources__link
  font-size: 0.86rem
  font-weight: 600
  color: #312e81
  text-decoration: none

  &:hover
    text-decoration: underline

.search-sources__snippet
  margin: 0
  font-size: 0.8rem
  color: #475569
</style>
