<template>
  <main class="history-container">
    <div class="history-header">
      <p class="section-tag">{{ t('cvHistory.tag') }}</p>
      <h1 class="welcome-text">{{ t('cvHistory.title') }}</h1>
      <p class="subtitle-text">
        {{ t('cvHistory.desc') }}
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-box glass-card">
      <div class="spinner">⏳</div> {{ t('cvHistory.loading') }}
    </div>

    <template v-else>
      <!-- Batch Actions Bar -->
      <div class="actions-bar glass-card" v-if="reports.length">
        <div class="left-actions">
          <label class="checkbox-container select-all-label">
            <input 
              type="checkbox" 
              :checked="isAllSelected" 
              :indeterminate="isPartiallySelected"
              @change="toggleSelectAll"
            />
            <span class="checkmark"></span>
            <span class="label-text">{{ isAllSelected ? t('cvHistory.deselectAll') : t('cvHistory.selectAll') }}</span>
          </label>
          <span class="selection-count" v-if="selectedIds.length > 0">
            {{ t('cvHistory.selected') }}: <strong>{{ selectedIds.length }}</strong> {{ t('cvHistory.reports') }}
          </span>
        </div>
        
        <div class="right-actions">
          <button 
            class="btn-batch-delete" 
            :disabled="selectedIds.length === 0 || deleting"
            @click="confirmBatchDelete"
          >
            <span v-if="deleting" class="spinner">⏳</span>
            {{ t('cvHistory.deleteSelected') }}
          </button>
        </div>
      </div>

      <!-- Reports List -->
      <div class="history-list" v-if="reports.length">
        <div 
          v-for="report in reports" 
          :key="report.id" 
          class="report-row-card glass-card"
          :class="{ 'row-selected': selectedIds.includes(report.id) }"
        >
          <div class="row-checkbox">
            <label class="checkbox-container">
              <input 
                type="checkbox" 
                :value="report.id" 
                v-model="selectedIds"
              />
              <span class="checkmark"></span>
            </label>
          </div>

          <div class="row-info" @click="viewReport(report.id)">
            <div class="report-meta-header">
              <span class="report-id-badge">#{{ report.id }}</span>
              <span class="report-date">{{ formatDate(report.created_at) }}</span>
            </div>
            <h3 class="report-title">
              {{ report.target_role || t('cvHistory.generalAnalysis') }}
            </h3>
            <p class="report-field" v-if="report.target_field">
              {{ t('cvHistory.field') }}: <span>{{ report.target_field }}</span>
            </p>
          </div>

          <div class="row-scores" @click="viewReport(report.id)">
            <div class="score-pill">
              <span class="score-label">{{ t('cvHistory.resume') }}</span>
              <span class="score-num" :class="getScoreClass(report.resume_score)">
                {{ report.resume_score ?? 'N/A' }}%
              </span>
            </div>
            <div class="score-pill">
              <span class="score-label">{{ t('cvHistory.atsMatch') }}</span>
              <span class="score-num" :class="getScoreClass(report.ats_score)">
                {{ report.ats_score ?? 'N/A' }}%
              </span>
            </div>
          </div>

          <div class="row-actions">
            <button class="btn-action-view" @click="viewReport(report.id)" :title="t('cvHistory.view')">
              👁️ {{ t('cvHistory.view') }}
            </button>
            <button class="btn-action-delete" @click="confirmSingleDelete(report)" :title="t('cvHistory.delete')">
              🗑️ {{ t('cvHistory.delete') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-history glass-card">
        <div class="empty-icon">📂</div>
        <h3>{{ t('cvHistory.emptyTitle') }}</h3>
        <p>{{ t('cvHistory.emptyDesc') }}</p>
        <router-link to="/cv-analysis" class="btn-upload-cv">
          📄 {{ t('cvHistory.uploadNow') }}
        </router-link>
      </div>
    </template>

    <!-- Delete Confirmation Modal -->
    <div class="modal-overlay" v-if="showDeleteModal" @click.self="closeDeleteModal">
      <div class="confirm-modal glass-card">
        <h3>⚠️ {{ t('cvHistory.confirmTitle') }}</h3>
        <p class="confirm-message">
          {{ deleteModalMessage }}
        </p>
        <div class="modal-buttons">
          <button class="btn-cancel" @click="closeDeleteModal" :disabled="deleting">{{ t('cvHistory.cancel') }}</button>
          <button class="btn-confirm-delete" @click="executeDeletion" :disabled="deleting">
            <span v-if="deleting" class="spinner">⏳</span>
            {{ t('cvHistory.confirmDelete') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Notification Toast -->
    <div class="toast-notification" :class="{ 'toast-show': showToast, 'toast-error': isToastError }">
      {{ toastMessage }}
    </div>
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '../api'

const { t } = useI18n()
const router = useRouter()
const reports = ref([])
const loading = ref(true)
const deleting = ref(false)
const selectedIds = ref([])

// Modal control
const showDeleteModal = ref(false)
const deleteType = ref('') // 'single' or 'batch'
const targetReportId = ref(null)
const deleteModalMessage = ref('')

// Toast control
const showToast = ref(false)
const toastMessage = ref('')
const isToastError = ref(false)

onMounted(async () => {
  await fetchHistory()
})

async function fetchHistory() {
  loading.value = true
  try {
    const res = await api.get('/cv/history')
    reports.value = res.data
  } catch (err) {
    console.error('Failed to load history:', err)
    triggerToast(t('cvHistory.loadError'), true)
  } finally {
    loading.value = false
  }
}

// Select All functionality
const isAllSelected = computed(() => {
  return reports.value.length > 0 && selectedIds.value.length === reports.value.length
})

const isPartiallySelected = computed(() => {
  return selectedIds.value.length > 0 && selectedIds.value.length < reports.value.length
})

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = reports.value.map(r => r.id)
  }
}

function viewReport(id) {
  router.push(`/cv-analysis/${id}`)
}

function getScoreClass(score) {
  if (score === null || score === undefined) return 'score-gray'
  if (score >= 85) return 'score-green'
  if (score >= 70) return 'score-yellow'
  return 'score-red'
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

// Single Delete Action
function confirmSingleDelete(report) {
  deleteType.value = 'single'
  targetReportId.value = report.id
  deleteModalMessage.value = `${t('cvHistory.confirmSingle')} #${report.id} (${report.target_role || t('cvHistory.generalAnalysis')})? ${t('cvHistory.cannotUndo')}`
  showDeleteModal.value = true
}

// Batch Delete Action
function confirmBatchDelete() {
  deleteType.value = 'batch'
  deleteModalMessage.value = `${t('cvHistory.confirmBatch')} ${selectedIds.value.length} ${t('cvHistory.confirmBatchSuffix')} ${t('cvHistory.cannotUndo')}`
  showDeleteModal.value = true
}

function closeDeleteModal() {
  if (!deleting.value) {
    showDeleteModal.value = false
    targetReportId.value = null
  }
}

async function executeDeletion() {
  deleting.value = true
  try {
    if (deleteType.value === 'single') {
      await api.delete(`/cv/analysis/${targetReportId.value}`)
      reports.value = reports.value.filter(r => r.id !== targetReportId.value)
      selectedIds.value = selectedIds.value.filter(id => id !== targetReportId.value)
      triggerToast(t('cvHistory.deletedSuccess'))
    } else if (deleteType.value === 'batch') {
      const res = await api.post('/cv/analysis/batch-delete', {
        analysis_ids: selectedIds.value
      })
      const deletedCount = res.data.deleted_count || selectedIds.value.length
      reports.value = reports.value.filter(r => !selectedIds.value.includes(r.id))
      selectedIds.value = []
      triggerToast(`${t('cvHistory.deletedBatch')} ${deletedCount} ${t('cvHistory.deletedBatchSuffix')}`)
    }
    showDeleteModal.value = false
  } catch (err) {
    console.error('Deletion error:', err)
    triggerToast(t('cvHistory.deleteError'), true)
  } finally {
    deleting.value = false
    targetReportId.value = null
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
.history-container {
  max-width: 1000px;
  width: 100%;
  margin: 0 auto;
  padding: 40px 24px;
  min-height: calc(100vh - 80px);
  text-align: left;
}

.history-header {
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

.welcome-text {
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

/* History List & Cards */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.report-row-card {
  display: flex;
  align-items: center;
  padding: 18px 24px;
  gap: 16px;
  background: var(--bg-actions-bar);
  transition: all var(--transition-fast);
}

.report-row-card:hover {
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

.report-meta-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.report-id-badge {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-link);
  background: var(--score-badge-bg);
  padding: 2px 8px;
  border-radius: 4px;
}

.report-date {
  font-size: 0.8rem;
  color: var(--text-label);
}

.report-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.report-field {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 0;
}

.report-field span {
  color: var(--text-body);
}

.row-scores {
  display: flex;
  gap: 16px;
  flex-shrink: 0;
  cursor: pointer;
}

.score-pill {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--bg-score-pill);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-sm);
  padding: 6px 12px;
  min-width: 80px;
}

.score-label {
  font-size: 0.65rem;
  color: var(--text-label);
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.05em;
  margin-bottom: 2px;
}

.score-num {
  font-size: 1.05rem;
  font-weight: 700;
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
.empty-history {
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

.empty-history h3 {
  font-size: 1.35rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 8px 0;
}

.empty-history p {
  font-size: 0.95rem;
  color: var(--text-secondary);
  max-width: 460px;
  line-height: 1.6;
  margin-bottom: 24px;
}

.btn-upload-cv {
  background: var(--gradient-primary);
  color: var(--text-on-primary);
  padding: 12px 24px;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 600;
  box-shadow: var(--shadow-glow);
  transition: all var(--transition-fast);
}

.btn-upload-cv:hover {
  opacity: 0.95;
  transform: translateY(-1px);
}

/* Modals */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--overlay-bg);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.25s ease-out;
}

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

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
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
  .report-row-card {
    flex-wrap: wrap;
    padding: 16px;
  }
  .row-scores {
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
