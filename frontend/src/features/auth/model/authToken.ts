// Token storage with memory-first approach for security
//
// Production behavior (USE_MEMORY_STORAGE = true):
//   Tokens are held only in a module-level JS variable (memoryToken).
//   They are never written to disk or browser storage, which means:
//   - Tokens survive page in-memory (same JS context) but are lost on full page reload/navigation.
//   - Tokens are NOT vulnerable to XSS-based exfiltration via localStorage/sessionStorage.
//   - This is the most secure option for storing JWTs in a SPA.
//
// Development behavior (USE_MEMORY_STORAGE = false):
//   Tokens fall back to sessionStorage so that they persist across hot-reloads
//   and page refreshes during local development. This is a convenience trade-off:
//   - sessionStorage is accessible to any JS running on the page (XSS risk).
//   - sessionStorage is cleared when the tab is closed.
//   - This mode MUST NEVER be used in production builds.

let memoryToken: string | null = null
const TOKEN_KEY = 'access_token'

// Check if we're in a browser environment
const isBrowser = typeof window !== 'undefined'

// When true (production build), tokens are stored in memory only.
// When false (development), sessionStorage is used as a convenience fallback.
const USE_MEMORY_STORAGE = import.meta.env.PROD

export function getToken(): string | null {
  if (USE_MEMORY_STORAGE) {
    return memoryToken
  }
  // Fallback to sessionStorage for development
  return isBrowser ? sessionStorage.getItem(TOKEN_KEY) : null
}

export function setToken(token: string): void {
  if (USE_MEMORY_STORAGE) {
    memoryToken = token
  } else {
    // Use sessionStorage for development
    if (isBrowser) {
      sessionStorage.setItem(TOKEN_KEY, token)
    }
  }
}

export function removeToken(): void {
  memoryToken = null
  if (isBrowser) {
    sessionStorage.removeItem(TOKEN_KEY)
  }
}

// Token expiration check (if JWT has expiration)
export function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    if (!payload.exp) return false
    
    const expirationTime = payload.exp * 1000 // Convert to milliseconds
    return Date.now() >= expirationTime
  } catch {
    // If we can't parse the token, assume it's invalid
    return true
  }
}

export function getTokenWithExpirationCheck(): string | null {
  const token = getToken()
  if (!token) return null
  
  if (isTokenExpired(token)) {
    removeToken()
    return null
  }
  
  return token
}
