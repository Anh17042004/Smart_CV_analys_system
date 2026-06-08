<template>
  <main class="interview-container">
    <!-- Setup Room (Before interview starts) -->
    <section v-if="!isInProgress && !isSessionCreated" class="setup-section glass-card">
      <div class="setup-header">
        <span class="tag-badge">{{ t('mockInterview.tag') }}</span>
        <h1>{{ t('mockInterview.title') }}</h1>
        <p class="subtitle-text">{{ t('mockInterview.desc') }}</p>
      </div>

      <div class="setup-grid">
        <!-- Scenario Selector -->
        <div class="setup-card">
          <label class="form-label">{{ t('mockInterview.scenario') }}</label>
          <div class="scenario-options">
            <button 
              type="button" 
              class="scenario-btn" 
              :class="{ active: scenario === 'general' }"
              @click="setScenario('general')"
            >
              <span class="icon">💼</span>
              <div>
                <h4>{{ t('mockInterview.general') }}</h4>
                <p>Phỏng vấn dựa trên lĩnh vực và cấp bậc</p>
              </div>
            </button>
            <button 
              type="button" 
              class="scenario-btn" 
              :class="{ active: scenario === 'cvBased' }"
              @click="setScenario('cvBased')"
            >
              <span class="icon">📄</span>
              <div>
                <h4>{{ t('mockInterview.cvBased') }}</h4>
                <p>AI phỏng vấn trực tiếp dựa trên CV của bạn</p>
              </div>
            </button>
            <button 
              type="button" 
              class="scenario-btn" 
              :class="{ active: scenario === 'jdBased' }"
              @click="setScenario('jdBased')"
            >
              <span class="icon">🎯</span>
              <div>
                <h4>{{ t('mockInterview.jdBased') }}</h4>
                <p>Phỏng vấn khớp CV với yêu cầu công việc cụ thể</p>
              </div>
            </button>
          </div>
        </div>

        <!-- Customizations -->
        <div class="setup-card">
          <h3 class="card-subtitle">{{ t('mockInterview.setupRoom') }}</h3>
          
          <div class="form-group-row">
            <!-- Field -->
            <div class="form-group">
              <label class="form-label">{{ t('mockInterview.field') }}</label>
              <input 
                type="text" 
                v-model="field" 
                class="form-input" 
                placeholder="VD: Software Engineering, Marketing..." 
              />
            </div>
            
            <!-- Level -->
            <div class="form-group">
              <label class="form-label">{{ t('mockInterview.level') }}</label>
              <input 
                type="text" 
                v-model="level" 
                class="form-input" 
                list="level-suggestions" 
                placeholder="VD: Intern, Junior, Senior..." 
              />
              <datalist id="level-suggestions">
                <option value="Intern">Intern</option>
                <option value="Fresher">Fresher</option>
                <option value="Junior">Junior</option>
                <option value="Middle">Middle</option>
                <option value="Senior">Senior</option>
                <option value="Lead/Manager">Lead / Manager</option>
              </datalist>
            </div>
          </div>

          <div class="form-group-row">
            <!-- Interview Type -->
            <div class="form-group">
              <label class="form-label">{{ t('mockInterview.interviewType') }}</label>
              <input 
                type="text" 
                v-model="interviewType" 
                class="form-input" 
                list="type-suggestions" 
                placeholder="VD: Technical, HR, English..." 
              />
              <datalist id="type-suggestions">
                <option value="Technical">Technical (Kỹ thuật)</option>
                <option value="HR">HR (Hành vi/Văn hóa)</option>
                <option value="English">English (Tiếng Anh chuyên môn)</option>
              </datalist>
            </div>

            <!-- Interview Language -->
            <div class="form-group">
              <label class="form-label">Ngôn ngữ phỏng vấn</label>
              <select v-model="language" class="form-select">
                <option value="Vietnamese">Tiếng Việt</option>
                <option value="English">Tiếng Anh</option>
              </select>
            </div>
          </div>

          <div class="form-group-row">
            <!-- Response Mode -->
            <div class="form-group">
              <label class="form-label">{{ t('mockInterview.responseMode') }}</label>
              <select v-model="responseMode" class="form-select">
                <option value="Text">{{ t('mockInterview.textMode') }}</option>
                <option value="Voice">{{ t('mockInterview.voiceMode') }}</option>
              </select>
            </div>

            <!-- Total Questions -->
            <div class="form-group">
              <label class="form-label">{{ t('mockInterview.totalQuestions') }}</label>
              <div class="question-count-selector">
                <button 
                  v-for="num in [3, 5, 8, 10]" 
                  :key="num"
                  type="button"
                  class="count-btn"
                  :class="{ active: totalQuestions === num }"
                  @click="totalQuestions = num"
                >
                  {{ num }}
                </button>
              </div>
            </div>
          </div>

          <!-- Context CV selector -->
          <div v-if="scenario === 'cvBased' || scenario === 'jdBased'" class="form-group">
            <label class="form-label">{{ t('mockInterview.selectCV') }}</label>
            <div class="cv-selection-modes">
              <!-- Mode selector buttons -->
              <div class="cv-mode-tabs">
                <button 
                  type="button" 
                  class="tab-btn" 
                  :class="{ active: cvSourceMode === 'history' }"
                  @click="cvSourceMode = 'history'"
                >
                  Chọn từ lịch sử
                </button>
                <button 
                  type="button" 
                  class="tab-btn" 
                  :class="{ active: cvSourceMode === 'upload' }"
                  @click="cvSourceMode = 'upload'"
                >
                  Tải lên file CV mới
                </button>
              </div>

              <!-- History Select Mode -->
              <div v-if="cvSourceMode === 'history'" class="mode-content">
                <select v-model="selectedCvId" class="form-select">
                  <option :value="null">-- {{ t('jobRec.chooseCv') }} --</option>
                  <option v-for="cv in cvHistory" :key="cv.id" :value="cv.cv_id">
                    CV #{{ cv.cv_id }} - {{ cv.target_role || 'Vai trò không xác định' }} ({{ formatDate(cv.created_at) }})
                  </option>
                </select>
                <p v-if="cvHistory.length === 0" class="input-helper-text">
                  Chưa có CV trong lịch sử. Bạn có thể chọn tab "Tải lên file CV mới".
                </p>
              </div>

              <!-- Direct Upload Mode -->
              <div v-else class="mode-content">
                <div 
                  class="quick-upload-zone"
                  :class="{ dragover: cvDragOver, uploaded: selectedCvId }"
                  @dragover.prevent="cvDragOver = true"
                  @dragleave.prevent="cvDragOver = false"
                  @drop.prevent="handleCvDrop"
                  @click="triggerCvFileInput"
                >
                  <input 
                    type="file" 
                    ref="cvFileInput" 
                    class="hidden-file-input" 
                    accept=".pdf,.docx" 
                    @change="handleCvFileChange"
                  />
                  <div class="upload-zone-content">
                    <span class="upload-icon">{{ isUploadingCv ? '⏳' : selectedCvId ? '✅' : '📤' }}</span>
                    <p class="upload-text">
                      {{ isUploadingCv ? 'Đang tải CV...' : selectedCvId ? `Đã nạp CV: ${uploadedCvFilename}` : 'Kéo thả file CV (.pdf, .docx) hoặc click để tải lên' }}
                    </p>
                    <p class="upload-subtext" v-if="!isUploadingCv && !selectedCvId">Trích xuất nội dung nhanh trong 1 giây để phỏng vấn ngay</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Context JD selector -->
          <div v-if="scenario === 'jdBased'" class="form-group">
            <label class="form-label">{{ t('mockInterview.selectJD') }}</label>
            <select v-model="selectedJdId" class="form-select">
              <option :value="null">-- {{ t('mockInterview.pasteJD') }} --</option>
              <option v-for="job in savedJobs" :key="job.id" :value="job.jd.id">
                {{ job.jd.company }} - {{ job.jd.title }}
              </option>
            </select>
            
            <div v-if="!selectedJdId" class="custom-jd-box">
              <div class="jd-header-row">
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
              <textarea 
                v-model="customJd" 
                class="form-textarea" 
                rows="4" 
                placeholder="Dán mô tả công việc (JD) mục tiêu tại đây..."
              ></textarea>
              <p v-if="jdFileName" class="jd-file-badge">
                <span class="badge-icon">📄</span>
                <span class="badge-text">{{ t('cvAnalysis.jdUploadedText') }} <strong>{{ jdFileName }}</strong></span>
                <button type="button" class="btn-clear-jd" @click="clearJdFile" title="Clear JD">✕</button>
              </p>
            </div>
          </div>

          <!-- Start Button -->
          <button 
            @click="startInterview" 
            class="btn-primary btn-start" 
            :disabled="isStarting || ( (scenario === 'cvBased' || scenario === 'jdBased') && !selectedCvId )"
          >
            <span v-if="isStarting">⏳ Starting...</span>
            <span v-else>{{ t('mockInterview.startInterview') }}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Interview Room (Simulator) -->
    <section v-else class="room-section">
      <div class="room-grid">
        <!-- AI Interviewer Avatar Card -->
        <div class="room-avatar-card glass-card">
          <div class="avatar-container">
            <div class="avatar-glow" :class="{ speaking: isAiSpeaking, recording: isListening, transcribing: isTranscribing }"></div>
            <div class="avatar-ring">
              <div class="avatar-visualizer">
                <!-- Soundwave Animation -->
                <div class="soundwave" :class="{ active: isAiSpeaking || isListening }">
                  <span v-for="i in 15" :key="i" class="bar"></span>
                </div>
                <!-- Status Icons -->
                <div class="status-overlay">
                  <span v-if="isAiSpeaking" class="status-emoji animate-pulse">🤖</span>
                  <span v-else-if="isListening" class="status-emoji animate-pulse">🎙️</span>
                  <span v-else-if="isTranscribing" class="status-emoji animate-pulse">⏳</span>
                  <span v-else class="status-emoji">🧑‍💼</span>
                </div>
              </div>
            </div>
          </div>

          <div class="avatar-info">
            <h3>AI Recruiter</h3>
            <p v-if="isAiSpeaking" class="status-text text-accent">{{ t('mockInterview.aiSpeaking') }}</p>
            <p v-else-if="isListening" class="status-text text-success">{{ t('mockInterview.micStatusActive') }}</p>
            <p v-else-if="isTranscribing" class="status-text text-warning">{{ t('mockInterview.micStatusTranscribing') }}</p>
            <p v-else class="status-text">{{ t('mockInterview.micStatusWaiting') }}</p>
          </div>

          <!-- Controls -->
          <div class="audio-controls">
            <button 
              class="audio-btn" 
              :class="{ disabled: !isAudioEnabled }"
              @click="isAudioEnabled = !isAudioEnabled"
              :title="isAudioEnabled ? 'Mute AI Audio' : 'Unmute AI Audio'"
            >
              <span v-if="isAudioEnabled">🔊</span>
              <span v-else>🔇</span>
            </button>
            <button class="audio-btn" @click="replayQuestion" title="Replay Question">
              🔄
            </button>
          </div>
        </div>

        <!-- Conversational Dialogue Room -->
        <div class="room-chat-card glass-card">
          <div class="chat-header">
            <div>
              <h3>Phòng Phỏng Vấn Ảo</h3>
              <p class="meta-desc">{{ field }} • {{ level }} • {{ interviewType }}</p>
            </div>
            <!-- Progress -->
            <div class="progress-box">
              <span class="progress-text">Câu {{ currentQuestionNumber }} / {{ totalQuestions }}</span>
              <div class="progress-bar-container">
                <div class="progress-bar-fill" :style="{ width: `${(currentQuestionNumber / totalQuestions) * 100}%` }"></div>
              </div>
            </div>
          </div>

          <!-- Message History -->
          <div class="chat-history" ref="chatHistoryEl">
            <div v-for="(msg, index) in chatHistory" :key="index" class="chat-message-row" :class="msg.role">
              <div class="chat-bubble">
                <p class="bubble-sender">{{ msg.role === 'ai' ? 'AI Interviewer' : 'Candidate' }}</p>
                <p class="bubble-text">{{ msg.text }}</p>
              </div>
            </div>

            <!-- AI Thinking indicator -->
            <div v-if="isAiThinking" class="chat-message-row ai">
              <div class="chat-bubble thinking-bubble">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
            </div>
          </div>

          <!-- User input area -->
          <div class="chat-input-bar">
            <!-- Text input mode -->
            <textarea 
              v-model="userAnswer" 
              class="chat-textarea" 
              :placeholder="isTranscribing ? 'AI đang nhận dạng giọng nói (Whisper)...' : isListening ? 'Giọng nói đang được ghi âm... Nhấn Mic lần nữa để hoàn thành.' : 'Nhập câu trả lời của bạn ở đây...'"
              @keydown.enter.prevent="submitTypedAnswer"
              :disabled="isAiSpeaking || isAiThinking || isTranscribing"
            ></textarea>
            
            <div class="chat-input-actions">
              <!-- Mic button for voice recognition -->
              <button 
                v-if="responseMode === 'Voice'"
                class="btn-mic" 
                :class="{ active: isListening, transcribing: isTranscribing }"
                @click="toggleListening"
                :disabled="isAiSpeaking || isAiThinking || isTranscribing"
                title="Ghi âm bằng giọng nói"
              >
                <span v-if="isTranscribing" class="small-spinner"></span>
                <span v-else>🎙️</span>
              </button>

              <button 
                @click="submitAnswer" 
                class="btn-primary btn-send"
                :disabled="!userAnswer.trim() || isAiSpeaking || isAiThinking || isTranscribing"
              >
                <span>{{ t('mockInterview.submitAnswer') }} ➔</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Global Loading Overlay -->
    <div v-if="isAiThinking" class="loading-overlay">
      <div class="loading-spinner-box glass-card">
        <div class="spinner"></div>
        <p class="loading-text">{{ loadingMessage }}</p>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { useTTS } from '../composables/useTTS'
import { useSTT } from '../composables/useSTT'

const { t } = useI18n()
const router = useRouter()

// Setup configurations
const isInProgress = ref(false)
const isSessionCreated = ref(false)
const isStarting = ref(false)
const scenario = ref('general')
const field = ref('AI Engineer')
const level = ref('Intern')
const interviewType = ref('Technical')
const responseMode = ref('Text')
const language = ref('Vietnamese')
const sessionLanguage = ref('Vietnamese')
const totalQuestions = ref(5)
const isAudioEnabled = ref(true)

// Context files lists
const cvHistory = ref([])
const savedJobs = ref([])
const selectedCvId = ref(null)
const selectedJdId = ref(null)
const customJd = ref('')

// Direct upload states
const cvSourceMode = ref('history')
const cvDragOver = ref(false)
const cvFileInput = ref(null)
const isUploadingCv = ref(false)
const uploadedCvFilename = ref('')

// Active interview state
const sessionId = ref(null)
const currentQuestionNumber = ref(1)
const currentQuestionText = ref('')
const userAnswer = ref('')
const chatHistory = ref([])
const isAiThinking = ref(false)
const loadingMessage = ref('Đang tạo phòng phỏng vấn...')
const chatHistoryEl = ref(null)
const jdFileInput = ref(null)
const jdExtracting = ref(false)
const jdFileName = ref('')

const { isAiSpeaking, speakQuestion, cancelSpeech } = useTTS(responseMode, isAudioEnabled, sessionLanguage)
const { isListening, isTranscribing, startListening, stopListening, toggleListening } = useSTT(userAnswer, responseMode, sessionLanguage, isAiSpeaking)

watch(interviewType, (newVal) => {
  if (newVal && newVal.toLowerCase().includes('english')) {
    language.value = 'English'
  } else {
    language.value = 'Vietnamese'
  }
})

// Formatter
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

function setScenario(val) {
  scenario.value = val
}

// Fetch CV analysis and Saved Jobs list for setup dropdowns
async function loadSetupData() {
  try {
    const [cvRes, jobsRes] = await Promise.all([
      api.get('/cv/history'),
      api.get('/jobs/saved')
    ])
    cvHistory.value = cvRes.data
    savedJobs.value = jobsRes.data
    
    // Auto select first CV if available
    if (cvHistory.value.length > 0) {
      selectedCvId.value = cvHistory.value[0].cv_id
    }
  } catch (err) {
    console.error('Failed to load setup dropdown resources:', err)
  }
}

function triggerCvFileInput() {
  if (cvFileInput.value) {
    cvFileInput.value.click()
  }
}

function handleCvFileChange(e) {
  const file = e.target.files[0]
  if (file) {
    uploadCvDirectly(file)
  }
}

function handleCvDrop(e) {
  cvDragOver.value = false
  const file = e.dataTransfer.files[0]
  if (file) {
    uploadCvDirectly(file)
  }
}

async function uploadCvDirectly(file) {
  if (isUploadingCv.value) return
  
  isUploadingCv.value = true
  selectedCvId.value = null
  uploadedCvFilename.value = ''
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await api.post('/cv/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    // cv_id is returned inside res.data.id
    selectedCvId.value = res.data.id
    uploadedCvFilename.value = file.name
  } catch (err) {
    alert('Không thể tải lên và trích xuất CV: ' + (err.response?.data?.detail || err.message))
  } finally {
    isUploadingCv.value = false
  }
}

// Start simulation
async function startInterview() {
  if (isStarting.value) return
  isStarting.value = true
  isAiThinking.value = true
  loadingMessage.value = 'Đang thiết lập phòng phỏng vấn và nạp AI Interviewer...'

  try {
    const payload = {
      field: field.value,
      level: level.value,
      interview_type: interviewType.value,
      response_mode: responseMode.value,
      language: language.value,
      total_questions: totalQuestions.value,
      cv_id: (scenario.value !== 'general') ? selectedCvId.value : null,
      jd_id: (scenario.value === 'jdBased') ? selectedJdId.value : null,
      custom_jd: (scenario.value === 'jdBased' && !selectedJdId.value) ? customJd.value : null
    }

    sessionLanguage.value = language.value

    const res = await api.post('/interview/start', payload)
    
    sessionId.value = res.data.session_id
    const q1 = res.data.first_question
    
    currentQuestionNumber.value = q1.question_number
    currentQuestionText.value = q1.question_text
    
    // Set active status
    isInProgress.value = true
    isSessionCreated.value = true
    
    // Append to chat history
    chatHistory.value.push({
      role: 'ai',
      text: q1.question_text
    })

    // Play voice output for Q1
    await nextTick()
    speakQuestion(q1.question_text, startListening)
    scrollToBottom()

  } catch (err) {
    alert('Không thể bắt đầu phỏng vấn: ' + (err.response?.data?.detail || err.message))
  } finally {
    isStarting.value = false
    isAiThinking.value = false
  }
}

// Submit typed answers
function submitTypedAnswer() {
  if (userAnswer.value.trim() && !isAiSpeaking.value && !isAiThinking.value) {
    submitAnswer()
  }
}

// Submit answer to current question
async function submitAnswer() {
  if (!userAnswer.value.trim() || isAiThinking.value) return
  
  stopListening()
  const answerToSubmit = userAnswer.value
  
  // Add to chat history
  chatHistory.value.push({
    role: 'user',
    text: answerToSubmit
  })
  userAnswer.value = ''
  
  isAiThinking.value = true
  if (currentQuestionNumber.value === totalQuestions.value) {
    loadingMessage.value = 'Đã hoàn thành các câu hỏi. AI đang tổng hợp và đánh giá toàn bộ buổi phỏng vấn (có thể mất 15-20 giây)...'
  } else {
    loadingMessage.value = 'AI đang chuẩn bị câu hỏi tiếp theo...'
  }

  
  await nextTick()
  scrollToBottom()

  try {
    const payload = {
      session_id: sessionId.value,
      question_number: currentQuestionNumber.value,
      answer_text: answerToSubmit
    }

    const res = await api.post('/interview/answer', payload)
    
    const evaluation = res.data.evaluation
    const nextQ = res.data.next_question
    const isCompleted = res.data.is_completed
    
    if (isCompleted) {
      loadingMessage.value = 'Đang tổng hợp nhận xét và tính điểm tổng quan...'
      // Delay slightly for nice UX
      setTimeout(() => {
        isAiThinking.value = false
        router.push(`/interview/result/${sessionId.value}`)
      }, 1500)
    } else if (nextQ) {
      currentQuestionNumber.value = nextQ.question_number
      currentQuestionText.value = nextQ.question_text
      
      // Append to chat history
      chatHistory.value.push({
        role: 'ai',
        text: nextQ.question_text
      })
      
      isAiThinking.value = false
      await nextTick()
      speakQuestion(nextQ.question_text, startListening)
      scrollToBottom()
    }
  } catch (err) {
    alert('Lỗi gửi câu trả lời: ' + (err.response?.data?.detail || err.message))
    isAiThinking.value = false
  }
}

function replayQuestion() {
  speakQuestion(currentQuestionText.value, startListening)
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
  try {
    const formData = new FormData()
    formData.append('file', selected)
    const res = await api.post('/cv/extract-text', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    customJd.value = res.data.text
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
  customJd.value = ''
  jdFileName.value = ''
  if (jdFileInput.value) {
    jdFileInput.value.value = ''
  }
}

function scrollToBottom() {
  if (chatHistoryEl.value) {
    chatHistoryEl.value.scrollTop = chatHistoryEl.value.scrollHeight
  }
}

// Load resources on mount
onMounted(() => {
  loadSetupData()
  
  // Trigger speech synthesis voices list initialization (Chrome async behavior)
  if (window.speechSynthesis) {
    window.speechSynthesis.getVoices()
    window.speechSynthesis.onvoiceschanged = () => {
      window.speechSynthesis.getVoices()
    }
  }
})
</script>

<style scoped>
.interview-container {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 40px 24px;
}

/* === SETUP VIEW === */
.setup-section {
  padding: 40px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-card);
  background-color: var(--bg-glass);
  box-shadow: var(--shadow-modal);
}

.setup-header {
  text-align: center;
  margin-bottom: 40px;
}

.setup-header h1 {
  font-size: 2.2rem;
  font-weight: 700;
  margin: 16px 0 8px;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.setup-grid {
  display: grid;
  grid-template-columns: 1.1fr 1.3fr;
  gap: 32px;
  align-items: start;
}

@media (max-width: 900px) {
  .setup-grid {
    grid-template-columns: 1fr;
  }
}

.setup-card {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 32px;
  border-radius: var(--radius-lg);
  background: var(--bg-card-inner);
  border: 1px solid var(--border-color);
}

.card-subtitle {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-heading);
  margin-bottom: 8px;
  border-left: 4px solid var(--primary);
  padding-left: 12px;
}

.scenario-options {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.scenario-btn {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 18px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.scenario-btn:hover {
  background: var(--bg-hover-subtle);
  border-color: var(--btn-outline-hover-border);
}

.scenario-btn.active {
  background: rgba(14, 165, 233, 0.08);
  border-color: var(--primary);
  box-shadow: 0 0 16px rgba(14, 165, 233, 0.15);
}

.scenario-btn .icon {
  font-size: 2rem;
}

.scenario-btn h4 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: var(--text-heading);
}

.scenario-btn p {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.3;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Quick CV Upload Styles */
.cv-selection-modes {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cv-mode-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  gap: 8px;
}

.tab-btn {
  padding: 10px 16px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}

.mode-content {
  margin-top: 4px;
}

.quick-upload-zone {
  border: 2px dashed var(--border-dashed);
  border-radius: var(--radius-md);
  padding: 24px;
  text-align: center;
  background: rgba(255, 255, 255, 0.01);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-upload-zone:hover {
  border-color: var(--primary);
  background: rgba(14, 165, 233, 0.02);
}

.quick-upload-zone.dragover {
  border-color: var(--primary);
  background: rgba(14, 165, 233, 0.05);
}

.quick-upload-zone.uploaded {
  border-color: var(--success);
  background: rgba(16, 185, 129, 0.03);
}

.hidden-file-input {
  display: none;
}

.upload-zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  font-size: 2.2rem;
  margin-bottom: 4px;
}

.upload-text {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.upload-subtext {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.form-group-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-input, .form-select, .form-textarea {
  background-color: var(--input-bg);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  transition: all var(--transition-fast);
}

.form-select option {
  background-color: var(--bg-dropdown);
  color: var(--text-primary);
}

.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 8px rgba(14, 165, 233, 0.2);
}

.question-count-selector {
  display: flex;
  gap: 12px;
}

.count-btn {
  flex: 1;
  padding: 12px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  cursor: pointer;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.count-btn:hover {
  background: var(--bg-hover-subtle);
}

.count-btn.active {
  background: var(--primary);
  color: var(--text-on-primary);
  border-color: var(--primary);
  box-shadow: var(--shadow-glow);
}

.custom-jd-box {
  margin-top: 12px;
}

.btn-start {
  width: 100%;
  padding: 16px;
  font-size: 1.05rem;
  font-weight: 700;
  border-radius: var(--radius-md);
  margin-top: 12px;
  cursor: pointer;
}

.input-helper-text {
  font-size: 0.75rem;
  margin-top: 4px;
}

.input-helper-text a {
  color: var(--primary-light);
  text-decoration: underline;
}

.error-text {
  color: var(--error);
}

/* === INTERVIEW ROOM VIEW === */
.room-section {
  width: 100%;
}

.room-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 32px;
  height: 640px;
}

@media (max-width: 900px) {
  .room-grid {
    grid-template-columns: 1fr;
    height: auto;
  }
}

/* Room Avatar Card */
.room-avatar-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-card);
  text-align: center;
  position: relative;
}

.avatar-container {
  width: 150px;
  height: 150px;
  position: relative;
  margin-bottom: 24px;
}

.avatar-glow {
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--accent) 0%, transparent 70%);
  opacity: 0.2;
  transition: all 0.3s ease;
}

.avatar-glow.speaking {
  animation: pulse-avatar 1.5s infinite alternate;
  background: radial-gradient(circle, var(--primary) 0%, transparent 70%);
  opacity: 0.4;
}

.avatar-glow.recording {
  animation: pulse-avatar 1.2s infinite alternate;
  background: radial-gradient(circle, var(--success) 0%, transparent 70%);
  opacity: 0.45;
}

.avatar-glow.transcribing {
  animation: pulse-avatar 1.5s infinite alternate;
  background: radial-gradient(circle, #eab308 0%, transparent 70%);
  opacity: 0.45;
}

.avatar-ring {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 3px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card-inner);
  box-shadow: inset 0 0 20px rgba(255, 255, 255, 0.05);
}

.avatar-visualizer {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-overlay {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: rgba(13, 17, 23, 0.8);
  border: 1px solid var(--border-color);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 10;
}

.status-emoji {
  font-size: 1.5rem;
}

.avatar-info h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 6px 0;
  color: var(--text-heading);
}

.status-text {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.4;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.audio-controls {
  display: flex;
  gap: 16px;
  margin-top: 24px;
}

.audio-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1.1rem;
  transition: all var(--transition-fast);
}

.audio-btn:hover {
  background: var(--bg-hover-subtle);
  border-color: var(--primary);
  transform: scale(1.05);
}

.audio-btn.disabled {
  background: rgba(239, 68, 68, 0.05);
  border-color: var(--error);
  color: #ef4444;
}

/* Soundwave CSS pulse animation */
.soundwave {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  height: 60px;
  width: 100%;
}

.soundwave .bar {
  display: block;
  width: 3px;
  height: 4px;
  background-color: var(--border-color);
  border-radius: 2px;
  transition: all 0.2s ease;
}

.soundwave.active .bar {
  background-color: var(--primary);
  animation: soundwave-pulse 1.2s infinite ease-in-out;
}

.soundwave.active .bar:nth-child(even) {
  background-color: var(--accent);
  animation-duration: 0.9s;
}

/* Set dynamic animation delays and durations */
.soundwave.active .bar:nth-child(1)  { animation-delay: 0.1s; height: 15px; }
.soundwave.active .bar:nth-child(2)  { animation-delay: 0.4s; height: 25px; }
.soundwave.active .bar:nth-child(3)  { animation-delay: 0.2s; height: 35px; }
.soundwave.active .bar:nth-child(4)  { animation-delay: 0.6s; height: 45px; }
.soundwave.active .bar:nth-child(5)  { animation-delay: 0.3s; height: 30px; }
.soundwave.active .bar:nth-child(6)  { animation-delay: 0.7s; height: 20px; }
.soundwave.active .bar:nth-child(7)  { animation-delay: 0.1s; height: 10px; }
.soundwave.active .bar:nth-child(8)  { animation-delay: 0.5s; height: 40px; }
.soundwave.active .bar:nth-child(9)  { animation-delay: 0.3s; height: 50px; }
.soundwave.active .bar:nth-child(10) { animation-delay: 0.8s; height: 35px; }
.soundwave.active .bar:nth-child(11) { animation-delay: 0.2s; height: 20px; }
.soundwave.active .bar:nth-child(12) { animation-delay: 0.6s; height: 15px; }
.soundwave.active .bar:nth-child(13) { animation-delay: 0.4s; height: 30px; }
.soundwave.active .bar:nth-child(14) { animation-delay: 0.9s; height: 45px; }
.soundwave.active .bar:nth-child(15) { animation-delay: 0.1s; height: 20px; }

/* Dialogue Room */
.room-chat-card {
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-card);
  overflow: hidden;
  height: 100%;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.01);
}

.chat-header h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 2px 0;
  color: var(--text-heading);
}

.meta-desc {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.progress-box {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  width: 140px;
}

.progress-text {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary-light);
}

.progress-bar-container {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: 3px;
  transition: width 0.4s ease;
}

/* Chat History */
.chat-history {
  flex-grow: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  scroll-behavior: smooth;
  background: radial-gradient(circle at top right, rgba(99, 102, 241, 0.03), transparent 40%),
              radial-gradient(circle at bottom left, rgba(14, 165, 233, 0.03), transparent 40%);
}

.chat-message-row {
  display: flex;
  width: 100%;
}

.chat-message-row.ai {
  justify-content: flex-start;
}

.chat-message-row.user {
  justify-content: flex-end;
}

.chat-bubble {
  max-width: 75%;
  padding: 16px;
  border-radius: var(--radius-lg);
  position: relative;
  text-align: left;
}

.chat-message-row.ai .chat-bubble {
  background: var(--bg-card-inner);
  border: 1px solid var(--border-color);
  border-bottom-left-radius: 2px;
  color: var(--text-primary);
}

.chat-message-row.user .chat-bubble {
  background: rgba(14, 165, 233, 0.1);
  border: 1px solid var(--border-highlight);
  border-bottom-right-radius: 2px;
  color: var(--text-primary);
}

.bubble-sender {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
}

.chat-message-row.ai .bubble-sender {
  color: var(--primary-light);
}

.chat-message-row.user .bubble-sender {
  color: var(--accent-2);
}

.bubble-text {
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
}

/* Typing Thinking Indicator Bubble */
.thinking-bubble {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 16px 20px;
}

.thinking-bubble .dot {
  width: 8px;
  height: 8px;
  background-color: var(--text-secondary);
  border-radius: 50%;
  animation: thinking-dots 1.4s infinite ease-in-out;
}

.thinking-bubble .dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-bubble .dot:nth-child(3) { animation-delay: 0.4s; }

/* Input bar */
.chat-input-bar {
  display: flex;
  flex-direction: column;
  padding: 20px 24px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-card-inner);
  gap: 12px;
}

.chat-textarea {
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  padding: 12px 16px;
  font-size: 0.9rem;
  resize: none;
  height: 64px;
  font-family: inherit;
  transition: all var(--transition-fast);
}

.chat-textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: inset 0 0 8px rgba(14, 165, 233, 0.1);
}

.chat-input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.btn-mic {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1.15rem;
  transition: all var(--transition-fast);
}

.btn-mic:hover {
  background: var(--bg-hover-subtle);
  border-color: var(--success);
}

.btn-mic.active {
  background: rgba(16, 185, 129, 0.15);
  border-color: var(--success);
  color: var(--success);
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.3);
  animation: soundwave-pulse 1s infinite alternate;
}

.btn-mic.transcribing {
  background: rgba(234, 179, 8, 0.15);
  border-color: #eab308;
  color: #eab308;
  box-shadow: 0 0 12px rgba(234, 179, 8, 0.3);
}

.small-spinner {
  display: inline-block;
  width: 18px;
  height: 18px;
  border: 2px solid rgba(234, 179, 8, 0.2);
  border-top-color: #eab308;
  border-radius: 50%;
  animation: spin 0.8s infinite linear;
}

.btn-send {
  padding: 10px 24px;
  font-weight: 600;
  font-size: 0.85rem;
  border-radius: var(--radius-md);
  cursor: pointer;
}

/* === LOADING OVERLAY === */
.loading-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(2, 6, 23, 0.8);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.loading-spinner-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  max-width: 400px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-card);
  text-align: center;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(14, 165, 233, 0.1);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s infinite linear;
  margin-bottom: 24px;
}

.loading-text {
  font-size: 0.95rem;
  color: var(--text-primary);
  font-weight: 500;
}

/* === KEYFRAME ANIMATIONS === */
@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse-avatar {
  to { transform: scale(1.15); opacity: 0.55; }
}

@keyframes soundwave-pulse {
  0% { transform: scaleY(1); }
  50% { transform: scaleY(2.2); }
  100% { transform: scaleY(0.7); }
}

@keyframes thinking-dots {
  0%, 100% { transform: scale(0.6); opacity: 0.4; }
  50% { transform: scale(1.2); opacity: 1; }
}

.animate-pulse {
  animation: pulse-light 1.5s infinite alternate;
}

@keyframes pulse-light {
  to { opacity: 0.6; }
}

.jd-header-row {
  display: flex;
  justify-content: flex-end;
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
