<template>
  <main class="recommendation-container">
    <div class="recommendation-header">
      <p class="section-tag">{{ t('jobRec.tag') }}</p>
      <h1 class="main-title">{{ t('jobRec.title') }}</h1>
      <p class="desc-text">
        {{ t('jobRec.desc') }}
      </p>
    </div>

    <div class="recommendation-grid">
      <!-- Select CV Column -->
      <section class="selection-column glass-card">
        <h2>{{ t('jobRec.selectResume') }}</h2>
        <p class="selection-support-text">{{ t('jobRec.selectDesc') }}</p>

        <div v-if="historyLoading" class="loading-text">
          {{ t('jobRec.loadingCVs') }}
        </div>
        <div v-else-if="cvList.length" class="input-group">
          <label class="input-label">{{ t('jobRec.yourResumes') }}</label>
          <select v-model="selectedCvId" class="input-field select-field">
            <option value="" disabled>{{ t('jobRec.chooseCv') }}</option>
            <option v-for="cv in cvList" :key="cv.id" :value="cv.cv_id">
              {{ t('dashboard.report') }} #{{ cv.id }} ({{ t('dashboard.score') }}: {{ cv.resume_score }}% - {{ cv.target_role || t('cvHistory.generalAnalysis') }})
            </option>
          </select>
        </div>

        <div v-if="cvList.length" class="input-group" style="margin-top: 20px;">
          <label class="input-label">{{ t('jobRec.numJobs') }}</label>
          <select v-model="limitVal" class="input-field select-field">
            <option :value="3">3 jobs</option>
            <option :value="5">5 jobs</option>
            <option :value="10">10 jobs</option>
            <option :value="20">20 jobs</option>
            <option :value="50">50 jobs</option>
          </select>
        </div>

        <div v-else class="empty-cv-alert">
          <p>{{ t('jobRec.noCVs') }}</p>
          <router-link to="/cv-analysis" class="btn-primary select-btn">{{ t('jobRec.uploadFirst') }}</router-link>
        </div>

        <button 
          v-if="cvList.length"
          @click="fetchRecommendations" 
          :disabled="loading || !selectedCvId" 
          class="btn-primary recommend-btn"
        >
          <span v-if="loading" class="spinner">⏳</span>
          {{ loading ? t('jobRec.matchingEmb') : t('jobRec.recommendJobs') }}
        </button>

        <p v-if="error" class="error-text">{{ error }}</p>
      </section>

      <!-- Matches Column -->
      <section class="matches-column glass-card">
        <div class="matches-title-row">
          <h2>{{ t('jobRec.topMatches') }}</h2>
          <p class="matches-desc-meta">{{ t('jobRec.rankedBy') }}</p>
        </div>

        <div class="matches-list">
          <template v-if="recommendations.length">
            <article 
              v-for="item in recommendations" 
              :key="item.jd.id" 
              class="match-card"
              @click="openJobDetails(item)"
            >
              <div class="match-card-header">
                <div>
                  <p class="match-company">{{ item.jd.company }}</p>
                  <h3 class="match-title-text">{{ item.jd.title }}</h3>
                  <p class="match-location-meta">
                    {{ item.jd.location }} • {{ item.jd.employment_type || t('common.fulltime') }}
                  </p>
                </div>
                <div class="match-card-actions" style="display: flex; align-items: center; gap: 12px;">
                  <button 
                    class="btn-save-bookmark" 
                    @click.stop="toggleSaveJob(item.jd)"
                    :class="{ 'is-saved': isSaved(item.jd.id) }"
                    :title="isSaved(item.jd.id) ? t('common.unsave') : t('common.save')"
                  >
                    {{ isSaved(item.jd.id) ? '♥' : '♡' }}
                  </button>
                  <div class="match-score-badge">
                    <p class="score-tag">{{ t('jobRec.matchLabel') }}</p>
                    <p class="score-number">{{ item.match_score }}%</p>
                  </div>
                </div>
              </div>
              
              <p class="match-snippet">
                {{ truncateText(item.jd.description, 180) }}
              </p>
              
              <div class="match-skills-tags">
                <span 
                  v-for="skill in item.jd.skills" 
                  :key="skill" 
                  class="pill-tag"
                >
                  {{ skill }}
                </span>
              </div>
              
              <span class="view-detail-hint">{{ t('jobRec.clickDetails') }}</span>
            </article>
          </template>
          <div v-else class="empty-matches-box">
            <span class="waiting-icon">💼</span>
            <p v-if="loading">{{ t('jobRec.searchingSemantic') }}</p>
            <p v-else>{{ t('jobRec.noRecommendations') }}</p>
          </div>
        </div>
      </section>
    </div>

    <!-- Job Details Drawer Modal -->
    <div v-if="activeJob" class="modal-overlay" @click.self="activeJob = null">
      <div class="modal-drawer">
        <div class="drawer-header">
          <div>
            <p class="drawer-company">{{ activeJob.jd.company }}</p>
            <h2>{{ activeJob.jd.title }}</h2>
            <p class="drawer-meta">{{ activeJob.jd.location }} • {{ activeJob.jd.experience || t('dashboard.noExpReq') }} • {{ activeJob.jd.salary_range || t('dashboard.negotiable') }}</p>
          </div>
          <button class="btn-close" @click="activeJob = null">✕</button>
        </div>

        <div class="drawer-content">
          <div class="drawer-score-block">
            <p class="drawer-score-title">{{ t('jobRec.compatibilityScore') }}</p>
            <h3 class="drawer-score-val">{{ activeJob.match_score }}%</h3>
          </div>

          <div class="drawer-section">
            <h4>{{ t('jobRec.keySkills') }}</h4>
            <div class="skills-tags">
              <span v-for="skill in activeJob.jd.skills" :key="skill" class="pill-tag big-pill">
                {{ skill }}
              </span>
            </div>
          </div>

          <div class="drawer-section">
            <h4>{{ t('jobRec.jobDescription') }}</h4>
            <p class="drawer-desc-full">{{ activeJob.jd.description }}</p>
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

const cvList = ref([])
const historyLoading = ref(true)
const selectedCvId = ref('')
const limitVal = ref(10)
const loading = ref(false)
const error = ref(null)
const recommendations = ref([])
const activeJob = ref(null)

async function loadHistory() {
  try {
    const res = await api.get('/cv/history')
    cvList.value = res.data
  } catch (err) {
    console.error('Lỗi khi tải danh sách CV:', err)
  } finally {
    historyLoading.value = false
  }
}

async function fetchRecommendations() {
  if (!selectedCvId.value) return
  loading.value = true
  error.value = null
  recommendations.value = []

  try {
    const res = await api.get(`/cv/recommend/${selectedCvId.value}?limit=${limitVal.value}`)
    recommendations.value = res.data.recommendations || []
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Lấy danh sách việc làm gợi ý thất bại'
  } finally {
    loading.value = false
  }
}

function openJobDetails(item) {
  activeJob.value = item
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

async function toggleSaveJob(jd) {
  const savedId = savedJobsMap.value[jd.id]
  if (savedId) {
    try {
      await api.delete(`/jobs/saved/${savedId}`)
      delete savedJobsMap.value[jd.id]
    } catch (err) {
      console.error('Lỗi khi bỏ lưu việc làm:', err)
    }
  } else {
    try {
      const res = await api.post('/jobs/saved', { jd_id: jd.id })
      savedJobsMap.value[jd.id] = res.data.id
    } catch (err) {
      console.error('Lỗi khi lưu việc làm:', err)
    }
  }
}

onMounted(() => {
  loadHistory()
  loadSavedJobs()
})
</script>

<style scoped>
.recommendation-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
  width: 100%;
}

.recommendation-header {
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

.recommendation-grid {
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
  gap: 24px;
  align-items: start;
}

@media (max-width: 992px) {
  .recommendation-grid {
    grid-template-columns: 1fr;
  }
}

.selection-column {
  text-align: left;
}

.selection-column h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-heading);
  margin-bottom: 4px;
}

.selection-support-text {
  font-size: 0.85rem;
  color: var(--text-label);
  margin-bottom: 20px;
}

.loading-text {
  color: var(--text-secondary);
  font-size: 0.95rem;
  padding: 16px 0;
}

.input-label {
  display: block;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-heading);
  margin-bottom: 8px;
}

.select-field {
  appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg fill='currentColor' height='24' viewBox='0 0 24 24' width='24' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/><path d='M0 0h24v24H0z' fill='none'/></svg>");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 40px;
}

.empty-cv-alert {
  border: 1px dashed var(--border-dashed);
  background-color: var(--bg-dropzone);
  border-radius: var(--radius-lg);
  padding: 24px;
  text-align: center;
  color: var(--text-label);
}

.select-btn {
  margin-top: 16px;
  padding: 10px 20px;
  font-size: 0.9rem;
}

.recommend-btn {
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

.matches-column {
  text-align: left;
}

.matches-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.matches-title-row h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0;
}

.matches-desc-meta {
  font-size: 0.85rem;
  color: var(--text-label);
}

.matches-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.match-card {
  background-color: var(--bg-card-inner);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.match-card:hover {
  border-color: var(--border-highlight);
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}

.match-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}

.match-company {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-accent);
  text-transform: uppercase;
  margin-bottom: 6px;
}

.match-title-text {
  font-size: 1.35rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 4px 0;
}

.match-location-meta {
  font-size: 0.85rem;
  color: var(--text-label);
  margin: 0;
}

.match-score-badge {
  background-color: var(--score-badge-bg);
  border: 1px solid var(--score-badge-border);
  border-radius: var(--radius-md);
  padding: 8px 16px;
  text-align: center;
}

.score-tag {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-link);
  text-transform: uppercase;
  margin-bottom: 2px;
}

.score-number {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--primary);
  margin: 0;
}

.match-snippet {
  font-size: 0.9rem;
  color: var(--text-body);
  line-height: 1.6;
  margin-bottom: 16px;
}

.match-skills-tags {
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

.empty-matches-box {
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

.drawer-score-block {
  background-color: var(--score-block-bg);
  border: 1px solid var(--score-block-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  text-align: center;
}

.drawer-score-title {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-link);
  text-transform: uppercase;
  margin-bottom: 4px;
}

.drawer-score-val {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--primary);
  margin: 0;
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
