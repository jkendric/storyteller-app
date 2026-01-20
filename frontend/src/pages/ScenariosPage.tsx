import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { api, Scenario } from '../api/client'
import ScenarioCard from '../components/scenarios/ScenarioCard'
import ScenarioForm from '../components/scenarios/ScenarioForm'
import Modal from '../components/ui/Modal'

export default function ScenariosPage() {
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingScenario, setEditingScenario] = useState<Scenario | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => api.getScenarios(),
  })

  const createMutation = useMutation({
    mutationFn: (data: Partial<Scenario>) => api.createScenario(data as any),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scenarios'] })
      setIsModalOpen(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Scenario> }) =>
      api.updateScenario(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scenarios'] })
      setEditingScenario(null)
      setIsModalOpen(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteScenario(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scenarios'] })
    },
  })

  const handleCreate = () => {
    setEditingScenario(null)
    setIsModalOpen(true)
  }

  const handleEdit = (scenario: Scenario) => {
    setEditingScenario(scenario)
    setIsModalOpen(true)
  }

  const handleDelete = (scenario: Scenario) => {
    if (confirm(`Delete scenario "${scenario.name}"?`)) {
      deleteMutation.mutate(scenario.id)
    }
  }

  const handleSubmit = (data: Partial<Scenario>) => {
    if (editingScenario) {
      updateMutation.mutate({ id: editingScenario.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingScenario(null)
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
          <h1 className="text-2xl font-bold text-white">Scenarios</h1>
          <p className="text-gray-400">
            Define settings, genres, and world-building for your stories
          </p>
        </div>
        <button onClick={handleCreate} className="btn btn-primary">
          <Plus className="w-4 h-4 mr-2" />
          New Scenario
        </button>
      </div>

      {data?.scenarios.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-400 mb-4">No scenarios yet</p>
          <button onClick={handleCreate} className="btn btn-primary">
            Create your first scenario
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data?.scenarios.map((scenario) => (
            <ScenarioCard
              key={scenario.id}
              scenario={scenario}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingScenario ? 'Edit Scenario' : 'New Scenario'}
      >
        <ScenarioForm
          scenario={editingScenario || undefined}
          onSubmit={handleSubmit}
          onCancel={handleCloseModal}
        />
      </Modal>
    </div>
  )
}
