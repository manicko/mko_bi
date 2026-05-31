import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LoginForm } from '../ui/LoginForm'
import { RegisterForm } from '../ui/RegisterForm'

// Create a wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    Navigate: ({ to }: { to: string }) => <div data-testid="navigate" data-to={to} />,
    Link: ({ to, children }: { to: string; children: React.ReactNode }) => (
      <a href={to} data-testid="link">
        {children}
      </a>
    ),
  }
})

// Mock auth API
vi.mock('../api/authApi', () => ({
  login: vi.fn(),
  registerRequest: vi.fn(),
  getProfile: vi.fn(),
  logout: vi.fn(),
  logoutClient: vi.fn(),
  refreshToken: vi.fn(),
}))

// Mock useAuth hook
vi.mock('../model/useAuth', () => ({
  useAuth: () => ({
    user: null,
    accessToken: null,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    registerRequest: vi.fn(),
    getProfile: vi.fn(),
  }),
}))

describe('AuthFlow - LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
  })

  it('renders login form with email and password fields', () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <LoginForm />
      </Wrapper>
    )

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })

  it('renders registration link', () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <LoginForm />
      </Wrapper>
    )

    expect(screen.getByText(/create an account/i)).toBeInTheDocument()
  })

  it('shows validation error for invalid email format', async () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <LoginForm />
      </Wrapper>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /login/i })

    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for empty password', async () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <LoginForm />
      </Wrapper>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /login/i })

    fireEvent.change(emailInput, { target: { value: 'user@example.com' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    })
  })

  it('accepts valid email and password input', () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <LoginForm />
      </Wrapper>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)

    fireEvent.change(emailInput, { target: { value: 'user@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })

    expect((emailInput as HTMLInputElement).value).toBe('user@example.com')
    expect((passwordInput as HTMLInputElement).value).toBe('password123')
  })
})

describe('AuthFlow - RegisterForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
  })

  it('renders registration form with email field', () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <RegisterForm />
      </Wrapper>
    )

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /submit request/i })).toBeInTheDocument()
  })

  it('shows validation error for invalid email format', async () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <RegisterForm />
      </Wrapper>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /submit request/i })

    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for blocked email domain', async () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <RegisterForm />
      </Wrapper>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /submit request/i })

    fireEvent.change(emailInput, { target: { value: 'user@tempmail.com' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/this email domain is not allowed/i)).toBeInTheDocument()
    })
  })

  it('renders login link for existing users', () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <RegisterForm />
      </Wrapper>
    )

    expect(screen.getByText(/already have an account\?/i)).toBeInTheDocument()
    expect(screen.getByText(/login/i)).toBeInTheDocument()
  })
})