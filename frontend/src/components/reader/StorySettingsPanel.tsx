import { useState, useEffect, useCallback } from 'react'
import { ChevronDown, ChevronRight, RotateCcw, Settings } from 'lucide-react'
import { api, Story, TargetWordPreset, WritingStyle, MoodSetting, PacingSetting } from '../../api/client'

interface StorySettingsPanelProps {
  story: Story
  onSettingsUpdate: (story: Story) => void
  isDisabled?: boolean
}

// Configuration for settings options
const LENGTH_OPTIONS: { value: TargetWordPreset; label: string; words: number }[] = [
  { value: 'short', label: 'Short', words: 750 },
  { value: 'medium', label: 'Medium', words: 1250 },
  { value: 'long', label: 'Long', words: 2000 },
  { value: 'epic', label: 'Epic', words: 3000 },
]

const STYLE_OPTIONS: { value: WritingStyle; label: string }[] = [
  { value: 'descriptive', label: 'Descriptive' },
  { value: 'action', label: 'Action-focused' },
  { value: 'dialogue', label: 'Dialogue-heavy' },
  { value: 'balanced', label: 'Balanced' },
]

const MOOD_OPTIONS: { value: MoodSetting; label: string }[] = [
  { value: 'light', label: 'Light' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'intense', label: 'Intense' },
  { value: 'dark', label: 'Dark' },
]

const PACING_OPTIONS: { value: PacingSetting; label: string }[] = [
  { value: 'slow', label: 'Slow' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'fast', label: 'Fast' },
]

// Default values
const DEFAULTS = {
  target_word_preset: 'medium' as TargetWordPreset,
  temperature: 0.7,
  writing_style: 'balanced' as WritingStyle,
  mood: 'moderate' as MoodSetting,
  pacing: 'moderate' as PacingSetting,
}

export default function StorySettingsPanel({
  story,
  onSettingsUpdate,
  isDisabled = false,
}: StorySettingsPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // Local state for settings (for immediate UI feedback)
  const [settings, setSettings] = useState({
    target_word_preset: story.target_word_preset,
    temperature: story.temperature,
    writing_style: story.writing_style,
    mood: story.mood,
    pacing: story.pacing,
  })

  // Sync local state when story changes (e.g., after refresh)
  useEffect(() => {
    setSettings({
      target_word_preset: story.target_word_preset,
      temperature: story.temperature,
      writing_style: story.writing_style,
      mood: story.mood,
      pacing: story.pacing,
    })
  }, [story.id, story.target_word_preset, story.temperature, story.writing_style, story.mood, story.pacing])

  // Debounced save function
  const saveSettings = useCallback(async (newSettings: typeof settings) => {
    setIsSaving(true)
    try {
      const updatedStory = await api.updateStory(story.id, newSettings)
      onSettingsUpdate(updatedStory)
    } catch (error) {
      console.error('Failed to save settings:', error)
      // Revert to previous settings on error
      setSettings({
        target_word_preset: story.target_word_preset,
        temperature: story.temperature,
        writing_style: story.writing_style,
        mood: story.mood,
        pacing: story.pacing,
      })
    } finally {
      setIsSaving(false)
    }
  }, [story.id, story.target_word_preset, story.temperature, story.writing_style, story.mood, story.pacing, onSettingsUpdate])

  // Update handler with debounce
  const handleSettingChange = useCallback(<K extends keyof typeof settings>(
    key: K,
    value: typeof settings[K]
  ) => {
    const newSettings = { ...settings, [key]: value }
    setSettings(newSettings)
    // Save immediately (could add debounce for slider)
    saveSettings(newSettings)
  }, [settings, saveSettings])

  // Reset to defaults
  const handleReset = useCallback(async () => {
    setSettings(DEFAULTS)
    await saveSettings(DEFAULTS)
  }, [saveSettings])

  // Check if any setting differs from default
  const hasChanges =
    settings.target_word_preset !== DEFAULTS.target_word_preset ||
    settings.temperature !== DEFAULTS.temperature ||
    settings.writing_style !== DEFAULTS.writing_style ||
    settings.mood !== DEFAULTS.mood ||
    settings.pacing !== DEFAULTS.pacing

  return (
    <div className="mt-6 border-t border-gray-700 pt-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-sm text-gray-300 hover:text-white transition-colors"
          disabled={isDisabled}
        >
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
          <Settings className="w-4 h-4" />
          <span className="font-medium">Story Settings</span>
          {isSaving && <span className="text-xs text-gray-500">(saving...)</span>}
        </button>

        {isExpanded && hasChanges && (
          <button
            onClick={handleReset}
            disabled={isDisabled || isSaving}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors disabled:opacity-50"
            title="Reset to defaults"
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </button>
        )}
      </div>

      {/* Settings Panel */}
      {isExpanded && (
        <div className="mt-4 space-y-4 bg-gray-800/50 rounded-lg p-4">
          {/* Length Preset */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Episode Length
            </label>
            <select
              value={settings.target_word_preset}
              onChange={(e) => handleSettingChange('target_word_preset', e.target.value as TargetWordPreset)}
              disabled={isDisabled || isSaving}
              className="input text-sm py-1.5"
            >
              {LENGTH_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label} (~{opt.words} words)
                </option>
              ))}
            </select>
          </div>

          {/* Creativity/Temperature Slider */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Creativity
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="0.5"
                max="1.0"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => handleSettingChange('temperature', parseFloat(e.target.value))}
                disabled={isDisabled || isSaving}
                className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
              />
              <span className="text-sm text-gray-300 w-8 text-right font-mono">
                {settings.temperature.toFixed(1)}
              </span>
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Focused</span>
              <span>Creative</span>
            </div>
          </div>

          {/* Writing Style */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Writing Style
            </label>
            <select
              value={settings.writing_style}
              onChange={(e) => handleSettingChange('writing_style', e.target.value as WritingStyle)}
              disabled={isDisabled || isSaving}
              className="input text-sm py-1.5"
            >
              {STYLE_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Mood */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Mood
            </label>
            <select
              value={settings.mood}
              onChange={(e) => handleSettingChange('mood', e.target.value as MoodSetting)}
              disabled={isDisabled || isSaving}
              className="input text-sm py-1.5"
            >
              {MOOD_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Pacing */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Pacing
            </label>
            <select
              value={settings.pacing}
              onChange={(e) => handleSettingChange('pacing', e.target.value as PacingSetting)}
              disabled={isDisabled || isSaving}
              className="input text-sm py-1.5"
            >
              {PACING_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  )
}
