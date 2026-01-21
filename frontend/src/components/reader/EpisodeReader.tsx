import { useState, useEffect, useRef } from 'react'
import { ChevronLeft, ChevronRight, Volume2, VolumeX } from 'lucide-react'
import type { Episode } from '../../api/client'
import { useAudioPlayerContext } from '../../contexts/AudioPlayerContext'
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
  const { play, pause, stop, isPlaying } = useAudioPlayerContext()
  const { queueContent, audioQueue } = useAudioStore()
  const prevEpisodesLengthRef = useRef(episodes.length)
  const wasGeneratingRef = useRef(isGenerating)
  const shouldAutoPlayRef = useRef(false)
  const prevIndexRef = useRef(currentIndex)
  const autoPlayOnFirstSentenceRef = useRef(false)

  // Auto-navigate to the new episode when it's added to the array
  useEffect(() => {
    if (episodes.length > prevEpisodesLengthRef.current) {
      // A new episode was added - navigate to it
      setCurrentIndex(episodes.length - 1)
    }
    prevEpisodesLengthRef.current = episodes.length
  }, [episodes.length])

  // Handle generation start and error recovery
  useEffect(() => {
    if (isGenerating && !wasGeneratingRef.current) {
      // Generation just started - remember if audio was playing, then stop
      const wasPlaying = isPlaying
      stop()
      // Set index to the new episode slot (one past current last)
      setCurrentIndex(episodes.length)

      // If audio was playing, set flag to auto-play when first sentence arrives
      // We can't call play() immediately because the queue is empty and the
      // audio processor would immediately set isPlaying back to false
      if (wasPlaying) {
        autoPlayOnFirstSentenceRef.current = true
      }

      // Reset auto-play flag - we've already handled playback for streaming
      // This prevents the auto-play effect from re-queuing when generation completes
      shouldAutoPlayRef.current = false
    } else if (!isGenerating && wasGeneratingRef.current) {
      // Generation just stopped - if we're on a non-existent episode slot
      // and there's no streaming content, navigate back to the last real episode
      // (this handles the error case where generation failed before any content arrived)
      if (currentIndex >= episodes.length && !streamingContent && episodes.length > 0) {
        setCurrentIndex(episodes.length - 1)
      }
    }
    wasGeneratingRef.current = isGenerating
  }, [isGenerating, episodes.length, stop, isPlaying, currentIndex, streamingContent])

  // Auto-play when queue has content and auto-play flag is set
  // This effect watches the queue and starts playback when content arrives,
  // avoiding race conditions from calling play() immediately after queueContent()
  useEffect(() => {
    if (autoPlayOnFirstSentenceRef.current && audioQueue.length > 0) {
      // Queue has content and we should auto-play - start playing
      play()
      autoPlayOnFirstSentenceRef.current = false
    }
  }, [audioQueue.length, play])

  // Queue content when navigating to a new chapter (if audio was playing)
  useEffect(() => {
    if (currentIndex !== prevIndexRef.current && shouldAutoPlayRef.current) {
      // Index changed and we should auto-play
      const newEpisode = episodes[currentIndex]
      if (newEpisode?.content) {
        // Queue the content - the effect above will start playback
        // when it detects the queue went from empty to populated
        queueContent(newEpisode.content)
        autoPlayOnFirstSentenceRef.current = true
      }
      shouldAutoPlayRef.current = false
    }
    prevIndexRef.current = currentIndex
  }, [currentIndex, episodes, queueContent])

  // currentIndex may point past the array during generation (to the new episode slot)
  const currentEpisode = episodes[currentIndex]

  // Show streaming content when:
  // 1. We're on a position that doesn't have an episode yet (during/after generation), OR
  // 2. We're generating and on the latest position
  const isOnNewEpisodeSlot = currentIndex >= episodes.length
  const showStreaming = isOnNewEpisodeSlot || (isGenerating && currentIndex === episodes.length - 1)

  // Prefer persisted episode content when available, fall back to streaming
  const displayContent = currentEpisode?.content
    ? currentEpisode.content
    : streamingContent || undefined

  const goToPrevious = () => {
    if (currentIndex > 0) {
      // Remember if audio was playing before stopping
      shouldAutoPlayRef.current = isPlaying
      stop()
      setCurrentIndex(currentIndex - 1)
    }
  }

  const goToNext = () => {
    if (currentIndex < episodes.length - 1) {
      // Remember if audio was playing before stopping
      shouldAutoPlayRef.current = isPlaying
      stop()
      setCurrentIndex(currentIndex + 1)
    }
  }

  const toggleAudio = () => {
    if (isPlaying) {
      pause()
    } else {
      // Always re-queue if streaming to ensure current content is played
      // Otherwise, only queue if the queue is empty
      if (displayContent && (showStreaming || audioQueue.length === 0)) {
        queueContent(displayContent)
      }
      play()
    }
  }

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
          {isGenerating && isOnNewEpisodeSlot && (
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
