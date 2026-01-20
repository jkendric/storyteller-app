import { Edit, Trash2 } from 'lucide-react'
import type { Character } from '../../api/client'

interface CharacterCardProps {
  character: Character
  onEdit: (character: Character) => void
  onDelete: (character: Character) => void
}

export default function CharacterCard({
  character,
  onEdit,
  onDelete,
}: CharacterCardProps) {
  return (
    <div className="card">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-white">{character.name}</h3>
        <div className="flex space-x-2">
          <button
            onClick={() => onEdit(character)}
            className="p-1.5 text-gray-400 hover:text-primary-400 transition-colors"
            title="Edit"
          >
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(character)}
            className="p-1.5 text-gray-400 hover:text-red-400 transition-colors"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {character.description && (
        <p className="text-gray-400 text-sm mb-2 line-clamp-2">
          {character.description}
        </p>
      )}

      {character.personality && (
        <div className="mb-2">
          <span className="text-xs text-gray-500 uppercase">Personality</span>
          <p className="text-gray-300 text-sm line-clamp-2">
            {character.personality}
          </p>
        </div>
      )}

      {character.motivations && (
        <div>
          <span className="text-xs text-gray-500 uppercase">Motivations</span>
          <p className="text-gray-300 text-sm line-clamp-2">
            {character.motivations}
          </p>
        </div>
      )}
    </div>
  )
}
