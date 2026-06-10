/**
 * CV MENTOR — Vue Router
 * ========================
 * File này định nghĩa tất cả routes (đường dẫn) của ứng dụng.
 * 
 * Kiến thức cần biết:
 * - createRouter(): tạo router instance
 * - createWebHistory(): dùng HTML5 History API (URL đẹp, không có #)
 * - meta.requireAuth: đánh dấu route cần đăng nhập
 * - beforeEach(): navigation guard — chạy trước mỗi lần chuyển trang
 * - Lazy loading: () => import('...') — chỉ load component khi cần
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  // ===== Public Routes =====
  {
    path: '/',
    name: 'Landing',
    component: () => import('../views/Landing.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue')
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('../views/About.vue')
  },

  // ===== Protected Routes =====
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requireAuth: true }
  },
  {
    path: '/cv-analysis/:id?',
    name: 'CVAnalysis',
    component: () => import('../views/CVAnalysis.vue'),
    meta: { requireAuth: true }
  },
  {
    path: '/job-recommendation',
    name: 'JobRecommendation',
    component: () => import('../views/JobRecommendation.vue'),
    meta: { requireAuth: true }
  },
  {
    path: '/job-search',
    name: 'JobSearch',
    component: () => import('../views/JobSearch.vue'),
    meta: { requireAuth: true }
  },
  {
    path: '/cv-history',
    name: 'CVHistory',
    component: () => import('../views/CVHistory.vue'),
    meta: { requireAuth: true }
  },
  {
    path: '/saved-jobs',
    name: 'SavedJobs',
    component: () => import('../views/SavedJobs.vue'),
    meta: { requireAuth: true }
  },
  {
    path: '/interview',
    name: 'MockInterview',
    component: () => import('../views/MockInterview.vue'),
    meta: { requireAuth: true }
  },
  {
    path: '/interview/result/:id',
    name: 'InterviewResult',
    component: () => import('../views/InterviewResult.vue'),
    meta: { requireAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// === Navigation Guard ===
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Tự động load lại profile user nếu có sẵn token trong localStorage
  if (authStore.token && !authStore.user) {
    try {
      await authStore.fetchUser()
    } catch (err) {
      console.warn('Phiên đăng nhập hết hạn hoặc token lỗi:', err)
    }
  }

  if (to.meta.requireAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
