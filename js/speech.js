// speech.js - Text-to-Speech wrapper with Hebrew support
// Supports: Native Web Speech API (Android/some desktops) + Google TTS fallback (Windows)
// Features: speakSequence() for reading name + fun fact with pauses

const Speech = {
  _voice: null,
  _ready: false,
  _useFallback: false,
  _initPromise: null,
  _fallbackAudio: null,
  _sequenceTimeouts: [],
  _isSpeaking: false,

  init() {
    if (this._initPromise) return this._initPromise;

    this._initPromise = new Promise((resolve) => {
      if (!window.speechSynthesis) {
        // No Web Speech API at all - try fallback
        this._useFallback = true;
        this._ready = true;
        resolve(true);
        return;
      }

      const findVoice = () => {
        const voices = speechSynthesis.getVoices();
        // Handle both he-IL and he_IL (Android quirk)
        this._voice = voices.find(v => /he[-_]IL/i.test(v.lang))
                   || voices.find(v => /^he/i.test(v.lang));
        if (this._voice) {
          this._ready = true;
          this._useFallback = false;
          resolve(true);
          return true;
        }
        return false;
      };

      // Try immediately
      if (findVoice()) return;

      // Listen for voiceschanged event
      const onVoicesChanged = () => {
        if (findVoice()) {
          speechSynthesis.removeEventListener('voiceschanged', onVoicesChanged);
        }
      };
      speechSynthesis.addEventListener('voiceschanged', onVoicesChanged);

      // Poll as fallback (Android may not fire voiceschanged reliably)
      let attempts = 0;
      const interval = setInterval(() => {
        attempts++;
        if (findVoice() || attempts > 15) {
          clearInterval(interval);
          speechSynthesis.removeEventListener('voiceschanged', onVoicesChanged);
          if (!this._ready) {
            // No native Hebrew voice found - use Google TTS fallback
            this._useFallback = true;
            this._ready = true;
            resolve(true);
          }
        }
      }, 200);
    });

    return this._initPromise;
  },

  speak(text) {
    if (!this._ready || !text) return;

    // Stop any ongoing sequence
    this._clearSequence();

    if (this._useFallback) {
      this._speakFallback(text);
    } else {
      this._speakNative(text);
    }
  },

  /**
   * Speak an array of text segments with pauses between them.
   * Example: speakSequence(['מכונית רגילה', 'מכונית רגילה היא הכי נפוצה!'], 1000)
   */
  speakSequence(segments, pauseMs) {
    if (!this._ready || !segments || segments.length === 0) return;
    pauseMs = pauseMs || 800;

    // Stop anything playing
    this.stop();

    if (this._useFallback) {
      this._speakFallbackSequence(segments, pauseMs);
    } else {
      this._speakNativeSequence(segments, pauseMs);
    }
  },

  _speakNative(text) {
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = this._voice;
    utterance.lang = 'he-IL';
    utterance.rate = 0.75;
    utterance.pitch = 1.05;
    speechSynthesis.speak(utterance);
  },

  _speakNativeSequence(segments, pauseMs) {
    this._isSpeaking = true;
    let index = 0;

    const speakNext = () => {
      if (!this._isSpeaking || index >= segments.length) {
        this._isSpeaking = false;
        return;
      }

      const text = segments[index];
      index++;

      if (!text) {
        // Skip empty segments
        speakNext();
        return;
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.voice = this._voice;
      utterance.lang = 'he-IL';
      utterance.rate = 0.75;
      utterance.pitch = 1.05;

      utterance.onend = () => {
        if (index < segments.length && this._isSpeaking) {
          // Pause before next segment
          const tid = setTimeout(speakNext, pauseMs);
          this._sequenceTimeouts.push(tid);
        } else {
          this._isSpeaking = false;
        }
      };

      utterance.onerror = () => {
        // Try next segment on error
        if (this._isSpeaking) {
          const tid = setTimeout(speakNext, pauseMs);
          this._sequenceTimeouts.push(tid);
        }
      };

      speechSynthesis.speak(utterance);
    };

    speakNext();
  },

  _speakFallback(text) {
    // Use Google Translate TTS as audio fallback
    // This requires internet but works on Windows without Hebrew TTS installed
    this._stopFallbackAudio();
    try {
      // Chunk long text for Google TTS URL limit
      const chunks = this._chunkText(text, 180);
      if (chunks.length === 1) {
        this._playFallbackChunk(chunks[0]);
      } else {
        // Play chunks sequentially
        this._speakFallbackSequence(chunks, 300);
      }
    } catch (e) {
      // Silently fail
    }
  },

  _speakFallbackSequence(segments, pauseMs) {
    this._isSpeaking = true;
    let index = 0;

    const playNext = () => {
      if (!this._isSpeaking || index >= segments.length) {
        this._isSpeaking = false;
        return;
      }

      const text = segments[index];
      index++;

      if (!text) {
        playNext();
        return;
      }

      // Chunk this segment if it's long
      const chunks = this._chunkText(text, 180);
      let chunkIndex = 0;

      const playChunk = () => {
        if (!this._isSpeaking || chunkIndex >= chunks.length) {
          // Move to next segment after pause
          if (index < segments.length && this._isSpeaking) {
            const tid = setTimeout(playNext, pauseMs);
            this._sequenceTimeouts.push(tid);
          } else {
            this._isSpeaking = false;
          }
          return;
        }

        this._playFallbackChunk(chunks[chunkIndex], () => {
          chunkIndex++;
          if (chunkIndex < chunks.length) {
            const tid = setTimeout(playChunk, 200);
            this._sequenceTimeouts.push(tid);
          } else {
            playChunk(); // Will trigger next segment logic
          }
        });
      };

      playChunk();
    };

    playNext();
  },

  _playFallbackChunk(text, onEnd) {
    try {
      const encoded = encodeURIComponent(text);
      const url = 'https://translate.google.com/translate_tts?ie=UTF-8&tl=iw&client=tw-ob&q=' + encoded;
      this._fallbackAudio = new Audio(url);
      this._fallbackAudio.playbackRate = 0.75;

      if (onEnd) {
        this._fallbackAudio.addEventListener('ended', onEnd, { once: true });
        this._fallbackAudio.addEventListener('error', onEnd, { once: true });
      }

      this._fallbackAudio.play().catch(() => {
        if (onEnd) onEnd();
      });
    } catch (e) {
      if (onEnd) onEnd();
    }
  },

  /**
   * Split long text at word boundaries for Google TTS URL length limit.
   * Returns array of chunks, each under maxLen characters when URL-encoded.
   */
  _chunkText(text, maxLen) {
    const encoded = encodeURIComponent(text);
    if (encoded.length <= maxLen) {
      return [text];
    }

    // Split at spaces
    const words = text.split(' ');
    const chunks = [];
    let current = '';

    for (let i = 0; i < words.length; i++) {
      const candidate = current ? current + ' ' + words[i] : words[i];
      if (encodeURIComponent(candidate).length > maxLen && current) {
        chunks.push(current);
        current = words[i];
      } else {
        current = candidate;
      }
    }
    if (current) {
      chunks.push(current);
    }

    return chunks;
  },

  _clearSequence() {
    this._isSpeaking = false;
    this._sequenceTimeouts.forEach(tid => clearTimeout(tid));
    this._sequenceTimeouts = [];
  },

  _stopFallbackAudio() {
    if (this._fallbackAudio) {
      this._fallbackAudio.pause();
      this._fallbackAudio.currentTime = 0;
      this._fallbackAudio = null;
    }
  },

  isAvailable() {
    return this._ready;
  },

  isFallback() {
    return this._useFallback;
  },

  stop() {
    // Clear any sequence in progress
    this._clearSequence();

    if (window.speechSynthesis) {
      speechSynthesis.cancel();
    }
    this._stopFallbackAudio();
  }
};
