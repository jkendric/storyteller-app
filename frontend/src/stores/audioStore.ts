import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface QueuedSentence {
  text: string
  isNewParagraph: boolean
}

interface AudioState {
  isPlaying: boolean
  currentSentenceIndex: number
  audioQueue: QueuedSentence[]
  queueVersion: number  // Increments when queue is cleared/replaced, used to ignore stale events
  volume: number
  playbackRate: number
  currentAudioUrl: string | null
  paragraphPauseMs: number

  // TTS Provider preferences
  selectedProviderId: number | null
  selectedVoice: string | null
  selectedVoiceCloneId: number | null
  useStreaming: boolean

  setIsPlaying: (playing: boolean) => void
  setCurrentSentenceIndex: (index: number) => void
  addToQueue: (sentence: string, isNewParagraph?: boolean) => void
  queueContent: (content: string) => void
  clearQueue: () => void
  setVolume: (volume: number) => void
  setPlaybackRate: (rate: number) => void
  setCurrentAudioUrl: (url: string | null) => void
  setParagraphPauseMs: (ms: number) => void
  nextSentence: () => void
  getQueueVersion: () => number

  // TTS Provider actions
  setSelectedProviderId: (providerId: number | null) => void
  setSelectedVoice: (voice: string | null) => void
  setSelectedVoiceCloneId: (voiceCloneId: number | null) => void
  setUseStreaming: (useStreaming: boolean) => void
}

export const useAudioStore = create<AudioState>()(
  persist(
    (set, get) => ({
      isPlaying: false,
      currentSentenceIndex: 0,
      audioQueue: [],
      queueVersion: 0,
      volume: 1,
      playbackRate: 1,
      currentAudioUrl: null,
      paragraphPauseMs: 750,

      // TTS Provider preferences (persisted)
      selectedProviderId: null,
      selectedVoice: null,
      selectedVoiceCloneId: null,
      useStreaming: false,

      setIsPlaying: (playing) => set({ isPlaying: playing }),

      setCurrentSentenceIndex: (index) => set({ currentSentenceIndex: index }),

      addToQueue: (sentence, isNewParagraph = false) =>
        set((state) => ({
          audioQueue: [...state.audioQueue, { text: sentence, isNewParagraph }],
        })),

      queueContent: (content) => {
        // Split content into paragraphs first, then sentences
        const paragraphs = content.split(/\n\s*\n/).filter((p) => p.trim().length > 0)

        const queuedSentences: QueuedSentence[] = []

        paragraphs.forEach((paragraph, pIndex) => {
          // Split paragraph into sentences
          const sentences = paragraph
            .split(/(?<=[.!?])\s+/)
            .map((s) => s.trim())
            .filter((s) => s.length > 0)

          sentences.forEach((sentence, sIndex) => {
            queuedSentences.push({
              text: sentence,
              // First sentence of a paragraph (except the very first) is a new paragraph
              isNewParagraph: pIndex > 0 && sIndex === 0,
            })
          })
        })

        console.log('[TTS] Queuing content:', {
          numSentences: queuedSentences.length,
          firstSentence: queuedSentences[0]?.text.substring(0, 50) + '...',
          secondSentence: queuedSentences[1]?.text.substring(0, 50) + '...',
          thirdSentence: queuedSentences[2]?.text.substring(0, 50) + '...',
        })

        set((state) => ({
          audioQueue: queuedSentences,
          currentSentenceIndex: 0,
          currentAudioUrl: null,
          queueVersion: state.queueVersion + 1,
        }))
      },

      clearQueue: () =>
        set((state) => ({
          audioQueue: [],
          currentSentenceIndex: 0,
          currentAudioUrl: null,
          queueVersion: state.queueVersion + 1,
        })),

      getQueueVersion: () => get().queueVersion,

      setVolume: (volume) => set({ volume }),

      setPlaybackRate: (rate) => set({ playbackRate: rate }),

      setCurrentAudioUrl: (url) => set({ currentAudioUrl: url }),

      setParagraphPauseMs: (ms) => set({ paragraphPauseMs: ms }),

      nextSentence: () =>
        set((state) => ({
          currentSentenceIndex: state.currentSentenceIndex + 1,
        })),

      // TTS Provider actions
      setSelectedProviderId: (providerId) => set({ selectedProviderId: providerId }),

      setSelectedVoice: (voice) => set({ selectedVoice: voice }),

      setSelectedVoiceCloneId: (voiceCloneId) => set({ selectedVoiceCloneId: voiceCloneId }),

      setUseStreaming: (useStreaming) => set({ useStreaming }),
    }),
    {
      name: 'audio-store',
      partialize: (state) => ({
        volume: state.volume,
        playbackRate: state.playbackRate,
        paragraphPauseMs: state.paragraphPauseMs,
        selectedProviderId: state.selectedProviderId,
        selectedVoice: state.selectedVoice,
        selectedVoiceCloneId: state.selectedVoiceCloneId,
        useStreaming: state.useStreaming,
      }),
    }
  )
)
