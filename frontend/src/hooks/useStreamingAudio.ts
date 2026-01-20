import { useState, useRef, useCallback } from 'react'
import { api } from '../api/client'

interface UseStreamingAudioOptions {
  onStart?: () => void
  onEnd?: () => void
  onError?: (error: Error) => void
}

interface UseStreamingAudioReturn {
  isStreaming: boolean
  isPlaying: boolean
  error: string | null
  startStreaming: (
    text: string,
    voice?: string,
    providerId?: number,
    voiceCloneId?: number
  ) => Promise<void>
  stopStreaming: () => void
  pause: () => void
  resume: () => void
}

export function useStreamingAudio(options: UseStreamingAudioOptions = {}): UseStreamingAudioReturn {
  const { onStart, onEnd, onError } = options

  const [isStreaming, setIsStreaming] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const audioContextRef = useRef<AudioContext | null>(null)
  const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const audioQueueRef = useRef<ArrayBuffer[]>([])
  const isPlayingQueueRef = useRef(false)

  const getAudioContext = useCallback(() => {
    if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
      audioContextRef.current = new AudioContext()
    }
    return audioContextRef.current
  }, [])

  const playAudioQueue = useCallback(async () => {
    if (isPlayingQueueRef.current) return

    const audioContext = getAudioContext()
    isPlayingQueueRef.current = true

    while (audioQueueRef.current.length > 0) {
      const chunk = audioQueueRef.current.shift()
      if (!chunk) continue

      try {
        // Decode the audio chunk
        const audioBuffer = await audioContext.decodeAudioData(chunk.slice(0))

        // Create a source node for this chunk
        const source = audioContext.createBufferSource()
        source.buffer = audioBuffer
        source.connect(audioContext.destination)
        sourceNodeRef.current = source

        // Play this chunk and wait for it to finish
        await new Promise<void>((resolve) => {
          source.onended = () => resolve()
          source.start(0)
        })
      } catch (err) {
        console.error('Error playing audio chunk:', err)
        // Continue with next chunk
      }
    }

    isPlayingQueueRef.current = false
    setIsPlaying(false)
    onEnd?.()
  }, [getAudioContext, onEnd])

  const startStreaming = useCallback(
    async (
      text: string,
      voice?: string,
      providerId?: number,
      voiceCloneId?: number
    ) => {
      // Reset state
      setError(null)
      setIsStreaming(true)
      setIsPlaying(true)
      audioQueueRef.current = []

      // Create abort controller for cancellation
      abortControllerRef.current = new AbortController()

      onStart?.()

      try {
        const response = await api.streamTTS(text, voice, providerId, voiceCloneId)

        if (!response.body) {
          throw new Error('No response body for streaming')
        }

        const reader = response.body.getReader()

        // Accumulate chunks for MP3 decoding
        const chunks: Uint8Array[] = []

        while (true) {
          const { done, value } = await reader.read()

          if (abortControllerRef.current?.signal.aborted) {
            reader.cancel()
            break
          }

          if (done) {
            break
          }

          if (value) {
            chunks.push(value)
          }
        }

        // Combine all chunks
        const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0)
        const combinedBuffer = new Uint8Array(totalLength)
        let offset = 0
        for (const chunk of chunks) {
          combinedBuffer.set(chunk, offset)
          offset += chunk.length
        }

        // Queue the complete audio for playback
        audioQueueRef.current.push(combinedBuffer.buffer)
        setIsStreaming(false)

        // Start playing the queue
        await playAudioQueue()
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Streaming failed'
        setError(errorMessage)
        onError?.(err instanceof Error ? err : new Error(errorMessage))
        setIsStreaming(false)
        setIsPlaying(false)
      }
    },
    [onStart, onError, playAudioQueue]
  )

  const stopStreaming = useCallback(() => {
    // Abort any ongoing fetch
    abortControllerRef.current?.abort()

    // Stop current audio
    if (sourceNodeRef.current) {
      try {
        sourceNodeRef.current.stop()
      } catch {
        // Source may have already stopped
      }
      sourceNodeRef.current = null
    }

    // Clear the queue
    audioQueueRef.current = []
    isPlayingQueueRef.current = false

    setIsStreaming(false)
    setIsPlaying(false)
  }, [])

  const pause = useCallback(() => {
    const audioContext = audioContextRef.current
    if (audioContext && audioContext.state === 'running') {
      audioContext.suspend()
      setIsPlaying(false)
    }
  }, [])

  const resume = useCallback(() => {
    const audioContext = audioContextRef.current
    if (audioContext && audioContext.state === 'suspended') {
      audioContext.resume()
      setIsPlaying(true)
    }
  }, [])

  return {
    isStreaming,
    isPlaying,
    error,
    startStreaming,
    stopStreaming,
    pause,
    resume,
  }
}

export default useStreamingAudio
