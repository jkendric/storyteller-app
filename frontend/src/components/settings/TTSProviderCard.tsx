import { useState } from 'react'
import { Edit, Trash2, Play, Star, Check, X, Loader2, Radio, Mic } from 'lucide-react'
import type { TTSProvider, TTSProviderTestResult } from '../../api/client'

interface TTSProviderCardProps {
  provider: TTSProvider
  onEdit: (provider: TTSProvider) => void
  onDelete: (provider: TTSProvider) => void
  onTest: (provider: TTSProvider) => Promise<TTSProviderTestResult>
  onSetDefault: (provider: TTSProvider) => void
  onManageVoiceClones?: (provider: TTSProvider) => void
}

const providerTypeLabels: Record<string, string> = {
  kokoro: 'Kokoro',
  piper: 'Piper',
  coqui_xtts: 'Coqui XTTS',
  openai_compatible: 'OpenAI Compatible',
  chatterbox: 'Chatterbox',
}

export default function TTSProviderCard({
  provider,
  onEdit,
  onDelete,
  onTest,
  onSetDefault,
  onManageVoiceClones,
}: TTSProviderCardProps) {
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<TTSProviderTestResult | null>(null)

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
            <span title="Default TTS provider">
              <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
            </span>
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
        {provider.supports_streaming && (
          <span className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded text-xs flex items-center gap-1">
            <Radio className="w-3 h-3" />
            Streaming
          </span>
        )}
        {provider.supports_voice_cloning && (
          <span className="px-2 py-1 bg-purple-900/50 text-purple-300 rounded text-xs flex items-center gap-1">
            <Mic className="w-3 h-3" />
            Voice Cloning
          </span>
        )}
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
        {provider.default_voice && (
          <div>
            <span className="text-gray-500">Voice: </span>
            <span className="text-gray-300">{provider.default_voice}</span>
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
          {testResult.voices && testResult.voices.length > 0 && (
            <div className="mt-2 text-gray-400">
              <span className="text-gray-500">Available voices: </span>
              {testResult.voices.slice(0, 5).join(', ')}
              {testResult.voices.length > 5 && ` +${testResult.voices.length - 5} more`}
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
        {provider.supports_voice_cloning && onManageVoiceClones && (
          <button
            onClick={() => onManageVoiceClones(provider)}
            className="text-xs px-2 py-1 text-gray-400 hover:text-purple-400 hover:bg-purple-400/10 rounded transition-colors"
          >
            Manage Voice Clones
          </button>
        )}
      </div>
    </div>
  )
}
