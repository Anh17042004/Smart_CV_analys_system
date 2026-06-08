/**
 * CV MENTOR — Auth Pinia Store
 * ===============================
 * File này quản lý trạng thái đăng nhập/đăng ký của user.
 *
 * Kiến thức cần biết:
 * - Pinia là state management cho Vue 3 (thay thế Vuex)
 * - defineStore(): tạo 1 store
 * - state: dữ liệu chia sẻ giữa các component
 * - getters: computed properties từ state
 * - actions: methods thay đổi state (có thể async)
 * 
 * Ví dụ sử dụng trong component:
 *   import { useAuthStore } from '@/stores/auth'
 *   const authStore = useAuthStore()
 *   await authStore.login('email', 'password')
 *   console.log(authStore.isAuthenticated)
 */

import { defineStore } from 'pinia'
import api from '../api'

const parseError = (error) => {
  const data = error.response?.data
  if (data) {
    if (Array.isArray(data.detail)) {
      return data.detail.map(err => {
        const field = err.loc[err.loc.length - 1]
        let msg = err.msg
        if (msg.includes('at least 8 characters')) {
          msg = 'phải chứa ít nhất 8 ký tự'
        }
        return `${field}: ${msg}`
      }).join(', ')
    }
    if (data.message) {
      return data.message
    }
  }
  return error.message || 'Thao tác thất bại'
}

export const useAuthStore = defineStore('auth', {
  // === State ===
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
  }),

  // === Getters (computed) ===
  getters: {
    isAuthenticated: (state) => !!state.token,
    userName: (state) => state.user?.full_name || 'User',
  },

  // === Actions ===
  actions: {
    async login(email, password) {
      try {
        const response = await api.post('/auth/login', { email, password })
        const token = response.data.access_token
        this.token = token
        localStorage.setItem('token', token)
        await this.fetchUser()
        return response.data
      } catch (error) {
        throw parseError(error)
      }
    },

    async register(email, password, fullName) {
      try {
        const response = await api.post('/auth/register', {
          email,
          password,
          full_name: fullName
        })
        return response.data
      } catch (error) {
        throw parseError(error)
      }
    },

    async fetchUser() {
      try {
        const response = await api.get('/auth/me')
        this.user = response.data
        return response.data
      } catch (error) {
        this.logout()
        throw parseError(error)
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
    },

    async updateProfile(fullName) {
      try {
        const response = await api.put('/auth/profile', { full_name: fullName })
        this.user = response.data
        return response.data
      } catch (error) {
        throw parseError(error)
      }
    },

    async changePassword(currentPassword, newPassword) {
      try {
        const response = await api.put('/auth/change-password', {
          current_password: currentPassword,
          new_password: newPassword
        })
        return response.data
      } catch (error) {
        throw parseError(error)
      }
    }
  }
})
