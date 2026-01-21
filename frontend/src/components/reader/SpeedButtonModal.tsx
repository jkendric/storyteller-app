import { useState, useEffect } from 'react'
import { Zap } from 'lucide-react'
import type { SpeedButton, SpeedButtonCreate, SpeedButtonUpdate } from '../../api/client'

interface SpeedButtonModalProps {
  isOpen: boolean
  button?: SpeedButton | null
  onClose: () => void
  onSave: (data: SpeedButtonCreate | SpeedButtonUpdate) => void
}

export default function SpeedButtonModal({
  isOpen,
  button,
  onClose,
  onSave,
}: SpeedButtonModalProps) {
  const [label, setLabel] = useState('')
  const [guidance, setGuidance] = useState('')
  const [useAlternate, setUseAlternate] = useState(false)

  const isEditing = !!button

  useEffect(() => {
    if (button) {
      setLabel(button.label)
      setGuidance(button.guidance || '')
      setUseAlternate(button.use_alternate)
    } else {
      setLabel('')
      setGuidance('')
      setUseAlternate(false)
    }
  }, [button, isOpen])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!label.trim()) return

    const data = {
      label: label.trim(),
      guidance: guidance.trim() || undefined,
      use_alternate: useAlternate,
    }

    onSave(data)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="card max-w-md w-full mx-4">
        <h3 className="text-lg font-semibold text-white mb-4">
          {isEditing ? 'Edit Speed Button' : 'Add Speed Button'}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="speedButtonLabel" className="label">
              Button Label
            </label>
            <input
              type="text"
              id="speedButtonLabel"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              className="input"
              placeholder="e.g., Action Scene"
              maxLength={50}
              required
            />
          </div>

          <div>
            <label htmlFor="speedButtonGuidance" className="label">
              Narrative Guidance
            </label>
            <textarea
              id="speedButtonGuidance"
              value={guidance}
              onChange={(e) => setGuidance(e.target.value)}
              className="textarea"
              rows={3}
              placeholder="Instructions for episode generation..."
            />
          </div>

          <div>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useAlternate}
                onChange={(e) => setUseAlternate(e.target.checked)}
                className="rounded border-gray-600 bg-gray-700 text-purple-500 focus:ring-purple-500"
              />
              <Zap className={`w-4 h-4 ${useAlternate ? 'text-purple-400' : 'text-gray-500'}`} />
              <span className={`text-sm ${useAlternate ? 'text-purple-300' : 'text-gray-400'}`}>
                Use alternate model
              </span>
            </label>
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!label.trim()}
              className="btn btn-primary"
            >
              {isEditing ? 'Save Changes' : 'Add Button'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
