import { create } from 'zustand'
import type { Story, Episode } from '../api/client'

interface StoryState {
  currentStory: Story | null
  episodes: Episode[]
  isGenerating: boolean
  streamingContent: string
  streamingSentences: string[]

  setCurrentStory: (story: Story | null) => void
  setEpisodes: (episodes: Episode[]) => void
  setIsGenerating: (generating: boolean) => void
  appendStreamingContent: (content: string) => void
  addStreamingSentence: (sentence: string) => void
  clearStreaming: () => void
  addEpisode: (episode: Episode) => void
  updateEpisode: (number: number, data: Partial<Episode>) => void
}

export const useStoryStore = create<StoryState>((set) => ({
  currentStory: null,
  episodes: [],
  isGenerating: false,
  streamingContent: '',
  streamingSentences: [],

  setCurrentStory: (story) => set({ currentStory: story }),

  setEpisodes: (episodes) => set({ episodes }),

  setIsGenerating: (generating) => set({ isGenerating: generating }),

  appendStreamingContent: (content) =>
    set((state) => ({
      streamingContent: state.streamingContent + content,
    })),

  addStreamingSentence: (sentence) =>
    set((state) => ({
      streamingSentences: [...state.streamingSentences, sentence],
    })),

  clearStreaming: () =>
    set({
      streamingContent: '',
      streamingSentences: [],
    }),

  addEpisode: (episode) =>
    set((state) => ({
      episodes: [...state.episodes, episode],
    })),

  updateEpisode: (number, data) =>
    set((state) => ({
      episodes: state.episodes.map((ep) =>
        ep.number === number ? { ...ep, ...data } : ep
      ),
    })),
}))
