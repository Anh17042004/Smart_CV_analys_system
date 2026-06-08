<template>
  <main class="result-container">
    <div v-if="loading" class="loading-state glass-card">
      <div class="spinner"></div>
      <p>Đang tải báo cáo đánh giá phỏng vấn...</p>
    </div>

    <div v-else-if="error" class="error-state glass-card">
      <span class="error-icon">⚠️</span>
      <h2>Không thể tải kết quả</h2>
      <p class="error-desc">{{ error }}</p>
      <button @click="goHome" class="btn-primary">Về Bảng Điều Khiển</button>
    </div>

    <div v-else-if="session" class="result-content">
      <!-- Header -->
      <div class="result-header glass-card">
        <div>
          <span class="tag-badge">{{ t('mockInterview.resultTitle') }}</span>
          <h1>Buổi Phỏng Vấn Hoàn Thành!</h1>
          <p class="meta-desc">
            Lĩnh vực: <strong>{{ session.field || 'Chung' }}</strong> • Cấp bậc: <strong>{{ session.level || 'Junior' }}</strong> • Loại: <strong>{{ session.interview_type || 'General' }}</strong> • Ngày: {{ formatDate(session.completed_at) }}
          </p>
        </div>
        <div class="header-actions">
          <button @click="startNewInterview" class="btn-primary">Luyện Tập Lại</button>
          <button @click="goHome" class="btn-secondary">Bảng Điều Khiển</button>
        </div>
      </div>

      <!-- Dashboard Grid -->
      <div class="dashboard-grid">
        <!-- Overall Score Ring -->
        <div class="score-card glass-card">
          <h3>{{ t('mockInterview.overallScore') }}</h3>
          <div class="circular-score-box">
            <svg class="circular-progress" viewBox="0 0 100 100">
              <circle class="bg-ring" cx="50" cy="50" r="40"></circle>
              <circle 
                class="fill-ring" 
                cx="50" 
                cy="50" 
                r="40" 
                :style="{ strokeDasharray: 251.2, strokeDashoffset: 251.2 - (251.2 * (session.overall_score || 0)) / 10 }"
              ></circle>
            </svg>
            <div class="score-inner">
              <span class="score-number">{{ session.overall_score !== null ? session.overall_score.toFixed(1) : '0.0' }}</span>
              <span class="score-max">/ 10</span>
            </div>
          </div>
          <p class="score-comment">{{ getScoreComment(session.overall_score) }}</p>
        </div>

        <!-- Metric Criteria Sliders -->
        <div class="criteria-card glass-card">
          <h3>Điểm Số Theo Tiêu Chí</h3>
          <div class="criteria-list">
            <!-- Content -->
            <div class="criteria-item">
              <div class="criteria-label">
                <span>🎯 {{ t('mockInterview.contentScore') }} (Nội dung)</span>
                <span class="criteria-value">{{ getCategoryScore('content') }} / 10</span>
              </div>
              <div class="slider-track">
                <div class="slider-fill" :style="{ width: `${getCategoryScore('content') * 10}%`, background: 'var(--primary)' }"></div>
              </div>
            </div>

            <!-- Structure -->
            <div class="criteria-item">
              <div class="criteria-label">
                <span>🏗️ {{ t('mockInterview.structureScore') }} (Cấu trúc)</span>
                <span class="criteria-value">{{ getCategoryScore('structure') }} / 10</span>
              </div>
              <div class="slider-track">
                <div class="slider-fill" :style="{ width: `${getCategoryScore('structure') * 10}%`, background: 'var(--accent)' }"></div>
              </div>
            </div>

            <!-- Communication -->
            <div class="criteria-item">
              <div class="criteria-label">
                <span>🗣️ {{ t('mockInterview.communicationScore') }} (Giao tiếp)</span>
                <span class="criteria-value">{{ getCategoryScore('communication') }} / 10</span>
              </div>
              <div class="slider-track">
                <div class="slider-fill" :style="{ width: `${getCategoryScore('communication') * 10}%`, background: 'var(--success)' }"></div>
              </div>
            </div>

            <!-- Confidence -->
            <div class="criteria-item">
              <div class="criteria-label">
                <span>💪 {{ t('mockInterview.confidenceScore') }} (Tự tin)</span>
                <span class="criteria-value">{{ getCategoryScore('confidence') }} / 10</span>
              </div>
              <div class="slider-track">
                <div class="slider-fill" :style="{ width: `${getCategoryScore('confidence') * 10}%`, background: 'var(--warning)' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- General Feedback & Bullet Lists -->
      <div class="feedback-grid">
        <!-- Overall Feedback Text -->
        <div class="feedback-card glass-card">
          <h3>📝 Nhận Xét Tổng Quan</h3>
          <p class="feedback-text">{{ session.overall_feedback }}</p>
        </div>

        <!-- Strengths & Weaknesses -->
        <div class="bullets-card glass-card">
          <div class="bullets-section">
            <h3 class="strengths-title">🔥 {{ t('mockInterview.strengths') }}</h3>
            <ul class="bullets-list">
              <li v-for="(item, idx) in session.strengths" :key="idx">• {{ item }}</li>
              <li v-if="!session.strengths?.length">AI không ghi nhận điểm mạnh nổi bật cụ thể nào.</li>
            </ul>
          </div>

          <div class="bullets-section divider-top">
            <h3 class="improvements-title">💡 {{ t('mockInterview.improvements') }}</h3>
            <ul class="bullets-list">
              <li v-for="(item, idx) in session.improvements" :key="idx">• {{ item }}</li>
              <li v-if="!session.improvements?.length">AI không ghi nhận điểm yếu cụ thể nào cần khắc phục gấp.</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Collapsible Q&A List -->
      <section class="qa-section glass-card">
        <h3>💬 Chi Tiết Cuộc Trò Chuyện & Điểm Số Từng Câu Hỏi</h3>
        <div class="qa-list">
          <div 
            v-for="ans in session.answers" 
            :key="ans.id" 
            class="qa-item" 
            :class="{ open: expandedAnswers.includes(ans.id) }"
          >
            <!-- Accordion Header -->
            <div class="qa-header" @click="toggleAnswerExpand(ans.id)">
              <div class="qa-header-left">
                <span class="question-number-badge">Q{{ ans.question_number }}</span>
                <h4 class="truncate-text">{{ ans.question_text }}</h4>
              </div>
              <div class="qa-header-right">
                <span class="score-badge">{{ ans.overall_score !== null ? ans.overall_score.toFixed(1) : '0.0' }} / 10</span>
                <span class="chevron">{{ expandedAnswers.includes(ans.id) ? '▲' : '▼' }}</span>
              </div>
            </div>

            <!-- Accordion Content -->
            <div v-show="expandedAnswers.includes(ans.id)" class="qa-content">
              <div class="qa-block">
                <p class="qa-label user-label">🗣️ Câu trả lời của bạn:</p>
                <div class="qa-bubble user-bubble">
                  {{ ans.answer_text }}
                </div>
              </div>

              <div class="qa-block">
                <p class="qa-label ai-label">🤖 Đánh giá từ AI Mentor:</p>
                <div class="qa-bubble ai-bubble">
                  <p class="eval-text">{{ ans.ai_feedback }}</p>
                  
                  <!-- Metric scores on question -->
                  <div class="sub-metrics-grid">
                    <span class="sub-metric">Content: <strong>{{ ans.content_score }}</strong></span>
                    <span class="sub-metric">Structure: <strong>{{ ans.structure_score }}</strong></span>
                    <span class="sub-metric">Communication: <strong>{{ ans.communication_score }}</strong></span>
                    <span class="sub-metric">Confidence: <strong>{{ ans.confidence_score }}</strong></span>
                  </div>
                </div>
              </div>

              <div v-if="ans.suggested_answer" class="qa-block">
                <p class="qa-label suggested-label">✨ {{ t('mockInterview.suggestedAnswer') }}:</p>
                <div class="qa-bubble suggested-bubble">
                  {{ ans.suggested_answer }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '../api'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref(null)
const session = ref(null)
const expandedAnswers = ref([])

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

async function loadResults() {
  const sessionId = route.params.id
  if (!sessionId) {
    error.value = 'Mã phiên phỏng vấn không hợp lệ.'
    loading.value = false
    return
  }

  loading.value = true
  error.value = null
  try {
    const res = await api.get(`/interview/session/${sessionId}`)
    session.value = res.data
    
    // Auto expand the first question by default
    if (session.value?.answers?.length > 0) {
      expandedAnswers.value = [session.value.answers[0].id]
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Không thể tải kết quả phỏng vấn.'
  } finally {
    loading.value = false
  }
}

function toggleAnswerExpand(id) {
  if (expandedAnswers.value.includes(id)) {
    expandedAnswers.value = expandedAnswers.value.filter(x => x !== id)
  } else {
    expandedAnswers.value.push(id)
  }
}

function getCategoryScore(cat) {
  if (!session.value || !session.value.scores_by_category) return 0.0
  const scores = session.value.scores_by_category
  if (typeof scores === 'string') {
    try {
      const parsed = JSON.parse(scores)
      return parsed[cat] || 0.0
    } catch (e) {
      return 0.0
    }
  }
  return scores[cat] || 0.0
}

function getScoreComment(score) {
  if (score === null || score === undefined) return 'Đang xử lý...'
  if (score >= 8.5) return 'Xuất sắc! Bạn đã sẵn sàng để phỏng vấn thực tế!'
  if (score >= 7.0) return 'Tốt! Câu trả lời khá đầy đủ, chỉ cần rèn luyện thêm độ tự tin.'
  if (score >= 5.0) return 'Khá. Cần bổ sung ví dụ thực tế và cải thiện cấu trúc (STAR).'
  return 'Cần cố gắng nhiều. Hãy đọc kỹ gợi ý mẫu để nâng cấp câu trả lời của mình.'
}

function goHome() {
  router.push('/dashboard')
}

function startNewInterview() {
  router.push('/interview')
}

onMounted(() => {
  loadResults()
})
</script>

<style scoped>
.result-container {
  max-width: 1000px;
  width: 100%;
  margin: 0 auto;
  padding: 40px 24px;
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 40px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-card);
  text-align: center;
  gap: 20px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(14, 165, 233, 0.1);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s infinite linear;
}

.error-icon {
  font-size: 3rem;
}

.error-desc {
  color: var(--text-secondary);
  font-size: 0.95rem;
  margin-bottom: 12px;
}

/* === RESULT LAYOUT === */
.result-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-card);
}

@media (max-width: 768px) {
  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }
}

.result-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  margin: 8px 0;
  color: var(--text-heading);
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* Dashboard Grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 32px;
}

@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

.score-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-card);
  text-align: center;
}

.score-card h3, .criteria-card h3, .feedback-card h3, .bullets-card h3, .qa-section h3 {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-heading);
  margin-bottom: 20px;
  text-align: left;
  width: 100%;
}

.score-card h3 {
  text-align: center;
}

.circular-score-box {
  width: 160px;
  height: 160px;
  position: relative;
  margin-bottom: 20px;
}

.circular-progress {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.bg-ring {
  fill: none;
  stroke: rgba(255, 255, 255, 0.03);
  stroke-width: 8;
}

.fill-ring {
  fill: none;
  stroke: url(#score-grad);
  /* Fallback color if gradient SVG fails */
  stroke: var(--primary);
  stroke-width: 8;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.8s ease-out;
}

.score-inner {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.score-number {
  font-size: 2.8rem;
  font-weight: 800;
  color: var(--text-heading);
}

.score-max {
  font-size: 1.1rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin-left: 2px;
  align-self: flex-end;
  margin-bottom: 16px;
}

.score-comment {
  font-size: 0.9rem;
  color: var(--text-primary);
  font-weight: 500;
  line-height: 1.4;
}

.criteria-card {
  padding: 32px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-card);
}

.criteria-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.criteria-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.criteria-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.criteria-value {
  color: var(--text-secondary);
}

.slider-track {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
}

.slider-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease-out;
}

/* Feedback & Bullets Grid */
.feedback-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

@media (max-width: 768px) {
  .feedback-grid {
    grid-template-columns: 1fr;
  }
}

.feedback-card, .bullets-card {
  padding: 32px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-card);
}

.feedback-text {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--text-body);
  white-space: pre-wrap;
  text-align: left;
}

.bullets-section h3 {
  margin-bottom: 12px;
}

.bullets-list {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  text-align: left;
}

.bullets-list li {
  font-size: 0.9rem;
  line-height: 1.4;
  color: var(--text-body);
}

.divider-top {
  border-top: 1px solid var(--border-color);
  margin-top: 24px;
  padding-top: 24px;
}

/* QA Details Section */
.qa-section {
  padding: 32px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-card);
}

.qa-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 24px;
}

.qa-item {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.01);
  overflow: hidden;
  transition: all var(--transition-fast);
}

.qa-item.open {
  border-color: var(--border-highlight);
  background: rgba(255, 255, 255, 0.02);
}

.qa-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  cursor: pointer;
  user-select: none;
  gap: 16px;
}

.qa-header:hover {
  background: rgba(255, 255, 255, 0.02);
}

.qa-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-grow: 1;
  min-width: 0;
}

.question-number-badge {
  background: var(--bg-score-pill);
  border: 1px solid var(--border-color);
  color: var(--primary-light);
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
}

.qa-header-left h4 {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0;
}

.truncate-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.qa-item.open .truncate-text {
  white-space: normal;
  overflow: visible;
}

.qa-header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.score-badge {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: var(--success);
  font-weight: 700;
  font-size: 0.85rem;
  padding: 4px 10px;
  border-radius: 6px;
}

.chevron {
  font-size: 0.75rem;
  color: var(--text-label);
}

/* Accordion Content */
.qa-content {
  padding: 24px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: rgba(2, 6, 23, 0.4);
}

.qa-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
}

.qa-label {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.user-label { color: var(--accent-2); }
.ai-label { color: var(--primary-light); }
.suggested-label { color: var(--success); }

.qa-bubble {
  padding: 16px;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
}

.user-bubble {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.ai-bubble {
  background: rgba(14, 165, 233, 0.02);
  border: 1px solid var(--border-highlight);
  color: var(--text-body);
}

.eval-text {
  margin-bottom: 16px;
}

.sub-metrics-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  border-top: 1px dashed var(--border-color);
  padding-top: 12px;
}

.sub-metric {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.sub-metric strong {
  color: var(--text-heading);
  font-size: 0.85rem;
}

.suggested-bubble {
  background: rgba(16, 185, 129, 0.02);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: var(--text-body);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
