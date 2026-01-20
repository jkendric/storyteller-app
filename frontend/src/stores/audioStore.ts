import { create } from 'zustand'

interface AudioState {
  isPlaying: boolean
  currentSentenceIndex: number
  audioQueue: string[]
  volume: number
  playbackRate: number
  currentAudioUrl: string | null

  setIsPlaying: (playing: boolean) => void
  setCurrentSentenceIndex: (index: number) => void
  addToQueue: (sentence: string) => void
  clearQueue: () => void
  setVolume: (volume: number) => void
  setPlaybackRate: (rate: number) => void
  setCurrentAudioUrl: (url: string | null) => void
  nextSentence: () => void
}

export const useAudioStore = create<AudioState>((set) => ({
  isPlaying: false,
  currentSentenceIndex: 0,
  audioQueue: [],
  volume: 1,
  playbackRate: 1,
  currentAudioUrl: null,

  setIsPlaying: (playing) => set({ isPlaying: playing }),

  setCurrentSentenceIndex: (index) => set({ currentSentenceIndex: index }),

  addToQueue: (sentence) =>
    set((state) => ({
      audioQueue: [...state.audioQueue, sentence],
    })),

  clearQueue: () =>
    set({
      audioQueue: [],
      currentSentenceIndex: 0,
      currentAudioUrl: null,
    }),

  setVolume: (volume) => set({ volume }),

  setPlaybackRate: (rate) => set({ playbackRate: rate }),

  setCurrentAudioUrl: (url) => set({ currentAudioUrl: url }),

  nextSentence: () =>
    set((state) => ({
      currentSentenceIndex: state.currentSentenceIndex + 1,
    })),
}))
