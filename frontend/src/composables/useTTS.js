import { ref, watch, onUnmounted } from 'vue'

export function useTTS(responseMode, isAudioEnabled, sessionLanguage) {
  const isAiSpeaking = ref(false)
  let googleAudioController = null

  function splitTextIntoChunks(text, maxLen = 150) {
    const chunks = []
    if (!text) return chunks

    const sentences = text.match(/[^.!?]+[.!?]*|.+/g) || [text]

    let currentChunk = ''
    for (const sentence of sentences) {
      if ((currentChunk + sentence).length > maxLen) {
        if (currentChunk.trim()) {
          chunks.push(currentChunk.trim())
          currentChunk = ''
        }
        
        if (sentence.length > maxLen) {
          const words = sentence.split(/\s+/)
          for (const word of words) {
            if ((currentChunk + ' ' + word).length > maxLen) {
              if (currentChunk.trim()) {
                chunks.push(currentChunk.trim())
              }
              currentChunk = word
            } else {
              currentChunk = currentChunk ? currentChunk + ' ' + word : word
            }
          }
        } else {
          currentChunk = sentence
        }
      } else {
        currentChunk = currentChunk ? currentChunk + ' ' + sentence : sentence
      }
    }

    if (currentChunk.trim()) {
      chunks.push(currentChunk.trim())
    }

    return chunks
  }

  function playGoogleTTS(text, langCode, onEnd, onError) {
    const chunks = splitTextIntoChunks(text, 150)
    let currentIdx = 0
    let audio = null
    let isCancelled = false

    const playNext = () => {
      if (isCancelled) return
      if (currentIdx >= chunks.length) {
        if (onEnd) onEnd()
        return
      }

      const chunk = chunks[currentIdx]
      const url = `/api/v1/tts?lang=${langCode}&text=${encodeURIComponent(chunk)}`

      audio = new Audio(url)
      audio.onended = () => {
        currentIdx++
        playNext()
      }
      audio.onerror = (e) => {
        console.error('[Google TTS] Audio playback error:', e)
        if (onError) onError(e)
      }
      
      audio.play().catch(err => {
        console.error('[Google TTS] play() failed:', err)
        if (onError) onError(err)
      })
    }

    playNext()

    return {
      cancel: () => {
        isCancelled = true
        if (audio) {
          audio.pause()
          audio.src = ''
          audio = null
        }
        currentIdx = chunks.length
      }
    }
  }

  function cancelSpeech() {
    if (googleAudioController) {
      googleAudioController.cancel()
      googleAudioController = null
    }
    window.speechSynthesis?.cancel()
    isAiSpeaking.value = false
  }

  function speakQuestion(text, onStartListening) {
    if (responseMode.value !== 'Voice' || !isAudioEnabled.value) {
      return
    }
    
    cancelSpeech()
    isAiSpeaking.value = true

    const lang = (sessionLanguage.value === 'English') ? 'en-US' : 'vi-VN'
    
    const performSpeakNative = () => {
      console.log('[TTS] Falling back to native SpeechSynthesis')
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = lang

      if (window.speechSynthesis) {
        const voices = window.speechSynthesis.getVoices()
        let voice = voices.find(v => {
          const l = v.lang.toLowerCase().replace('_', '-');
          return l === lang.toLowerCase() || l === lang.split('-')[0].toLowerCase();
        })
        
        if (!voice) {
          voice = voices.find(v => v.lang.toLowerCase().startsWith(lang.split('-')[0].toLowerCase()))
        }

        if (voice) {
          utterance.voice = voice
          console.log(`[TTS Native] Using voice: ${voice.name} (${voice.lang})`)
        } else {
          console.warn(`[TTS Native] No suitable voice found for lang: ${lang}.`)
        }
      }

      utterance.onend = () => {
        isAiSpeaking.value = false
        if (responseMode.value === 'Voice' && onStartListening) {
          onStartListening()
        }
      }

      utterance.onerror = (e) => {
        console.error('[TTS Native] Utterance error:', e)
        isAiSpeaking.value = false
      }

      window.speechSynthesis.speak(utterance)
    }

    if (lang === 'vi-VN') {
      console.log('[TTS] Attempting Google Translate TTS for Vietnamese...')
      try {
        googleAudioController = playGoogleTTS(
          text,
          'vi',
          // onEnd
          () => {
            isAiSpeaking.value = false
            googleAudioController = null
            if (responseMode.value === 'Voice' && onStartListening) {
              onStartListening()
            }
          },
          // onError
          (err) => {
            console.warn('[TTS] Google Translate TTS failed, falling back to native TTS:', err)
            googleAudioController = null
            performSpeakNative()
          }
        )
      } catch (e) {
        console.warn('[TTS] Failed to initialize Google Translate TTS, falling back:', e)
        performSpeakNative()
      }
    } else {
      // English logic
      const performSpeak = () => {
        const utterance = new SpeechSynthesisUtterance(text)
        utterance.lang = lang

        if (window.speechSynthesis) {
          const voices = window.speechSynthesis.getVoices()
          let voice = voices.find(v => {
            const l = v.lang.toLowerCase().replace('_', '-');
            return l === lang.toLowerCase() || l === lang.split('-')[0].toLowerCase();
          })
          
          if (!voice) {
            voice = voices.find(v => v.lang.toLowerCase().startsWith(lang.split('-')[0].toLowerCase()))
          }

          if (voice) {
            utterance.voice = voice
          }
        }

        utterance.onend = () => {
          isAiSpeaking.value = false
          if (responseMode.value === 'Voice' && onStartListening) {
            onStartListening()
          }
        }

        utterance.onerror = (e) => {
          console.error('[TTS Native] Utterance error:', e)
          isAiSpeaking.value = false
        }

        window.speechSynthesis.speak(utterance)
      }

      if (window.speechSynthesis && window.speechSynthesis.getVoices().length === 0) {
        const oldOnVoicesChanged = window.speechSynthesis.onvoiceschanged
        window.speechSynthesis.onvoiceschanged = () => {
          if (oldOnVoicesChanged) oldOnVoicesChanged()
          window.speechSynthesis.onvoiceschanged = oldOnVoicesChanged
          performSpeak()
        }
        setTimeout(() => {
          if (isAiSpeaking.value && window.speechSynthesis.speaking === false) {
            performSpeak()
          }
        }, 400)
      } else {
        performSpeak()
      }
    }
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
