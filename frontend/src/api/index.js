/**
 * CV MENTOR — Axios API Client
 * ================================
 * File này tạo 1 axios instance dùng chung cho toàn app.
 * 
 * Kiến thức cần biết:
 * - axios.create(): tạo instance với config mặc định
 * - baseURL: tất cả request sẽ thêm prefix "/api"
 * - interceptors.request: chạy TRƯỚC mỗi request (gắn JWT token)
 * - interceptors.response: chạy SAU mỗi response (xử lý lỗi 401)
 * 
 * Ví dụ sử dụng:
 *   import api from '@/api'
 *   const { data } = await api.get('/auth/me')  // GET /api/auth/me
 *   const { data } = await api.post('/auth/login', { email, password })
 */

import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,  // 60 giây (AI cần thời gian xử lý)
  headers: {
    'Content-Type': 'application/json'
  }
})

// === Request Interceptor ===
// Tự động gắn JWT token vào header Authorization trước MỌI request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// === Response Interceptor ===
// Xử lý lỗi chung: nếu 401 → xóa token, redirect login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      // TODO: redirect to login page (sẽ thêm khi có router)
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
