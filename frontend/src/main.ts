import { createApp } from 'vue'
import App from './App.vue'
import axiosPlugin from './plugins/axios'
import router from './router'
import '@/styles/reset.sass'

const app = createApp(App)

app.use(axiosPlugin)
app.use(router)

app.mount('#app')
