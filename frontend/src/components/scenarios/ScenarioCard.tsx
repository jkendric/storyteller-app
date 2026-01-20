import { Edit, Trash2 } from 'lucide-react'
import type { Scenario } from '../../api/client'

interface ScenarioCardProps {
  scenario: Scenario
  onEdit: (scenario: Scenario) => void
  onDelete: (scenario: Scenario) => void
}

export default function ScenarioCard({
  scenario,
  onEdit,
  onDelete,
}: ScenarioCardProps) {
  return (
    <div className="card">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-white">{scenario.name}</h3>
        <div className="flex space-x-2">
          <button
            onClick={() => onEdit(scenario)}
            className="p-1.5 text-gray-400 hover:text-primary-400 transition-colors"
            title="Edit"
          >
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(scenario)}
            className="p-1.5 text-gray-400 hover:text-red-400 transition-colors"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        {scenario.genre && (
          <span className="px-2 py-1 bg-primary-900/50 text-primary-300 rounded text-xs">
            {scenario.genre}
          </span>
        )}
        {scenario.tone && (
          <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">
            {scenario.tone}
          </span>
        )}
        {scenario.time_period && (
          <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">
            {scenario.time_period}
          </span>
        )}
      </div>

      {scenario.premise && (
        <p className="text-gray-400 text-sm mb-2 line-clamp-3">
          {scenario.premise}
        </p>
      )}

      {scenario.setting && (
        <div>
          <span className="text-xs text-gray-500 uppercase">Setting</span>
          <p className="text-gray-300 text-sm line-clamp-2">{scenario.setting}</p>
        </div>
      )}
    </div>
  )
}
