<script setup lang="ts">
type ExtractResultItem = {
  url: string
  raw_content?: string | null
  images?: string[]
  favicon?: string | null
}

type ExtractFailedResultItem = {
  url: string
  error?: string | null
}

type ExtractPayload = {
  results: ExtractResultItem[]
  failed_results?: ExtractFailedResultItem[]
  response_time?: number
}

defineProps<{
  payload: ExtractPayload
}>()

function truncate(value: string | null | undefined, maxLength = 320) {
  if (!value) return ''
  if (value.length <= maxLength) return value
  return `${value.slice(0, maxLength)}...`
}
</script>

<template>
  <section class="extract-sources">
    <header class="extract-sources__header">
      <span class="extract-sources__badge">Web Extract</span>
      <p class="extract-sources__meta">
        {{ payload.results.length }} páginas extraídas
        <span v-if="payload.response_time"> · {{ payload.response_time.toFixed(2) }}s</span>
      </p>
    </header>

    <ul class="extract-sources__list">
      <li
        v-for="result in payload.results"
        :key="result.url"
        class="extract-sources__item"
      >
        <a
          class="extract-sources__link"
          :href="result.url"
          target="_blank"
          rel="noreferrer"
        >
          {{ result.url }}
        </a>
        <p
          v-if="result.raw_content"
          class="extract-sources__snippet"
        >
          {{ truncate(result.raw_content) }}
        </p>
        <p
          v-if="result.images?.length"
          class="extract-sources__meta"
        >
          {{ result.images.length }} imágenes detectadas
        </p>
      </li>
    </ul>

    <ul
      v-if="payload.failed_results?.length"
      class="extract-sources__failed"
    >
      <li
        v-for="failed in payload.failed_results"
        :key="failed.url"
      >
        {{ failed.url }}<span v-if="failed.error"> · {{ failed.error }}</span>
      </li>
    </ul>
  </section>
</template>

<style scoped lang="sass">
.extract-sources
  margin-top: 0.5rem
  padding: 0.9rem
  border-radius: 0.95rem
  background: rgba(15, 23, 42, 0.04)
  border: 1px solid rgba(15, 23, 42, 0.08)

.extract-sources__header
  display: grid
  gap: 0.2rem
  margin-bottom: 0.75rem

.extract-sources__badge
  font-size: 0.66rem
  font-weight: 700
  letter-spacing: 0.08em
  text-transform: uppercase
  color: #0f766e

.extract-sources__meta
  margin: 0
  font-size: 0.75rem
  color: #64748b

.extract-sources__list,
.extract-sources__failed
  list-style: none
  margin: 0
  padding: 0
  display: grid
  gap: 0.75rem

.extract-sources__item
  display: grid
  gap: 0.25rem

.extract-sources__link
  font-size: 0.86rem
  font-weight: 600
  color: #0f766e
  text-decoration: none
  word-break: break-all

  &:hover
    text-decoration: underline

.extract-sources__snippet
  margin: 0
  font-size: 0.8rem
  color: #475569
  white-space: pre-wrap
</style>
