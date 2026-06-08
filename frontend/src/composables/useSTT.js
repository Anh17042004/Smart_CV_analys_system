import { ref, onUnmounted } from 'vue'
import api from '../api'

export function useSTT(userAnswer, responseMode, sessionLanguage, isAiSpeaking) {
  const isListening = ref(false)
  const isTranscribing = ref(false)
  const isWhisperAvailable = ref(false)
  
  // Browser SpeechRecognition fallback
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  let recognition = null
  let preSpeechText = ''
  
  // Whisper MediaRecorder variables
  let mediaRecorder = null
  let audioChunks = []
  let stream = null

  // Check Whisper availability on backend
  async function checkWhisperStatus() {
    try {
      const res = await api.get('/stt/config')
      isWhisperAvailable.value = !!res.data.whisper_available
    } catch (err) {
      console.warn('Failed to fetch STT config, falling back to native SpeechRecognition:', err)
      isWhisperAvailable.value = false
    }
    initNativeSpeech()
  }

  // Initialize native speech recognition for fallback
  function initNativeSpeech() {
    if (SpeechRecognition && !recognition) {
      recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true

      recognition.onresult = (event) => {
        let finalTranscript = ''
        let interimTranscript = ''

        for (let i = 0; i < event.results.length; ++i) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' '
          } else {
            interimTranscript += transcript
          }
        }
        userAnswer.value = (preSpeechText + finalTranscript + interimTranscript).trim()
      }

      recognition.onerror = (event) => {
        console.warn('SpeechRecognition error:', event.error)
        if (event.error !== 'no-speech') {
          isListening.value = false
        }
      }

      recognition.onend = () => {
        isListening.value = false
      }
    }
  }

  // Call status check immediately
  checkWhisperStatus()

  async function startListening() {
    if (isListening.value || (isAiSpeaking && isAiSpeaking.value)) return

    if (isWhisperAvailable.value) {
      // Use MediaRecorder for Whisper STT
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        
        // Find a supported mime type for audio recording
        let options = {}
        if (MediaRecorder.isTypeSupported('audio/webm')) {
          options = { mimeType: 'audio/webm' }
        } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
          options = { mimeType: 'audio/ogg' }
        }
        
        mediaRecorder = new MediaRecorder(stream, options)
        audioChunks = []

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunks.push(event.data)
          }
        }

        mediaRecorder.onstop = async () => {
          const mimeType = mediaRecorder.mimeType || 'audio/webm'
          const audioBlob = new Blob(audioChunks, { type: mimeType })
          
          // Stop all audio tracks to release the microphone
          if (stream) {
            stream.getTracks().forEach(track => track.stop())
          }

          // Upload audio blob to backend
          await uploadAndTranscribe(audioBlob, mimeType)
        }

        isListening.value = true
        mediaRecorder.start()
      } catch (err) {
        console.error('Failed to access microphone for Whisper STT:', err)
        alert('Không thể truy cập microphone. Vui lòng cấp quyền micro cho trang web.')
        isListening.value = false
      }
    } else {
      // Fallback to browser-native SpeechRecognition
      if (!recognition) {
        alert('Nhận dạng giọng nói không được hỗ trợ trên trình duyệt này và Whisper không khả dụng. Vui lòng dùng Chrome hoặc Edge.')
        return
      }
      isListening.value = true
      recognition.lang = (sessionLanguage && sessionLanguage.value === 'English') ? 'en-US' : 'vi-VN'
      preSpeechText = userAnswer.value ? userAnswer.value.trim() + ' ' : ''
      
      try {
        recognition.start()
      } catch (err) {
        console.error('Failed to start SpeechRecognition:', err)
        isListening.value = false
      }
    }
  }

  async function stopListening() {
    if (!isListening.value) return

    if (isWhisperAvailable.value && mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
      isListening.value = false
    } else if (recognition) {
      recognition.stop()
      isListening.value = false
      preSpeechText = ''
    }
  }

  function toggleListening() {
    if (isListening.value) {
      stopListening()
    } else {
      startListening()
    }
  }

  async function uploadAndTranscribe(blob, mimeType) {
    isTranscribing.value = true
    
    // Map mimeType to file extension
    let extension = 'webm'
    if (mimeType.includes('ogg')) {
      extension = 'ogg'
    } else if (mimeType.includes('wav')) {
      extension = 'wav'
    } else if (mimeType.includes('mp4') || mimeType.includes('m4a')) {
      extension = 'm4a'
    }
    
    const file = new File([blob], `speech.${extension}`, { type: mimeType })
    const formData = new FormData()
    formData.append('file', file)
    
    const langParam = (sessionLanguage && sessionLanguage.value === 'English') ? 'English' : 'Vietnamese'
    
    try {
      const res = await api.post(`/stt/transcribe?language=${langParam}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      const text = res.data.text || ''
      if (text.trim()) {
        const space = userAnswer.value ? ' ' : ''
        userAnswer.value = (userAnswer.value + space + text).trim()
      }
    } catch (err) {
      console.error('Transcription error:', err)
      alert('Không thể nhận diện giọng nói từ Whisper: ' + (err.response?.data?.detail || err.message))
    } finally {
      isTranscribing.value = false
    }
  }

  onUnmounted(() => {
    if (isListening.value) {
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop()
      }
      if (recognition) {
        recognition.stop()
      }
    }
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
    }
  })

  return {
    isListening,
    isTranscribing,
    startListening,
    stopListening,
    toggleListening,
    isSupported: !!SpeechRecognition || !!navigator.mediaDevices?.getUserMedia
  }
}
