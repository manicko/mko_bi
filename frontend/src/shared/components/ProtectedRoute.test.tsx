import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ProtectedRoute } from './ProtectedRoute'

// Mock react-router-dom's Navigate component
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    Navigate: ({ to }: { to: string }) => <div data-testid="navigate" data-to={to} />,
  }
})

// Mock useAuth hook - use named export from features/auth
vi.mock('../../features/auth', () => ({
  useAuth: vi.fn(),
}))

// Mock MUI components
vi.mock('@mui/material', () => ({
  Box: ({ children }: { children: React.ReactNode }) => <div data-testid="box">{children}</div>,
  CircularProgress: () => <div data-testid="circular-progress">Loading...</div>,
}))

import { useAuth } from '../../features/auth'

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders children when authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      accessToken: 'valid-token',
      isLoading: false,
      user: null,
      login: vi.fn(),
      logout: vi.fn(),
      registerRequest: vi.fn(),
      getProfile: vi.fn(),
    })

    render(
      <MemoryRouter>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </MemoryRouter>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('shows loading spinner when isLoading is true', () => {
    vi.mocked(useAuth).mockReturnValue({
      accessToken: null,
      isLoading: true,
      user: null,
      login: vi.fn(),
      logout: vi.fn(),
      registerRequest: vi.fn(),
      getProfile: vi.fn(),
    })

    render(
      <MemoryRouter>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </MemoryRouter>
    )

    expect(screen.getByTestId('circular-progress')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('redirects to login when not authenticated and not loading', () => {
    vi.mocked(useAuth).mockReturnValue({
      accessToken: null,
      isLoading: false,
      user: null,
      login: vi.fn(),
      logout: vi.fn(),
      registerRequest: vi.fn(),
      getProfile: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </MemoryRouter>
    )

    // Navigate component should be rendered (redirect to login)
    expect(screen.getByTestId('navigate')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('preserves location state when redirecting', () => {
    vi.mocked(useAuth).mockReturnValue({
      accessToken: null,
      isLoading: false,
      user: null,
      login: vi.fn(),
      logout: vi.fn(),
      registerRequest: vi.fn(),
      getProfile: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </MemoryRouter>
    )

    const navigateElement = screen.getByTestId('navigate')
    expect(navigateElement).toHaveAttribute('data-to', '/login')
  })
})