<template>
  <div id="app-layout">
    <Navbar />
    <router-view />
  </div>
</template>

<script setup>
import { watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from './components/Navbar.vue'
import { useAuthStore } from './stores/auth'
import api from './api'

const authStore = useAuthStore()
const router = useRouter()

// ──────────────────────────────────────
// WebSocket Presence (Online/Offline tracking)
// ──────────────────────────────────────
let presenceWs = null
let heartbeatInterval = null
let reconnectTimeout = null

function connectPresence() {
  const token = authStore.token
  if (!token) return

  // Tránh kết nối trùng lặp
  if (presenceWs && presenceWs.readyState === WebSocket.OPEN) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = import.meta.env.VITE_API_URL
    ? new URL(import.meta.env.VITE_API_URL).host
    : window.location.host
  const wsUrl = `${protocol}//${host}/api/v1/admin/ws/presence?token=${token}`

  try {
    presenceWs = new WebSocket(wsUrl)

    presenceWs.onopen = () => {
      console.log('🟢 Presence WebSocket connected')
      // Heartbeat ping mỗi 30 giây để giữ kết nối
      heartbeatInterval = setInterval(() => {
        if (presenceWs && presenceWs.readyState === WebSocket.OPEN) {
          presenceWs.send('ping')
        }
      }, 30000)
    }

    presenceWs.onclose = () => {
      console.log('🔴 Presence WebSocket disconnected')
      clearInterval(heartbeatInterval)
      heartbeatInterval = null
      // Auto-reconnect sau 5 giây (chỉ khi user vẫn đang đăng nhập)
      if (authStore.token) {
        reconnectTimeout = setTimeout(connectPresence, 5000)
      }
    }

    presenceWs.onerror = (err) => {
      console.warn('Presence WS error:', err)
    }
  } catch (e) {
    console.warn('Failed to connect presence WS:', e)
  }
}

function disconnectPresence() {
  clearInterval(heartbeatInterval)
  clearTimeout(reconnectTimeout)
  heartbeatInterval = null
  reconnectTimeout = null
  if (presenceWs) {
    presenceWs.onclose = null // Ngăn auto-reconnect
    presenceWs.close()
    presenceWs = null
  }
}

// ──────────────────────────────────────
// Page View Tracking
// ──────────────────────────────────────
async function trackPageView(path) {
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const utmSource = urlParams.get('utm_source')

    await api.post('/admin/track', {
      path: path,
      referrer: utmSource || document.referrer || null,
    })
  } catch (e) {
    // Bỏ qua lỗi tracking (không ảnh hưởng UX)
  }
}

// ──────────────────────────────────────
// Lifecycle
// ──────────────────────────────────────

// Theo dõi trạng thái đăng nhập: kết nối/ngắt WS
watch(
  () => authStore.token,
  (newToken) => {
    if (newToken) {
      connectPresence()
    } else {
      disconnectPresence()
    }
  }
)

// Theo dõi chuyển route → ghi nhận truy cập
router.afterEach((to) => {
  trackPageView(to.fullPath)
})

onMounted(() => {
  // Kết nối WS nếu đã đăng nhập sẵn
  if (authStore.token) {
    connectPresence()
  }
  // Track trang đầu tiên
  trackPageView(window.location.pathname)
})

onUnmounted(() => {
  disconnectPresence()
})
</script>

<style scoped>
#app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
