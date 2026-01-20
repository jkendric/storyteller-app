import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { api, Character } from '../api/client'
import CharacterCard from '../components/characters/CharacterCard'
import CharacterForm from '../components/characters/CharacterForm'
import Modal from '../components/ui/Modal'

export default function CharactersPage() {
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingCharacter, setEditingCharacter] = useState<Character | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['characters'],
    queryFn: () => api.getCharacters(),
  })

  const createMutation = useMutation({
    mutationFn: (data: Partial<Character>) => api.createCharacter(data as any),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['characters'] })
      setIsModalOpen(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Character> }) =>
      api.updateCharacter(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['characters'] })
      setEditingCharacter(null)
      setIsModalOpen(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteCharacter(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['characters'] })
    },
  })

  const handleCreate = () => {
    setEditingCharacter(null)
    setIsModalOpen(true)
  }

  const handleEdit = (character: Character) => {
    setEditingCharacter(character)
    setIsModalOpen(true)
  }

  const handleDelete = (character: Character) => {
    if (confirm(`Delete character "${character.name}"?`)) {
      deleteMutation.mutate(character.id)
    }
  }

  const handleSubmit = (data: Partial<Character>) => {
    if (editingCharacter) {
      updateMutation.mutate({ id: editingCharacter.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingCharacter(null)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Characters</h1>
          <p className="text-gray-400">
            Create and manage characters for your stories
          </p>
        </div>
        <button onClick={handleCreate} className="btn btn-primary">
          <Plus className="w-4 h-4 mr-2" />
          New Character
        </button>
      </div>

      {data?.characters.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-400 mb-4">No characters yet</p>
          <button onClick={handleCreate} className="btn btn-primary">
            Create your first character
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data?.characters.map((character) => (
            <CharacterCard
              key={character.id}
              character={character}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingCharacter ? 'Edit Character' : 'New Character'}
      >
        <CharacterForm
          character={editingCharacter || undefined}
          onSubmit={handleSubmit}
          onCancel={handleCloseModal}
        />
      </Modal>
    </div>
  )
}
