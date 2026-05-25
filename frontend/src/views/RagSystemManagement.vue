<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { apiBaseUrl, apiClient, isAxiosError } from '@/plugins/axios'

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

type RagSettings = {
  systemName: string
  embeddingProvider: string
  chunkSize: number
  chunkOverlap: number
  topK: number
  retrievalMode: 'similarity' | 'mmr' | 'hybrid'
  responseStyle: 'concise' | 'balanced' | 'detailed'
  temperature: number
  promptInstructions: string
}

const documents = ref<DocumentSummary[]>([])
const selectedDocumentIds = ref<string[]>([])
const uploadName = ref('')
const uploadFile = ref<File | null>(null)
const errorMessage = ref('')
const infoMessage = ref('')
const isUploading = ref(false)
const isRefreshing = ref(false)
const isPinging = ref(false)
const endpointResponse = ref('')
const editedNames = reactive<Record<string, string>>({})

const ragSettings = reactive<RagSettings>({
  systemName: 'RAG Workspace',
  embeddingProvider: 'pending',
  chunkSize: 900,
  chunkOverlap: 120,
  topK: 4,
  retrievalMode: 'similarity',
  responseStyle: 'balanced',
  temperature: 0.2,
  promptInstructions: '',
})

const uploadedDocuments = computed(() => documents.value.filter((item) => item.kind === 'uploaded'))
const generatedDocuments = computed(() => documents.value.filter((item) => item.kind === 'generated'))
const selectedDocuments = computed(() =>
  documents.value.filter((item) => selectedDocumentIds.value.includes(item.id)),
)

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  uploadFile.value = input.files?.[0] ?? null
}

async function fetchDocuments() {
  isRefreshing.value = true
  try {
    const { data } = await apiClient.get<DocumentSummary[]>('/documents')
    documents.value = data

    for (const document of data) {
      editedNames[document.id] = document.display_name
    }

    selectedDocumentIds.value = selectedDocumentIds.value.filter((id) =>
      data.some((document) => document.id === id),
    )
  } finally {
    isRefreshing.value = false
  }
}

async function uploadDocument() {
  if (!uploadFile.value || isUploading.value) return

  const form = new FormData()
  form.append('file', uploadFile.value)
  if (uploadName.value.trim()) {
    form.append('display_name', uploadName.value.trim())
  }

  errorMessage.value = ''
  infoMessage.value = ''
  isUploading.value = true

  try {
    await apiClient.post('/rag-system/documents', form)
    uploadFile.value = null
    uploadName.value = ''
    infoMessage.value = 'Documento subido. Ya puedes incluirlo en tu selección RAG.'
    await fetchDocuments()
  } catch (error) {
    errorMessage.value = isAxiosError(error)
      ? error.response?.data?.detail ?? 'No se pudo subir el documento.'
      : 'No se pudo subir el documento.'
  } finally {
    isUploading.value = false
  }
}

async function renameDocument(documentId: string) {
  const displayName = editedNames[documentId]?.trim()
  if (!displayName) return

  errorMessage.value = ''
  infoMessage.value = ''

  try {
    await apiClient.patch(`/documents/${documentId}`, { display_name: displayName })
    infoMessage.value = 'Documento renombrado.'
    await fetchDocuments()
  } catch (error) {
    errorMessage.value = isAxiosError(error)
      ? error.response?.data?.detail ?? 'No se pudo renombrar el documento.'
      : 'No se pudo renombrar el documento.'
  }
}

async function deleteDocument(documentId: string) {
  errorMessage.value = ''
  infoMessage.value = ''

  try {
    await apiClient.delete(`/documents/${documentId}`)
    selectedDocumentIds.value = selectedDocumentIds.value.filter((id) => id !== documentId)
    infoMessage.value = 'Documento eliminado.'
    await fetchDocuments()
  } catch (error) {
    errorMessage.value = isAxiosError(error)
      ? error.response?.data?.detail ?? 'No se pudo eliminar el documento.'
      : 'No se pudo eliminar el documento.'
  }
}

function toggleDocumentSelection(documentId: string) {
  if (selectedDocumentIds.value.includes(documentId)) {
    selectedDocumentIds.value = selectedDocumentIds.value.filter((id) => id !== documentId)
    return
  }

  selectedDocumentIds.value = [...selectedDocumentIds.value, documentId]
}

function downloadUrl(documentId: string, format: 'docx' | 'pdf') {
  return `${apiBaseUrl}/documents/${documentId}/download?format=${format}`
}

async function pingRagEndpoint() {
  errorMessage.value = ''
  infoMessage.value = ''
  endpointResponse.value = ''
  isPinging.value = true

  try {
    const { data } = await apiClient.get<string>('/rag-system')
    endpointResponse.value = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
    infoMessage.value = 'El endpoint de prueba respondió correctamente.'
  } catch (error) {
    errorMessage.value = isAxiosError(error)
      ? error.response?.data?.detail ?? 'El endpoint de prueba no respondió como se esperaba.'
      : 'El endpoint de prueba no respondió como se esperaba.'
  } finally {
    isPinging.value = false
  }
}

function resetLocalSettings() {
  ragSettings.systemName = 'RAG Workspace'
  ragSettings.embeddingProvider = 'pending'
  ragSettings.chunkSize = 900
  ragSettings.chunkOverlap = 120
  ragSettings.topK = 4
  ragSettings.retrievalMode = 'similarity'
  ragSettings.responseStyle = 'balanced'
  ragSettings.temperature = 0.2
  ragSettings.promptInstructions = ''
  infoMessage.value = 'Configuración local restablecida. Aún no se persiste en backend.'
}

onMounted(() => {
  void fetchDocuments()
})
</script>

<template>
  <main class="rag-lab">
    <section class="rag-lab__hero">
      <div>
        <p class="rag-lab__eyebrow">Knowledge Base Console</p>
        <h1>RAG System Management</h1>
        <p>
          Prepara la base documental, define parámetros de recuperación y prueba el endpoint
          actual mientras completas la API del módulo RAG.
        </p>
      </div>

      <div class="rag-hero-card">
        <span>{{ selectedDocumentIds.length }} documentos seleccionados</span>
        <strong>{{ uploadedDocuments.length }} documentos base disponibles</strong>
        <small>La configuración de esta pantalla todavía es local al frontend.</small>
      </div>
    </section>

    <p
      v-if="errorMessage"
      class="rag-banner rag-banner--error"
    >
      {{ errorMessage }}
    </p>

    <p
      v-else-if="infoMessage"
      class="rag-banner rag-banner--info"
    >
      {{ infoMessage }}
    </p>

    <section class="rag-layout">
      <aside class="rag-sidebar">
        <div class="rag-card">
          <div class="rag-card__header">
            <h2>Subir documentos</h2>
            <button
              type="button"
              class="rag-button rag-button--ghost"
              :disabled="isRefreshing"
              @click="fetchDocuments"
            >
              {{ isRefreshing ? 'Actualizando...' : 'Refrescar' }}
            </button>
          </div>

          <input
            type="file"
            accept=".docx,.pdf,application/pdf"
            @change="onFileChange"
          />
          <input
            v-model="uploadName"
            type="text"
            placeholder="Nombre para mostrar"
          />
          <button
            type="button"
            class="rag-button"
            :disabled="!uploadFile || isUploading"
            @click="uploadDocument"
          >
            {{ isUploading ? 'Subiendo...' : 'Subir a la base documental' }}
          </button>
        </div>

        <div class="rag-card">
          <h2>Corpus disponible</h2>

          <ul class="rag-list">
            <li
              v-for="document in uploadedDocuments"
              :key="document.id"
              class="rag-list__item"
              :class="{ 'rag-list__item--selected': selectedDocumentIds.includes(document.id) }"
            >
              <label class="rag-list__toggle">
                <input
                  :checked="selectedDocumentIds.includes(document.id)"
                  type="checkbox"
                  @change="toggleDocumentSelection(document.id)"
                />
                <span>
                  <strong>{{ document.display_name }}</strong>
                  <small>{{ document.original_filename }}</small>
                </span>
              </label>

              <div class="rag-list__meta">
                <input
                  v-model="editedNames[document.id]"
                  type="text"
                />
                <div class="rag-list__actions">
                  <button
                    type="button"
                    class="rag-button rag-button--ghost"
                    @click="renameDocument(document.id)"
                  >
                    Renombrar
                  </button>
                  <a :href="downloadUrl(document.id, 'docx')">DOCX</a>
                  <a :href="downloadUrl(document.id, 'pdf')">PDF</a>
                  <button
                    type="button"
                    class="rag-button rag-button--danger"
                    @click="deleteDocument(document.id)"
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            </li>
          </ul>

          <p
            v-if="!uploadedDocuments.length"
            class="rag-empty"
          >
            Todavía no hay documentos subidos para construir el corpus.
          </p>
        </div>

        <div class="rag-card">
          <h2>Derivados actuales</h2>
          <ul class="rag-derived">
            <li
              v-for="document in generatedDocuments"
              :key="document.id"
            >
              <strong>{{ document.display_name }}</strong>
              <span>{{ document.source_document_id || 'sin origen' }}</span>
            </li>
          </ul>
          <p
            v-if="!generatedDocuments.length"
            class="rag-empty"
          >
            Aquí aparecerán variantes generadas u otros artefactos que quieras reutilizar.
          </p>
        </div>
      </aside>

      <section class="rag-main">
        <div class="rag-card">
          <div class="rag-card__header">
            <h2>Configuración local del sistema</h2>
            <button
              type="button"
              class="rag-button rag-button--ghost"
              @click="resetLocalSettings"
            >
              Restablecer
            </button>
          </div>

          <div class="rag-form-grid">
            <label>
              Nombre del sistema
              <input
                v-model="ragSettings.systemName"
                type="text"
                placeholder="Ej: Base interna de soporte"
              />
            </label>

            <label>
              Proveedor de embeddings
              <input
                v-model="ragSettings.embeddingProvider"
                type="text"
                placeholder="Ej: openai, ollama, bge-small"
              />
            </label>

            <label>
              Chunk size
              <input
                v-model.number="ragSettings.chunkSize"
                type="number"
                min="100"
                step="50"
              />
            </label>

            <label>
              Chunk overlap
              <input
                v-model.number="ragSettings.chunkOverlap"
                type="number"
                min="0"
                step="10"
              />
            </label>

            <label>
              Top K
              <input
                v-model.number="ragSettings.topK"
                type="number"
                min="1"
                max="20"
              />
            </label>

            <label>
              Temperatura
              <input
                v-model.number="ragSettings.temperature"
                type="number"
                min="0"
                max="1"
                step="0.1"
              />
            </label>

            <label>
              Modo de retrieval
              <select v-model="ragSettings.retrievalMode">
                <option value="similarity">
                  Similarity
                </option>
                <option value="mmr">
                  MMR
                </option>
                <option value="hybrid">
                  Hybrid
                </option>
              </select>
            </label>

            <label>
              Estilo de respuesta
              <select v-model="ragSettings.responseStyle">
                <option value="concise">
                  Concise
                </option>
                <option value="balanced">
                  Balanced
                </option>
                <option value="detailed">
                  Detailed
                </option>
              </select>
            </label>
          </div>

          <label>
            Instrucciones del sistema
            <textarea
              v-model="ragSettings.promptInstructions"
              rows="5"
              placeholder="Ej: responde solo con base en documentos seleccionados y cita la fuente interna."
            />
          </label>
        </div>

        <div class="rag-card">
          <h2>Resumen de indexación prevista</h2>
          <div class="rag-summary">
            <div>
              <span>Corpus seleccionado</span>
              <strong>{{ selectedDocuments.length }} documentos</strong>
            </div>
            <div>
              <span>Chunking</span>
              <strong>{{ ragSettings.chunkSize }}/{{ ragSettings.chunkOverlap }}</strong>
            </div>
            <div>
              <span>Retrieval</span>
              <strong>{{ ragSettings.retrievalMode }}</strong>
            </div>
            <div>
              <span>Top K</span>
              <strong>{{ ragSettings.topK }}</strong>
            </div>
          </div>

          <ul class="rag-selection">
            <li
              v-for="document in selectedDocuments"
              :key="document.id"
            >
              {{ document.display_name }}
            </li>
          </ul>

          <p
            v-if="!selectedDocuments.length"
            class="rag-empty"
          >
            Selecciona documentos a la izquierda para definir qué entrará al índice.
          </p>
        </div>

        <div class="rag-card">
          <div class="rag-card__header">
            <h2>Prueba del endpoint actual</h2>
            <button
              type="button"
              class="rag-button"
              :disabled="isPinging"
              @click="pingRagEndpoint"
            >
              {{ isPinging ? 'Probando...' : 'Llamar GET /rag-system' }}
            </button>
          </div>

          <p class="rag-helper">
            Esta sección no asume una API RAG terminada. Solo prueba el endpoint actual que
            vayas construyendo en FastAPI.
          </p>

          <div class="rag-code">
            <span>Endpoint</span>
            <code>GET {{ apiBaseUrl }}/rag-system</code>
          </div>

          <pre
            v-if="endpointResponse"
            class="rag-response"
          ><code>{{ endpointResponse }}</code></pre>
        </div>

        <div class="rag-card rag-card--notes">
          <h2>Siguiente integración backend</h2>
          <ul class="rag-notes">
            <li>Persistir esta configuración en un schema y endpoint propio del módulo RAG.</li>
            <li>Agregar un endpoint para indexar solo los documentos seleccionados.</li>
            <li>Incluir estado de indexación, fecha de última sincronización y conteo de chunks.</li>
            <li>Crear una ruta de prueba para preguntas y respuestas con fuentes recuperadas.</li>
          </ul>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped lang="sass">
.rag-lab
  min-height: 100vh
  padding: 2rem
  display: grid
  gap: 1.5rem
  background: radial-gradient(circle at top left, rgba(245, 158, 11, 0.18), transparent 28%), linear-gradient(180deg, #f8fafc 0%, #eef6ff 100%)

.rag-lab__hero
  max-width: 1200px
  margin: 0 auto
  width: 100%
  display: grid
  gap: 1rem
  grid-template-columns: minmax(0, 1fr) minmax(280px, 320px)
  align-items: start

  h1
    margin: 0.35rem 0 0.75rem

  p
    margin: 0
    color: #475569

.rag-lab__eyebrow
  margin: 0
  color: #92400e !important
  font-size: 0.82rem
  font-weight: 700
  text-transform: uppercase
  letter-spacing: 0.12em

.rag-hero-card
  padding: 1.2rem
  border-radius: 1.2rem
  background: rgba(255, 251, 235, 0.92)
  border: 1px solid rgba(245, 158, 11, 0.24)
  display: grid
  gap: 0.35rem

  span, small
    color: #78350f

  strong
    font-size: 1.1rem
    color: #451a03

.rag-banner
  max-width: 1200px
  width: 100%
  margin: 0 auto
  padding: 0.95rem 1rem
  border-radius: 1rem

.rag-banner--error
  background: #fee2e2
  color: #991b1b

.rag-banner--info
  background: #dcfce7
  color: #166534

.rag-layout
  max-width: 1200px
  margin: 0 auto
  width: 100%
  display: grid
  gap: 1.25rem
  grid-template-columns: minmax(320px, 390px) minmax(0, 1fr)

.rag-sidebar,
.rag-main
  display: grid
  gap: 1.25rem
  align-content: start

.rag-card
  padding: 1.25rem
  border-radius: 1.25rem
  background: rgba(255, 255, 255, 0.94)
  border: 1px solid rgba(148, 163, 184, 0.18)
  box-shadow: 0 20px 45px -34px rgba(15, 23, 42, 0.45)
  display: grid
  gap: 0.9rem

  h2
    margin: 0

  input, select, textarea
    width: 100%
    border: 1px solid rgba(148, 163, 184, 0.34)
    border-radius: 0.85rem
    padding: 0.8rem 0.9rem
    font: inherit
    background: #fff

  textarea
    resize: vertical

  a
    color: #1d4ed8
    text-decoration: none
    font-weight: 600

.rag-card__header
  display: flex
  justify-content: space-between
  gap: 0.75rem
  align-items: center

.rag-card--notes
  background: linear-gradient(180deg, rgba(255, 251, 235, 0.96), rgba(255, 255, 255, 0.96))

.rag-button
  border: 0
  border-radius: 0.9rem
  padding: 0.8rem 1rem
  cursor: pointer
  font: inherit
  background: linear-gradient(135deg, #0f766e, #0f766e 55%, #0f172a)
  color: white

  &:disabled
    cursor: not-allowed
    opacity: 0.6

.rag-button--ghost
  background: #e2e8f0
  color: #0f172a

.rag-button--danger
  background: #fee2e2
  color: #991b1b

.rag-list,
.rag-derived,
.rag-selection,
.rag-notes
  list-style: none
  margin: 0
  padding: 0
  display: grid
  gap: 0.85rem

.rag-list__item
  padding: 0.95rem
  border-radius: 1rem
  border: 1px solid rgba(148, 163, 184, 0.24)
  background: rgba(248, 250, 252, 0.9)
  display: grid
  gap: 0.8rem

.rag-list__item--selected
  border-color: rgba(13, 148, 136, 0.4)
  background: rgba(240, 253, 250, 0.98)

.rag-list__toggle
  display: grid
  grid-template-columns: auto minmax(0, 1fr)
  gap: 0.7rem
  align-items: start
  cursor: pointer

  input
    width: auto
    margin-top: 0.2rem

  span
    display: grid
    gap: 0.2rem

  small
    color: #64748b
    word-break: break-word

.rag-list__meta
  display: grid
  gap: 0.6rem

.rag-list__actions
  display: flex
  flex-wrap: wrap
  gap: 0.5rem
  align-items: center

.rag-derived li,
.rag-selection li
  padding: 0.8rem 0.9rem
  border-radius: 0.9rem
  background: rgba(15, 23, 42, 0.04)
  display: grid
  gap: 0.2rem

  span
    color: #64748b
    font-size: 0.86rem

.rag-form-grid
  display: grid
  grid-template-columns: repeat(2, minmax(0, 1fr))
  gap: 0.9rem

  label
    display: grid
    gap: 0.45rem

.rag-summary
  display: grid
  grid-template-columns: repeat(4, minmax(0, 1fr))
  gap: 0.85rem

  div
    padding: 0.95rem
    border-radius: 1rem
    background: rgba(15, 23, 42, 0.04)
    display: grid
    gap: 0.3rem

  span
    color: #64748b
    font-size: 0.82rem

.rag-helper
  margin: 0
  color: #475569

.rag-code
  padding: 0.95rem 1rem
  border-radius: 1rem
  background: #0f172a
  color: #e2e8f0
  display: grid
  gap: 0.4rem

  span
    color: #94a3b8
    font-size: 0.8rem
    text-transform: uppercase
    letter-spacing: 0.08em

.rag-response
  margin: 0
  padding: 1rem
  border-radius: 1rem
  background: rgba(15, 23, 42, 0.96)
  color: #f8fafc
  overflow-x: auto

.rag-empty
  margin: 0
  color: #64748b

@media (max-width: 960px)
  .rag-lab__hero,
  .rag-layout,
  .rag-summary,
  .rag-form-grid
    grid-template-columns: 1fr
</style>
