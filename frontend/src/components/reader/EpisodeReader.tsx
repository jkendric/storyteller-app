import { useState } from 'react'
import { ChevronLeft, ChevronRight, Volume2, VolumeX } from 'lucide-react'
import type { Episode } from '../../api/client'
import { useAudioPlayer } from '../../hooks/useAudioPlayer'
import { useAudioStore } from '../../stores/audioStore'

interface EpisodeReaderProps {
  episodes: Episode[]
  streamingContent?: string
  isGenerating?: boolean
}

export default function EpisodeReader({
  episodes,
  streamingContent,
  isGenerating,
}: EpisodeReaderProps) {
  const [currentIndex, setCurrentIndex] = useState(episodes.length - 1)
  const { play, pause, stop, isPlaying } = useAudioPlayer()
  const { clearQueue } = useAudioStore()

  const currentEpisode = episodes[currentIndex]

  const goToPrevious = () => {
    if (currentIndex > 0) {
      stop()
      setCurrentIndex(currentIndex - 1)
    }
  }

  const goToNext = () => {
    if (currentIndex < episodes.length - 1) {
      stop()
      setCurrentIndex(currentIndex + 1)
    }
  }

  const toggleAudio = () => {
    if (isPlaying) {
      pause()
    } else {
      play()
    }
  }

  // Show streaming content if we're generating and on the latest episode
  const showStreaming = isGenerating && currentIndex === episodes.length - 1
  const displayContent = showStreaming
    ? streamingContent
    : currentEpisode?.content

  if (episodes.length === 0 && !isGenerating) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-400">No episodes yet. Generate your first episode!</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={goToPrevious}
          disabled={currentIndex === 0}
          className="btn btn-secondary disabled:opacity-50"
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Previous
        </button>

        <div className="flex items-center space-x-4">
          <span className="text-gray-400">
            Episode {currentEpisode?.number || episodes.length + 1} of{' '}
            {isGenerating ? episodes.length + 1 : episodes.length}
          </span>
          <button
            onClick={toggleAudio}
            className={`p-2 rounded-lg transition-colors ${
              isPlaying
                ? 'bg-primary-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            title={isPlaying ? 'Pause audio' : 'Play audio'}
          >
            {isPlaying ? (
              <VolumeX className="w-5 h-5" />
            ) : (
              <Volume2 className="w-5 h-5" />
            )}
          </button>
        </div>

        <button
          onClick={goToNext}
          disabled={currentIndex >= episodes.length - 1 && !isGenerating}
          className="btn btn-secondary disabled:opacity-50"
        >
          Next
          <ChevronRight className="w-4 h-4 ml-1" />
        </button>
      </div>

      {/* Episode content */}
      <div className="card">
        {currentEpisode?.title && (
          <h2 className="text-2xl font-serif font-bold text-white mb-6">
            {currentEpisode.title}
          </h2>
        )}

        <div className="prose-story font-serif text-lg">
          {displayContent?.split('\n').map((paragraph, i) => (
            <p key={i}>{paragraph}</p>
          ))}
          {isGenerating && showStreaming && (
            <span className="inline-block w-2 h-5 bg-primary-500 animate-pulse ml-1" />
          )}
        </div>

        {currentEpisode?.word_count > 0 && (
          <div className="mt-6 pt-4 border-t border-gray-700 text-sm text-gray-500">
            {currentEpisode.word_count} words
          </div>
        )}
      </div>
    </div>
  )
}
