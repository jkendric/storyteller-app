import { useState } from 'react'
import { Edit, Trash2, Play, Star, Zap, Check, X, Loader2 } from 'lucide-react'
import type { LLMProvider, ProviderTestResult } from '../../api/client'

interface ProviderCardProps {
  provider: LLMProvider
  onEdit: (provider: LLMProvider) => void
  onDelete: (provider: LLMProvider) => void
  onTest: (provider: LLMProvider) => Promise<ProviderTestResult>
  onSetDefault: (provider: LLMProvider) => void
  onSetAlternate: (provider: LLMProvider) => void
}

const providerTypeLabels: Record<string, string> = {
  ollama: 'Ollama',
  lmstudio: 'LM Studio',
  koboldcpp: 'KoboldCpp',
}

export default function ProviderCard({
  provider,
  onEdit,
  onDelete,
  onTest,
  onSetDefault,
  onSetAlternate,
}: ProviderCardProps) {
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<ProviderTestResult | null>(null)

  const handleTest = async () => {
    setIsTesting(true)
    setTestResult(null)
    try {
      const result = await onTest(provider)
      setTestResult(result)
    } finally {
      setIsTesting(false)
    }
  }

  return (
    <div className={`card ${!provider.enabled ? 'opacity-60' : ''}`}>
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-2">
          {provider.is_default && (
            <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" title="Default provider" />
          )}
          {provider.is_alternate && (
            <Zap className="w-4 h-4 text-purple-400" title="Alternate provider" />
          )}
          <h3 className="text-lg font-semibold text-white">{provider.name}</h3>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleTest}
            disabled={isTesting}
            className="p-1.5 text-gray-400 hover:text-green-400 transition-colors disabled:opacity-50"
            title="Test connection"
          >
            {isTesting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
          </button>
          <button
            onClick={() => onEdit(provider)}
            className="p-1.5 text-gray-400 hover:text-primary-400 transition-colors"
            title="Edit"
          >
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(provider)}
            className="p-1.5 text-gray-400 hover:text-red-400 transition-colors"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        <span className="px-2 py-1 bg-primary-900/50 text-primary-300 rounded text-xs">
          {providerTypeLabels[provider.provider_type] || provider.provider_type}
        </span>
        {!provider.enabled && (
          <span className="px-2 py-1 bg-gray-700 text-gray-400 rounded text-xs">
            Disabled
          </span>
        )}
      </div>

      <div className="space-y-2 text-sm">
        <div>
          <span className="text-gray-500">URL: </span>
          <span className="text-gray-300 font-mono text-xs">{provider.base_url}</span>
        </div>
        {provider.default_model && (
          <div>
            <span className="text-gray-500">Model: </span>
            <span className="text-gray-300">{provider.default_model}</span>
          </div>
        )}
      </div>

      {testResult && (
        <div className={`mt-3 p-2 rounded text-sm ${
          testResult.status === 'ok'
            ? 'bg-green-900/30 border border-green-700'
            : 'bg-red-900/30 border border-red-700'
        }`}>
          <div className="flex items-center gap-2">
            {testResult.status === 'ok' ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <X className="w-4 h-4 text-red-400" />
            )}
            <span className={testResult.status === 'ok' ? 'text-green-300' : 'text-red-300'}>
              {testResult.message}
            </span>
          </div>
          {testResult.models && testResult.models.length > 0 && (
            <div className="mt-2 text-gray-400">
              <span className="text-gray-500">Available models: </span>
              {testResult.models.slice(0, 5).join(', ')}
              {testResult.models.length > 5 && ` +${testResult.models.length - 5} more`}
            </div>
          )}
        </div>
      )}

      <div className="flex gap-2 mt-4 pt-3 border-t border-gray-700">
        {!provider.is_default && (
          <button
            onClick={() => onSetDefault(provider)}
            className="text-xs px-2 py-1 text-gray-400 hover:text-yellow-400 hover:bg-yellow-400/10 rounded transition-colors"
          >
            Set as Default
          </button>
        )}
        {!provider.is_alternate && (
          <button
            onClick={() => onSetAlternate(provider)}
            className="text-xs px-2 py-1 text-gray-400 hover:text-purple-400 hover:bg-purple-400/10 rounded transition-colors"
          >
            Set as Alternate
          </button>
        )}
      </div>
    </div>
  )
}
