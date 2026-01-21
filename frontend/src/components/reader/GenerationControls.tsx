import { useState } from 'react'
import { Sparkles, Square, GitBranch, Zap } from 'lucide-react'
import SpeedButtonList from './SpeedButtonList'
import StorySettingsPanel from './StorySettingsPanel'
import { Story } from '../../api/client'

interface GenerationControlsProps {
  isGenerating: boolean
  episodeCount: number
  story: Story
  onGenerate: (guidance?: string, useAlternate?: boolean) => void
  onStop: () => void
  onFork: (fromEpisode: number, newTitle: string) => void
  onStoryUpdate: (story: Story) => void
}

export default function GenerationControls({
  isGenerating,
  episodeCount,
  story,
  onGenerate,
  onStop,
  onFork,
  onStoryUpdate,
}: GenerationControlsProps) {
  const [guidance, setGuidance] = useState('')
  const [useAlternate, setUseAlternate] = useState(false)
  const [showForkModal, setShowForkModal] = useState(false)
  const [forkEpisode, setForkEpisode] = useState(episodeCount)
  const [forkTitle, setForkTitle] = useState('')

  const handleGenerate = () => {
    onGenerate(guidance || undefined, useAlternate)
    setGuidance('')
  }

  const handleFork = () => {
    if (forkTitle.trim()) {
      onFork(forkEpisode, forkTitle.trim())
      setShowForkModal(false)
      setForkTitle('')
    }
  }

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-white mb-4">
        Episode {episodeCount + 1}
      </h3>

      {/* Guidance input */}
      <div className="mb-4">
        <label htmlFor="guidance" className="label">
          Narrative Guidance (optional)
        </label>
        <textarea
          id="guidance"
          value={guidance}
          onChange={(e) => setGuidance(e.target.value)}
          className="textarea"
          rows={3}
          placeholder="Suggest plot points, character actions, or themes to explore..."
          disabled={isGenerating}
        />
      </div>

      {/* Model selection */}
      <div className="mb-4">
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={useAlternate}
            onChange={(e) => setUseAlternate(e.target.checked)}
            disabled={isGenerating}
            className="rounded border-gray-600 bg-gray-700 text-purple-500 focus:ring-purple-500"
          />
          <Zap className={`w-4 h-4 ${useAlternate ? 'text-purple-400' : 'text-gray-500'}`} />
          <span className={`text-sm ${useAlternate ? 'text-purple-300' : 'text-gray-400'}`}>
            Use alternate model
          </span>
        </label>
      </div>

      {/* Action buttons */}
      <div className="flex space-x-3">
        {isGenerating ? (
          <button onClick={onStop} className="btn btn-danger flex-1">
            <Square className="w-4 h-4 mr-2" />
            Stop Generation
          </button>
        ) : (
          <button onClick={handleGenerate} className="btn btn-primary flex-1">
            <Sparkles className="w-4 h-4 mr-2" />
            Generate Episode
          </button>
        )}

        {episodeCount > 0 && (
          <button
            onClick={() => setShowForkModal(true)}
            className="btn btn-secondary"
            disabled={isGenerating}
          >
            <GitBranch className="w-4 h-4 mr-2" />
            Fork
          </button>
        )}
      </div>

      {/* Speed buttons */}
      <SpeedButtonList
        isDisabled={isGenerating}
        onQuickGenerate={(guidance, useAlternate) => {
          onGenerate(guidance, useAlternate)
        }}
      />

      {/* Story Settings */}
      <StorySettingsPanel
        story={story}
        onSettingsUpdate={onStoryUpdate}
        isDisabled={isGenerating}
      />

      {/* Fork modal */}
      {showForkModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="card max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">
              Fork Story
            </h3>

            <div className="space-y-4">
              <div>
                <label htmlFor="forkEpisode" className="label">
                  Fork from Episode
                </label>
                <select
                  id="forkEpisode"
                  value={forkEpisode}
                  onChange={(e) => setForkEpisode(Number(e.target.value))}
                  className="input"
                >
                  {Array.from({ length: episodeCount }, (_, i) => i + 1).map(
                    (num) => (
                      <option key={num} value={num}>
                        Episode {num}
                      </option>
                    )
                  )}
                </select>
              </div>

              <div>
                <label htmlFor="forkTitle" className="label">
                  New Story Title
                </label>
                <input
                  type="text"
                  id="forkTitle"
                  value={forkTitle}
                  onChange={(e) => setForkTitle(e.target.value)}
                  className="input"
                  placeholder="Enter title for the forked story"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowForkModal(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleFork}
                disabled={!forkTitle.trim()}
                className="btn btn-primary"
              >
                Create Fork
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
