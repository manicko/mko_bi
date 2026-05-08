// Token storage with memory-first approach for security
// In production, tokens are stored in memory (not persisted)
// In development, sessionStorage can be used as fallback

let memoryToken: string | null = null
const TOKEN_KEY = 'access_token'

// Check if we're in a browser environment
const isBrowser = typeof window !== 'undefined'

// For production: use memory storage
// For development: can use sessionStorage as fallback
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
