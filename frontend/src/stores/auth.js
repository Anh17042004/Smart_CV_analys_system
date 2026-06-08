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
        throw error.response?.data?.detail || error.message || 'Đăng nhập thất bại'
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
        throw error.response?.data?.detail || error.message || 'Đăng ký thất bại'
      }
    },

    async fetchUser() {
      try {
        const response = await api.get('/auth/me')
        this.user = response.data
        return response.data
      } catch (error) {
        this.logout()
        throw error.response?.data?.detail || error.message || 'Không thể lấy thông tin người dùng'
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
        throw error.response?.data?.detail || error.message || 'Cập nhật thông tin thất bại'
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
        throw error.response?.data?.detail || error.message || 'Đổi mật khẩu thất bại'
      }
    }
  }
})
