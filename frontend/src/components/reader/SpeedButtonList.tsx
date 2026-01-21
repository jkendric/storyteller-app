import { useState, useEffect } from 'react'
import { Settings, Plus } from 'lucide-react'
import { useSpeedButtonStore } from '../../stores/speedButtonStore'
import SpeedButtonItem from './SpeedButtonItem'
import SpeedButtonModal from './SpeedButtonModal'
import type { SpeedButton, SpeedButtonCreate, SpeedButtonUpdate } from '../../api/client'

interface SpeedButtonListProps {
  isDisabled: boolean
  onQuickGenerate: (guidance?: string, useAlternate?: boolean) => void
}

export default function SpeedButtonList({
  isDisabled,
  onQuickGenerate,
}: SpeedButtonListProps) {
  const {
    speedButtons,
    isLoading,
    fetchSpeedButtons,
    createSpeedButton,
    updateSpeedButton,
    deleteSpeedButton,
  } = useSpeedButtonStore()

  const [isManageMode, setIsManageMode] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingButton, setEditingButton] = useState<SpeedButton | null>(null)

  useEffect(() => {
    fetchSpeedButtons()
  }, [fetchSpeedButtons])

  const handleUse = (button: SpeedButton) => {
    onQuickGenerate(button.guidance || undefined, button.use_alternate)
  }

  const handleEdit = (button: SpeedButton) => {
    setEditingButton(button)
    setIsModalOpen(true)
  }

  const handleDelete = async (button: SpeedButton) => {
    if (window.confirm(`Delete "${button.label}"?`)) {
      await deleteSpeedButton(button.id)
    }
  }

  const handleAdd = () => {
    setEditingButton(null)
    setIsModalOpen(true)
  }

  const handleSave = async (data: SpeedButtonCreate | SpeedButtonUpdate) => {
    try {
      if (editingButton) {
        await updateSpeedButton(editingButton.id, data)
      } else {
        await createSpeedButton(data as SpeedButtonCreate)
      }
      setIsModalOpen(false)
      setEditingButton(null)
    } catch {
      // Error is handled by the store
    }
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingButton(null)
  }

  if (isLoading && speedButtons.length === 0) {
    return (
      <div className="mt-4 text-gray-500 text-sm">
        Loading presets...
      </div>
    )
  }

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-400">Quick Generate</span>
        <button
          onClick={() => setIsManageMode(!isManageMode)}
          className={`p-1.5 rounded transition-colors ${
            isManageMode
              ? 'bg-purple-600 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-700'
          }`}
          title={isManageMode ? 'Done managing' : 'Manage presets'}
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {speedButtons.map((button) => (
          <SpeedButtonItem
            key={button.id}
            button={button}
            isManageMode={isManageMode}
            isDisabled={isDisabled}
            onUse={handleUse}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        ))}

        {isManageMode && (
          <button
            onClick={handleAdd}
            className="
              px-3 py-1.5 rounded-full text-sm font-medium
              flex items-center gap-1.5
              border-2 border-dashed border-gray-600
              text-gray-400 hover:text-white hover:border-purple-500
              transition-colors
            "
          >
            <Plus className="w-3 h-3" />
            Add
          </button>
        )}
      </div>

      <SpeedButtonModal
        isOpen={isModalOpen}
        button={editingButton}
        onClose={handleCloseModal}
        onSave={handleSave}
      />
    </div>
  )
}
