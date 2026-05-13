/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_TAVILY_API_KEY?: string
  readonly VITE_APP_BACKEND_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
