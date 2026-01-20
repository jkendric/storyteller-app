import { useCallback, useRef, useEffect } from 'react'
import { useAudioStore } from '../stores/audioStore'
import { api } from '../api/client'

export function useAudioPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const isProcessingRef = useRef(false)

  const {
    isPlaying,
    currentSentenceIndex,
    audioQueue,
    volume,
    playbackRate,
    setIsPlaying,
    setCurrentAudioUrl,
    nextSentence,
    clearQueue,
  } = useAudioStore()

  // Initialize audio element
  useEffect(() => {
    audioRef.current = new Audio()
    audioRef.current.addEventListener('ended', handleAudioEnded)
    audioRef.current.addEventListener('error', handleAudioError)

    return () => {
      if (audioRef.current) {
        audioRef.current.removeEventListener('ended', handleAudioEnded)
        audioRef.current.removeEventListener('error', handleAudioError)
        audioRef.current.pause()
      }
    }
  }, [])

  // Update volume and playback rate
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume
      audioRef.current.playbackRate = playbackRate
    }
  }, [volume, playbackRate])

  const handleAudioEnded = useCallback(() => {
    nextSentence()
  }, [nextSentence])

  const handleAudioError = useCallback(() => {
    console.error('Audio playback error')
    nextSentence()
  }, [nextSentence])

  // Process queue when index changes or new items added
  useEffect(() => {
    if (!isPlaying || isProcessingRef.current) return
    if (currentSentenceIndex >= audioQueue.length) return

    processNextSentence()
  }, [isPlaying, currentSentenceIndex, audioQueue.length])

  const processNextSentence = useCallback(async () => {
    if (isProcessingRef.current) return
    if (currentSentenceIndex >= audioQueue.length) return

    isProcessingRef.current = true
    const sentence = audioQueue[currentSentenceIndex]

    try {
      const result = await api.generateTTS(sentence)
      setCurrentAudioUrl(result.audio_url)

      if (audioRef.current) {
        audioRef.current.src = result.audio_url
        audioRef.current.volume = volume
        audioRef.current.playbackRate = playbackRate
        await audioRef.current.play()
      }
    } catch (error) {
      console.error('TTS generation failed:', error)
      nextSentence()
    } finally {
      isProcessingRef.current = false
    }
  }, [
    currentSentenceIndex,
    audioQueue,
    volume,
    playbackRate,
    setCurrentAudioUrl,
    nextSentence,
  ])

  const play = useCallback(() => {
    setIsPlaying(true)
    if (audioRef.current && audioRef.current.paused && audioRef.current.src) {
      audioRef.current.play()
    }
  }, [setIsPlaying])

  const pause = useCallback(() => {
    setIsPlaying(false)
    if (audioRef.current) {
      audioRef.current.pause()
    }
  }, [setIsPlaying])

  const stop = useCallback(() => {
    setIsPlaying(false)
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
    }
    clearQueue()
  }, [setIsPlaying, clearQueue])

  return {
    play,
    pause,
    stop,
    isPlaying,
    currentSentenceIndex,
    queueLength: audioQueue.length,
  }
}
