import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Icons from 'unplugin-icons/vite'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  root: fileURLToPath(new URL('./', import.meta.url)),
  plugins: [
    vue(),
    Icons({
      compiler: 'vue3',
    }),
    vueDevTools(),
  ],
  build: {
    outDir: fileURLToPath(new URL('../dist/frontend', import.meta.url)),
    emptyOutDir: true,
  },
  cacheDir: fileURLToPath(new URL('../node_modules/.vite/frontend', import.meta.url)),
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
