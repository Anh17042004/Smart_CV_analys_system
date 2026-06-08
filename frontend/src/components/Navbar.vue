<template>
  <header class="navbar-header">
    <div class="navbar-container">
      <router-link to="/" class="brand-link">
        <img :src="logo" alt="CV Mentor" class="brand-logo" />
      </router-link>

      <nav class="nav-links">
        <router-link to="/dashboard" class="nav-item">{{ t('nav.dashboard') }}</router-link>
        <router-link to="/cv-analysis" class="nav-item">{{ t('nav.cvAnalysis') }}</router-link>
        <router-link to="/interview" class="nav-item">{{ t('nav.mockInterview') }}</router-link>
        
        <div 
          class="dropdown" 
          @mouseenter="showDropdown = true" 
          @mouseleave="showDropdown = false"
        >
          <button 
            class="nav-item dropdown-toggle" 
            :class="{ 'active': isJobsRoute }"
          >
            {{ t('nav.jobs') }} <span class="arrow">▼</span>
          </button>
          <div v-show="showDropdown" class="dropdown-menu">
            <router-link to="/job-recommendation" class="dropdown-item" @click="showDropdown = false">
              {{ t('nav.matchJobs') }}
            </router-link>
            <router-link to="/job-search" class="dropdown-item" @click="showDropdown = false">
              {{ t('nav.searchJobs') }}
            </router-link>
          </div>
        </div>
      </nav>

      <div class="auth-buttons">
        <!-- Language Toggle -->
        <button class="lang-toggle-btn" @click="toggleLanguage" :title="locale === 'vi' ? 'Switch to English' : 'Chuyển sang Tiếng Việt'">
          <span class="lang-flag">{{ locale === 'vi' ? '🇬🇧' : '🇻🇳' }}</span>
          <span class="lang-code">{{ locale === 'vi' ? 'EN' : 'VI' }}</span>
        </button>

        <!-- Theme Toggle -->
        <button class="theme-toggle-btn" @click="toggleTheme" :title="theme === 'dark' ? t('nav.lightMode') : t('nav.darkMode')">
          <span v-if="theme === 'dark'">☀️</span>
          <span v-else>🌙</span>
        </button>

        <template v-if="authStore.isAuthenticated">
          <div class="user-dropdown-container">
            <button class="avatar-button" @click.stop="showUserDropdown = !showUserDropdown">
              <span class="avatar-fallback">{{ userInitials }}</span>
            </button>
            
            <div v-show="showUserDropdown" class="user-dropdown-menu" @click.stop>
              <div class="user-dropdown-header">
                <p class="user-dropdown-name">{{ authStore.user?.full_name || authStore.userName }}</p>
                <p class="user-dropdown-email">{{ authStore.user?.email || 'No email' }}</p>
                <span class="user-role-badge" :class="authStore.user?.role || 'user'">
                  {{ authStore.user?.role || 'User' }}
                </span>
              </div>
              
              <div class="user-dropdown-divider"></div>
              
              <div class="user-dropdown-links">
                <button class="user-dropdown-item" @click.stop="openProfileModal">
                  👤 {{ t('profile.title') }}
                </button>
                <router-link to="/dashboard" class="user-dropdown-item" @click="showUserDropdown = false">
                  {{ t('nav.dashboardLink') }}
                </router-link>
                <router-link to="/cv-history" class="user-dropdown-item" @click="showUserDropdown = false">
                  {{ t('nav.cvHistory') }}
                </router-link>
                <router-link to="/saved-jobs" class="user-dropdown-item" @click="showUserDropdown = false">
                  {{ t('nav.savedJobs') }}
                </router-link>
                <router-link to="/cv-analysis" class="user-dropdown-item" @click="showUserDropdown = false">
                  {{ t('nav.analyzeCV') }}
                </router-link>
                <router-link to="/job-recommendation" class="user-dropdown-item" @click="showUserDropdown = false">
                  {{ t('nav.matchJobsShort') }}
                </router-link>
                <router-link to="/job-search" class="user-dropdown-item" @click="showUserDropdown = false">
                  {{ t('nav.searchJobsShort') }}
                </router-link>
                <router-link to="/interview" class="user-dropdown-item" @click="showUserDropdown = false">
                  {{ t('nav.mockInterview') }}
                </router-link>
              </div>
              
              <div class="user-dropdown-divider"></div>
              
              <button @click="handleLogout" class="user-dropdown-item logout-item">
                {{ t('nav.logout') }}
              </button>
            </div>
          </div>
        </template>
        <template v-else>
          <router-link to="/login" class="btn-login-outline">{{ t('nav.login') }}</router-link>
          <router-link to="/register" class="btn-primary-nav">{{ t('nav.register') }}</router-link>
        </template>
      </div>
    </div>
  </header>

  <!-- Profile & Password Modal -->
  <div v-if="showProfileModal" class="modal-overlay" @click="closeProfileModal">
    <div class="modal-card glass-card" @click.stop>
      <div class="modal-header">
        <h3>{{ t('profile.title') }}</h3>
        <button class="close-btn" @click="closeProfileModal">✕</button>
      </div>
      
      <div class="modal-body">
        <!-- Notification Alert -->
        <div v-if="profileMessage" class="alert-box" :class="profileMessageType">
          {{ profileMessage }}
        </div>

        <!-- Update Profile Info Form -->
        <form @submit.prevent="handleUpdateProfile" class="profile-form">
          <h4 class="form-section-title">📝 {{ t('profile.updateInfo') }}</h4>
          <div class="form-group">
            <label class="form-label">{{ t('profile.fullName') }}</label>
            <input 
              type="text" 
              v-model="formFullName" 
              class="form-input" 
              required 
            />
          </div>
          
          <div class="form-group">
            <label class="form-label">{{ t('profile.email') }}</label>
            <input 
              type="text" 
              :value="authStore.user?.email" 
              class="form-input disabled" 
              disabled 
            />
          </div>

          <div class="form-group">
            <label class="form-label">{{ t('profile.role') }}</label>
            <input 
              type="text" 
              :value="authStore.user?.role" 
              class="form-input disabled" 
              disabled 
            />
          </div>

          <button type="submit" class="btn-primary btn-save" :disabled="isUpdatingProfile">
            <span v-if="isUpdatingProfile">⏳</span>
            <span v-else>{{ t('profile.saveChanges') }}</span>
          </button>
        </form>

        <div class="modal-divider"></div>

        <!-- Change Password Form -->
        <form @submit.prevent="handleChangePassword" class="profile-form">
          <h4 class="form-section-title">🔒 {{ t('profile.changePassword') }}</h4>
          <div class="form-group">
            <label class="form-label">{{ t('profile.currentPassword') }}</label>
            <div class="password-group">
              <input 
                :type="showCurrentPassword ? 'text' : 'password'" 
                v-model="formCurrentPassword" 
                class="form-input" 
                required 
              />
              <button 
                type="button" 
                class="password-toggle" 
                @click="showCurrentPassword = !showCurrentPassword"
                tabindex="-1"
              >
                {{ showCurrentPassword ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">{{ t('profile.newPassword') }}</label>
            <div class="password-group">
              <input 
                :type="showNewPassword ? 'text' : 'password'" 
                v-model="formNewPassword" 
                class="form-input" 
                required 
              />
              <button 
                type="button" 
                class="password-toggle" 
                @click="showNewPassword = !showNewPassword"
                tabindex="-1"
              >
                {{ showNewPassword ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">{{ t('profile.confirmPassword') }}</label>
            <div class="password-group">
              <input 
                :type="showConfirmPassword ? 'text' : 'password'" 
                v-model="formConfirmPassword" 
                class="form-input" 
                required 
              />
              <button 
                type="button" 
                class="password-toggle" 
                @click="showConfirmPassword = !showConfirmPassword"
                tabindex="-1"
              >
                {{ showConfirmPassword ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>

          <button type="submit" class="btn-outline-submit" :disabled="isChangingPassword">
            <span v-if="isChangingPassword">⏳</span>
            <span v-else>{{ t('profile.changePassword') }}</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import logo from '../assets/logo.png'
import { useAuthStore } from '../stores/auth'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const showDropdown = ref(false)
const showUserDropdown = ref(false)
const theme = ref(localStorage.getItem('theme') || 'dark')

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem('theme', theme.value)
  if (theme.value === 'light') {
    document.documentElement.classList.add('light-theme')
  } else {
    document.documentElement.classList.remove('light-theme')
  }
}

function toggleLanguage() {
  const newLocale = locale.value === 'vi' ? 'en' : 'vi'
  locale.value = newLocale
  localStorage.setItem('locale', newLocale)
}

const isJobsRoute = computed(() => {
  return ['JobRecommendation', 'JobSearch'].includes(route.name)
})

const userInitials = computed(() => {
  const name = authStore.user?.full_name || authStore.userName || ''
  if (!name) return 'U'
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name[0].toUpperCase()
})

function handleLogout() {
  authStore.logout()
  showUserDropdown.value = false
  router.push('/login')
}

const showProfileModal = ref(false)
const formFullName = ref('')
const formCurrentPassword = ref('')
const formNewPassword = ref('')
const formConfirmPassword = ref('')
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)
const isUpdatingProfile = ref(false)
const isChangingPassword = ref(false)
const profileMessage = ref('')
const profileMessageType = ref('')

function openProfileModal() {
  showUserDropdown.value = false
  formFullName.value = authStore.user?.full_name || authStore.userName || ''
  formCurrentPassword.value = ''
  formNewPassword.value = ''
  formConfirmPassword.value = ''
  showCurrentPassword.value = false
  showNewPassword.value = false
  showConfirmPassword.value = false
  profileMessage.value = ''
  profileMessageType.value = ''
  showProfileModal.value = true
}

function closeProfileModal() {
  showProfileModal.value = false
  showCurrentPassword.value = false
  showNewPassword.value = false
  showConfirmPassword.value = false
}

async function handleUpdateProfile() {
  if (!formFullName.value.trim()) return
  isUpdatingProfile.value = true
  profileMessage.value = ''
  try {
    await authStore.updateProfile(formFullName.value)
    profileMessage.value = t('profile.updateSuccess')
    profileMessageType.value = 'success'
  } catch (error) {
    profileMessage.value = error || t('profile.errorUpdate')
    profileMessageType.value = 'error'
  } finally {
    isUpdatingProfile.value = false
  }
}

async function handleChangePassword() {
  if (!formCurrentPassword.value) {
    profileMessage.value = t('profile.currentPasswordRequired')
    profileMessageType.value = 'error'
    return
  }
  if (formNewPassword.value.length < 8) {
    profileMessage.value = t('profile.newPasswordLength')
    profileMessageType.value = 'error'
    return
  }
  if (formNewPassword.value !== formConfirmPassword.value) {
    profileMessage.value = t('profile.passwordMismatch')
    profileMessageType.value = 'error'
    return
  }

  isChangingPassword.value = true
  profileMessage.value = ''
  try {
    await authStore.changePassword(formCurrentPassword.value, formNewPassword.value)
    profileMessage.value = t('profile.passwordSuccess')
    profileMessageType.value = 'success'
    formCurrentPassword.value = ''
    formNewPassword.value = ''
    formConfirmPassword.value = ''
  } catch (error) {
    profileMessage.value = error || t('profile.errorPassword')
    profileMessageType.value = 'error'
  } finally {
    isChangingPassword.value = false
  }
}

function closeDropdowns() {
  showDropdown.value = false
  showUserDropdown.value = false
}

onMounted(() => {
  window.addEventListener('click', closeDropdowns)
  theme.value = localStorage.getItem('theme') || 'dark'
  if (theme.value === 'light') {
    document.documentElement.classList.add('light-theme')
  } else {
    document.documentElement.classList.remove('light-theme')
  }
})

onUnmounted(() => {
  window.removeEventListener('click', closeDropdowns)
})
</script>

<style scoped>
.navbar-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background-color: var(--bg-navbar);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-color);
}

.navbar-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px 24px;
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
}

.logo-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background-color: var(--logo-bg);
  border: 1px solid var(--logo-border);
  border-radius: 12px;
  color: var(--text-link);
  font-weight: 700;
  font-size: 1.1rem;
  box-shadow: var(--logo-shadow);
}

.brand-logo {
  display: block;
  width: 160px;
  height: auto;
  object-fit: contain;
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-subtitle {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-accent);
  margin: 0;
  text-transform: uppercase;
}

.brand-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-item {
  color: var(--nav-text);
  font-size: 0.9rem;
  padding: 8px 16px;
  border-radius: 9999px;
  transition: all var(--transition-fast);
  text-decoration: none;
  font-weight: 500;
  background: transparent;
  border: none;
  cursor: pointer;
}

.nav-item:hover, .router-link-active.nav-item, .nav-item.active {
  color: var(--nav-active-text);
  background-color: var(--nav-active-bg);
}

.dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
}

.arrow {
  font-size: 0.65rem;
  transition: transform var(--transition-fast);
  opacity: 0.7;
  display: inline-block;
}

.dropdown:hover .arrow {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(4px);
  background-color: var(--bg-dropdown);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 8px;
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  box-shadow: var(--shadow-dropdown);
  z-index: 1000;
}

.dropdown-menu::before {
  content: '';
  position: absolute;
  top: -10px;
  left: 0;
  right: 0;
  height: 10px;
  background: transparent;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--nav-text);
  font-size: 0.85rem;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: all var(--transition-fast);
  text-align: left;
  font-weight: 500;
}

.dropdown-item:hover, .router-link-active.dropdown-item {
  color: var(--primary);
  background-color: var(--btn-outline-hover-bg);
}

.auth-buttons {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-login-outline {
  color: var(--btn-outline-text);
  border: 1px solid var(--btn-outline-border);
  padding: 8px 20px;
  border-radius: 9999px;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all var(--transition-fast);
  text-decoration: none;
}

.btn-login-outline:hover {
  border-color: var(--btn-outline-hover-border);
  background-color: var(--btn-outline-hover-bg);
}

.btn-primary-nav {
  background: var(--gradient-primary);
  color: var(--text-on-primary);
  padding: 8px 20px;
  border-radius: 9999px;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all var(--transition-fast);
  text-decoration: none;
  box-shadow: var(--shadow-glow);
}

.btn-primary-nav:hover {
  opacity: 0.95;
  transform: translateY(-1px);
}

/* User Dropdown */
.user-dropdown-container {
  position: relative;
  display: inline-block;
}

.avatar-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--gradient-primary);
  border: 2px solid var(--avatar-border);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-glow);
}

.avatar-button:hover {
  transform: scale(1.05);
  border-color: var(--text-link);
}

.avatar-fallback {
  color: var(--text-on-primary);
  font-weight: 700;
  font-size: 0.95rem;
  letter-spacing: -0.05em;
}

.user-dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  transform: translateY(12px);
  background-color: var(--bg-dropdown);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
  width: 280px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-modal);
  z-index: 1000;
  text-align: left;
}

.user-dropdown-header {
  padding-bottom: 4px;
}

.user-dropdown-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 2px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-dropdown-email {
  font-size: 0.8rem;
  color: var(--text-label);
  margin: 0 0 10px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role-badge {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 2px 8px;
  border-radius: 4px;
}

.user-role-badge.admin {
  background-color: var(--role-admin-bg);
  border: 1px solid var(--role-admin-border);
  color: var(--role-admin-text);
}

.user-role-badge.user {
  background-color: var(--role-user-bg);
  border: 1px solid var(--role-user-border);
  color: var(--role-user-text);
}

.user-dropdown-divider {
  height: 1px;
  background-color: var(--dropdown-divider);
  margin: 12px 0;
}

.user-dropdown-links {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--nav-text);
  font-size: 0.85rem;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: all var(--transition-fast);
  background: transparent;
  border: none;
  cursor: pointer;
  width: 100%;
  font-weight: 500;
  text-align: left;
}

.user-dropdown-item:hover {
  color: var(--nav-active-text);
  background-color: var(--dropdown-item-hover-bg);
}

.logout-item {
  color: #f87171;
}

.logout-item:hover {
  background-color: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

@media (max-width: 768px) {
  .nav-links {
    display: none;
  }
}

.theme-toggle-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--theme-toggle-bg);
  border: 1px solid var(--theme-toggle-border);
  color: var(--theme-toggle-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-size: 1.1rem;
}

.theme-toggle-btn:hover {
  background: var(--nav-active-bg);
  transform: scale(1.05);
  border-color: var(--primary);
}

/* Language Toggle */
.lang-toggle-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 9999px;
  background: var(--theme-toggle-bg);
  border: 1px solid var(--theme-toggle-border);
  color: var(--theme-toggle-color);
  cursor: pointer;
  transition: all var(--transition-fast);
  font-size: 0.8rem;
  font-weight: 600;
}

.lang-toggle-btn:hover {
  background: var(--nav-active-bg);
  border-color: var(--primary);
  transform: scale(1.05);
}

.lang-flag {
  font-size: 1rem;
}

.lang-code {
  font-size: 0.75rem;
  letter-spacing: 0.05em;
}

/* === PROFILE MODAL === */
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(2, 6, 23, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease-out;
}

.modal-card {
  width: 100%;
  max-width: 480px;
  background-color: var(--bg-dropdown);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-modal);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.01);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-heading);
}

.close-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color var(--transition-fast);
}

.close-btn:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 24px;
  max-height: 80vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.modal-divider {
  height: 1px;
  background-color: var(--border-color);
  margin: 8px 0;
}

.form-section-title {
  margin: 0 0 16px 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--primary-light);
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-input {
  background-color: var(--input-bg);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  transition: all var(--transition-fast);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 8px rgba(14, 165, 233, 0.15);
}

.form-input.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: rgba(255, 255, 255, 0.02);
}

.btn-primary.btn-save {
  padding: 10px 16px;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: var(--radius-md);
  cursor: pointer;
  align-self: flex-start;
}

.btn-outline-submit {
  padding: 10px 16px;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: var(--radius-md);
  cursor: pointer;
  align-self: flex-start;
  background: transparent;
  border: 1px solid var(--btn-outline-border);
  color: var(--btn-outline-text);
  transition: all var(--transition-fast);
}

.btn-outline-submit:hover:not(:disabled) {
  border-color: var(--primary);
  background-color: var(--btn-outline-hover-bg);
  color: var(--primary-light);
}

.alert-box {
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  font-weight: 500;
  line-height: 1.4;
  animation: fadeIn 0.2s ease-out;
}

.alert-box.success {
  background-color: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.alert-box.error {
  background-color: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #f87171;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
