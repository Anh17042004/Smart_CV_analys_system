<template>
  <main class="analysis-container">
    <div class="analysis-header">
      <p class="section-tag">{{ t('cvAnalysis.tag') }}</p>
      <h1 class="main-title">{{ t('cvAnalysis.title') }}</h1>
      <p class="desc-text">
        {{ t('cvAnalysis.desc') }}
      </p>
    </div>

    <div class="analysis-grid">
      <!-- Inputs Column -->
      <section class="inputs-column glass-card">
        <h2>{{ t('cvAnalysis.uploadTitle') }}</h2>
        <p class="file-support-text">{{ t('cvAnalysis.supportedFormats') }}</p>

        <div 
          class="dropzone-area" 
          @dragover.prevent="dragOver = true" 
          @dragleave.prevent="dragOver = false"
          @drop.prevent="handleDrop"
          :class="{ 'dropzone-active': dragOver }"
        >
          <input 
            type="file" 
            ref="fileInput" 
            accept=".pdf,.docx" 
            @change="handleFileSelect" 
            class="hidden-file-input" 
          />
          <div class="dropzone-label" @click="$refs.fileInput.click()">
            <span class="upload-icon">📁</span>
            <p v-if="file">{{ file.name }} ({{ formatSize(file.size) }})</p>
            <p v-else v-html="t('cvAnalysis.dragDrop') + ' <span class=\'browse-text\'>' + t('cvAnalysis.browse') + '</span>'"></p>
          </div>
        </div>

        <div class="divider">
          <span>{{ t('cvAnalysis.andOr') }}</span>
        </div>

        <div class="input-group">
          <div class="jd-header-row">
            <label class="input-label">{{ t('cvAnalysis.jdLabel') }}</label>
            <button type="button" class="btn-jd-upload" @click="$refs.jdFileInput.click()" :disabled="jdExtracting">
              <span v-if="jdExtracting" class="spinner">⏳</span>
              <span>{{ jdExtracting ? t('cvAnalysis.extractingJd') : t('cvAnalysis.jdUploadBrowse') }}</span>
            </button>
            <input 
              type="file" 
              ref="jdFileInput" 
              accept=".pdf,.docx" 
              @change="handleJdFileSelect" 
              class="hidden-file-input" 
            />
          </div>
          <p class="input-desc">{{ t('cvAnalysis.jdDesc') }}</p>
          <textarea 
            v-model="jobDescription" 
            rows="6" 
            :placeholder="t('cvAnalysis.jdPlaceholder')" 
            class="input-field textarea-field"
          ></textarea>
          <p v-if="jdFileName" class="jd-file-badge">
            <span class="badge-icon">📄</span>
            <span class="badge-text">{{ t('cvAnalysis.jdUploadedText') }} <strong>{{ jdFileName }}</strong></span>
            <button type="button" class="btn-clear-jd" @click="clearJdFile" title="Clear JD">✕</button>
          </p>
        </div>

        <button 
          @click="startAnalysis" 
          :disabled="!file || loading" 
          class="btn-primary analyze-btn"
        >
          <span v-if="loading" class="spinner">⏳</span>
          {{ loading ? t('cvAnalysis.analyzing') : t('cvAnalysis.startAnalysis') }}
        </button>

        <p v-if="error" class="error-text">{{ error }}</p>
      </section>

      <!-- Results Column -->
      <section class="results-column glass-card">
        <template v-if="result">
          <!-- Action Row for PDF download -->
          <div class="results-actions-row">
            <button @click="downloadPdf" class="btn-pdf-download" :disabled="pdfDownloading">
              <span v-if="pdfDownloading" class="spinner">⏳</span>
              <span v-else>📥</span>
              {{ pdfDownloading ? t('cvAnalysis.downloadingPdf') : t('cvAnalysis.downloadPdf') }}
            </button>
          </div>
          <!-- Scores Row -->
          <div class="results-top-row">
            <div>
              <p class="results-tag">{{ t('cvAnalysis.cvScore') }}</p>
              <h2 class="score-value" :class="getScoreClass(result.resume_score)">{{ result.resume_score }}%</h2>
            </div>
            <div>
              <p class="results-tag">{{ t('cvAnalysis.atsScore') }}</p>
              <h2 class="score-value" :class="getScoreClass(result.ats_score)">{{ result.ats_score }}%</h2>
            </div>
            <div class="role-badge">
              <p class="badge-title">{{ t('cvAnalysis.detectedRole') }}</p>
              <p class="badge-value">{{ result.target_role || t('cvAnalysis.notDetected') }}</p>
            </div>
          </div>

          <!-- Summary Block -->
          <div class="result-card-block">
            <h3 class="block-title">{{ t('cvAnalysis.aiFeedback') }}</h3>
            <p class="feedback-text">{{ result.detailed_feedback }}</p>
          </div>

          <!-- Lists Grid -->
          <div class="lists-grid">
            <div class="info-list-card">
              <h3 class="list-title strengths-title">{{ t('cvAnalysis.strengths') }}</h3>
              <ul class="info-list">
                <li v-for="item in result.strengths" :key="item">• {{ item }}</li>
              </ul>
            </div>

            <div class="info-list-card">
              <h3 class="list-title weaknesses-title">{{ t('cvAnalysis.weaknesses') }}</h3>
              <ul class="info-list">
                <li v-for="item in result.weaknesses" :key="item">• {{ item }}</li>
              </ul>
            </div>
          </div>

          <!-- Improvements -->
          <div class="result-card-block">
            <h3 class="block-title improvements-title">{{ t('cvAnalysis.improvements') }}</h3>
            <ul class="info-list">
              <li v-for="item in result.improvements" :key="item">• {{ item }}</li>
            </ul>
          </div>

          <!-- Skills Analysis -->
          <div v-if="result.skills_analysis" class="result-card-block">
            <h3 class="block-title">{{ t('cvAnalysis.skillsBreakdown') }} ({{ t('common.match') }}: {{ result.skills_analysis.match_percentage }}%)</h3>
            <div class="skills-containers">
              <div class="skills-sub-group">
                <p class="skills-sub-title matched-skills">{{ t('cvAnalysis.matchedSkills') }}</p>
                <div class="skills-tags">
                  <span 
                    v-for="s in result.skills_analysis.matched_skills" 
                    :key="s" 
                    class="skill-tag tag-matched"
                  >
                    {{ s }}
                  </span>
                </div>
              </div>
              <div class="skills-sub-group">
                <p class="skills-sub-title missing-skills">{{ t('cvAnalysis.missingSkills') }}</p>
                <div class="skills-tags">
                  <span 
                    v-for="s in result.skills_analysis.missing_skills" 
                    :key="s" 
                    class="skill-tag tag-missing"
                  >
                    {{ s }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Job Match (if JD supplied) -->
          <div v-if="result.job_match" class="result-card-block highlight-block">
            <h3 class="block-title">{{ t('cvAnalysis.targetJobMatch') }} ({{ result.job_match.match_percentage }}%)</h3>
            <p class="skills-sub-title missing-skills">{{ t('cvAnalysis.gapsToFill') }}</p>
            <ul class="info-list">
              <li v-for="gap in result.job_match.gaps" :key="gap">• {{ gap }}</li>
            </ul>
          </div>

          <!-- Recommended Courses -->
          <div v-if="result.recommended_courses && result.recommended_courses.length" class="result-card-block">
            <h3 class="block-title">{{ t('cvAnalysis.recommendedCourses') }}</h3>
            <div class="courses-list">
              <div v-for="course in result.recommended_courses" :key="course.name" class="course-item">
                <p class="course-name">{{ course.name }}</p>
                <p class="course-provider">By {{ course.provider }} • Skills: {{ Array.isArray(course.skills) ? course.skills.join(', ') : course.skills }}</p>
              </div>
            </div>
          </div>

          <!-- Auto recommended jobs -->
          <div v-if="result.recommendations && result.recommendations.length" class="result-card-block">
            <h3 class="block-title">{{ t('cvAnalysis.matchingJobs') }}</h3>
            <div class="jobs-rec-list">
              <div v-for="rec in result.recommendations.slice(0, 3)" :key="rec.jd.id" class="job-rec-item">
                <div class="job-rec-header">
                  <div>
                    <p class="job-rec-company">{{ rec.jd.company }}</p>
                    <p class="job-rec-title">{{ rec.jd.title }}</p>
                  </div>
                  <span class="job-rec-score">{{ rec.match_score }}% {{ t('common.match').toLowerCase() }}</span>
                </div>
              </div>
            </div>
          </div>

        </template>
        <div v-else class="empty-results-box">
          <span class="waiting-icon">📊</span>
          <p class="waiting-title">{{ t('cvAnalysis.waitingTitle') }}</p>
          <p class="waiting-desc">{{ t('cvAnalysis.waitingDesc') }}</p>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '../api'

const { t } = useI18n()

const route = useRoute()
const file = ref(null)
const fileInput = ref(null)
const jobDescription = ref('')
const loading = ref(false)
const dragOver = ref(false)
const error = ref(null)
const result = ref(null)
const pdfDownloading = ref(false)
const jdFileInput = ref(null)
const jdExtracting = ref(false)
const jdFileName = ref('')

async function loadAnalysis(id) {
  if (!id) return
  loading.value = true
  error.value = null
  result.value = null
  try {
    const res = await api.get(`/cv/result/${id}`)
    result.value = res.data
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Không thể tải chi tiết báo cáo'
  } finally {
    loading.value = false
  }
}

async function downloadPdf() {
  if (!result.value?.id) return
  pdfDownloading.value = true
  try {
    const res = await api.get(`/cv/report/${result.value.id}`, {
      responseType: 'blob'
    })
    const blob = new Blob([res.data], { type: 'application/pdf' })
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = `cv_report_${result.value.id}.pdf`
    link.click()
    window.URL.revokeObjectURL(link.href)
  } catch (err) {
    alert('Lỗi khi tải file báo cáo PDF: ' + (err.message || err))
  } finally {
    pdfDownloading.value = false
  }
}

onMounted(() => {
  if (route.params.id) {
    loadAnalysis(route.params.id)
  }
})

watch(() => route.params.id, (newId) => {
  if (newId) {
    loadAnalysis(newId)
  } else {
    result.value = null
  }
})

function handleFileSelect(event) {
  const selected = event.target.files?.[0]
  if (selected) {
    file.value = selected
  }
}

function handleDrop(event) {
  dragOver.value = false
  const droppedFile = event.dataTransfer?.files?.[0]
  if (droppedFile) {
    const ext = droppedFile.name.split('.').pop().toLowerCase()
    if (ext === 'pdf' || ext === 'docx') {
      file.value = droppedFile
    } else {
      error.value = 'Chỉ chấp nhận định dạng file .pdf hoặc .docx'
    }
  }
}

function formatSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

async function startAnalysis() {
  if (!file.value) return
  loading.value = true
  error.value = null
  result.value = null

  try {
    // 1. Upload CV file
    const formData = new FormData()
    formData.append('file', file.value)
    const uploadRes = await api.post('/cv/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    const cvId = uploadRes.data.id

    // 2. Trigger analysis
    const analyzeRes = await api.post('/cv/analyze', {
      cv_id: cvId,
      job_description: jobDescription.value || null
    })
    result.value = analyzeRes.data
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Phân tích CV thất bại'
  } finally {
    loading.value = false
  }
}

async function handleJdFileSelect(event) {
  const selected = event.target.files?.[0]
  if (!selected) return
  
  const ext = selected.name.split('.').pop().toLowerCase()
  if (ext !== 'pdf' && ext !== 'docx') {
    alert('Chỉ chấp nhận file định dạng .pdf hoặc .docx')
    return
  }
  
  jdExtracting.value = true
  error.value = null
  try {
    const formData = new FormData()
    formData.append('file', selected)
    const res = await api.post('/cv/extract-text', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    jobDescription.value = res.data.text
    jdFileName.value = res.data.filename
  } catch (err) {
    alert('Lỗi trích xuất văn bản từ JD: ' + (err.response?.data?.detail || err.message))
  } finally {
    jdExtracting.value = false
    if (jdFileInput.value) {
      jdFileInput.value.value = ''
    }
  }
}

function clearJdFile() {
  jobDescription.value = ''
  jdFileName.value = ''
  if (jdFileInput.value) {
    jdFileInput.value.value = ''
  }
}

function getScoreClass(score) {
  if (!score) return ''
  if (score >= 85) return 'score-green'
  if (score >= 70) return 'score-yellow'
  return 'score-red'
}
</script>

<style scoped>
.analysis-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
  width: 100%;
}

.analysis-header {
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

.analysis-grid {
  display: grid;
  grid-template-columns: 0.95fr 1.05fr;
  gap: 24px;
  align-items: start;
}

@media (max-width: 992px) {
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}

.inputs-column {
  text-align: left;
}

.inputs-column h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-heading);
  margin-bottom: 4px;
}

.file-support-text {
  font-size: 0.85rem;
  color: var(--text-label);
  margin-bottom: 20px;
}

.dropzone-area {
  border: 1px dashed var(--border-dashed);
  background-color: var(--bg-dropzone);
  border-radius: var(--radius-lg);
  padding: 32px;
  text-align: center;
  transition: all var(--transition-normal);
}

.dropzone-active {
  border-color: #0ea5e9;
  background-color: rgba(14, 165, 233, 0.05);
}

.hidden-file-input {
  display: none;
}

.dropzone-label {
  cursor: pointer;
}

.upload-icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 12px;
}

.dropzone-label p {
  font-size: 0.95rem;
  color: var(--text-secondary);
}

.browse-text {
  color: var(--text-link);
  font-weight: 600;
}

.browse-text:hover {
  text-decoration: underline;
}

.divider {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.3em;
  color: var(--text-label);
  margin: 24px 0;
}

.divider::before, .divider::after {
  content: '';
  flex-grow: 1;
  height: 1px;
  background-color: var(--border-divider);
}

.input-group {
  margin-bottom: 24px;
}

.input-label {
  display: block;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-heading);
  margin-bottom: 4px;
}

.input-desc {
  font-size: 0.85rem;
  color: var(--text-label);
  margin-bottom: 12px;
}

.textarea-field {
  resize: vertical;
}

.analyze-btn {
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

.empty-results-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

.waiting-icon {
  font-size: 3.5rem;
  margin-bottom: 16px;
  opacity: 0.5;
}

.waiting-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.waiting-desc {
  font-size: 0.9rem;
  color: var(--text-label);
  max-width: 340px;
  line-height: 1.5;
}

.results-top-row {
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 24px;
}

.results-tag {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-label);
  text-transform: uppercase;
  margin-bottom: 6px;
}

.score-value {
  font-size: 3rem;
  font-weight: 600;
  margin: 0;
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

.role-badge {
  flex-grow: 1;
  background-color: var(--bg-badge);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 12px 20px;
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
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0;
}

.result-card-block {
  background-color: var(--bg-card-inner);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 24px;
}

.block-title {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-accent);
  text-transform: uppercase;
  margin-bottom: 16px;
}

.feedback-text {
  font-size: 0.95rem;
  color: var(--text-body);
  line-height: 1.6;
  margin: 0;
}

.lists-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

@media (max-width: 576px) {
  .lists-grid {
    grid-template-columns: 1fr;
  }
}

.info-list-card {
  background-color: var(--bg-card-inner);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.list-title {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  margin-bottom: 16px;
}

.strengths-title {
  color: #10b981;
}

.weaknesses-title {
  color: #f59e0b;
}

.improvements-title {
  color: var(--text-link);
}

.info-list {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-list li {
  font-size: 0.9rem;
  color: var(--text-body);
  line-height: 1.4;
}

.skills-containers {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.skills-sub-title {
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 10px;
}

.matched-skills {
  color: #10b981;
}

.missing-skills {
  color: #f59e0b;
}

.skills-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-tag {
  font-size: 0.8rem;
  padding: 4px 12px;
  border-radius: 9999px;
  font-weight: 500;
}

.tag-matched {
  background-color: var(--tag-matched-bg);
  border: 1px solid var(--tag-matched-border);
  color: var(--tag-matched-text);
}

.tag-missing {
  background-color: var(--tag-missing-bg);
  border: 1px solid var(--tag-missing-border);
  color: var(--tag-missing-text);
}

.highlight-block {
  border-color: rgba(245, 158, 11, 0.25);
  background-color: rgba(245, 158, 11, 0.03);
}

.courses-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.course-item {
  border-bottom: 1px solid var(--border-divider);
  padding-bottom: 12px;
}

.course-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.course-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-heading);
  margin-bottom: 4px;
}

.course-provider {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 0;
}

.jobs-rec-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.job-rec-item {
  background-color: var(--bg-score-pill);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 16px;
}

.job-rec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.job-rec-company {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-label);
  text-transform: uppercase;
  margin-bottom: 4px;
}

.job-rec-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0;
}

.job-rec-score {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-link);
  background-color: var(--score-badge-bg);
  padding: 4px 12px;
  border-radius: 9999px;
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

.results-actions-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.btn-pdf-download {
  background: var(--gradient-primary);
  color: var(--text-on-primary);
  border: none;
  padding: 10px 18px;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-glow);
}

.btn-pdf-download:hover:not(:disabled) {
  opacity: 0.95;
  transform: translateY(-1px);
}

.btn-pdf-download:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.jd-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.btn-jd-upload {
  background: var(--bg-card-inner);
  border: 1px solid var(--border-card);
  color: var(--text-heading);
  padding: 6px 12px;
  border-radius: var(--radius-md);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all var(--transition-fast);
}

.btn-jd-upload:hover:not(:disabled) {
  background: var(--border-card);
  color: var(--text-link);
}

.btn-jd-upload:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.jd-file-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background-color: var(--bg-score-pill);
  border: 1px solid var(--border-card);
  padding: 6px 12px;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 8px;
}

.btn-clear-jd {
  background: none;
  border: none;
  color: var(--text-label);
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color var(--transition-fast);
}

.btn-clear-jd:hover {
  color: var(--text-danger, #ef4444);
}
</style>
