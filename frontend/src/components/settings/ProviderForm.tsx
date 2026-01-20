import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import type { LLMProvider, LLMProviderCreate, ProviderType } from '../../api/client'
import { api } from '../../api/client'

interface ProviderFormProps {
  provider?: LLMProvider
  onSubmit: (data: LLMProviderCreate) => void
  onCancel: () => void
}

const providerTypeOptions: { value: ProviderType; label: string; defaultPort: number }[] = [
  { value: 'ollama', label: 'Ollama', defaultPort: 11434 },
  { value: 'lmstudio', label: 'LM Studio', defaultPort: 1234 },
  { value: 'koboldcpp', label: 'KoboldCpp', defaultPort: 5001 },
]

export default function ProviderForm({
  provider,
  onSubmit,
  onCancel,
}: ProviderFormProps) {
  const [formData, setFormData] = useState<LLMProviderCreate>({
    name: provider?.name || '',
    provider_type: provider?.provider_type || 'ollama',
    base_url: provider?.base_url || 'http://localhost:11434/v1',
    default_model: provider?.default_model || '',
    is_default: provider?.is_default || false,
    is_alternate: provider?.is_alternate || false,
    enabled: provider?.enabled ?? true,
  })

  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [isLoadingModels, setIsLoadingModels] = useState(false)
  const [testError, setTestError] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target
    const newValue = type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    setFormData((prev) => ({ ...prev, [name]: newValue }))
  }

  const handleProviderTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newType = e.target.value as ProviderType
    const option = providerTypeOptions.find((o) => o.value === newType)

    setFormData((prev) => ({
      ...prev,
      provider_type: newType,
      base_url: `http://localhost:${option?.defaultPort || 11434}/v1`,
    }))
    setAvailableModels([])
    setTestError(null)
  }

  const handleTestAndFetchModels = async () => {
    setIsLoadingModels(true)
    setTestError(null)
    setAvailableModels([])

    try {
      const result = await api.testProviderUrl(formData.base_url)
      if (result.status === 'ok' && result.models) {
        setAvailableModels(result.models)
        if (!formData.default_model && result.models.length > 0) {
          setFormData((prev) => ({ ...prev, default_model: result.models![0] }))
        }
      } else {
        setTestError(result.message || 'Failed to connect')
      }
    } catch (error) {
      setTestError(error instanceof Error ? error.message : 'Connection failed')
    } finally {
      setIsLoadingModels(false)
    }
  }

  // Auto-fetch models when editing existing provider
  useEffect(() => {
    if (provider?.id) {
      api.getProviderModels(provider.id)
        .then((response) => {
          const models = response.models.map((m) => m.id || m.name || 'unknown')
          setAvailableModels(models)
        })
        .catch(() => {
          // Ignore errors for initial load
        })
    }
  }, [provider?.id])

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="name" className="label">
          Name *
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          className="input"
          placeholder="e.g., My Ollama Server"
          required
        />
      </div>

      <div>
        <label htmlFor="provider_type" className="label">
          Provider Type *
        </label>
        <select
          id="provider_type"
          name="provider_type"
          value={formData.provider_type}
          onChange={handleProviderTypeChange}
          className="input"
        >
          {providerTypeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="base_url" className="label">
          Base URL *
        </label>
        <div className="flex gap-2">
          <input
            type="url"
            id="base_url"
            name="base_url"
            value={formData.base_url}
            onChange={handleChange}
            className="input flex-1"
            placeholder="http://localhost:11434/v1"
            required
          />
          <button
            type="button"
            onClick={handleTestAndFetchModels}
            disabled={isLoadingModels}
            className="btn btn-secondary whitespace-nowrap"
          >
            {isLoadingModels ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              'Test & Fetch Models'
            )}
          </button>
        </div>
        {testError && (
          <p className="text-red-400 text-sm mt-1">{testError}</p>
        )}
      </div>

      <div>
        <label htmlFor="default_model" className="label">
          Default Model
        </label>
        {availableModels.length > 0 ? (
          <select
            id="default_model"
            name="default_model"
            value={formData.default_model}
            onChange={handleChange}
            className="input"
          >
            <option value="">Select a model</option>
            {availableModels.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            id="default_model"
            name="default_model"
            value={formData.default_model}
            onChange={handleChange}
            className="input"
            placeholder="e.g., llama3.2, mistral-nemo"
          />
        )}
        <p className="text-gray-500 text-xs mt-1">
          Click "Test & Fetch Models" to see available models
        </p>
      </div>

      <div className="space-y-3">
        <label className="label">Role</label>
        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              name="is_default"
              checked={formData.is_default}
              onChange={handleChange}
              className="rounded border-gray-600 bg-gray-700 text-primary-500 focus:ring-primary-500"
            />
            <span className="text-gray-300">Default provider (main storytelling model)</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              name="is_alternate"
              checked={formData.is_alternate}
              onChange={handleChange}
              className="rounded border-gray-600 bg-gray-700 text-purple-500 focus:ring-purple-500"
            />
            <span className="text-gray-300">Alternate provider (uncensored model)</span>
          </label>
        </div>
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          name="enabled"
          checked={formData.enabled}
          onChange={handleChange}
          className="rounded border-gray-600 bg-gray-700 text-primary-500 focus:ring-primary-500"
        />
        <span className="text-gray-300">Enabled</span>
      </label>

      <div className="flex justify-end space-x-3 pt-4">
        <button type="button" onClick={onCancel} className="btn btn-secondary">
          Cancel
        </button>
        <button type="submit" className="btn btn-primary">
          {provider ? 'Update' : 'Create'} Provider
        </button>
      </div>
    </form>
  )
}
