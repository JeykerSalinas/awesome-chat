/// <reference types="vite/client" />
/// <reference types="unplugin-icons/types/vue" />
import 'vue-router'
import '@/types/vue'

interface ImportMetaEnv {
  readonly VITE_TAVILY_API_KEY?: string
  readonly VITE_APP_BACKEND_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module 'vue-router' {
  interface RouteMeta {
    menuLabel?: string
    visibleInMenu?: boolean
    menuOrder?: number
  }
}
