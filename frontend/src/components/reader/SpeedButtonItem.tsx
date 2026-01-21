import { Zap, Pencil, Trash2 } from 'lucide-react'
import type { SpeedButton } from '../../api/client'

interface SpeedButtonItemProps {
  button: SpeedButton
  isManageMode: boolean
  isDisabled: boolean
  onUse: (button: SpeedButton) => void
  onEdit: (button: SpeedButton) => void
  onDelete: (button: SpeedButton) => void
}

export default function SpeedButtonItem({
  button,
  isManageMode,
  isDisabled,
  onUse,
  onEdit,
  onDelete,
}: SpeedButtonItemProps) {
  const handleClick = () => {
    if (!isDisabled && !isManageMode) {
      onUse(button)
    }
  }

  return (
    <div className="relative group">
      <button
        onClick={handleClick}
        disabled={isDisabled}
        title={button.guidance || button.label}
        className={`
          px-3 py-1.5 rounded-full text-sm font-medium
          flex items-center gap-1.5
          transition-all duration-150
          ${isDisabled
            ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
            : isManageMode
              ? 'bg-gray-700 text-gray-300 cursor-default'
              : 'bg-gray-700 text-gray-200 hover:bg-purple-600 hover:text-white cursor-pointer'
          }
        `}
      >
        {button.use_alternate && (
          <Zap className="w-3 h-3 text-purple-400" />
        )}
        <span className="truncate max-w-[120px]">{button.label}</span>
      </button>

      {isManageMode && (
        <div className="absolute -top-1 -right-1 flex gap-0.5">
          <button
            onClick={() => onEdit(button)}
            className="p-1 bg-gray-600 rounded-full hover:bg-blue-600 transition-colors"
            title="Edit"
          >
            <Pencil className="w-3 h-3 text-white" />
          </button>
          {!button.is_default && (
            <button
              onClick={() => onDelete(button)}
              className="p-1 bg-gray-600 rounded-full hover:bg-red-600 transition-colors"
              title="Delete"
            >
              <Trash2 className="w-3 h-3 text-white" />
            </button>
          )}
        </div>
      )}
    </div>
  )
}
