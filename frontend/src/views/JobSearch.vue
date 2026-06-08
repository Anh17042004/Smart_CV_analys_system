<template>
  <main class="search-container">
    <div class="search-header">
      <p class="section-tag">{{ t('jobSearch.tag') }}</p>
      <h1 class="main-title">{{ t('jobSearch.title') }}</h1>
      <p class="desc-text">
        {{ t('jobSearch.desc') }}
      </p>
    </div>

    <div class="search-grid">
      <!-- Search Form Column -->
      <section class="form-column glass-card">
        <h2>{{ t('jobSearch.filters') }}</h2>
        <p class="form-support-text">{{ t('jobSearch.filtersDesc') }}</p>

        <div class="input-group">
          <label class="input-label">{{ t('jobSearch.keywords') }}</label>
          <input 
            type="text" 
            v-model="keyword" 
            :placeholder="t('jobSearch.keywordsPlaceholder')" 
            class="input-field"
            @keyup.enter="performSearch"
          />
        </div>

        <div class="input-group">
          <label class="input-label">{{ t('jobSearch.location') }}</label>
          <input 
            type="text" 
            v-model="location" 
            :placeholder="t('jobSearch.locationPlaceholder')" 
            class="input-field"
            @keyup.enter="performSearch"
          />
        </div>

        <button 
          @click="performSearch" 
          :disabled="loading" 
          class="btn-primary search-btn"
        >
          <span v-if="loading" class="spinner">⏳</span>
          {{ loading ? t('jobSearch.searching') : t('jobSearch.searchJobs') }}
        </button>

        <p v-if="error" class="error-text">{{ error }}</p>
      </section>

      <!-- Results Column -->
      <section class="results-column glass-card">
        <div class="results-title-row">
          <h2>{{ t('jobSearch.searchResults') }}</h2>
          <p class="results-desc-meta" v-if="jobs.length">{{ jobs.length }} {{ t('jobSearch.jobsFound') }}</p>
        </div>

        <div class="results-list">
          <template v-if="jobs.length">
            <article 
              v-for="job in jobs" 
              :key="job.id" 
              class="job-card"
              @click="openJobDetails(job)"
            >
              <div class="job-card-header">
                <div>
                  <p class="job-company">{{ job.company }}</p>
                  <h3 class="job-title-text">{{ job.title }}</h3>
                  <p class="job-location-meta">
                    {{ job.location }} • {{ job.employment_type || t('common.fulltime') }}
                  </p>
                </div>
                <div class="job-card-actions" style="display: flex; align-items: center; gap: 12px;">
                  <button 
                    class="btn-save-bookmark" 
                    @click.stop="toggleSaveJob(job)"
                    :class="{ 'is-saved': isSaved(job.id) }"
                    :title="isSaved(job.id) ? t('common.unsave') : t('common.save')"
                  >
                    {{ isSaved(job.id) ? '♥' : '♡' }}
                  </button>
                  <div class="job-salary-badge" v-if="job.salary_range">
                    <p class="salary-tag">{{ t('jobSearch.salary') }}</p>
                    <p class="salary-number">{{ job.salary_range }}</p>
                  </div>
                </div>
              </div>
              
              <p class="job-snippet">
                {{ truncateText(job.description, 180) }}
              </p>
              
              <div class="job-skills-tags">
                <span 
                  v-for="skill in job.skills" 
                  :key="skill" 
                  class="pill-tag"
                >
                  {{ skill }}
                </span>
              </div>
              
              <span class="view-detail-hint">{{ t('jobSearch.clickDetails') }}</span>
            </article>
          </template>
          <div v-else class="empty-results-box">
            <span class="waiting-icon">🔍</span>
            <p v-if="loading">{{ t('jobSearch.searchingDb') }}</p>
            <p v-else>{{ t('jobSearch.noJobs') }}</p>
          </div>
        </div>
      </section>
    </div>

    <!-- Job Details Drawer Modal -->
    <div v-if="activeJob" class="modal-overlay" @click.self="activeJob = null">
      <div class="modal-drawer">
        <div class="drawer-header">
          <div>
            <p class="drawer-company">{{ activeJob.company }}</p>
            <h2>{{ activeJob.title }}</h2>
            <p class="drawer-meta">{{ activeJob.location }} • {{ activeJob.experience || t('dashboard.noExpReq') }} • {{ activeJob.salary_range || t('dashboard.negotiable') }}</p>
          </div>
          <button class="btn-close" @click="activeJob = null">✕</button>
        </div>

        <div class="drawer-content">
          <div class="drawer-section" v-if="activeJob.skills && activeJob.skills.length">
            <h4>{{ t('jobSearch.keySkills') }}</h4>
            <div class="skills-tags">
              <span v-for="skill in activeJob.skills" :key="skill" class="pill-tag big-pill">
                {{ skill }}
              </span>
            </div>
          </div>

          <div class="drawer-section">
            <h4>{{ t('jobSearch.jobDescription') }}</h4>
            <p class="drawer-desc-full">{{ activeJob.description }}</p>
          </div>

          <div class="drawer-section" v-if="activeJob.source_url">
            <h4>{{ t('jobSearch.sourceLink') }}</h4>
            <a :href="activeJob.source_url" target="_blank" class="source-link">{{ activeJob.source_url }}</a>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api'

const { t } = useI18n()

const keyword = ref('')
const location = ref('')
const loading = ref(false)
const error = ref(null)
const jobs = ref([])
const activeJob = ref(null)

async function performSearch() {
  loading.value = true
  error.value = null
  jobs.value = []

  try {
    const res = await api.post('/jobs/search', {
      keyword: keyword.value,
      location: location.value || null
    })
    jobs.value = res.data.results || []
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Tìm kiếm việc làm thất bại'
  } finally {
    loading.value = false
  }
}

function openJobDetails(job) {
  activeJob.value = job
}

function truncateText(text, length) {
  if (!text) return ''
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

const savedJobsMap = ref({})

async function loadSavedJobs() {
  try {
    const res = await api.get('/jobs/saved')
    const map = {}
    res.data.forEach(item => {
      map[item.jd.id] = item.id
    })
    savedJobsMap.value = map
  } catch (err) {
    console.error('Lỗi khi tải danh sách việc làm đã lưu:', err)
  }
}

function isSaved(jdId) {
  return !!savedJobsMap.value[jdId]
}

async function toggleSaveJob(job) {
  const savedId = savedJobsMap.value[job.id]
  if (savedId) {
    try {
      await api.delete(`/jobs/saved/${savedId}`)
      delete savedJobsMap.value[job.id]
    } catch (err) {
      console.error('Lỗi khi bỏ lưu việc làm:', err)
    }
  } else {
    try {
      const res = await api.post('/jobs/saved', { jd_id: job.id })
      savedJobsMap.value[job.id] = res.data.id
    } catch (err) {
      console.error('Lỗi khi lưu việc làm:', err)
    }
  }
}

// Perform default search on mount to populate some initial jobs
onMounted(() => {
  performSearch()
  loadSavedJobs()
})
</script>

<style scoped>
.search-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
  width: 100%;
}

.search-header {
  margin-bottom: 32px;
  text-align: left;
}

.section-tag {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.35em;
  color: var(--text-accent);
  text-transform: uppercase;
  margin-bottom: 8px;
}

.main-title {
  font-size: 2.25rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 12px 0;
  letter-spacing: -0.02em;
}

.desc-text {
  font-size: 1.05rem;
  color: var(--text-secondary);
  max-width: 800px;
  line-height: 1.5;
}

.search-grid {
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
  gap: 24px;
  align-items: start;
}

@media (max-width: 992px) {
  .search-grid {
    grid-template-columns: 1fr;
  }
}

.form-column {
  text-align: left;
}

.form-column h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-heading);
  margin-bottom: 4px;
}

.form-support-text {
  font-size: 0.85rem;
  color: var(--text-label);
  margin-bottom: 20px;
}

.input-label {
  display: block;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-heading);
  margin-bottom: 8px;
}

.search-btn {
  margin-top: 24px;
  width: 100%;
  padding: 14px;
  font-size: 1rem;
}

.error-text {
  color: #ef4444;
  font-size: 0.9rem;
  margin-top: 16px;
}

.results-column {
  text-align: left;
}

.results-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.results-title-row h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0;
}

.results-desc-meta {
  font-size: 0.85rem;
  color: var(--text-label);
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.job-card {
  background-color: var(--bg-card-inner);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.job-card:hover {
  border-color: var(--border-highlight);
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}

.job-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}

.job-company {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-accent);
  text-transform: uppercase;
  margin-bottom: 6px;
}

.job-title-text {
  font-size: 1.35rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 4px 0;
}

.job-location-meta {
  font-size: 0.85rem;
  color: var(--text-label);
  margin: 0;
}

.job-salary-badge {
  background-color: var(--salary-badge-bg);
  border: 1px solid var(--salary-badge-border);
  border-radius: var(--radius-md);
  padding: 8px 16px;
  text-align: center;
  max-width: 180px;
}

.salary-tag {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: #10b981;
  text-transform: uppercase;
  margin-bottom: 2px;
}

.salary-number {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0;
  white-space: nowrap;
}

.job-snippet {
  font-size: 0.9rem;
  color: var(--text-body);
  line-height: 1.6;
  margin-bottom: 16px;
}

.job-skills-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.pill-tag {
  background-color: var(--pill-bg);
  border: 1px solid var(--pill-border);
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 0.75rem;
  color: var(--pill-text);
}

.view-detail-hint {
  display: block;
  font-size: 0.8rem;
  color: var(--text-link);
  font-weight: 500;
}

.empty-results-box {
  border: 1px dashed var(--border-dashed);
  background-color: var(--bg-dropzone);
  border-radius: var(--radius-lg);
  padding: 48px 24px;
  text-align: center;
  color: var(--text-label);
}

.waiting-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 12px;
  opacity: 0.5;
}

.spinner {
  display: inline-block;
  margin-right: 8px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Modal Drawer styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: var(--overlay-bg);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.modal-drawer {
  width: 100%;
  max-width: 560px;
  height: 100%;
  background-color: var(--bg-modal);
  border-left: 1px solid var(--border-card);
  padding: 40px;
  overflow-y: auto;
  box-shadow: -10px 0 30px rgba(0, 0, 0, 0.3);
  animation: slideIn 0.3s ease-out;
  text-align: left;
}

@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 1px solid var(--border-divider);
  padding-bottom: 24px;
  margin-bottom: 24px;
}

.drawer-company {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-link);
  text-transform: uppercase;
  margin-bottom: 6px;
}

.drawer-header h2 {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 8px 0;
}

.drawer-meta {
  font-size: 0.9rem;
  color: var(--text-label);
  margin: 0;
}

.btn-close {
  background: transparent;
  color: var(--btn-close-color);
  font-size: 1.5rem;
  line-height: 1;
  transition: color var(--transition-fast);
}

.btn-close:hover {
  color: var(--text-heading);
}

.drawer-content {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.drawer-section h4 {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.35em;
  color: var(--text-label);
  text-transform: uppercase;
  margin-bottom: 12px;
}

.big-pill {
  font-size: 0.85rem;
  padding: 6px 14px;
}

.drawer-desc-full {
  font-size: 0.95rem;
  color: var(--text-body);
  line-height: 1.7;
  white-space: pre-wrap;
}

.source-link {
  color: var(--text-link);
  text-decoration: none;
  font-size: 0.95rem;
}

.source-link:hover {
  text-decoration: underline;
}

.btn-save-bookmark {
  background: transparent;
  border: none;
  color: var(--btn-unsave-color);
  font-size: 1.4rem;
  cursor: pointer;
  padding: 6px;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-save-bookmark:hover {
  color: #ef4444;
  transform: scale(1.1);
}

.btn-save-bookmark.is-saved {
  color: #ef4444;
}

.skills-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
