import { useState } from 'react'
import type { Character } from '../../api/client'

interface CharacterFormProps {
  character?: Character
  onSubmit: (data: Partial<Character>) => void
  onCancel: () => void
}

export default function CharacterForm({
  character,
  onSubmit,
  onCancel,
}: CharacterFormProps) {
  const [formData, setFormData] = useState({
    name: character?.name || '',
    description: character?.description || '',
    personality: character?.personality || '',
    motivations: character?.motivations || '',
    backstory: character?.backstory || '',
    relationships: character?.relationships || '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="name" className="label">
          Name *
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          className="input"
          required
        />
      </div>

      <div>
        <label htmlFor="description" className="label">
          Description
        </label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          className="textarea"
          rows={3}
          placeholder="Physical appearance, mannerisms, etc."
        />
      </div>

      <div>
        <label htmlFor="personality" className="label">
          Personality
        </label>
        <textarea
          id="personality"
          name="personality"
          value={formData.personality}
          onChange={handleChange}
          className="textarea"
          rows={3}
          placeholder="Character traits, temperament, quirks..."
        />
      </div>

      <div>
        <label htmlFor="motivations" className="label">
          Motivations
        </label>
        <textarea
          id="motivations"
          name="motivations"
          value={formData.motivations}
          onChange={handleChange}
          className="textarea"
          rows={2}
          placeholder="What drives this character?"
        />
      </div>

      <div>
        <label htmlFor="backstory" className="label">
          Backstory
        </label>
        <textarea
          id="backstory"
          name="backstory"
          value={formData.backstory}
          onChange={handleChange}
          className="textarea"
          rows={4}
          placeholder="Character's history and background..."
        />
      </div>

      <div>
        <label htmlFor="relationships" className="label">
          Relationships
        </label>
        <textarea
          id="relationships"
          name="relationships"
          value={formData.relationships}
          onChange={handleChange}
          className="textarea"
          rows={2}
          placeholder="Family, friends, enemies, connections..."
        />
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <button type="button" onClick={onCancel} className="btn btn-secondary">
          Cancel
        </button>
        <button type="submit" className="btn btn-primary">
          {character ? 'Update' : 'Create'} Character
        </button>
      </div>
    </form>
  )
}
