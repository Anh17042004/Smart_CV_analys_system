import { ref, watch, onUnmounted } from 'vue'

export function useTTS(responseMode, isAudioEnabled, sessionLanguage, ttsVoiceType) {
  const isAiSpeaking = ref(false)
  let activeAudio = null

  function playEdgeTTS(text, voice, onEnd, onError) {
    const apiBaseUrl = import.meta.env.VITE_API_URL || ''
    const url = `${apiBaseUrl}/api/v1/tts?text=${encodeURIComponent(text)}&voice=${voice}`

    const audio = new Audio(url)
    activeAudio = audio

    audio.onended = () => {
      activeAudio = null
      if (onEnd) onEnd()
    }

    audio.onerror = (e) => {
      console.error('[Edge TTS] Audio playback error:', e)
      activeAudio = null
      if (onError) onError(e)
    }

    audio.play().catch(err => {
      console.error('[Edge TTS] play() failed:', err)
      activeAudio = null
      if (onError) onError(err)
    })
  }

  function cancelSpeech() {
    if (activeAudio) {
      activeAudio.pause()
      activeAudio.src = ''
      activeAudio = null
    }
    isAiSpeaking.value = false
  }

  function speakQuestion(text, onStartListening) {
    if (responseMode.value !== 'Voice' || !isAudioEnabled.value) {
      return
    }
    
    cancelSpeech()
    isAiSpeaking.value = true

    // Map voice name based on language and user preference
    const isEnglish = sessionLanguage.value === 'English'
    const voiceMode = (ttsVoiceType && ttsVoiceType.value === 'male') ? 'male' : 'female'
    
    let voice = 'vi-VN-HoaiMyNeural'
    if (isEnglish) {
      voice = (voiceMode === 'male') ? 'en-US-GuyNeural' : 'en-US-AriaNeural'
    } else {
      voice = (voiceMode === 'male') ? 'vi-VN-NamMinhNeural' : 'vi-VN-HoaiMyNeural'
    }

    playEdgeTTS(
      text,
      voice,
      // onEnd
      () => {
        isAiSpeaking.value = false
        if (responseMode.value === 'Voice' && onStartListening) {
          onStartListening()
        }
      },
      // onError
      (err) => {
        console.warn('[TTS] Edge TTS failed:', err)
        isAiSpeaking.value = false
      }
    )
  }

  watch(isAudioEnabled, (newVal) => {
    if (!newVal) {
      cancelSpeech()
    }
  })

  onUnmounted(() => {
    cancelSpeech()
  })

  return {
    isAiSpeaking,
    speakQuestion,
    cancelSpeech
  }
}
