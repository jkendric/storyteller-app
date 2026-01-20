import { useState } from 'react'
import type { Scenario } from '../../api/client'

interface ScenarioFormProps {
  scenario?: Scenario
  onSubmit: (data: Partial<Scenario>) => void
  onCancel: () => void
}

export default function ScenarioForm({
  scenario,
  onSubmit,
  onCancel,
}: ScenarioFormProps) {
  const [formData, setFormData] = useState({
    name: scenario?.name || '',
    setting: scenario?.setting || '',
    time_period: scenario?.time_period || '',
    genre: scenario?.genre || '',
    tone: scenario?.tone || '',
    premise: scenario?.premise || '',
    themes: scenario?.themes || '',
    world_rules: scenario?.world_rules || '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
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

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="genre" className="label">
            Genre
          </label>
          <select
            id="genre"
            name="genre"
            value={formData.genre}
            onChange={handleChange}
            className="input"
          >
            <option value="">Select genre</option>
            <option value="Fantasy">Fantasy</option>
            <option value="Science Fiction">Science Fiction</option>
            <option value="Mystery">Mystery</option>
            <option value="Romance">Romance</option>
            <option value="Thriller">Thriller</option>
            <option value="Horror">Horror</option>
            <option value="Historical">Historical</option>
            <option value="Literary">Literary</option>
          </select>
        </div>

        <div>
          <label htmlFor="tone" className="label">
            Tone
          </label>
          <select
            id="tone"
            name="tone"
            value={formData.tone}
            onChange={handleChange}
            className="input"
          >
            <option value="">Select tone</option>
            <option value="Serious">Serious</option>
            <option value="Light-hearted">Light-hearted</option>
            <option value="Dark">Dark</option>
            <option value="Humorous">Humorous</option>
            <option value="Suspenseful">Suspenseful</option>
            <option value="Romantic">Romantic</option>
            <option value="Epic">Epic</option>
          </select>
        </div>
      </div>

      <div>
        <label htmlFor="time_period" className="label">
          Time Period
        </label>
        <input
          type="text"
          id="time_period"
          name="time_period"
          value={formData.time_period}
          onChange={handleChange}
          className="input"
          placeholder="e.g., Victorian era, 23rd century, Medieval..."
        />
      </div>

      <div>
        <label htmlFor="setting" className="label">
          Setting
        </label>
        <textarea
          id="setting"
          name="setting"
          value={formData.setting}
          onChange={handleChange}
          className="textarea"
          rows={3}
          placeholder="Describe the world, location, environment..."
        />
      </div>

      <div>
        <label htmlFor="premise" className="label">
          Premise
        </label>
        <textarea
          id="premise"
          name="premise"
          value={formData.premise}
          onChange={handleChange}
          className="textarea"
          rows={3}
          placeholder="The core concept or starting situation..."
        />
      </div>

      <div>
        <label htmlFor="themes" className="label">
          Themes
        </label>
        <textarea
          id="themes"
          name="themes"
          value={formData.themes}
          onChange={handleChange}
          className="textarea"
          rows={2}
          placeholder="Central themes to explore (e.g., redemption, love, power)..."
        />
      </div>

      <div>
        <label htmlFor="world_rules" className="label">
          World Rules
        </label>
        <textarea
          id="world_rules"
          name="world_rules"
          value={formData.world_rules}
          onChange={handleChange}
          className="textarea"
          rows={3}
          placeholder="Special rules for this world (magic systems, technology limits, etc.)..."
        />
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <button type="button" onClick={onCancel} className="btn btn-secondary">
          Cancel
        </button>
        <button type="submit" className="btn btn-primary">
          {scenario ? 'Update' : 'Create'} Scenario
        </button>
      </div>
    </form>
  )
}
