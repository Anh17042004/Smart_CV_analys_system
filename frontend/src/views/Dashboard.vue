<template>
  <main class="dashboard-container">
    <div class="dashboard-header">
      <p class="section-tag">{{ t('dashboard.title') }}</p>
      <h1 class="welcome-text">👋 {{ t('dashboard.welcome') }} {{ authStore.userName }}!</h1>
      <p class="subtitle-text">
        {{ t('dashboard.subtitle') }}
      </p>
    </div>

    <!-- Stat Cards -->
    <div v-if="loading" class="loading-box glass-card">
      {{ t('dashboard.loading') }}
    </div>
    <div v-else class="stats-grid">
      <div class="stat-card glass-card">
        <p class="stat-title">{{ t('dashboard.savedReports') }}</p>
        <h2 class="stat-value">{{ reports.length }}</h2>
        <p class="stat-desc">{{ t('dashboard.reportsDesc') }}</p>
      </div>
      <div class="stat-card glass-card">
        <p class="stat-title">{{ t('dashboard.availableJobs') }}</p>
        <h2 class="stat-value">{{ jobsCount }}</h2>
        <p class="stat-desc">{{ t('dashboard.jobsDesc') }}</p>
      </div>
      <div class="stat-card glass-card">
        <p class="stat-title">{{ t('dashboard.targetRoleFit') }}</p>
        <h2 class="stat-value">{{ t('dashboard.live') }}</h2>
        <p class="stat-desc">{{ t('dashboard.targetRoleDesc') }}</p>
      </div>
    </div>

    <div class="dashboard-body">
      <!-- Recent Reports -->
      <section class="reports-section glass-card">
        <div class="section-title-row">
          <h2>{{ t('dashboard.recentReports') }}</h2>
          <router-link to="/cv-analysis" class="header-link">{{ t('dashboard.uploadAnother') }}</router-link>
        </div>

        <div class="reports-list">
          <template v-if="reports.length">
            <article 
              v-for="report in reports.slice(0, 5)" 
              :key="report.id" 
              class="report-card report-card-clickable"
              @click="goToReport(report.id)"
            >
              <div class="report-main-info">
                <div>
                  <p class="report-filename">{{ t('dashboard.report') }} #{{ report.id }}</p>
                  <h3 class="report-score-title">
                    {{ t('dashboard.score') }}: 
                    <span :class="getScoreClass(report.resume_score)">
                      {{ report.resume_score ?? 'N/A' }}%
                    </span>
                  </h3>
                  <p class="report-date">{{ t('dashboard.analyzedOn') }} {{ formatDate(report.created_at) }}</p>
                </div>
                <div class="report-badge">
                  <p class="badge-title">{{ t('dashboard.targetRole') }}</p>
                  <p class="badge-value">{{ report.target_role || t('dashboard.notDetected') }}</p>
                </div>
              </div>
            </article>
          </template>
          <div v-else class="empty-list-box">
            {{ t('dashboard.noReports') }}
          </div>
        </div>
      </section>
 
      <!-- Quick Actions & Saved Jobs Column -->
      <div class="right-column-sections">
        <section class="actions-section glass-card">
          <h2>{{ t('dashboard.quickActions') }}</h2>
          <div class="actions-list">
            <router-link to="/cv-analysis" class="action-card">
              <p class="action-title">{{ t('dashboard.analyzeCVTitle') }}</p>
              <p class="action-desc">{{ t('dashboard.analyzeCVDesc') }}</p>
            </router-link>
            <router-link to="/job-recommendation" class="action-card">
              <p class="action-title">{{ t('dashboard.matchJobsTitle') }}</p>
              <p class="action-desc">{{ t('dashboard.matchJobsDesc') }}</p>
            </router-link>
            <router-link to="/interview" class="action-card">
              <p class="action-title">{{ t('dashboard.mockInterviewTitle') }}</p>
              <p class="action-desc">{{ t('dashboard.mockInterviewDesc') }}</p>
            </router-link>
          </div>
        </section>

        <!-- Saved Jobs -->
        <section class="saved-jobs-section glass-card" style="margin-top: 24px;">
          <h2>{{ t('dashboard.savedJobs') }}</h2>
          <div class="saved-jobs-list">
            <template v-if="savedJobs.length">
              <div 
                v-for="item in savedJobs" 
                :key="item.id" 
                class="saved-job-card"
                @click="openSavedJobDetails(item)"
              >
                <div class="saved-job-info">
                  <p class="saved-job-company">{{ item.jd.company }}</p>
                  <h4 class="saved-job-title">{{ item.jd.title }}</h4>
                  <p class="saved-job-location">{{ item.jd.location }}</p>
                </div>
                <button 
                  class="btn-unsave" 
                  @click.stop="unsaveJob(item.id)"
                  :title="t('dashboard.removeJob')"
                >
                  ✕
                </button>
              </div>
            </template>
            <div v-else class="empty-saved-box">
              {{ t('dashboard.noSavedJobs') }}
            </div>
          </div>
        </section>
      </div>
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
            <h4>{{ t('dashboard.keySkills') }}</h4>
            <div class="skills-tags">
              <span v-for="skill in activeJob.skills" :key="skill" class="pill-tag big-pill">
                {{ skill }}
              </span>
            </div>
          </div>

          <div class="drawer-section">
            <h4>{{ t('dashboard.jobDescription') }}</h4>
            <p class="drawer-desc-full">{{ activeJob.description }}</p>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '../api'

const { t } = useI18n()

const authStore = useAuthStore()
const router = useRouter()
const reports = ref([])
const jobsCount = ref(0)
const loading = ref(true)
const savedJobs = ref([])
const activeJob = ref(null)

async function loadDashboardData() {
  try {
    const [reportsRes, jobsRes, savedRes] = await Promise.all([
      api.get('/cv/history'),
      api.post('/jobs/search', { keyword: '' }),
      api.get('/jobs/saved')
    ])
    reports.value = reportsRes.data
    jobsCount.value = jobsRes.data.total || 0
    savedJobs.value = savedRes.data || []
  } catch (err) {
    console.error('Lỗi khi tải thông tin dashboard:', err)
  } finally {
    loading.value = false
  }
}

function goToReport(id) {
  router.push(`/cv-analysis/${id}`)
}

function openSavedJobDetails(item) {
  activeJob.value = item.jd
}

async function unsaveJob(savedId) {
  try {
    await api.delete(`/jobs/saved/${savedId}`)
    savedJobs.value = savedJobs.value.filter(item => item.id !== savedId)
  } catch (err) {
    console.error('Lỗi khi bỏ lưu việc làm:', err)
    alert('Không thể bỏ lưu việc làm: ' + (err.message || err))
  }
}

function getScoreClass(score) {
  if (!score) return 'score-gray'
  if (score >= 85) return 'score-green'
  if (score >= 70) return 'score-yellow'
  return 'score-red'
}

function formatDate(dateStr) {
  if (!dateStr) return 'Unknown date'
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return dateStr
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
  width: 100%;
}

.dashboard-header {
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

.welcome-text {
  font-size: 2.5rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 12px 0;
  letter-spacing: -0.02em;
}

.subtitle-text {
  font-size: 1.05rem;
  color: var(--text-secondary);
  max-width: 800px;
  line-height: 1.5;
}

.loading-box {
  padding: 32px;
  text-align: center;
  color: var(--text-secondary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  text-align: left;
  padding: 24px;
}

.stat-title {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-label);
  text-transform: uppercase;
  margin-bottom: 12px;
}

.stat-value {
  font-size: 2.75rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 8px 0;
}

.stat-desc {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.dashboard-body {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 24px;
}

@media (max-width: 992px) {
  .dashboard-body {
    grid-template-columns: 1fr;
  }
}

.reports-section {
  text-align: left;
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-title-row h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0;
}

.header-link {
  font-size: 0.9rem;
  color: var(--text-link);
  font-weight: 500;
}

.header-link:hover {
  text-decoration: underline;
}

.reports-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.report-card {
  background-color: var(--bg-card-inner);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 20px;
}

.report-main-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
}

.report-filename {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-link);
  text-transform: uppercase;
  margin-bottom: 6px;
}

.report-score-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 4px 0;
}

.score-green {
  color: #10b981;
}

.score-yellow {
  color: #f59e0b;
}

.score-red {
  color: #ef4444;
}

.score-gray {
  color: var(--text-secondary);
}

.report-date {
  font-size: 0.85rem;
  color: var(--text-label);
  margin: 0;
}

.report-badge {
  background-color: var(--bg-badge);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  text-align: left;
}

.badge-title {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-label);
  text-transform: uppercase;
  margin-bottom: 4px;
}

.badge-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0;
}

.empty-list-box {
  border: 1px dashed var(--border-dashed);
  background-color: var(--bg-dropzone);
  border-radius: var(--radius-lg);
  padding: 36px;
  color: var(--text-label);
  text-align: center;
}

.actions-section {
  text-align: left;
}

.actions-section h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-heading);
  margin-bottom: 20px;
}

.actions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.action-card {
  display: block;
  background-color: var(--bg-card-inner);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  transition: all var(--transition-normal);
  text-decoration: none;
}

.action-card:hover {
  border-color: var(--border-highlight);
  background-color: var(--bg-hover-subtle);
}

.action-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-heading);
  margin-bottom: 6px;
}

.action-desc {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* Saved Jobs Styles */
.saved-jobs-section {
  text-align: left;
}

.saved-jobs-section h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-heading);
  margin-bottom: 20px;
}

.saved-jobs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.saved-job-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--bg-card-inner);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.saved-job-card:hover {
  border-color: var(--border-highlight);
  background-color: var(--bg-hover-card);
  box-shadow: var(--shadow-glow);
}

.saved-job-company {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.25em;
  color: var(--text-link);
  text-transform: uppercase;
  margin-bottom: 4px;
}

.saved-job-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 4px 0;
}

.saved-job-location {
  font-size: 0.8rem;
  color: var(--text-label);
  margin: 0;
}

.btn-unsave {
  background: transparent;
  border: none;
  color: var(--btn-unsave-color);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color var(--transition-fast);
}

.btn-unsave:hover {
  color: #ef4444;
}

.empty-saved-box {
  border: 1px dashed var(--border-dashed);
  background-color: var(--bg-dropzone);
  border-radius: var(--radius-lg);
  padding: 24px;
  color: var(--text-label);
  text-align: center;
  font-size: 0.85rem;
  line-height: 1.5;
}

/* Clickable Report Card */
.report-card-clickable {
  cursor: pointer;
  transition: all var(--transition-normal);
}

.report-card-clickable:hover {
  border-color: var(--border-highlight);
  background-color: var(--bg-hover-card);
  box-shadow: var(--shadow-glow);
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
  border: none;
  cursor: pointer;
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

.pill-tag {
  background-color: var(--pill-bg);
  border: 1px solid var(--pill-border);
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 0.75rem;
  color: var(--pill-text);
}

.skills-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
