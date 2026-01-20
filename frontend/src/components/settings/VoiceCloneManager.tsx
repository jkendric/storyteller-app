import { useState, useEffect, useRef } from 'react'
import { Upload, Trash2, Play, Pause, X, Loader2, AlertCircle } from 'lucide-react'
import { api, type TTSProvider, type VoiceClone } from '../../api/client'

interface VoiceCloneManagerProps {
  provider: TTSProvider
  onClose: () => void
}

export default function VoiceCloneManager({ provider, onClose }: VoiceCloneManagerProps) {
  const [voiceClones, setVoiceClones] = useState<VoiceClone[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Upload form state
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [newCloneName, setNewCloneName] = useState('')
  const [newCloneDescription, setNewCloneDescription] = useState('')
  const [newCloneLanguage, setNewCloneLanguage] = useState('en')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  // Audio playback state
  const [playingCloneId, setPlayingCloneId] = useState<number | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    loadVoiceClones()
    return () => {
      // Cleanup audio on unmount
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
    }
  }, [provider.id])

  const loadVoiceClones = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await api.getVoiceClones(provider.id)
      setVoiceClones(response.voice_clones)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load voice clones')
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file type
      if (!file.type.startsWith('audio/')) {
        setUploadError('Please select an audio file (WAV or MP3)')
        return
      }
      setSelectedFile(file)
      setUploadError(null)
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile || !newCloneName) return

    setIsUploading(true)
    setUploadError(null)

    try {
      await api.createVoiceClone(
        provider.id,
        {
          name: newCloneName,
          description: newCloneDescription || undefined,
          language: newCloneLanguage,
        },
        selectedFile
      )

      // Reset form
      setNewCloneName('')
      setNewCloneDescription('')
      setNewCloneLanguage('en')
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      // Reload list
      await loadVoiceClones()
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDelete = async (clone: VoiceClone) => {
    if (!confirm(`Delete voice clone "${clone.name}"?`)) return

    try {
      await api.deleteVoiceClone(provider.id, clone.id)
      setVoiceClones((prev) => prev.filter((c) => c.id !== clone.id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete voice clone')
    }
  }

  const handlePlayPause = (clone: VoiceClone) => {
    if (playingCloneId === clone.id) {
      // Stop playing
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
      setPlayingCloneId(null)
    } else {
      // Start playing
      if (audioRef.current) {
        audioRef.current.pause()
      }
      const audio = new Audio(api.getVoiceCloneAudioUrl(provider.id, clone.id))
      audio.onended = () => setPlayingCloneId(null)
      audio.onerror = () => {
        setPlayingCloneId(null)
        setError('Failed to play audio')
      }
      audio.play()
      audioRef.current = audio
      setPlayingCloneId(clone.id)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-gray-700">
          <div>
            <h2 className="text-xl font-bold text-white">Voice Clones</h2>
            <p className="text-sm text-gray-400">{provider.name}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Upload Form */}
          <div className="bg-gray-700/50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-white mb-4">Upload Voice Sample</h3>
            <form onSubmit={handleUpload} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="clone-name" className="label">
                    Name *
                  </label>
                  <input
                    type="text"
                    id="clone-name"
                    value={newCloneName}
                    onChange={(e) => setNewCloneName(e.target.value)}
                    className="input"
                    placeholder="e.g., My Custom Voice"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="clone-language" className="label">
                    Language
                  </label>
                  <select
                    id="clone-language"
                    value={newCloneLanguage}
                    onChange={(e) => setNewCloneLanguage(e.target.value)}
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
                    <option value="zh-cn">Chinese</option>
                    <option value="ja">Japanese</option>
                    <option value="ko">Korean</option>
                  </select>
                </div>
              </div>

              <div>
                <label htmlFor="clone-description" className="label">
                  Description
                </label>
                <input
                  type="text"
                  id="clone-description"
                  value={newCloneDescription}
                  onChange={(e) => setNewCloneDescription(e.target.value)}
                  className="input"
                  placeholder="Optional description"
                />
              </div>

              <div>
                <label className="label">Audio File *</label>
                <div className="flex items-center gap-3">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="audio/wav,audio/mpeg,audio/mp3,.wav,.mp3"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="btn btn-secondary flex items-center gap-2"
                  >
                    <Upload className="w-4 h-4" />
                    Choose File
                  </button>
                  {selectedFile && (
                    <span className="text-gray-300 text-sm">{selectedFile.name}</span>
                  )}
                </div>
                <p className="text-gray-500 text-xs mt-1">
                  WAV or MP3, minimum 6 seconds for XTTS voice cloning
                </p>
              </div>

              {uploadError && (
                <div className="flex items-center gap-2 text-red-400 text-sm">
                  <AlertCircle className="w-4 h-4" />
                  {uploadError}
                </div>
              )}

              <button
                type="submit"
                disabled={isUploading || !selectedFile || !newCloneName}
                className="btn btn-primary w-full flex items-center justify-center gap-2"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Upload Voice Clone
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Voice Clones List */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">
              Existing Voice Clones ({voiceClones.length})
            </h3>

            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : error ? (
              <div className="flex items-center gap-2 text-red-400 py-4">
                <AlertCircle className="w-5 h-5" />
                {error}
              </div>
            ) : voiceClones.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                No voice clones yet. Upload a voice sample to get started.
              </p>
            ) : (
              <div className="space-y-3">
                {voiceClones.map((clone) => (
                  <div
                    key={clone.id}
                    className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-white">{clone.name}</h4>
                        <span className="px-2 py-0.5 bg-gray-600 text-gray-300 rounded text-xs">
                          {clone.language}
                        </span>
                        {clone.audio_duration && (
                          <span className="text-gray-500 text-xs">
                            {clone.audio_duration}s
                          </span>
                        )}
                      </div>
                      {clone.description && (
                        <p className="text-sm text-gray-400 mt-1">{clone.description}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handlePlayPause(clone)}
                        className="p-2 text-gray-400 hover:text-blue-400 transition-colors"
                        title={playingCloneId === clone.id ? 'Pause' : 'Play sample'}
                      >
                        {playingCloneId === clone.id ? (
                          <Pause className="w-4 h-4" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        onClick={() => handleDelete(clone)}
                        className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
