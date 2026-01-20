import { Link } from 'react-router-dom'
import { BookOpen, Edit, Trash2, GitBranch } from 'lucide-react'
import type { Story } from '../../api/client'

interface StoryCardProps {
  story: Story
  onEdit: (story: Story) => void
  onDelete: (story: Story) => void
}

const statusColors = {
  draft: 'bg-gray-600 text-gray-200',
  in_progress: 'bg-primary-600 text-white',
  completed: 'bg-green-600 text-white',
  abandoned: 'bg-red-600 text-white',
}

const statusLabels = {
  draft: 'Draft',
  in_progress: 'In Progress',
  completed: 'Completed',
  abandoned: 'Abandoned',
}

export default function StoryCard({ story, onEdit, onDelete }: StoryCardProps) {
  return (
    <div className="card">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-semibold text-white">{story.title}</h3>
          {story.parent_story_id && (
            <div className="flex items-center text-xs text-gray-500 mt-1">
              <GitBranch className="w-3 h-3 mr-1" />
              Forked from episode {story.fork_from_episode}
            </div>
          )}
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => onEdit(story)}
            className="p-1.5 text-gray-400 hover:text-primary-400 transition-colors"
            title="Edit"
          >
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(story)}
            className="p-1.5 text-gray-400 hover:text-red-400 transition-colors"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-4">
        <span
          className={`px-2 py-1 rounded text-xs ${statusColors[story.status]}`}
        >
          {statusLabels[story.status]}
        </span>
        <span className="text-gray-400 text-sm">
          {story.episode_count} episode{story.episode_count !== 1 ? 's' : ''}
        </span>
      </div>

      {story.characters.length > 0 && (
        <div className="mb-4">
          <span className="text-xs text-gray-500 uppercase">Characters</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {story.characters.map((char) => (
              <span
                key={char.id}
                className="px-2 py-0.5 bg-gray-700 text-gray-300 rounded text-xs"
              >
                {char.character_name}
                <span className="text-gray-500 ml-1">({char.role})</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <Link
        to={`/stories/${story.id}`}
        className="btn btn-primary w-full flex items-center justify-center"
      >
        <BookOpen className="w-4 h-4 mr-2" />
        {story.episode_count > 0 ? 'Continue Reading' : 'Start Writing'}
      </Link>
    </div>
  )
}
