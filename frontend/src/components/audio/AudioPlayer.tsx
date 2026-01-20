import { Play, Pause, Square, Volume2, VolumeX } from 'lucide-react'
import { useAudioStore } from '../../stores/audioStore'
import { useAudioPlayerContext } from '../../contexts/AudioPlayerContext'

export default function AudioPlayer() {
  const { volume, playbackRate, setVolume, setPlaybackRate } = useAudioStore()
  const { play, pause, stop, isPlaying, currentSentenceIndex, queueLength } =
    useAudioPlayerContext()

  const progress = queueLength > 0 ? (currentSentenceIndex / queueLength) * 100 : 0

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Audio Player</h3>
        <span className="text-sm text-gray-400">
          {currentSentenceIndex} / {queueLength} sentences
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-gray-700 rounded-full mb-4 overflow-hidden">
        <div
          className="h-full bg-primary-500 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {isPlaying ? (
            <button
              onClick={pause}
              className="p-3 bg-primary-600 text-white rounded-full hover:bg-primary-700 transition-colors"
            >
              <Pause className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={play}
              className="p-3 bg-primary-600 text-white rounded-full hover:bg-primary-700 transition-colors"
            >
              <Play className="w-5 h-5" />
            </button>
          )}
          <button
            onClick={stop}
            className="p-2 bg-gray-700 text-gray-300 rounded-full hover:bg-gray-600 transition-colors"
          >
            <Square className="w-4 h-4" />
          </button>
        </div>

        {/* Volume control */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setVolume(volume === 0 ? 1 : 0)}
            className="text-gray-400 hover:text-white transition-colors"
          >
            {volume === 0 ? (
              <VolumeX className="w-5 h-5" />
            ) : (
              <Volume2 className="w-5 h-5" />
            )}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={volume}
            onChange={(e) => setVolume(parseFloat(e.target.value))}
            className="w-20 accent-primary-500"
          />
        </div>

        {/* Speed control */}
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-400">Speed:</span>
          <select
            value={playbackRate}
            onChange={(e) => setPlaybackRate(parseFloat(e.target.value))}
            className="bg-gray-700 text-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value="0.5">0.5x</option>
            <option value="0.75">0.75x</option>
            <option value="1">1x</option>
            <option value="1.25">1.25x</option>
            <option value="1.5">1.5x</option>
            <option value="2">2x</option>
          </select>
        </div>
      </div>
    </div>
  )
}
