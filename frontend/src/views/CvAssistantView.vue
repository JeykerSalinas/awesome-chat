<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, reactive, ref } from 'vue'

type DocumentSummary = {
  id: string
  display_name: string
  original_filename: string
  kind: 'uploaded' | 'generated'
  source_document_id?: string | null
  created_at: string
  updated_at: string
  available_formats: Array<'docx' | 'pdf'>
}

type ExtractResult = {
  url: string
  raw_content?: string | null
}

type OfferExtract = {
  results: ExtractResult[]
  response_time?: number
}

type StructuredResponse = {
  answer: string
  key_adjustments: string[]
  warnings: string[]
}

type OptimizeResponse = {
  content: string
  generated_document?: DocumentSummary | null
  offer_extract?: OfferExtract | null
  structured_response?: StructuredResponse | null
}

const apiBaseUrl = import.meta.env.VITE_APP_BACKEND_URL ?? 'http://127.0.0.1:8001'

const documents = ref<DocumentSummary[]>([])
const selectedDocumentId = ref('')
const jobUrl = ref('')
const instructions = ref('')
const uploadName = ref('')
const uploadFile = ref<File | null>(null)
const isUploading = ref(false)
const isOptimizing = ref(false)
const errorMessage = ref('')
const optimizationResult = ref<OptimizeResponse | null>(null)
const editedNames = reactive<Record<string, string>>({})

const sourceDocuments = computed(() => documents.value.filter((item) => item.kind === 'uploaded'))
const firstOfferResult = computed(() => optimizationResult.value?.offer_extract?.results?.[0] ?? null)

async function fetchDocuments() {
  const { data } = await axios.get<DocumentSummary[]>(`${apiBaseUrl}/documents`)
  documents.value = data
  for (const document of data) {
    editedNames[document.id] = document.display_name
  }
  const firstSourceDocument = data.find((item) => item.kind === 'uploaded')
  if (!selectedDocumentId.value && firstSourceDocument) {
    selectedDocumentId.value = firstSourceDocument.id
  }
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  uploadFile.value = input.files?.[0] ?? null
}

async function uploadDocument() {
  if (!uploadFile.value || isUploading.value) return

  const form = new FormData()
  form.append('file', uploadFile.value)
  if (uploadName.value.trim()) {
    form.append('display_name', uploadName.value.trim())
  }

  errorMessage.value = ''
  isUploading.value = true
  try {
    await axios.post(`${apiBaseUrl}/documents`, form)
    uploadFile.value = null
    uploadName.value = ''
    await fetchDocuments()
  } catch (error) {
    errorMessage.value = axios.isAxiosError(error)
      ? error.response?.data?.detail ?? 'No se pudo subir el documento.'
      : 'No se pudo subir el documento.'
  } finally {
    isUploading.value = false
  }
}

async function renameDocument(documentId: string) {
  const displayName = editedNames[documentId]?.trim()
  if (!displayName) return

  await axios.patch(`${apiBaseUrl}/documents/${documentId}`, { display_name: displayName })
  await fetchDocuments()
}

async function deleteDocument(documentId: string) {
  await axios.delete(`${apiBaseUrl}/documents/${documentId}`)
  if (selectedDocumentId.value === documentId) {
    selectedDocumentId.value = ''
  }
  await fetchDocuments()
}

function downloadUrl(documentId: string, format: 'docx' | 'pdf') {
  return `${apiBaseUrl}/documents/${documentId}/download?format=${format}`
}

async function optimizeCv() {
  if (!selectedDocumentId.value || isOptimizing.value) return

  errorMessage.value = ''
  optimizationResult.value = null
  isOptimizing.value = true
  try {
    const { data } = await axios.post<OptimizeResponse>(`${apiBaseUrl}/cv-assistant/optimize`, {
      document_id: selectedDocumentId.value,
      job_url: jobUrl.value.trim(),
      instructions: instructions.value.trim() || null,
    })
    optimizationResult.value = data
    await fetchDocuments()
  } catch (error) {
    errorMessage.value = axios.isAxiosError(error)
      ? error.response?.data?.detail ?? 'No se pudo adaptar el CV.'
      : 'No se pudo adaptar el CV.'
  } finally {
    isOptimizing.value = false
  }
}

function truncate(value: string | null | undefined, maxLength = 420) {
  if (!value) return ''
  if (value.length <= maxLength) return value
  return `${value.slice(0, maxLength)}...`
}

onMounted(() => {
  void fetchDocuments()
})
</script>

<template>
  <main class="cv-lab">
    <section class="cv-lab__hero">
      <h1>CV Tailor Lab</h1>
      <p>
        Sube tu CV base en <code>.docx</code>, analiza una oferta con Tavily Extract y genera
        versiones adaptadas sin inventar experiencia ni logros.
      </p>
    </section>

    <p
      v-if="errorMessage"
      class="cv-lab__error"
    >
      {{ errorMessage }}
    </p>

    <section class="cv-lab__layout">
      <aside class="cv-lab__sidebar">
        <div class="cv-card">
          <h2>Subir CV</h2>
          <input
            type="file"
            accept=".docx"
            @change="onFileChange"
          />
          <input
            v-model="uploadName"
            type="text"
            placeholder="Nombre para mostrar"
          />
          <button
            type="button"
            :disabled="!uploadFile || isUploading"
            @click="uploadDocument"
          >
            {{ isUploading ? 'Subiendo...' : 'Subir documento' }}
          </button>
        </div>

        <div class="cv-card">
          <h2>Documentos</h2>
          <ul class="cv-list">
            <li
              v-for="document in documents"
              :key="document.id"
              class="cv-list__item"
              :class="{ 'cv-list__item--selected': document.id === selectedDocumentId }"
            >
              <button
                type="button"
                class="cv-list__select"
                @click="selectedDocumentId = document.id"
              >
                <strong>{{ document.display_name }}</strong>
                <span>{{ document.kind === 'uploaded' ? 'Base' : 'Generado' }}</span>
              </button>

              <div class="cv-list__actions">
                <input
                  v-model="editedNames[document.id]"
                  type="text"
                />
                <div class="cv-list__buttons">
                  <button
                    type="button"
                    @click="renameDocument(document.id)"
                  >
                    Renombrar
                  </button>
                  <a :href="downloadUrl(document.id, 'docx')">DOCX</a>
                  <a :href="downloadUrl(document.id, 'pdf')">PDF</a>
                  <button
                    type="button"
                    class="cv-list__danger"
                    @click="deleteDocument(document.id)"
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            </li>
          </ul>
        </div>
      </aside>

      <section class="cv-card cv-card--agent">
        <h2>Evaluar oferta y generar versión</h2>
        <label>
          CV base
          <select v-model="selectedDocumentId">
            <option
              disabled
              value=""
            >
              Selecciona un CV base
            </option>
            <option
              v-for="document in sourceDocuments"
              :key="document.id"
              :value="document.id"
            >
              {{ document.display_name }}
            </option>
          </select>
        </label>

        <label>
          URL de la oferta
          <input
            v-model="jobUrl"
            type="url"
            placeholder="https://..."
          />
        </label>

        <label>
          Instrucciones extra
          <textarea
            v-model="instructions"
            rows="4"
            placeholder="Ej: prioriza backend Python y experiencia con APIs."
          />
        </label>

        <button
          type="button"
          class="cv-card__primary"
          :disabled="!selectedDocumentId || !jobUrl || isOptimizing"
          @click="optimizeCv"
        >
          {{ isOptimizing ? 'Generando versión...' : 'Generar versión del CV' }}
        </button>

        <div
          v-if="optimizationResult"
          class="cv-result"
        >
          <h3>Respuesta del agente</h3>
          <p>{{ optimizationResult.content }}</p>

          <ul
            v-if="optimizationResult.structured_response?.key_adjustments?.length"
            class="cv-result__list"
          >
            <li
              v-for="item in optimizationResult.structured_response.key_adjustments"
              :key="item"
            >
              {{ item }}
            </li>
          </ul>

          <ul
            v-if="optimizationResult.structured_response?.warnings?.length"
            class="cv-result__warnings"
          >
            <li
              v-for="warning in optimizationResult.structured_response.warnings"
              :key="warning"
            >
              {{ warning }}
            </li>
          </ul>

          <div
            v-if="optimizationResult.generated_document"
            class="cv-result__downloads"
          >
            <strong>Versión generada:</strong>
            <span>{{ optimizationResult.generated_document.display_name }}</span>
            <a :href="downloadUrl(optimizationResult.generated_document.id, 'docx')">Descargar DOCX</a>
            <a :href="downloadUrl(optimizationResult.generated_document.id, 'pdf')">Descargar PDF</a>
          </div>

          <div
            v-if="firstOfferResult"
            class="cv-result__extract"
          >
            <h4>Oferta extraída</h4>
            <a
              :href="firstOfferResult.url"
              target="_blank"
              rel="noreferrer"
            >
              {{ firstOfferResult.url }}
            </a>
            <p>{{ truncate(firstOfferResult.raw_content) }}</p>
          </div>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped lang="sass">
.cv-lab
  min-height: 100vh
  padding: 2rem
  display: grid
  gap: 1.5rem
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)

.cv-lab__hero
  max-width: 1100px
  margin: 0 auto
  width: 100%

  h1
    margin: 0 0 0.75rem

  p
    margin: 0
    color: #475569

.cv-lab__error
  max-width: 1100px
  margin: 0 auto
  width: 100%
  padding: 0.9rem 1rem
  border-radius: 0.9rem
  background: #fee2e2
  color: #991b1b

.cv-lab__layout
  max-width: 1100px
  margin: 0 auto
  width: 100%
  display: grid
  gap: 1.25rem
  grid-template-columns: minmax(320px, 380px) minmax(0, 1fr)

.cv-lab__sidebar
  display: grid
  gap: 1.25rem
  align-content: start

.cv-card
  padding: 1.25rem
  border-radius: 1.25rem
  background: rgba(255, 255, 255, 0.92)
  border: 1px solid rgba(99, 102, 241, 0.12)
  display: grid
  gap: 0.85rem

  h2, h3, h4
    margin: 0

  input, select, textarea
    width: 100%
    border: 1px solid rgba(99, 102, 241, 0.16)
    border-radius: 0.8rem
    padding: 0.8rem 0.9rem
    font: inherit
    background: white

  button, a
    font: inherit

  button
    border: 0
    border-radius: 0.85rem
    padding: 0.8rem 1rem
    cursor: pointer
    background: #e0e7ff
    color: #312e81

  a
    color: #312e81
    text-decoration: none

.cv-card--agent
  align-content: start

.cv-card__primary
  background: linear-gradient(135deg, #6366f1, #4f46e5) !important
  color: white !important

.cv-list
  list-style: none
  margin: 0
  padding: 0
  display: grid
  gap: 0.85rem

.cv-list__item
  padding: 0.9rem
  border-radius: 1rem
  border: 1px solid rgba(99, 102, 241, 0.12)
  background: rgba(99, 102, 241, 0.04)
  display: grid
  gap: 0.75rem

  &--selected
    border-color: rgba(79, 70, 229, 0.35)
    background: rgba(79, 70, 229, 0.08)

.cv-list__select
  padding: 0
  background: transparent !important
  text-align: left
  display: grid
  gap: 0.2rem

  span
    font-size: 0.8rem
    color: #64748b

.cv-list__actions
  display: grid
  gap: 0.6rem

.cv-list__buttons
  display: flex
  flex-wrap: wrap
  gap: 0.5rem
  align-items: center

.cv-list__danger
  background: #fee2e2 !important
  color: #991b1b !important

.cv-result
  padding: 1rem
  border-radius: 1rem
  background: rgba(15, 23, 42, 0.04)
  display: grid
  gap: 0.9rem

  p
    margin: 0
    color: #334155

.cv-result__list,
.cv-result__warnings
  margin: 0
  padding-left: 1rem
  display: grid
  gap: 0.35rem

.cv-result__warnings
  color: #92400e

.cv-result__downloads
  display: flex
  flex-wrap: wrap
  gap: 0.6rem
  align-items: center

.cv-result__extract
  display: grid
  gap: 0.45rem

@media (max-width: 960px)
  .cv-lab__layout
    grid-template-columns: 1fr
</style>
