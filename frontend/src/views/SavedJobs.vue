<template>
  <main class="saved-container">
    <div class="saved-header">
      <p class="section-tag">{{ t('savedJobs.tag') }}</p>
      <h1 class="page-title">❤️ {{ t('savedJobs.title') }}</h1>
      <p class="subtitle-text">
        {{ t('savedJobs.desc') }}
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-box glass-card">
      <div class="spinner">⏳</div> {{ t('savedJobs.loading') }}
    </div>

    <template v-else>
      <!-- Batch Actions Bar -->
      <div class="actions-bar glass-card" v-if="savedJobs.length">
        <div class="left-actions">
          <label class="checkbox-container select-all-label">
            <input 
              type="checkbox" 
              :checked="isAllSelected" 
              :indeterminate="isPartiallySelected"
              @change="toggleSelectAll"
            />
            <span class="checkmark"></span>
            <span class="label-text">{{ isAllSelected ? t('savedJobs.deselectAll') : t('savedJobs.selectAll') }}</span>
          </label>
          <span class="selection-count" v-if="selectedIds.length > 0">
            {{ t('savedJobs.selected') }}: <strong>{{ selectedIds.length }}</strong> {{ t('savedJobs.jobs') }}
          </span>
        </div>
        
        <div class="right-actions">
          <button 
            class="btn-batch-delete" 
            :disabled="selectedIds.length === 0 || deleting"
            @click="confirmBatchDelete"
          >
            <span v-if="deleting" class="spinner">⏳</span>
            {{ t('savedJobs.deleteSelected') }}
          </button>
        </div>
      </div>

      <!-- Jobs List -->
      <div class="jobs-list" v-if="savedJobs.length">
        <div 
          v-for="item in savedJobs" 
          :key="item.id" 
          class="job-row-card glass-card"
          :class="{ 'row-selected': selectedIds.includes(item.id) }"
        >
          <div class="row-checkbox">
            <label class="checkbox-container">
              <input 
                type="checkbox" 
                :value="item.id" 
                v-model="selectedIds"
              />
              <span class="checkmark"></span>
            </label>
          </div>

          <div class="row-info" @click="openJobDetails(item)">
            <div class="job-meta-header">
              <span class="company-badge">{{ item.jd.company }}</span>
              <span class="job-date" v-if="item.created_at">{{ formatDate(item.created_at) }}</span>
            </div>
            <h3 class="job-title">{{ item.jd.title }}</h3>
            <p class="job-location">{{ item.jd.location }} • {{ item.jd.employment_type || t('common.fulltime') }}</p>
            <div class="job-skills-row" v-if="item.jd.skills && item.jd.skills.length">
              <span v-for="skill in item.jd.skills.slice(0, 5)" :key="skill" class="pill-tag">
                {{ skill }}
              </span>
              <span v-if="item.jd.skills.length > 5" class="pill-tag more-tag">+{{ item.jd.skills.length - 5 }}</span>
            </div>
          </div>

          <div class="row-meta-right">
            <div class="salary-box" v-if="item.jd.salary_range">
              <span class="salary-label">{{ t('jobSearch.salary') }}</span>
              <span class="salary-value">{{ item.jd.salary_range }}</span>
            </div>
            <div class="match-box" v-if="item.match_score">
              <span class="match-label">{{ t('savedJobs.matchScore') }}</span>
              <span class="match-value">{{ item.match_score }}%</span>
            </div>
          </div>

          <div class="row-actions">
            <button class="btn-action-view" @click="openJobDetails(item)" :title="t('savedJobs.view')">
              👁️ {{ t('savedJobs.view') }}
            </button>
            <button class="btn-action-delete" @click="confirmSingleDelete(item)" :title="t('savedJobs.delete')">
              🗑️ {{ t('savedJobs.delete') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-state glass-card">
        <div class="empty-icon">💼</div>
        <h3>{{ t('savedJobs.emptyTitle') }}</h3>
        <p>{{ t('savedJobs.emptyDesc') }}</p>
        <div class="empty-actions">
          <router-link to="/job-recommendation" class="btn-primary empty-btn">
            {{ t('savedJobs.matchJobs') }}
          </router-link>
          <router-link to="/job-search" class="btn-outline-action">
            {{ t('savedJobs.searchJobs') }}
          </router-link>
        </div>
      </div>
    </template>

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
          <div class="drawer-score-block" v-if="activeJob.match_score">
            <p class="drawer-score-title">{{ t('savedJobs.matchScore') }}</p>
            <h3 class="drawer-score-val">{{ activeJob.match_score }}%</h3>
          </div>

          <div class="drawer-section" v-if="activeJob.jd.skills && activeJob.jd.skills.length">
            <h4>{{ t('savedJobs.requiredSkills') }}</h4>
            <div class="skills-tags">
              <span v-for="skill in activeJob.jd.skills" :key="skill" class="pill-tag big-pill">
                {{ skill }}
              </span>
            </div>
          </div>

          <div class="drawer-section">
            <h4>{{ t('savedJobs.jobDescription') }}</h4>
            <p class="drawer-desc-full">{{ activeJob.jd.description }}</p>
          </div>

          <div class="drawer-section" v-if="activeJob.jd.source_url">
            <h4>{{ t('savedJobs.source') }}</h4>
            <a :href="activeJob.jd.source_url" target="_blank" class="source-link">{{ activeJob.jd.source_url }}</a>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div class="modal-overlay confirm-overlay" v-if="showDeleteModal" @click.self="closeDeleteModal">
      <div class="confirm-modal glass-card">
        <h3>⚠️ {{ t('savedJobs.confirmTitle') }}</h3>
        <p class="confirm-message">{{ deleteModalMessage }}</p>
        <div class="modal-buttons">
          <button class="btn-cancel" @click="closeDeleteModal" :disabled="deleting">{{ t('cvHistory.cancel') }}</button>
          <button class="btn-confirm-delete" @click="executeDeletion" :disabled="deleting">
            <span v-if="deleting" class="spinner">⏳</span>
            {{ t('cvHistory.confirmDelete') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div class="toast-notification" :class="{ 'toast-show': showToast, 'toast-error': isToastError }">
      {{ toastMessage }}
    </div>
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api'

const { t, locale } = useI18n()

const savedJobs = ref([])
const loading = ref(true)
const deleting = ref(false)
const selectedIds = ref([])
const activeJob = ref(null)

// Modal
const showDeleteModal = ref(false)
const deleteType = ref('')
const targetDeleteId = ref(null)
const deleteModalMessage = ref('')

// Toast
const showToast = ref(false)
const toastMessage = ref('')
const isToastError = ref(false)

onMounted(async () => {
  await fetchSavedJobs()
})

async function fetchSavedJobs() {
  loading.value = true
  try {
    const res = await api.get('/jobs/saved')
    savedJobs.value = res.data || []
  } catch (err) {
    console.error('Failed to load saved jobs:', err)
    triggerToast(t('savedJobs.loadError'), true)
  } finally {
    loading.value = false
  }
}

const isAllSelected = computed(() => {
  return savedJobs.value.length > 0 && selectedIds.value.length === savedJobs.value.length
})

const isPartiallySelected = computed(() => {
  return selectedIds.value.length > 0 && selectedIds.value.length < savedJobs.value.length
})

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = savedJobs.value.map(j => j.id)
  }
}

function openJobDetails(item) {
  activeJob.value = item
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function confirmSingleDelete(item) {
  deleteType.value = 'single'
  targetDeleteId.value = item.id
  if (locale.value === 'vi') {
    deleteModalMessage.value = `Bạn có chắc muốn xóa "${item.jd.title}" tại ${item.jd.company} khỏi danh sách yêu thích?`
  } else {
    deleteModalMessage.value = `Are you sure you want to remove "${item.jd.title}" at ${item.jd.company} from your saved list?`
  }
  showDeleteModal.value = true
}

function confirmBatchDelete() {
  deleteType.value = 'batch'
  if (locale.value === 'vi') {
    deleteModalMessage.value = `Bạn có chắc muốn xóa ${selectedIds.value.length} job đã chọn khỏi danh sách yêu thích?`
  } else {
    deleteModalMessage.value = `Are you sure you want to remove ${selectedIds.value.length} selected job(s) from your saved list?`
  }
  showDeleteModal.value = true
}

function closeDeleteModal() {
  if (!deleting.value) {
    showDeleteModal.value = false
    targetDeleteId.value = null
  }
}

async function executeDeletion() {
  deleting.value = true
  try {
    if (deleteType.value === 'single') {
      await api.delete(`/jobs/saved/${targetDeleteId.value}`)
      savedJobs.value = savedJobs.value.filter(j => j.id !== targetDeleteId.value)
      selectedIds.value = selectedIds.value.filter(id => id !== targetDeleteId.value)
      triggerToast(t('savedJobs.deletedSuccess'))
    } else if (deleteType.value === 'batch') {
      // Delete one by one since no batch API exists
      const idsToDelete = [...selectedIds.value]
      let deletedCount = 0
      for (const id of idsToDelete) {
        try {
          await api.delete(`/jobs/saved/${id}`)
          deletedCount++
        } catch (err) {
          console.error(`Failed to delete saved job ${id}:`, err)
        }
      }
      savedJobs.value = savedJobs.value.filter(j => !idsToDelete.includes(j.id))
      selectedIds.value = []
      triggerToast(`${t('savedJobs.deletedBatch')} ${deletedCount} ${t('savedJobs.deletedBatchSuffix')}`)
    }
    showDeleteModal.value = false
  } catch (err) {
    console.error('Deletion error:', err)
    triggerToast(t('savedJobs.deleteError'), true)
  } finally {
    deleting.value = false
    targetDeleteId.value = null
  }
}

function triggerToast(msg, isErr = false) {
  toastMessage.value = msg
  isToastError.value = isErr
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 4000)
}
</script>

<style scoped>
.saved-container {
  max-width: 1000px;
  width: 100%;
  margin: 0 auto;
  padding: 40px 24px;
  min-height: calc(100vh - 80px);
  text-align: left;
}

.saved-header {
  margin-bottom: 32px;
}

.section-tag {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-link);
  text-transform: uppercase;
  margin-bottom: 8px;
}

.page-title {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--text-heading);
  margin: 0 0 10px 0;
}

.subtitle-text {
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.loading-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 200px;
  font-size: 1.1rem;
  color: var(--text-secondary);
}

/* Actions Bar */
.actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  margin-bottom: 20px;
  border-radius: var(--radius-md);
  background: var(--bg-actions-bar);
}

.left-actions {
  display: flex;
  align-items: center;
  gap: 24px;
}

.select-all-label {
  font-size: 0.9rem;
  color: var(--text-body);
}

.selection-count {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.btn-batch-delete {
  background-color: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #ef4444;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-batch-delete:hover:not(:disabled) {
  background-color: #ef4444;
  color: #ffffff;
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
}

.btn-batch-delete:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background-color: var(--bg-score-pill);
  border-color: var(--border-card);
  color: var(--text-label);
}

/* Custom Checkbox */
.checkbox-container {
  display: block;
  position: relative;
  padding-left: 28px;
  cursor: pointer;
  user-select: none;
  line-height: 18px;
}

.checkbox-container input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkmark {
  position: absolute;
  top: 0;
  left: 0;
  height: 18px;
  width: 18px;
  background-color: var(--checkbox-bg);
  border: 1px solid var(--checkbox-border);
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.checkbox-container:hover input ~ .checkmark {
  border-color: var(--text-link);
  background-color: rgba(14, 165, 233, 0.05);
}

.checkbox-container input:checked ~ .checkmark {
  background-color: #0ea5e9;
  border-color: #0ea5e9;
}

.checkbox-container input:indeterminate ~ .checkmark {
  background-color: #0ea5e9;
  border-color: #0ea5e9;
}

.checkmark:after {
  content: "";
  position: absolute;
  display: none;
}

.checkbox-container input:checked ~ .checkmark:after {
  display: block;
}

.checkbox-container input:indeterminate ~ .checkmark:after {
  display: block;
  left: 5px;
  top: 7px;
  width: 6px;
  height: 2px;
  background: white;
}

.checkbox-container .checkmark:after {
  left: 6px;
  top: 2px;
  width: 4px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.label-text {
  margin-left: 4px;
}

/* Jobs List */
.jobs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.job-row-card {
  display: flex;
  align-items: center;
  padding: 20px 24px;
  gap: 16px;
  background: var(--bg-actions-bar);
  transition: all var(--transition-fast);
}

.job-row-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-highlight);
  background: var(--bg-hover-subtle);
  box-shadow: var(--shadow-md);
}

.row-selected {
  border-color: rgba(14, 165, 233, 0.4);
  background: rgba(14, 165, 233, 0.03);
}

.row-checkbox {
  flex-shrink: 0;
}

.row-info {
  flex-grow: 1;
  cursor: pointer;
  min-width: 0;
}

.job-meta-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.company-badge {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.25em;
  color: var(--text-link);
  text-transform: uppercase;
}

.job-date {
  font-size: 0.75rem;
  color: var(--text-label);
}

.job-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.job-location {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 0 0 8px 0;
}

.job-skills-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.pill-tag {
  background-color: var(--pill-bg);
  border: 1px solid var(--pill-border);
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 0.7rem;
  color: var(--pill-text);
}

.more-tag {
  font-weight: 600;
  color: var(--text-link);
}

.row-meta-right {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
  cursor: pointer;
}

.salary-box, .match-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--bg-score-pill);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-sm);
  padding: 6px 14px;
  min-width: 90px;
}

.salary-label, .match-label {
  font-size: 0.6rem;
  color: var(--text-label);
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.05em;
  margin-bottom: 2px;
}

.salary-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: #10b981;
  white-space: nowrap;
}

.match-value {
  font-size: 1rem;
  font-weight: 700;
  color: var(--primary);
}

.row-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.btn-action-view {
  background: var(--bg-hover-subtle);
  border: 1px solid var(--border-card);
  color: var(--text-body);
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.btn-action-view:hover {
  background: var(--btn-outline-hover-bg);
  border-color: var(--text-link);
  color: var(--text-link);
}

.btn-action-delete {
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #f87171;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.btn-action-delete:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
  color: #ef4444;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 60px 40px;
  background: var(--bg-actions-bar);
}

.empty-icon {
  font-size: 3.5rem;
  margin-bottom: 20px;
  opacity: 0.4;
}

.empty-state h3 {
  font-size: 1.35rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 8px 0;
}

.empty-state p {
  font-size: 0.95rem;
  color: var(--text-secondary);
  max-width: 460px;
  line-height: 1.6;
  margin-bottom: 24px;
}

.empty-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.empty-btn {
  padding: 12px 24px;
  font-size: 0.9rem;
}

.btn-outline-action {
  display: inline-flex;
  align-items: center;
  padding: 12px 24px;
  border: 1px solid var(--btn-outline-border);
  color: var(--btn-outline-text);
  border-radius: var(--radius-full);
  font-weight: 600;
  font-size: 0.9rem;
  transition: all var(--transition-normal);
  text-decoration: none;
}

.btn-outline-action:hover {
  border-color: var(--btn-outline-hover-border);
  background-color: var(--btn-outline-hover-bg);
}

/* Modal Drawer */
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

.confirm-overlay {
  justify-content: center;
  align-items: center;
  z-index: 2000;
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

.source-link {
  color: var(--text-link);
  text-decoration: none;
  font-size: 0.95rem;
}

.source-link:hover {
  text-decoration: underline;
}

.skills-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* Confirm Modal */
.confirm-modal {
  max-width: 480px;
  width: 90%;
  padding: 32px;
  background-color: var(--modal-confirm-bg);
  border: 1px solid var(--border-card);
  box-shadow: var(--shadow-modal);
  animation: scaleUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.confirm-modal h3 {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 16px 0;
}

.confirm-message {
  font-size: 0.95rem;
  color: var(--text-body);
  line-height: 1.6;
  margin-bottom: 28px;
}

.modal-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel {
  background: var(--bg-hover-subtle);
  border: 1px solid var(--border-card);
  color: var(--text-body);
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.btn-cancel:hover:not(:disabled) {
  background: var(--nav-active-bg);
  color: var(--text-heading);
}

.btn-confirm-delete {
  background-color: #ef4444;
  color: #ffffff;
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-confirm-delete:hover:not(:disabled) {
  background-color: #dc2626;
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
}

.btn-confirm-delete:disabled, .btn-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Spinner */
.spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes scaleUp {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

/* Toast */
.toast-notification {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: rgba(16, 185, 129, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #ffffff;
  padding: 14px 24px;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 500;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
  z-index: 3000;
  transform: translateY(100px);
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-error {
  background: rgba(239, 68, 68, 0.9);
  border-color: rgba(239, 68, 68, 0.3);
}

.toast-show {
  transform: translateY(0);
  opacity: 1;
}

@media (max-width: 768px) {
  .job-row-card {
    flex-wrap: wrap;
    padding: 16px;
  }
  .row-meta-right {
    flex-direction: row;
    width: 100%;
    margin-left: 34px;
    margin-top: 8px;
  }
  .row-actions {
    width: 100%;
    margin-left: 34px;
    justify-content: flex-end;
  }
}
</style>
