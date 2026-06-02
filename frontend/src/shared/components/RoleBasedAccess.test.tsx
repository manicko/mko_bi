import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RoleBasedAccess } from './RoleBasedAccess'

// Mock useAuth hook - use named export from features/auth
vi.mock('../../features/auth', () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from '../../features/auth'

const createMockUser = (role: string) => ({
  user: {
    id: '1',
    email: `${role}@test.com`,
    role: role as 'admin' | 'editor' | 'viewer',
    display_name: role.charAt(0).toUpperCase() + role.slice(1),
    created_at: '',
    force_password_change: false,
  },
  accessToken: 'valid-token',
  isLoading: false,
  login: vi.fn(),
  logout: vi.fn(),
  registerRequest: vi.fn(),
  getProfile: vi.fn(),
})

describe('RoleBasedAccess', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders children when user has required role', () => {
    vi.mocked(useAuth).mockReturnValue(createMockUser('admin'))

    render(
      <RoleBasedAccess roles={['admin', 'editor']}>
        <div>Admin Content</div>
      </RoleBasedAccess>
    )

    expect(screen.getByText('Admin Content')).toBeInTheDocument()
  })

  it('renders children when user has single required role', () => {
    vi.mocked(useAuth).mockReturnValue(createMockUser('editor'))

    render(
      <RoleBasedAccess roles={['admin', 'editor']}>
        <div>Editor Content</div>
      </RoleBasedAccess>
    )

    expect(screen.getByText('Editor Content')).toBeInTheDocument()
  })

  it('renders fallback when user does not have required role', () => {
    vi.mocked(useAuth).mockReturnValue(createMockUser('viewer'))

    render(
      <RoleBasedAccess roles={['admin', 'editor']} fallback={<div>Access Denied</div>}>
        <div>Protected Content</div>
      </RoleBasedAccess>
    )

    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('renders null fallback by default when user does not have required role', () => {
    vi.mocked(useAuth).mockReturnValue(createMockUser('viewer'))

    render(
      <RoleBasedAccess roles={['admin']}>
        <div>Protected Content</div>
      </RoleBasedAccess>
    )

    // Default fallback is null, so nothing should be rendered
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    // The component renders an empty fragment by default, so we check that no content exists
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })

  it('renders fallback when user is null', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      accessToken: null,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      registerRequest: vi.fn(),
      getProfile: vi.fn(),
    })

    render(
      <RoleBasedAccess roles={['admin']} fallback={<div>Login Required</div>}>
        <div>Protected Content</div>
      </RoleBasedAccess>
    )

    expect(screen.getByText('Login Required')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('accepts single role string', () => {
    vi.mocked(useAuth).mockReturnValue(createMockUser('admin'))

    render(
      <RoleBasedAccess roles={['admin']}>
        <div>Admin Only Content</div>
      </RoleBasedAccess>
    )

    expect(screen.getByText('Admin Only Content')).toBeInTheDocument()
  })

  it('matches any role in the roles array', () => {
    vi.mocked(useAuth).mockReturnValue(createMockUser('editor'))

    render(
      <RoleBasedAccess roles={['admin', 'editor', 'viewer']}>
        <div>All Roles Content</div>
      </RoleBasedAccess>
    )

    expect(screen.getByText('All Roles Content')).toBeInTheDocument()
  })

  it('renders different content for different roles', () => {
    vi.mocked(useAuth).mockReturnValue(createMockUser('admin'))

    render(
      <RoleBasedAccess roles={['admin']} fallback={<div>Not Admin</div>}>
        <button>Admin Button</button>
      </RoleBasedAccess>
    )

    expect(screen.getByRole('button', { name: 'Admin Button' })).toBeInTheDocument()
    expect(screen.queryByText('Not Admin')).not.toBeInTheDocument()
  })
})