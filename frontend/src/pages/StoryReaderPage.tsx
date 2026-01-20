import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { api } from '../api/client'
import { useStoryStore } from '../stores/storyStore'
import { useStreamingText } from '../hooks/useStreamingText'
import EpisodeReader from '../components/reader/EpisodeReader'
import GenerationControls from '../components/reader/GenerationControls'
import AudioPlayer from '../components/audio/AudioPlayer'

export default function StoryReaderPage() {
  const { storyId } = useParams<{ storyId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const id = parseInt(storyId || '0', 10)

  const {
    episodes,
    isGenerating,
    streamingContent,
    setCurrentStory,
    setEpisodes,
    clearStreaming,
  } = useStoryStore()

  const { startGeneration, stopGeneration } = useStreamingText()

  const { data: story, isLoading: storyLoading } = useQuery({
    queryKey: ['story', id],
    queryFn: () => api.getStory(id),
    enabled: !!id,
  })

  const { data: episodesData, isLoading: episodesLoading } = useQuery({
    queryKey: ['episodes', id],
    queryFn: () => api.getEpisodes(id),
    enabled: !!id,
  })

  // Sync story and episodes to store
  useEffect(() => {
    if (story) {
      setCurrentStory(story)
    }
  }, [story, setCurrentStory])

  useEffect(() => {
    if (episodesData) {
      setEpisodes(episodesData.episodes)
    }
  }, [episodesData, setEpisodes])

  // Clear streaming on unmount
  useEffect(() => {
    return () => {
      clearStreaming()
    }
  }, [clearStreaming])

  const handleGenerate = (guidance?: string, useAlternate?: boolean) => {
    startGeneration({
      storyId: id,
      guidance,
      useAlternate,
      onComplete: () => {
        queryClient.invalidateQueries({ queryKey: ['episodes', id] })
        queryClient.invalidateQueries({ queryKey: ['story', id] })
      },
      onError: (error) => {
        console.error('Generation error:', error)
      },
    })
  }

  const handleFork = async (fromEpisode: number, newTitle: string) => {
    try {
      const forkedStory = await api.forkStory(id, fromEpisode, newTitle)
      navigate(`/stories/${forkedStory.id}`)
    } catch (error) {
      console.error('Fork error:', error)
    }
  }

  if (storyLoading || episodesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
      </div>
    )
  }

  if (!story) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">Story not found</p>
        <button onClick={() => navigate('/stories')} className="btn btn-primary mt-4">
          Back to Stories
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/stories')}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white">{story.title}</h1>
            <p className="text-gray-400">
              {episodes.length} episode{episodes.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content - Reader */}
        <div className="lg:col-span-2">
          <EpisodeReader
            episodes={episodes}
            streamingContent={streamingContent}
            isGenerating={isGenerating}
          />
        </div>

        {/* Sidebar - Controls */}
        <div className="space-y-6">
          <GenerationControls
            isGenerating={isGenerating}
            episodeCount={episodes.length}
            onGenerate={handleGenerate}
            onStop={stopGeneration}
            onFork={handleFork}
          />

          <AudioPlayer />

          {/* Story info */}
          <div className="card">
            <h3 className="text-lg font-semibold text-white mb-3">Story Info</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Status</span>
                <span className="text-white capitalize">
                  {story.status.replace('_', ' ')}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Episodes</span>
                <span className="text-white">{episodes.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Total Words</span>
                <span className="text-white">
                  {episodes.reduce((sum, ep) => sum + ep.word_count, 0).toLocaleString()}
                </span>
              </div>
            </div>

            {story.characters.length > 0 && (
              <>
                <hr className="border-gray-700 my-3" />
                <h4 className="text-sm font-medium text-gray-300 mb-2">Characters</h4>
                <div className="flex flex-wrap gap-1">
                  {story.characters.map((char) => (
                    <span
                      key={char.id}
                      className="px-2 py-0.5 bg-gray-700 text-gray-300 rounded text-xs"
                    >
                      {char.character_name}
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
