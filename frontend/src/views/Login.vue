<template>
  <main class="auth-layout">
    <section class="auth-card glass-card">
      <p class="auth-pretitle">{{ t('auth.loginTag') }}</p>
      <h1 class="auth-title">{{ t('auth.loginTitle') }}</h1>
      <p class="auth-desc">{{ t('auth.loginDesc') }}</p>
      
      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="input-group">
          <input 
            v-model="email" 
            type="email" 
            :placeholder="t('auth.email')" 
            class="input-field" 
            required 
          />
        </div>
        <div class="input-group">
          <input 
            v-model="password" 
            type="password" 
            :placeholder="t('auth.password')" 
            class="input-field" 
            required 
          />
        </div>
        
        <p v-if="error" class="error-text">{{ error }}</p>
        
        <button 
          type="submit" 
          :disabled="loading" 
          class="btn-primary auth-btn"
        >
          {{ loading ? t('auth.connecting') : t('auth.continue') }}
        </button>
      </form>
      
      <p class="auth-footer-text">
        {{ t('auth.newHere') }} <router-link to="/register" class="cyan-link">{{ t('auth.createAccount') }}</router-link>
      </p>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref(null)

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

async function handleLogin() {
  loading.value = true
  error.value = null
  try {
    await authStore.login(email.value, password.value)
    const redirectPath = route.query.redirect || '/dashboard'
    router.push(redirectPath)
  } catch (err) {
    error.value = err
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-layout {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 73px);
  padding: 40px 20px;
}

.auth-card {
  width: 100%;
  max-width: 440px;
  padding: 36px;
  text-align: left;
}

.auth-pretitle {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-accent);
  text-transform: uppercase;
  margin-bottom: 8px;
}

.auth-title {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 12px 0;
  line-height: 1.25;
  letter-spacing: -0.025em;
}

.auth-desc {
  font-size: 0.95rem;
  color: var(--text-secondary);
  margin-bottom: 28px;
  line-height: 1.5;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.auth-btn {
  margin-top: 8px;
  width: 100%;
  padding: 14px;
}

.error-text {
  color: #ef4444;
  font-size: 0.85rem;
  margin: 0;
}

.auth-footer-text {
  font-size: 0.9rem;
  color: var(--text-label);
  margin-top: 24px;
}

.cyan-link {
  color: var(--text-link);
  font-weight: 500;
}

.cyan-link:hover {
  text-decoration: underline;
}
</style>
