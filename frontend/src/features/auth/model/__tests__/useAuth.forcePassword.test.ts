import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'

// Mock authApi - this is what useAuth imports and calls
vi.mock('../../api/authApi', () => ({
  login: vi.fn(),
  registerRequest: vi.fn(),
  logout: vi.fn(),
  refreshToken: vi.fn(),
  getProfile: vi.fn(),
}))

// Import after vi.mock is set up
import { getProfile, refreshToken } from '../../api/authApi'
import { useAuth } from '../useAuth'

// Access mocked versions
const mockedGetProfile = vi.mocked(getProfile)
const mockedRefreshToken = vi.mocked(refreshToken)

describe('useAuth - force_password_change', () => {
  let originalLocation: Location

  beforeEach(() => {
    sessionStorage.clear()
    vi.clearAllMocks()
    // Set up window.location mock
    originalLocation = window.location
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
      configurable: true,
    })
  })

  afterEach(() => {
    sessionStorage.clear()
    vi.clearAllMocks()
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
      configurable: true,
    })
  })

  describe('useEffect redirect logic', () => {
    it('redirects to change-password when force_password_change is true after refresh', async () => {
      mockedRefreshToken.mockResolvedValue({
        access_token: 'mock-refresh-token',
        token_type: 'bearer',
      })
      mockedGetProfile.mockResolvedValue({
        id: 'user-1',
        email: 'test@example.com',
        role: 'viewer',
        display_name: 'test',
        created_at: '2024-01-01',
        force_password_change: true,
      })

      // Clear token to trigger refresh flow
      Object.defineProperty(window, 'sessionStorage', {
        value: {
          clear: vi.fn(),
          getItem: vi.fn().mockReturnValue(null),
          setItem: vi.fn(),
          removeItem: vi.fn(),
        },
        writable: true,
        configurable: true,
      })

      renderHook(() => useAuth())

      await waitFor(() => {
        expect(window.location.href).toBe('/profile/change-password?force=true')
      })
    })

    it('proceeds to dashboard (no redirect) when force_password_change is false after refresh', async () => {
      mockedRefreshToken.mockResolvedValue({
        access_token: 'mock-refresh-token',
        token_type: 'bearer',
      })
      mockedGetProfile.mockResolvedValue({
        id: 'user-1',
        email: 'test@example.com',
        role: 'viewer',
        display_name: 'test',
        created_at: '2024-01-01',
        force_password_change: false,
      })

      renderHook(() => useAuth())

      await waitFor(() => {
        expect(mockedGetProfile).toHaveBeenCalled()
      })

      expect(window.location.href).toBe('')
    })

    it('redirects to change-password when force_password_change is true on existing token', async () => {
      mockedGetProfile.mockResolvedValue({
        id: 'user-1',
        email: 'test@example.com',
        role: 'viewer',
        display_name: 'test',
        created_at: '2024-01-01',
        force_password_change: true,
      })

      // Set a token to trigger existing token flow
      Object.defineProperty(window, 'sessionStorage', {
        value: {
          clear: vi.fn(),
          getItem: vi.fn().mockReturnValue('existing-token'),
          setItem: vi.fn(),
          removeItem: vi.fn(),
        },
        writable: true,
        configurable: true,
      })

      renderHook(() => useAuth())

      await waitFor(() => {
        expect(window.location.href).toBe('/profile/change-password?force=true')
      })
    })

    it('proceeds to dashboard when force_password_change is false on existing token', async () => {
      mockedGetProfile.mockResolvedValue({
        id: 'user-1',
        email: 'test@example.com',
        role: 'viewer',
        display_name: 'test',
        created_at: '2024-01-01',
        force_password_change: false,
      })

      // Set a token to trigger existing token flow
      Object.defineProperty(window, 'sessionStorage', {
        value: {
          clear: vi.fn(),
          getItem: vi.fn().mockReturnValue('existing-token'),
          setItem: vi.fn(),
          removeItem: vi.fn(),
        },
        writable: true,
        configurable: true,
      })

      renderHook(() => useAuth())

      await waitFor(() => {
        expect(mockedGetProfile).toHaveBeenCalled()
      })

      expect(window.location.href).toBe('')
    })
  })
})