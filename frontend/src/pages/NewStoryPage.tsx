import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Plus, X } from 'lucide-react'
import { api, Character, Scenario } from '../api/client'

interface SelectedCharacter {
  character: Character
  role: 'protagonist' | 'supporting' | 'antagonist'
}

export default function NewStoryPage() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null)
  const [selectedCharacters, setSelectedCharacters] = useState<SelectedCharacter[]>([])
  const [showCharacterPicker, setShowCharacterPicker] = useState(false)

  const { data: charactersData } = useQuery({
    queryKey: ['characters'],
    queryFn: () => api.getCharacters(),
  })

  const { data: scenariosData } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => api.getScenarios(),
  })

  const createMutation = useMutation({
    mutationFn: (data: {
      title: string
      scenario_id: number
      characters: Array<{ character_id: number; role: string }>
    }) => api.createStory(data),
    onSuccess: (story) => {
      navigate(`/stories/${story.id}`)
    },
    onError: (error) => {
      console.error('Failed to create story:', error)
      alert(`Failed to create story: ${error.message}`)
    },
  })

  const handleAddCharacter = (character: Character, role: SelectedCharacter['role']) => {
    if (!selectedCharacters.find((sc) => sc.character.id === character.id)) {
      setSelectedCharacters([...selectedCharacters, { character, role }])
    }
    setShowCharacterPicker(false)
  }

  const handleRemoveCharacter = (characterId: number) => {
    setSelectedCharacters(
      selectedCharacters.filter((sc) => sc.character.id !== characterId)
    )
  }

  const handleChangeRole = (characterId: number, role: SelectedCharacter['role']) => {
    setSelectedCharacters(
      selectedCharacters.map((sc) =>
        sc.character.id === characterId ? { ...sc, role } : sc
      )
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !selectedScenario) return

    createMutation.mutate({
      title: title.trim(),
      scenario_id: selectedScenario.id,
      characters: selectedCharacters.map((sc) => ({
        character_id: sc.character.id,
        role: sc.role,
      })),
    })
  }

  const availableCharacters =
    charactersData?.characters.filter(
      (c) => !selectedCharacters.find((sc) => sc.character.id === c.id)
    ) || []

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Create New Story</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Title */}
        <div className="card">
          <label htmlFor="title" className="label">
            Story Title *
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input"
            placeholder="Enter a title for your story"
            required
          />
        </div>

        {/* Scenario selection */}
        <div className="card">
          <label className="label">Select Scenario *</label>
          {scenariosData?.scenarios.length === 0 ? (
            <p className="text-gray-400">
              No scenarios available.{' '}
              <a href="/scenarios" className="text-primary-400 hover:underline">
                Create one first.
              </a>
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {scenariosData?.scenarios.map((scenario) => (
                <button
                  key={scenario.id}
                  type="button"
                  onClick={() => setSelectedScenario(scenario)}
                  className={`p-4 rounded-lg border-2 text-left transition-colors ${
                    selectedScenario?.id === scenario.id
                      ? 'border-primary-500 bg-primary-900/20'
                      : 'border-gray-700 hover:border-gray-600'
                  }`}
                >
                  <h3 className="font-semibold text-white">{scenario.name}</h3>
                  <div className="flex gap-2 mt-1">
                    {scenario.genre && (
                      <span className="text-xs text-gray-400">{scenario.genre}</span>
                    )}
                    {scenario.tone && (
                      <span className="text-xs text-gray-500">• {scenario.tone}</span>
                    )}
                  </div>
                  {scenario.premise && (
                    <p className="text-sm text-gray-400 mt-2 line-clamp-2">
                      {scenario.premise}
                    </p>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Character selection */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <label className="label mb-0">Characters</label>
            <button
              type="button"
              onClick={() => setShowCharacterPicker(true)}
              className="btn btn-secondary text-sm"
              disabled={availableCharacters.length === 0}
            >
              <Plus className="w-4 h-4 mr-1" />
              Add Character
            </button>
          </div>

          {selectedCharacters.length === 0 ? (
            <p className="text-gray-400 text-sm">
              No characters added yet. Add characters to populate your story.
            </p>
          ) : (
            <div className="space-y-2">
              {selectedCharacters.map(({ character, role }) => (
                <div
                  key={character.id}
                  className="flex items-center justify-between p-3 bg-gray-900 rounded-lg"
                >
                  <span className="text-white">{character.name}</span>
                  <div className="flex items-center space-x-2">
                    <select
                      value={role}
                      onChange={(e) =>
                        handleChangeRole(
                          character.id,
                          e.target.value as SelectedCharacter['role']
                        )
                      }
                      className="bg-gray-700 text-gray-300 rounded px-2 py-1 text-sm"
                    >
                      <option value="protagonist">Protagonist</option>
                      <option value="supporting">Supporting</option>
                      <option value="antagonist">Antagonist</option>
                    </select>
                    <button
                      type="button"
                      onClick={() => handleRemoveCharacter(character.id)}
                      className="text-gray-400 hover:text-red-400"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Submit */}
        <div className="space-y-3">
          {(!title.trim() || !selectedScenario) && (
            <p className="text-yellow-500 text-sm text-right">
              {!title.trim() && !selectedScenario
                ? '⚠️ Please enter a title and select a scenario'
                : !title.trim()
                ? '⚠️ Please enter a story title'
                : '⚠️ Please select a scenario'}
            </p>
          )}
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => navigate('/stories')}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!title.trim() || !selectedScenario || createMutation.isPending}
              className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Story'}
            </button>
          </div>
        </div>
      </form>

      {/* Character picker modal */}
      {showCharacterPicker && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="card max-w-md w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Add Character</h3>
              <button
                onClick={() => setShowCharacterPicker(false)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {availableCharacters.length === 0 ? (
              <p className="text-gray-400">All characters have been added.</p>
            ) : (
              <div className="space-y-2">
                {availableCharacters.map((character) => (
                  <div
                    key={character.id}
                    className="p-3 bg-gray-900 rounded-lg"
                  >
                    <h4 className="font-medium text-white">{character.name}</h4>
                    {character.description && (
                      <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                        {character.description}
                      </p>
                    )}
                    <div className="flex gap-2 mt-2">
                      <button
                        onClick={() => handleAddCharacter(character, 'protagonist')}
                        className="text-xs px-2 py-1 bg-primary-600 text-white rounded hover:bg-primary-700"
                      >
                        Protagonist
                      </button>
                      <button
                        onClick={() => handleAddCharacter(character, 'supporting')}
                        className="text-xs px-2 py-1 bg-gray-600 text-white rounded hover:bg-gray-500"
                      >
                        Supporting
                      </button>
                      <button
                        onClick={() => handleAddCharacter(character, 'antagonist')}
                        className="text-xs px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                      >
                        Antagonist
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
