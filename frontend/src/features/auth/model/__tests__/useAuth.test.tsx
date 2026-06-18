import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock auth API - must be before other imports
vi.mock('../../api/authApi', () => ({
  login: vi.fn(),
  registerRequest: vi.fn(),
  getProfile: vi.fn(),
  logout: vi.fn(),
  refreshToken: vi.fn(),
  logoutClient: vi.fn(),
}))

// Mock authToken module
vi.mock('../authToken', () => ({
  getToken: vi.fn(),
  setToken: vi.fn(),
  removeToken: vi.fn(),
}))

// Mock shared/api/refreshHandler to break circular dependency
vi.mock('../../../shared/api/refreshHandler', () => ({
  registerRefreshHandler: vi.fn(),
}))

// Import after mocks
import { useAuth } from '../useAuth'
import { login, registerRequest, getProfile, logout, refreshToken } from '../../api/authApi'
import { getToken, setToken, removeToken } from '../authToken'

// Mock session storage
const sessionStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
})

// Helper to create wrapper with QueryClient and Router
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
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorageMock.clear()
    mockNavigate.mockClear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('initialization', () => {
    it('sets isLoading to true initially', async () => {
      vi.mocked(getToken).mockReturnValue('valid-token')
      vi.mocked(getProfile).mockResolvedValue({
        id: '1',
        email: 'user@test.com',
        role: 'viewer',
        display_name: 'Test User',
        created_at: '',
        force_password_change: false,
      })

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      // isLoading starts true, then becomes false after profile fetch resolves
      expect(result.current.isLoading).toBe(true)
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })

    it('fetches profile when token exists', async () => {
      vi.mocked(getToken).mockReturnValue('valid-token')
      vi.mocked(getProfile).mockResolvedValue({
        id: '1',
        email: 'user@test.com',
        role: 'viewer',
        display_name: 'Test User',
        created_at: '',
        force_password_change: false,
      })

      renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(getProfile).toHaveBeenCalled()
      })
    })

    it('sets user when profile fetch succeeds', async () => {
      const mockUser = {
        id: '1',
        email: 'user@test.com',
        role: 'viewer' as const,
        display_name: 'Test User',
        created_at: '',
        force_password_change: false,
      }

      vi.mocked(getToken).mockReturnValue('valid-token')
      vi.mocked(getProfile).mockResolvedValue(mockUser)

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.user).toEqual(mockUser)
      expect(result.current.accessToken).toBe('valid-token')
    })

    it('sets user to null when profile fetch fails', async () => {
      vi.mocked(getToken).mockReturnValue('invalid-token')
      vi.mocked(getProfile).mockRejectedValue(new Error('Unauthorized'))

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.user).toBeNull()
      expect(removeToken).toHaveBeenCalled()
    })

    it('calls refreshToken when no token exists', async () => {
      vi.mocked(getToken).mockReturnValue(null)
      vi.mocked(refreshToken).mockResolvedValue({
        access_token: 'new-token',
        token_type: 'bearer',
      })
      vi.mocked(getProfile).mockResolvedValue({
        id: '1',
        email: 'user@test.com',
        role: 'viewer',
        display_name: 'Test User',
        created_at: '',
        force_password_change: false,
      })

      renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(refreshToken).toHaveBeenCalled()
      })
    })

    it('sets user to null when refresh fails', async () => {
      vi.mocked(getToken).mockReturnValue(null)
      vi.mocked(refreshToken).mockRejectedValue(new Error('No refresh cookie'))

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.user).toBeNull()
      expect(removeToken).toHaveBeenCalled()
    })
  })

  describe('login', () => {
    it('calls login API and sets user on success', async () => {
      vi.mocked(getToken).mockReturnValue(null)
      vi.mocked(login).mockResolvedValue({
        access_token: 'new-token',
        token_type: 'bearer',
        user: {
          id: '1',
          email: 'user@test.com',
          role: 'viewer',
          display_name: 'Test User',
          created_at: '',
          force_password_change: false,
        },
      })

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await act(async () => {
        await result.current.login('user@test.com', 'password123')
      })

      expect(login).toHaveBeenCalledWith('user@test.com', 'password123')
      expect(setToken).toHaveBeenCalledWith('new-token')
      await waitFor(() => {
        expect(result.current.user?.email).toBe('user@test.com')
      })
    })

    it('removes token and sets user to null on login failure', async () => {
      vi.mocked(getToken).mockReturnValue(null)
      vi.mocked(login).mockRejectedValue(new Error('Invalid credentials'))

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await act(async () => {
        await expect(result.current.login('user@test.com', 'wrong')).rejects.toThrow('Invalid credentials')
      })

      // Wait for state updates to complete
      await waitFor(() => {
        expect(result.current.user).toBeNull()
      })

      expect(removeToken).toHaveBeenCalled()
    })
  })

describe('logout', () => {
     it('calls logout API and clears user', async () => {
       vi.mocked(getToken).mockReturnValue(null)
       vi.mocked(logout).mockResolvedValue({ message: 'Logged out successfully' })

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await act(async () => {
        await result.current.logout()
      })

      expect(logout).toHaveBeenCalled()
      expect(result.current.user).toBeNull()
    })

    it('clears user even when logout API fails', async () => {
      vi.mocked(getToken).mockReturnValue(null)
      vi.mocked(logout).mockRejectedValue(new Error('Not logged in'))

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      // Should not throw because error is caught
      await act(async () => {
        await result.current.logout()
      })

      expect(result.current.user).toBeNull()
    })
  })

  describe('registerRequest', () => {
    it('calls registerRequest API with email', async () => {
      vi.mocked(getToken).mockReturnValue(null)
      vi.mocked(registerRequest).mockResolvedValue({
        message: 'Registration request submitted',
        id: 'req-123',
      })

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await act(async () => {
        await result.current.registerRequest('newuser@test.com')
      })

      expect(registerRequest).toHaveBeenCalledWith('newuser@test.com')
    })
  })

  describe('getProfile', () => {
    it('fetches and sets user profile', async () => {
      vi.mocked(getToken).mockReturnValue(null)
      vi.mocked(getProfile).mockResolvedValue({
        id: '1',
        email: 'user@test.com',
        role: 'viewer',
        display_name: 'Test User',
        created_at: '',
        force_password_change: false,
      })

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await act(async () => {
        await result.current.getProfile()
      })

      expect(getProfile).toHaveBeenCalled()
      await waitFor(() => {
        expect(result.current.user?.email).toBe('user@test.com')
      })
    })

    it('throws error and clears auth state on profile fetch failure', async () => {
      vi.mocked(getToken).mockReturnValue(null)
      vi.mocked(getProfile).mockRejectedValue(new Error('Unauthorized'))

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await act(async () => {
        await expect(result.current.getProfile()).rejects.toThrow('Unauthorized')
      })

      // Wait for state updates
      await waitFor(() => {
        expect(result.current.user).toBeNull()
      })

      expect(removeToken).toHaveBeenCalled()
    })
  })

  describe('force_password_change redirect', () => {
    it('redirects on initial load when profile has force_password_change', async () => {
      vi.mocked(getToken).mockReturnValue('valid-token')
      vi.mocked(getProfile).mockResolvedValue({
        id: '1',
        email: 'user@test.com',
        role: 'viewer',
        display_name: 'Test User',
        created_at: '',
        force_password_change: true,
      })

      renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/profile/change-password?force=true')
      })
    })

    it('redirects after refresh when profile has force_password_change', async () => {
      vi.mocked(getToken).mockReturnValue(null)
      vi.mocked(refreshToken).mockResolvedValue({
        access_token: 'new-token',
        token_type: 'bearer',
      })
      vi.mocked(getProfile).mockResolvedValue({
        id: '1',
        email: 'user@test.com',
        role: 'viewer',
        display_name: 'Test User',
        created_at: '',
        force_password_change: true,
      })

      renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/profile/change-password?force=true')
      })
    })

    it('does not redirect when force_password_change is false', async () => {
      vi.mocked(getToken).mockReturnValue('valid-token')
      vi.mocked(getProfile).mockResolvedValue({
        id: '1',
        email: 'user@test.com',
        role: 'viewer',
        display_name: 'Test User',
        created_at: '',
        force_password_change: false,
      })

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })
})