import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../App'

// Mock fetch
globalThis.fetch = vi.fn()

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  )
}

describe('App', () => {
  it('renders without crashing', () => {
    ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ stories: [], total: 0 }),
    })

    render(<App />, { wrapper: createWrapper() })
    expect(screen.getByText('Storyteller')).toBeInTheDocument()
  })

  it('shows navigation links', () => {
    ;(globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ stories: [], total: 0 }),
    })

    render(<App />, { wrapper: createWrapper() })
    // Use getByRole to find navigation links specifically
    const nav = screen.getByRole('navigation')
    expect(nav).toBeInTheDocument()
    expect(screen.getAllByText('Home').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Characters').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Scenarios').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Stories').length).toBeGreaterThan(0)
  })
})
