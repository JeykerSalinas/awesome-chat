import axios from 'axios'
import type { App, InjectionKey } from 'vue'
import type { AxiosInstance } from 'axios'

export const apiBaseUrl = import.meta.env.VITE_APP_BACKEND_URL ?? 'http://127.0.0.1:8001'

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
})

export const apiClientKey: InjectionKey<AxiosInstance> = Symbol('apiClient')

export const isAxiosError = axios.isAxiosError

export default {
  install(app: App) {
    app.config.globalProperties.$api = apiClient
    app.provide(apiClientKey, apiClient)
  },
}
