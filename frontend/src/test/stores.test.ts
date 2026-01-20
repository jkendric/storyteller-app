import { describe, it, expect, beforeEach } from 'vitest'
import { useStoryStore } from '../stores/storyStore'
import { useAudioStore } from '../stores/audioStore'

describe('storyStore', () => {
  beforeEach(() => {
    useStoryStore.setState({
      currentStory: null,
      episodes: [],
      isGenerating: false,
      streamingContent: '',
      streamingSentences: [],
    })
  })

  it('sets current story', () => {
    const story = {
      id: 1,
      title: 'Test Story',
      scenario_id: 1,
      status: 'draft' as const,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      episode_count: 0,
      characters: [],
    }

    useStoryStore.getState().setCurrentStory(story)
    expect(useStoryStore.getState().currentStory).toEqual(story)
  })

  it('sets episodes', () => {
    const episodes = [
      {
        id: 1,
        story_id: 1,
        number: 1,
        title: 'Episode 1',
        content: 'Content',
        word_count: 100,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]

    useStoryStore.getState().setEpisodes(episodes)
    expect(useStoryStore.getState().episodes).toEqual(episodes)
  })

  it('appends streaming content', () => {
    useStoryStore.getState().appendStreamingContent('Hello ')
    useStoryStore.getState().appendStreamingContent('World')
    expect(useStoryStore.getState().streamingContent).toBe('Hello World')
  })

  it('adds streaming sentences', () => {
    useStoryStore.getState().addStreamingSentence('First sentence.')
    useStoryStore.getState().addStreamingSentence('Second sentence.')
    expect(useStoryStore.getState().streamingSentences).toEqual([
      'First sentence.',
      'Second sentence.',
    ])
  })

  it('clears streaming', () => {
    useStoryStore.getState().appendStreamingContent('Content')
    useStoryStore.getState().addStreamingSentence('Sentence')
    useStoryStore.getState().clearStreaming()
    expect(useStoryStore.getState().streamingContent).toBe('')
    expect(useStoryStore.getState().streamingSentences).toEqual([])
  })
})

describe('audioStore', () => {
  beforeEach(() => {
    useAudioStore.setState({
      isPlaying: false,
      currentSentenceIndex: 0,
      audioQueue: [],
      volume: 1,
      playbackRate: 1,
      currentAudioUrl: null,
    })
  })

  it('sets volume', () => {
    useAudioStore.getState().setVolume(0.5)
    expect(useAudioStore.getState().volume).toBe(0.5)
  })

  it('sets playback rate', () => {
    useAudioStore.getState().setPlaybackRate(1.5)
    expect(useAudioStore.getState().playbackRate).toBe(1.5)
  })

  it('adds to queue', () => {
    useAudioStore.getState().addToQueue('First')
    useAudioStore.getState().addToQueue('Second')
    expect(useAudioStore.getState().audioQueue).toEqual(['First', 'Second'])
  })

  it('clears queue', () => {
    useAudioStore.getState().addToQueue('Item')
    useAudioStore.getState().setCurrentSentenceIndex(5)
    useAudioStore.getState().clearQueue()
    expect(useAudioStore.getState().audioQueue).toEqual([])
    expect(useAudioStore.getState().currentSentenceIndex).toBe(0)
  })

  it('advances to next sentence', () => {
    useAudioStore.getState().nextSentence()
    expect(useAudioStore.getState().currentSentenceIndex).toBe(1)
    useAudioStore.getState().nextSentence()
    expect(useAudioStore.getState().currentSentenceIndex).toBe(2)
  })
})
