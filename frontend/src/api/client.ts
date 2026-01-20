const API_BASE = '/api'

export interface Character {
  id: number
  name: string
  description?: string
  personality?: string
  motivations?: string
  backstory?: string
  relationships?: string
  created_at: string
  updated_at: string
}

export interface Scenario {
  id: number
  name: string
  setting?: string
  time_period?: string
  genre?: string
  tone?: string
  premise?: string
  themes?: string
  world_rules?: string
  created_at: string
  updated_at: string
}

export interface StoryCharacter {
  id: number
  character_id: number
  role: 'protagonist' | 'supporting' | 'antagonist'
  character_name?: string
}

export interface Story {
  id: number
  title: string
  scenario_id: number
  status: 'draft' | 'in_progress' | 'completed' | 'abandoned'
  parent_story_id?: number
  fork_from_episode?: number
  created_at: string
  updated_at: string
  episode_count: number
  characters: StoryCharacter[]
}

export interface Episode {
  id: number
  story_id: number
  number: number
  title?: string
  content?: string
  summary?: string
  guidance?: string
  word_count: number
  audio_url?: string
  created_at: string
  updated_at: string
}

export interface Voice {
  id: string
  name: string
  language?: string
  gender?: string
}

export type ProviderType = 'ollama' | 'lmstudio' | 'koboldcpp'

export interface LLMProvider {
  id: number
  name: string
  provider_type: ProviderType
  base_url: string
  default_model?: string
  is_default: boolean
  is_alternate: boolean
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface LLMProviderCreate {
  name: string
  provider_type: ProviderType
  base_url: string
  default_model?: string
  is_default?: boolean
  is_alternate?: boolean
  enabled?: boolean
}

export interface LLMProviderUpdate {
  name?: string
  provider_type?: ProviderType
  base_url?: string
  default_model?: string
  is_default?: boolean
  is_alternate?: boolean
  enabled?: boolean
}

export interface ProviderTestResult {
  status: 'ok' | 'error'
  message?: string
  models?: string[]
}

export interface ProviderModelsResponse {
  models: Array<{ id?: string; name?: string }>
}

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || `Request failed: ${response.status}`)
    }

    return response.json()
  }

  // Characters
  async getCharacters(): Promise<{ characters: Character[]; total: number }> {
    return this.request('/characters')
  }

  async getCharacter(id: number): Promise<Character> {
    return this.request(`/characters/${id}`)
  }

  async createCharacter(data: Omit<Character, 'id' | 'created_at' | 'updated_at'>): Promise<Character> {
    return this.request('/characters', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateCharacter(id: number, data: Partial<Character>): Promise<Character> {
    return this.request(`/characters/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteCharacter(id: number): Promise<void> {
    await this.request(`/characters/${id}`, { method: 'DELETE' })
  }

  // Scenarios
  async getScenarios(): Promise<{ scenarios: Scenario[]; total: number }> {
    return this.request('/scenarios')
  }

  async getScenario(id: number): Promise<Scenario> {
    return this.request(`/scenarios/${id}`)
  }

  async createScenario(data: Omit<Scenario, 'id' | 'created_at' | 'updated_at'>): Promise<Scenario> {
    return this.request('/scenarios', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateScenario(id: number, data: Partial<Scenario>): Promise<Scenario> {
    return this.request(`/scenarios/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteScenario(id: number): Promise<void> {
    await this.request(`/scenarios/${id}`, { method: 'DELETE' })
  }

  // Stories
  async getStories(): Promise<{ stories: Story[]; total: number }> {
    return this.request('/stories')
  }

  async getStory(id: number): Promise<Story> {
    return this.request(`/stories/${id}`)
  }

  async createStory(data: {
    title: string
    scenario_id: number
    characters: Array<{ character_id: number; role: string }>
  }): Promise<Story> {
    return this.request('/stories', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateStory(id: number, data: Partial<Story>): Promise<Story> {
    return this.request(`/stories/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteStory(id: number): Promise<void> {
    await this.request(`/stories/${id}`, { method: 'DELETE' })
  }

  async forkStory(id: number, fromEpisode: number, newTitle: string): Promise<Story> {
    return this.request(`/stories/${id}/fork`, {
      method: 'POST',
      body: JSON.stringify({ from_episode: fromEpisode, new_title: newTitle }),
    })
  }

  // Episodes
  async getEpisodes(storyId: number): Promise<{ episodes: Episode[]; total: number }> {
    return this.request(`/stories/${storyId}/episodes`)
  }

  async getEpisode(storyId: number, number: number): Promise<Episode> {
    return this.request(`/stories/${storyId}/episodes/${number}`)
  }

  async updateEpisode(storyId: number, number: number, data: Partial<Episode>): Promise<Episode> {
    return this.request(`/stories/${storyId}/episodes/${number}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteEpisode(storyId: number, number: number): Promise<void> {
    await this.request(`/stories/${storyId}/episodes/${number}`, { method: 'DELETE' })
  }

  // TTS
  async generateTTS(text: string, voice?: string): Promise<{ audio_url: string }> {
    return this.request('/tts/generate', {
      method: 'POST',
      body: JSON.stringify({ text, voice }),
    })
  }

  async getVoices(): Promise<Voice[]> {
    return this.request('/tts/voices')
  }

  // LLM Providers
  async getProviders(): Promise<{ providers: LLMProvider[]; total: number }> {
    return this.request('/settings/providers')
  }

  async getProvider(id: number): Promise<LLMProvider> {
    return this.request(`/settings/providers/${id}`)
  }

  async createProvider(data: LLMProviderCreate): Promise<LLMProvider> {
    return this.request('/settings/providers', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateProvider(id: number, data: LLMProviderUpdate): Promise<LLMProvider> {
    return this.request(`/settings/providers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteProvider(id: number): Promise<void> {
    await this.request(`/settings/providers/${id}`, { method: 'DELETE' })
  }

  async testProvider(id: number): Promise<ProviderTestResult> {
    return this.request(`/settings/providers/${id}/test`, { method: 'POST' })
  }

  async getProviderModels(id: number): Promise<ProviderModelsResponse> {
    return this.request(`/settings/providers/${id}/models`)
  }

  async testProviderUrl(baseUrl: string): Promise<ProviderTestResult> {
    return this.request(`/settings/providers/test-url?base_url=${encodeURIComponent(baseUrl)}`, {
      method: 'POST',
    })
  }

  // Health
  async getHealth(): Promise<{ status: string; services: Record<string, string> }> {
    return this.request('/health')
  }
}

export const api = new ApiClient()
