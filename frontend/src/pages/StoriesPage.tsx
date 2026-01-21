import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { api, Story } from '../api/client'
import StoryCard from '../components/stories/StoryCard'
import Modal from '../components/ui/Modal'

export default function StoriesPage() {
  const queryClient = useQueryClient()
  const [editingStory, setEditingStory] = useState<Story | null>(null)
  const [editTitle, setEditTitle] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['stories'],
    queryFn: () => api.getStories(),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Story> }) =>
      api.updateStory(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stories'] })
      setEditingStory(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteStory(id),
    onMutate: async (deletedId) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['stories'] })
      // Snapshot the previous value
      const previousStories = queryClient.getQueryData(['stories'])
      // Optimistically remove the story
      queryClient.setQueryData(['stories'], (old: { stories: Story[]; total: number } | undefined) => {
        if (!old) return old
        return {
          ...old,
          stories: old.stories.filter((s) => s.id !== deletedId),
          total: old.total - 1,
        }
      })
      return { previousStories }
    },
    onError: (_err, _deletedId, context) => {
      // Rollback on error
      if (context?.previousStories) {
        queryClient.setQueryData(['stories'], context.previousStories)
      }
    },
    onSettled: () => {
      // Refetch to ensure sync with server
      queryClient.invalidateQueries({ queryKey: ['stories'] })
    },
  })

  const handleEdit = (story: Story) => {
    setEditingStory(story)
    setEditTitle(story.title)
  }

  const handleDelete = (story: Story) => {
    if (confirm(`Delete story "${story.title}" and all its episodes?`)) {
      deleteMutation.mutate(story.id)
    }
  }

  const handleSaveEdit = () => {
    if (editingStory && editTitle.trim()) {
      updateMutation.mutate({
        id: editingStory.id,
        data: { title: editTitle.trim() },
      })
    }
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
          <h1 className="text-2xl font-bold text-white">Stories</h1>
          <p className="text-gray-400">
            Your episodic narratives and story forks
          </p>
        </div>
        <Link to="/stories/new" className="btn btn-primary">
          <Plus className="w-4 h-4 mr-2" />
          New Story
        </Link>
      </div>

      {data?.stories.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-400 mb-4">No stories yet</p>
          <Link to="/stories/new" className="btn btn-primary">
            Create your first story
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data?.stories.map((story) => (
            <StoryCard
              key={story.id}
              story={story}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Edit title modal */}
      <Modal
        isOpen={!!editingStory}
        onClose={() => setEditingStory(null)}
        title="Edit Story"
      >
        <div className="space-y-4">
          <div>
            <label htmlFor="title" className="label">
              Title
            </label>
            <input
              type="text"
              id="title"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="input"
            />
          </div>
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => setEditingStory(null)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button onClick={handleSaveEdit} className="btn btn-primary">
              Save
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
