/**
 * CV MENTOR — Vue App Entry Point
 * ==================================
 * Mount Vue app với Pinia (state) + Router (navigation)
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import i18n from './i18n'

// Global styles
import './assets/styles/main.css'

const app = createApp(App)

// Đăng ký plugins
app.use(createPinia())  // State management
app.use(router)          // Routing
app.use(i18n)            // Internationalization

// Mount app vào #app trong index.html
app.mount('#app')
