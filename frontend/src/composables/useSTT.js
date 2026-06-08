import { ref, onUnmounted } from 'vue'

export function useSTT(userAnswer, responseMode, sessionLanguage, isAiSpeaking) {
  const isListening = ref(false)
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  let recognition = null
  let preSpeechText = ''

  if (SpeechRecognition) {
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

  function startListening() {
    if (!recognition) {
      alert('Nhận dạng giọng nói (SpeechRecognition) không được trình duyệt này hỗ trợ. Vui lòng sử dụng Google Chrome hoặc Edge.')
      return
    }
    if (isListening.value || (isAiSpeaking && isAiSpeaking.value)) return

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

  function stopListening() {
    if (recognition && isListening.value) {
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

  onUnmounted(() => {
    stopListening()
  })

  return {
    isListening,
    startListening,
    stopListening,
    toggleListening,
    isSupported: !!SpeechRecognition
  }
}
