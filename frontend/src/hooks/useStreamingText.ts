import { useCallback, useRef } from 'react'
import { useStoryStore } from '../stores/storyStore'
import { useAudioStore } from '../stores/audioStore'

interface StreamingOptions {
  storyId: number
  guidance?: string
  targetWords?: number
  useAlternate?: boolean
  onComplete?: (episodeId: number, title: string, wordCount: number) => void
  onError?: (error: string) => void
}

export function useStreamingText() {
  const abortControllerRef = useRef<AbortController | null>(null)

  const {
    setIsGenerating,
    appendStreamingContent,
    addStreamingSentence,
    clearStreaming,
  } = useStoryStore()

  const { addToQueue } = useAudioStore()

  const startGeneration = useCallback(
    async (options: StreamingOptions) => {
      const { storyId, guidance, targetWords, useAlternate, onComplete, onError } = options

      // Abort any existing generation
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }

      abortControllerRef.current = new AbortController()
      clearStreaming()
      setIsGenerating(true)

      try {
        const response = await fetch(
          `/api/stories/${storyId}/episodes/generate`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              guidance,
              target_words: targetWords,
              use_alternate: useAlternate ?? false,
            }),
            signal: abortControllerRef.current.signal,
          }
        )

        if (!response.ok) {
          throw new Error(`Generation failed: ${response.status}`)
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error('No response body')
        }

        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('event:')) {
              continue
            }
            if (line.startsWith('data:')) {
              const data = line.slice(5).trim()
              if (!data) continue

              // Parse the event from the previous line
              const eventMatch = lines.find((l) =>
                l.startsWith('event:')
              )
              const eventType = eventMatch
                ? eventMatch.slice(6).trim()
                : 'message'

              handleEvent(eventType, data, onComplete, onError)
            }
          }
        }
      } catch (error) {
        if ((error as Error).name === 'AbortError') {
          return
        }
        onError?.((error as Error).message)
      } finally {
        setIsGenerating(false)
      }
    },
    [
      clearStreaming,
      setIsGenerating,
      appendStreamingContent,
      addStreamingSentence,
      addToQueue,
    ]
  )

  const handleEvent = useCallback(
    (
      eventType: string,
      data: string,
      onComplete?: (episodeId: number, title: string, wordCount: number) => void,
      onError?: (error: string) => void
    ) => {
      switch (eventType) {
        case 'token':
          appendStreamingContent(data)
          break
        case 'sentence':
          addStreamingSentence(data)
          addToQueue(data)
          break
        case 'complete':
          try {
            const result = JSON.parse(data)
            onComplete?.(result.episode_id, result.title, result.word_count)
          } catch {
            // Data might be just the episode ID
          }
          break
        case 'error':
          onError?.(data)
          break
      }
    },
    [appendStreamingContent, addStreamingSentence, addToQueue]
  )

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    setIsGenerating(false)
  }, [setIsGenerating])

  return {
    startGeneration,
    stopGeneration,
  }
}
