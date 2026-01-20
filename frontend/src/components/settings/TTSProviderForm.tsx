import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import type { TTSProvider, TTSProviderCreate, TTSProviderType } from '../../api/client'
import { api } from '../../api/client'

interface TTSProviderFormProps {
  provider?: TTSProvider
  onSubmit: (data: TTSProviderCreate) => void
  onCancel: () => void
}

const providerTypeOptions: {
  value: TTSProviderType
  label: string
  defaultPort: number
  defaultSupportsStreaming: boolean
  defaultSupportsVoiceCloning: boolean
}[] = [
  { value: 'kokoro', label: 'Kokoro', defaultPort: 8880, defaultSupportsStreaming: true, defaultSupportsVoiceCloning: false },
  { value: 'piper', label: 'Piper', defaultPort: 5000, defaultSupportsStreaming: false, defaultSupportsVoiceCloning: false },
  { value: 'coqui_xtts', label: 'Coqui XTTS', defaultPort: 8000, defaultSupportsStreaming: true, defaultSupportsVoiceCloning: true },
  { value: 'openai_compatible', label: 'OpenAI Compatible', defaultPort: 8080, defaultSupportsStreaming: true, defaultSupportsVoiceCloning: false },
  { value: 'chatterbox', label: 'Chatterbox', defaultPort: 8000, defaultSupportsStreaming: true, defaultSupportsVoiceCloning: true },
]

export default function TTSProviderForm({
  provider,
  onSubmit,
  onCancel,
}: TTSProviderFormProps) {
  const [formData, setFormData] = useState<TTSProviderCreate>({
    name: provider?.name || '',
    provider_type: provider?.provider_type || 'kokoro',
    base_url: provider?.base_url || 'http://localhost:8880',
    default_voice: provider?.default_voice || '',
    supports_streaming: provider?.supports_streaming ?? true,
    supports_voice_cloning: provider?.supports_voice_cloning ?? false,
    provider_settings: provider?.provider_settings || {},
    is_default: provider?.is_default || false,
    enabled: provider?.enabled ?? true,
  })

  // Chatterbox-specific settings
  const [chatterboxSettings, setChatterboxSettings] = useState({
    temperature: (provider?.provider_settings?.temperature as number) ?? 1.0,
    exaggeration: (provider?.provider_settings?.exaggeration as number) ?? 1.0,
    cfg_weight: (provider?.provider_settings?.cfg_weight as number) ?? 0.5,
    output_format: (provider?.provider_settings?.output_format as string) ?? 'wav',
    language: (provider?.provider_settings?.language as string) ?? 'en',
    prefetch_depth: (provider?.provider_settings?.prefetch_depth as number) ?? 5,
    chunk_size: (provider?.provider_settings?.chunk_size as number) ?? 4096,
  })

  const [availableVoices, setAvailableVoices] = useState<string[]>([])
  const [isLoadingVoices, setIsLoadingVoices] = useState(false)
  const [testError, setTestError] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Include Chatterbox settings in provider_settings if applicable
    if (formData.provider_type === 'chatterbox') {
      onSubmit({
        ...formData,
        provider_settings: chatterboxSettings,
      })
    } else {
      onSubmit(formData)
    }
  }

  const handleChatterboxSettingChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    const numValue = parseFloat(value)
    setChatterboxSettings((prev) => ({
      ...prev,
      [name]: isNaN(numValue) ? value : numValue,
    }))
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target
    const newValue = type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    setFormData((prev) => ({ ...prev, [name]: newValue }))
  }

  const handleProviderTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newType = e.target.value as TTSProviderType
    const option = providerTypeOptions.find((o) => o.value === newType)

    setFormData((prev) => ({
      ...prev,
      provider_type: newType,
      base_url: `http://localhost:${option?.defaultPort || 8880}`,
      supports_streaming: option?.defaultSupportsStreaming ?? true,
      supports_voice_cloning: option?.defaultSupportsVoiceCloning ?? false,
    }))
    setAvailableVoices([])
    setTestError(null)
  }

  const handleTestAndFetchVoices = async () => {
    setIsLoadingVoices(true)
    setTestError(null)
    setAvailableVoices([])

    try {
      const result = await api.testTTSProviderUrl(formData.base_url, formData.provider_type)
      if (result.status === 'ok' && result.voices) {
        setAvailableVoices(result.voices)
        if (!formData.default_voice && result.voices.length > 0) {
          setFormData((prev) => ({ ...prev, default_voice: result.voices![0] }))
        }
        // Update capabilities from test result
        if (result.supports_streaming !== undefined) {
          setFormData((prev) => ({ ...prev, supports_streaming: result.supports_streaming! }))
        }
        if (result.supports_voice_cloning !== undefined) {
          setFormData((prev) => ({ ...prev, supports_voice_cloning: result.supports_voice_cloning! }))
        }
      } else {
        setTestError(result.message || 'Failed to connect')
      }
    } catch (error) {
      setTestError(error instanceof Error ? error.message : 'Connection failed')
    } finally {
      setIsLoadingVoices(false)
    }
  }

  // Auto-fetch voices when editing existing provider
  useEffect(() => {
    if (provider?.id) {
      api.getTTSProviderVoices(provider.id)
        .then((response) => {
          const voices = response.voices.map((v) => v.id || v.name || 'unknown')
          setAvailableVoices(voices)
        })
        .catch(() => {
          // Ignore errors for initial load
        })
    }
  }, [provider?.id])

  const selectedOption = providerTypeOptions.find((o) => o.value === formData.provider_type)

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
          placeholder="e.g., My Kokoro Server"
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
        <p className="text-gray-500 text-xs mt-1">
          Default port: {selectedOption?.defaultPort}
        </p>
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
            placeholder={`http://localhost:${selectedOption?.defaultPort}`}
            required
          />
          <button
            type="button"
            onClick={handleTestAndFetchVoices}
            disabled={isLoadingVoices}
            className="btn btn-secondary whitespace-nowrap"
          >
            {isLoadingVoices ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              'Test & Fetch Voices'
            )}
          </button>
        </div>
        {testError && (
          <p className="text-red-400 text-sm mt-1">{testError}</p>
        )}
      </div>

      <div>
        <label htmlFor="default_voice" className="label">
          Default Voice
        </label>
        {availableVoices.length > 0 ? (
          <select
            id="default_voice"
            name="default_voice"
            value={formData.default_voice}
            onChange={handleChange}
            className="input"
          >
            <option value="">Select a voice</option>
            {availableVoices.map((voice) => (
              <option key={voice} value={voice}>
                {voice}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            id="default_voice"
            name="default_voice"
            value={formData.default_voice}
            onChange={handleChange}
            className="input"
            placeholder="e.g., af_bella"
          />
        )}
        <p className="text-gray-500 text-xs mt-1">
          Click "Test & Fetch Voices" to see available voices
        </p>
      </div>

      {/* Capabilities section - only show for OpenAI Compatible */}
      {formData.provider_type === 'openai_compatible' && (
        <div className="space-y-3">
          <label className="label">Capabilities</label>
          <div className="space-y-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                name="supports_streaming"
                checked={formData.supports_streaming}
                onChange={handleChange}
                className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500"
              />
              <span className="text-gray-300">Supports real-time streaming</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                name="supports_voice_cloning"
                checked={formData.supports_voice_cloning}
                onChange={handleChange}
                className="rounded border-gray-600 bg-gray-700 text-purple-500 focus:ring-purple-500"
              />
              <span className="text-gray-300">Supports voice cloning</span>
            </label>
          </div>
        </div>
      )}

      {/* Chatterbox-specific settings */}
      {formData.provider_type === 'chatterbox' && (
        <div className="space-y-4 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
          <h4 className="text-sm font-medium text-gray-300">Chatterbox Settings</h4>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="temperature" className="label text-xs">
                Temperature ({chatterboxSettings.temperature.toFixed(1)})
              </label>
              <input
                type="range"
                id="temperature"
                name="temperature"
                min="0.1"
                max="2.0"
                step="0.1"
                value={chatterboxSettings.temperature}
                onChange={handleChatterboxSettingChange}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
              <p className="text-gray-500 text-xs mt-1">Controls randomness (0.1-2.0)</p>
            </div>

            <div>
              <label htmlFor="exaggeration" className="label text-xs">
                Exaggeration ({chatterboxSettings.exaggeration.toFixed(1)})
              </label>
              <input
                type="range"
                id="exaggeration"
                name="exaggeration"
                min="0"
                max="2.0"
                step="0.1"
                value={chatterboxSettings.exaggeration}
                onChange={handleChatterboxSettingChange}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
              <p className="text-gray-500 text-xs mt-1">Emotional intensity (0-2.0)</p>
            </div>

            <div>
              <label htmlFor="cfg_weight" className="label text-xs">
                CFG Weight ({chatterboxSettings.cfg_weight.toFixed(2)})
              </label>
              <input
                type="range"
                id="cfg_weight"
                name="cfg_weight"
                min="0"
                max="1.0"
                step="0.05"
                value={chatterboxSettings.cfg_weight}
                onChange={handleChatterboxSettingChange}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
              <p className="text-gray-500 text-xs mt-1">Classifier-free guidance (0-1.0)</p>
            </div>

            <div>
              <label htmlFor="output_format" className="label text-xs">
                Output Format
              </label>
              <select
                id="output_format"
                name="output_format"
                value={chatterboxSettings.output_format}
                onChange={handleChatterboxSettingChange}
                className="input"
              >
                <option value="wav">WAV</option>
                <option value="opus">Opus</option>
              </select>
              <p className="text-gray-500 text-xs mt-1">Audio output format</p>
            </div>
          </div>

          <div>
            <label htmlFor="language" className="label text-xs">
              Language
            </label>
            <select
              id="language"
              name="language"
              value={chatterboxSettings.language}
              onChange={handleChatterboxSettingChange}
              className="input"
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
              <option value="it">Italian</option>
              <option value="pt">Portuguese</option>
              <option value="pl">Polish</option>
              <option value="tr">Turkish</option>
              <option value="ru">Russian</option>
              <option value="nl">Dutch</option>
              <option value="cs">Czech</option>
              <option value="ar">Arabic</option>
              <option value="zh">Chinese</option>
              <option value="ja">Japanese</option>
              <option value="ko">Korean</option>
              <option value="hu">Hungarian</option>
            </select>
          </div>

          <h4 className="text-sm font-medium text-gray-300 pt-2">Playback Settings</h4>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="prefetch_depth" className="label text-xs">
                Prefetch Depth ({chatterboxSettings.prefetch_depth})
              </label>
              <input
                type="range"
                id="prefetch_depth"
                name="prefetch_depth"
                min="1"
                max="10"
                step="1"
                value={chatterboxSettings.prefetch_depth}
                onChange={handleChatterboxSettingChange}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
              <p className="text-gray-500 text-xs mt-1">Sentences to generate ahead (1-10)</p>
            </div>

            <div>
              <label htmlFor="chunk_size" className="label text-xs">
                Chunk Size ({chatterboxSettings.chunk_size})
              </label>
              <input
                type="range"
                id="chunk_size"
                name="chunk_size"
                min="1024"
                max="8192"
                step="512"
                value={chatterboxSettings.chunk_size}
                onChange={handleChatterboxSettingChange}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
              <p className="text-gray-500 text-xs mt-1">Streaming chunk size in bytes</p>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-3">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            name="is_default"
            checked={formData.is_default}
            onChange={handleChange}
            className="rounded border-gray-600 bg-gray-700 text-yellow-500 focus:ring-yellow-500"
          />
          <span className="text-gray-300">Default TTS provider</span>
        </label>
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
