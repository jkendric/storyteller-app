import { createContext, useContext, useRef, useEffect, useCallback, useState, type ReactNode } from 'react'
import { useAudioStore } from '../stores/audioStore'
import { api, type TTSProvider } from '../api/client'

// Default prefetch depth (used when provider settings don't specify one)
const DEFAULT_PREFETCH_DEPTH = 3

interface AudioPlayerContextValue {
  isPlaying: boolean
  currentSentenceIndex: number
  queueLength: number
  play: () => void
  pause: () => void
  stop: () => void
}

const AudioPlayerContext = createContext<AudioPlayerContextValue | null>(null)

export function useAudioPlayerContext(): AudioPlayerContextValue {
  const context = useContext(AudioPlayerContext)
  if (!context) {
    throw new Error('useAudioPlayerContext must be used within AudioPlayerProvider')
  }
  return context
}

interface AudioPlayerProviderProps {
  children: ReactNode
}

export function AudioPlayerProvider({ children }: AudioPlayerProviderProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const isProcessingRef = useRef(false)

  // Prefetch buffer for smooth playback
  const prefetchCacheRef = useRef<Map<number, string>>(new Map())  // index → audio_url
  const prefetchingRef = useRef<Set<number>>(new Set())  // indices currently being fetched

  // Track queue version to ignore stale audio events after queue changes
  const playingQueueVersionRef = useRef<number>(0)

  // Track provider to detect changes and clear cache
  const lastProviderIdRef = useRef<number | null>(null)

  // Current provider settings (fetched from API)
  const [providerSettings, setProviderSettings] = useState<TTSProvider['provider_settings'] | null>(null)

  const {
    isPlaying,
    currentSentenceIndex,
    audioQueue,
    volume,
    playbackRate,
    paragraphPauseMs,
    setIsPlaying,
    setCurrentAudioUrl,
    nextSentence,
    clearQueue,
    getQueueVersion,
    selectedProviderId,
    selectedVoice,
    selectedVoiceCloneId,
  } = useAudioStore()

  // Refs for event handlers to avoid stale closures
  const nextSentenceRef = useRef(nextSentence)
  nextSentenceRef.current = nextSentence
  const getQueueVersionRef = useRef(getQueueVersion)
  getQueueVersionRef.current = getQueueVersion

  // Fetch provider settings when provider changes
  useEffect(() => {
    // If provider changed, clear prefetch cache
    if (lastProviderIdRef.current !== selectedProviderId) {
      console.log('[TTS] Provider changed, clearing prefetch cache', {
        old: lastProviderIdRef.current,
        new: selectedProviderId,
      })
      prefetchCacheRef.current.clear()
      prefetchingRef.current.clear()
      lastProviderIdRef.current = selectedProviderId
    }

    // Fetch provider settings
    if (selectedProviderId) {
      api.getTTSProvider(selectedProviderId)
        .then((provider) => {
          setProviderSettings(provider.provider_settings || null)
          console.log('[TTS] Loaded provider settings', provider.provider_settings)
        })
        .catch((error) => {
          console.warn('[TTS] Failed to fetch provider settings:', error)
          setProviderSettings(null)
        })
    } else {
      setProviderSettings(null)
    }
  }, [selectedProviderId])

  // Get prefetch depth from provider settings or use default
  const prefetchDepth = (providerSettings?.prefetch_depth as number) || DEFAULT_PREFETCH_DEPTH

  // Initialize audio element once
  useEffect(() => {
    const audio = new Audio()
    audioRef.current = audio

    const handleEnded = () => {
      console.log('[TTS] Audio ended', {
        playingVersion: playingQueueVersionRef.current,
        currentVersion: getQueueVersionRef.current(),
      })
      isProcessingRef.current = false
      // Only advance to next sentence if queue version hasn't changed
      // This prevents stale events from affecting a new queue after chapter switch
      if (playingQueueVersionRef.current === getQueueVersionRef.current()) {
        console.log('[TTS] Advancing to next sentence')
        nextSentenceRef.current()
      } else {
        console.log('[TTS] Queue version mismatch, not advancing')
      }
    }

    const handleError = (e: Event) => {
      // Ignore errors when source is empty (happens when stop() clears the audio)
      if (!audio.src || audio.src === '' || audio.src === window.location.href) {
        console.log('[TTS] Ignoring error for empty audio source')
        return
      }

      console.error('[TTS] Audio playback error', e)
      isProcessingRef.current = false
      // Only advance to next sentence if queue version hasn't changed
      if (playingQueueVersionRef.current === getQueueVersionRef.current()) {
        console.log('[TTS] Advancing after error')
        nextSentenceRef.current()
      } else {
        console.log('[TTS] Queue version mismatch after error, not advancing')
      }
    }

    audio.addEventListener('ended', handleEnded)
    audio.addEventListener('error', handleError)

    return () => {
      audio.removeEventListener('ended', handleEnded)
      audio.removeEventListener('error', handleError)
      audio.pause()
      audio.src = ''
      abortControllerRef.current?.abort()
    }
  }, [])

  // Update volume and playback rate
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume
      audioRef.current.playbackRate = playbackRate
    }
  }, [volume, playbackRate])

  // Prefetch the next sentence while current one is playing
  const prefetchNext = useCallback(async (index: number, forQueueVersion: number) => {
    // Guard: don't prefetch if already cached, already fetching, or out of bounds
    if (prefetchCacheRef.current.has(index)) return
    if (prefetchingRef.current.has(index)) return
    if (index >= audioQueue.length) return

    prefetchingRef.current.add(index)

    try {
      const result = await api.generateTTS(
        audioQueue[index].text,
        selectedVoice || undefined,
        selectedProviderId || undefined,
        selectedVoiceCloneId || undefined
      )
      // Only cache if queue version hasn't changed
      if (getQueueVersion() === forQueueVersion) {
        prefetchCacheRef.current.set(index, result.audio_url)
      }
    } catch (error) {
      // Silently fail - will generate on-demand when needed
      console.debug('Prefetch failed for sentence', index, error)
    } finally {
      prefetchingRef.current.delete(index)
    }
  }, [audioQueue, getQueueVersion, selectedVoice, selectedProviderId, selectedVoiceCloneId])

  const processNextSentence = useCallback(async () => {
    console.log('[TTS] processNextSentence called', {
      isProcessing: isProcessingRef.current,
      currentSentenceIndex,
      queueLength: audioQueue.length,
      queueVersion: getQueueVersion(),
    })

    if (isProcessingRef.current) {
      console.log('[TTS] Already processing, skipping')
      return
    }
    if (currentSentenceIndex >= audioQueue.length) {
      console.log('[TTS] No more sentences, stopping')
      setIsPlaying(false)
      return
    }

    isProcessingRef.current = true

    // Capture current queue version so we can detect if queue changes during async operations
    const startingQueueVersion = getQueueVersion()
    playingQueueVersionRef.current = startingQueueVersion

    const queuedSentence = audioQueue[currentSentenceIndex]
    console.log('[TTS] Processing sentence', currentSentenceIndex, ':', queuedSentence.text.substring(0, 50) + '...')

    // Add pause before new paragraphs
    if (queuedSentence.isNewParagraph && paragraphPauseMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, paragraphPauseMs))

      // Check if queue changed during the pause - if so, abort this processing
      if (getQueueVersion() !== startingQueueVersion) {
        isProcessingRef.current = false
        return
      }
    }

    // Check prefetch cache first
    const cachedUrl = prefetchCacheRef.current.get(currentSentenceIndex)

    let audioUrl: string

    if (cachedUrl) {
      // Use cached audio URL
      audioUrl = cachedUrl
      prefetchCacheRef.current.delete(currentSentenceIndex)
    } else {
      // Generate if not cached
      // Create new abort controller for this request
      abortControllerRef.current?.abort()
      abortControllerRef.current = new AbortController()

      try {
        const result = await api.generateTTS(
          queuedSentence.text,
          selectedVoice || undefined,
          selectedProviderId || undefined,
          selectedVoiceCloneId || undefined,
          abortControllerRef.current.signal
        )
        audioUrl = result.audio_url
      } catch (error) {
        // Ignore abort errors
        if (error instanceof Error && error.name === 'AbortError') {
          isProcessingRef.current = false
          return
        }
        console.error('TTS generation failed:', error)
        isProcessingRef.current = false
        // Only advance if queue hasn't changed
        if (getQueueVersion() === startingQueueVersion) {
          nextSentence()
        }
        return
      }
    }

    // Check if queue changed during TTS generation - if so, abort
    if (getQueueVersion() !== startingQueueVersion) {
      isProcessingRef.current = false
      return
    }

    setCurrentAudioUrl(audioUrl)

    if (audioRef.current) {
      audioRef.current.src = audioUrl
      audioRef.current.volume = volume
      audioRef.current.playbackRate = playbackRate

      try {
        await audioRef.current.play()
      } catch (error) {
        // Play can fail if audio was stopped/cleared during the await
        isProcessingRef.current = false
        return
      }

      // Prefetch multiple sentences ahead for smoother playback
      if (getQueueVersion() === startingQueueVersion) {
        for (let i = 1; i <= prefetchDepth; i++) {
          prefetchNext(currentSentenceIndex + i, startingQueueVersion)
        }
      }
    }
  }, [
    currentSentenceIndex,
    audioQueue,
    volume,
    playbackRate,
    paragraphPauseMs,
    setCurrentAudioUrl,
    setIsPlaying,
    nextSentence,
    prefetchNext,
    getQueueVersion,
    prefetchDepth,
    selectedVoice,
    selectedProviderId,
    selectedVoiceCloneId,
  ])

  // Process queue when playing and index changes or new items added
  useEffect(() => {
    if (!isPlaying) {
      return
    }
    if (isProcessingRef.current) {
      return
    }
    if (currentSentenceIndex >= audioQueue.length) {
      return
    }

    processNextSentence()
  }, [isPlaying, currentSentenceIndex, audioQueue.length, processNextSentence])

  const play = useCallback(() => {
    console.log('[TTS] play() called')
    setIsPlaying(true)
    if (audioRef.current && audioRef.current.paused && audioRef.current.src) {
      audioRef.current.play()
    }
  }, [setIsPlaying])

  const pause = useCallback(() => {
    console.log('[TTS] pause() called')
    setIsPlaying(false)
    if (audioRef.current) {
      audioRef.current.pause()
    }
  }, [setIsPlaying])

  const stop = useCallback(() => {
    console.log('[TTS] stop() called')
    // Abort any pending TTS request
    abortControllerRef.current?.abort()
    abortControllerRef.current = null
    isProcessingRef.current = false

    // Clear prefetch cache
    prefetchCacheRef.current.clear()
    prefetchingRef.current.clear()

    setIsPlaying(false)
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      audioRef.current.src = ''
    }
    clearQueue()
  }, [setIsPlaying, clearQueue])

  const value: AudioPlayerContextValue = {
    isPlaying,
    currentSentenceIndex,
    queueLength: audioQueue.length,
    play,
    pause,
    stop,
  }

  return (
    <AudioPlayerContext.Provider value={value}>
      {children}
    </AudioPlayerContext.Provider>
  )
}
