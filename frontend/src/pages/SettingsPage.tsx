import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Settings } from 'lucide-react'
import { api, LLMProvider, LLMProviderCreate } from '../api/client'
import ProviderCard from '../components/settings/ProviderCard'
import ProviderForm from '../components/settings/ProviderForm'
import Modal from '../components/ui/Modal'

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingProvider, setEditingProvider] = useState<LLMProvider | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['providers'],
    queryFn: () => api.getProviders(),
  })

  const createMutation = useMutation({
    mutationFn: (data: LLMProviderCreate) => api.createProvider(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['providers'] })
      setIsModalOpen(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<LLMProvider> }) =>
      api.updateProvider(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['providers'] })
      setEditingProvider(null)
      setIsModalOpen(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteProvider(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['providers'] })
    },
  })

  const handleCreate = () => {
    setEditingProvider(null)
    setIsModalOpen(true)
  }

  const handleEdit = (provider: LLMProvider) => {
    setEditingProvider(provider)
    setIsModalOpen(true)
  }

  const handleDelete = (provider: LLMProvider) => {
    if (confirm(`Delete provider "${provider.name}"?`)) {
      deleteMutation.mutate(provider.id)
    }
  }

  const handleTest = async (provider: LLMProvider) => {
    return api.testProvider(provider.id)
  }

  const handleSetDefault = (provider: LLMProvider) => {
    updateMutation.mutate({
      id: provider.id,
      data: { is_default: true },
    })
  }

  const handleSetAlternate = (provider: LLMProvider) => {
    updateMutation.mutate({
      id: provider.id,
      data: { is_alternate: true },
    })
  }

  const handleSubmit = (data: LLMProviderCreate) => {
    if (editingProvider) {
      updateMutation.mutate({ id: editingProvider.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingProvider(null)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
      </div>
    )
  }

  const defaultProvider = data?.providers.find((p) => p.is_default)
  const alternateProvider = data?.providers.find((p) => p.is_alternate)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Settings className="w-6 h-6" />
            Settings
          </h1>
          <p className="text-gray-400">
            Configure LLM providers and application settings
          </p>
        </div>
      </div>

      {/* Provider Status Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card bg-gradient-to-br from-yellow-900/20 to-gray-800">
          <h3 className="text-sm font-medium text-yellow-400 mb-1">Default Provider</h3>
          {defaultProvider ? (
            <p className="text-white">{defaultProvider.name}</p>
          ) : (
            <p className="text-gray-500 italic">Not configured</p>
          )}
        </div>
        <div className="card bg-gradient-to-br from-purple-900/20 to-gray-800">
          <h3 className="text-sm font-medium text-purple-400 mb-1">Alternate Provider</h3>
          {alternateProvider ? (
            <p className="text-white">{alternateProvider.name}</p>
          ) : (
            <p className="text-gray-500 italic">Not configured</p>
          )}
        </div>
      </div>

      {/* LLM Providers Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">LLM Providers</h2>
          <button onClick={handleCreate} className="btn btn-primary">
            <Plus className="w-4 h-4 mr-2" />
            Add Provider
          </button>
        </div>

        {data?.providers.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-gray-400 mb-4">No LLM providers configured</p>
            <button onClick={handleCreate} className="btn btn-primary">
              Add your first provider
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data?.providers.map((provider) => (
              <ProviderCard
                key={provider.id}
                provider={provider}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onTest={handleTest}
                onSetDefault={handleSetDefault}
                onSetAlternate={handleSetAlternate}
              />
            ))}
          </div>
        )}
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingProvider ? 'Edit Provider' : 'New Provider'}
      >
        <ProviderForm
          provider={editingProvider || undefined}
          onSubmit={handleSubmit}
          onCancel={handleCloseModal}
        />
      </Modal>
    </div>
  )
}
