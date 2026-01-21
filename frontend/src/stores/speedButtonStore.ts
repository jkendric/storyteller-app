import { create } from 'zustand'
import { api, SpeedButton, SpeedButtonCreate, SpeedButtonUpdate } from '../api/client'

interface SpeedButtonState {
  speedButtons: SpeedButton[]
  isLoading: boolean
  error: string | null

  fetchSpeedButtons: () => Promise<void>
  createSpeedButton: (data: SpeedButtonCreate) => Promise<SpeedButton>
  updateSpeedButton: (id: number, data: SpeedButtonUpdate) => Promise<SpeedButton>
  deleteSpeedButton: (id: number) => Promise<void>
  reorderSpeedButtons: (buttonIds: number[]) => Promise<void>
  clearError: () => void
}

export const useSpeedButtonStore = create<SpeedButtonState>((set, get) => ({
  speedButtons: [],
  isLoading: false,
  error: null,

  fetchSpeedButtons: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.getSpeedButtons()
      set({ speedButtons: response.speed_buttons, isLoading: false })
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Failed to fetch speed buttons',
        isLoading: false,
      })
    }
  },

  createSpeedButton: async (data: SpeedButtonCreate) => {
    set({ error: null })
    try {
      const newButton = await api.createSpeedButton(data)
      set((state) => ({
        speedButtons: [...state.speedButtons, newButton],
      }))
      return newButton
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to create speed button'
      set({ error: errorMsg })
      throw err
    }
  },

  updateSpeedButton: async (id: number, data: SpeedButtonUpdate) => {
    set({ error: null })
    try {
      const updatedButton = await api.updateSpeedButton(id, data)
      set((state) => ({
        speedButtons: state.speedButtons.map((btn) =>
          btn.id === id ? updatedButton : btn
        ),
      }))
      return updatedButton
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to update speed button'
      set({ error: errorMsg })
      throw err
    }
  },

  deleteSpeedButton: async (id: number) => {
    set({ error: null })
    try {
      await api.deleteSpeedButton(id)
      set((state) => ({
        speedButtons: state.speedButtons.filter((btn) => btn.id !== id),
      }))
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to delete speed button'
      set({ error: errorMsg })
      throw err
    }
  },

  reorderSpeedButtons: async (buttonIds: number[]) => {
    set({ error: null })
    try {
      const response = await api.reorderSpeedButtons(buttonIds)
      set({ speedButtons: response.speed_buttons })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to reorder speed buttons'
      set({ error: errorMsg })
      throw err
    }
  },

  clearError: () => set({ error: null }),
}))
