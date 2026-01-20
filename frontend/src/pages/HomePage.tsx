import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, Users, Map, Plus, ArrowRight } from 'lucide-react'
import { api } from '../api/client'

export default function HomePage() {
  const { data: storiesData } = useQuery({
    queryKey: ['stories'],
    queryFn: () => api.getStories(),
  })

  const { data: charactersData } = useQuery({
    queryKey: ['characters'],
    queryFn: () => api.getCharacters(),
  })

  const { data: scenariosData } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => api.getScenarios(),
  })

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30000,
  })

  const recentStories = storiesData?.stories.slice(0, 3) || []
  const storyCount = storiesData?.total || 0
  const characterCount = charactersData?.total || 0
  const scenarioCount = scenariosData?.total || 0

  return (
    <div className="space-y-8">
      {/* Hero section */}
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-white mb-4">
          Welcome to Storyteller
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
          Create dynamic, episodic stories with AI-powered generation and
          audiobook-style narration.
        </p>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/stories/new"
          className="card hover:border-primary-500 transition-colors group"
        >
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-primary-600/20 text-primary-400 rounded-lg group-hover:bg-primary-600 group-hover:text-white transition-colors">
              <Plus className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">New Story</h3>
              <p className="text-gray-400 text-sm">
                Start a fresh narrative adventure
              </p>
            </div>
          </div>
        </Link>

        <Link
          to="/characters"
          className="card hover:border-primary-500 transition-colors group"
        >
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gray-700 text-gray-400 rounded-lg group-hover:bg-primary-600 group-hover:text-white transition-colors">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Characters</h3>
              <p className="text-gray-400 text-sm">
                {characterCount} character{characterCount !== 1 ? 's' : ''} created
              </p>
            </div>
          </div>
        </Link>

        <Link
          to="/scenarios"
          className="card hover:border-primary-500 transition-colors group"
        >
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gray-700 text-gray-400 rounded-lg group-hover:bg-primary-600 group-hover:text-white transition-colors">
              <Map className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Scenarios</h3>
              <p className="text-gray-400 text-sm">
                {scenarioCount} scenario{scenarioCount !== 1 ? 's' : ''} defined
              </p>
            </div>
          </div>
        </Link>
      </div>

      {/* Stats */}
      <div className="card">
        <h2 className="text-xl font-semibold text-white mb-4">Dashboard</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-900 rounded-lg">
            <div className="text-3xl font-bold text-primary-400">{storyCount}</div>
            <div className="text-gray-400 text-sm">Stories</div>
          </div>
          <div className="text-center p-4 bg-gray-900 rounded-lg">
            <div className="text-3xl font-bold text-primary-400">{characterCount}</div>
            <div className="text-gray-400 text-sm">Characters</div>
          </div>
          <div className="text-center p-4 bg-gray-900 rounded-lg">
            <div className="text-3xl font-bold text-primary-400">{scenarioCount}</div>
            <div className="text-gray-400 text-sm">Scenarios</div>
          </div>
          <div className="text-center p-4 bg-gray-900 rounded-lg">
            <div className="flex justify-center space-x-2">
              <span
                className={`w-3 h-3 rounded-full ${
                  health?.services?.ollama === 'connected'
                    ? 'bg-green-500'
                    : 'bg-red-500'
                }`}
              />
              <span
                className={`w-3 h-3 rounded-full ${
                  health?.services?.tts === 'connected'
                    ? 'bg-green-500'
                    : 'bg-yellow-500'
                }`}
              />
            </div>
            <div className="text-gray-400 text-sm mt-1">Services</div>
          </div>
        </div>
      </div>

      {/* Recent stories */}
      {recentStories.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Recent Stories</h2>
            <Link
              to="/stories"
              className="text-primary-400 hover:text-primary-300 flex items-center text-sm"
            >
              View all <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>
          <div className="space-y-3">
            {recentStories.map((story) => (
              <Link
                key={story.id}
                to={`/stories/${story.id}`}
                className="block p-4 bg-gray-900 rounded-lg hover:bg-gray-900/70 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <BookOpen className="w-5 h-5 text-primary-400" />
                    <div>
                      <h3 className="font-medium text-white">{story.title}</h3>
                      <p className="text-sm text-gray-400">
                        {story.episode_count} episode{story.episode_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500">
                    {new Date(story.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Getting started guide */}
      {storyCount === 0 && (
        <div className="card bg-gradient-to-r from-primary-900/50 to-gray-800">
          <h2 className="text-xl font-semibold text-white mb-4">Getting Started</h2>
          <ol className="space-y-3 text-gray-300">
            <li className="flex items-start space-x-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-600 text-white flex items-center justify-center text-sm">
                1
              </span>
              <span>
                <strong>Create Characters</strong> - Define the protagonists,
                antagonists, and supporting cast for your stories.
              </span>
            </li>
            <li className="flex items-start space-x-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-600 text-white flex items-center justify-center text-sm">
                2
              </span>
              <span>
                <strong>Define Scenarios</strong> - Set up the world, time period,
                genre, and rules for your narrative.
              </span>
            </li>
            <li className="flex items-start space-x-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-600 text-white flex items-center justify-center text-sm">
                3
              </span>
              <span>
                <strong>Start a Story</strong> - Combine characters and scenarios to
                begin generating episodes.
              </span>
            </li>
          </ol>
        </div>
      )}
    </div>
  )
}
