import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import {
  getToken,
  setToken,
  removeToken,
  isTokenExpired,
  getTokenWithExpirationCheck,
} from '../authToken'

// In test environment (DEV), USE_MEMORY_STORAGE is false, so sessionStorage is used.
// We clear it before/after each test to ensure isolation.

describe('authToken', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  afterEach(() => {
    sessionStorage.clear()
  })

  describe('setToken / getToken', () => {
    it('stores and retrieves a token', () => {
      setToken('test-token-123')
      expect(getToken()).toBe('test-token-123')
    })

    it('returns null when no token is set', () => {
      expect(getToken()).toBeNull()
    })

    it('overwrites existing token', () => {
      setToken('first-token')
      setToken('second-token')
      expect(getToken()).toBe('second-token')
    })
  })

  describe('removeToken', () => {
    it('removes a stored token', () => {
      setToken('test-token')
      removeToken()
      expect(getToken()).toBeNull()
    })

    it('does nothing when no token exists', () => {
      expect(() => removeToken()).not.toThrow()
      expect(getToken()).toBeNull()
    })
  })

  describe('isTokenExpired', () => {
    it('returns false for token without exp claim', () => {
      const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
      const payload = btoa(JSON.stringify({ sub: '123' }))
      const token = `${header}.${payload}.signature`

      expect(isTokenExpired(token)).toBe(false)
    })

    it('returns false for token with future expiration', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 3600
      const header = btoa(JSON.stringify({ alg: 'H256', typ: 'JWT' }))
      const payload = btoa(JSON.stringify({ sub: '123', exp: futureExp }))
      const token = `${header}.${payload}.signature`

      expect(isTokenExpired(token)).toBe(false)
    })

    it('returns true for token with past expiration', () => {
      const pastExp = Math.floor(Date.now() / 1000) - 3600
      const header = btoa(JSON.stringify({ alg: 'H256', typ: 'JWT' }))
      const payload = btoa(JSON.stringify({ sub: '123', exp: pastExp }))
      const token = `${header}.${payload}.signature`

      expect(isTokenExpired(token)).toBe(true)
    })

    it('returns true for malformed token', () => {
      expect(isTokenExpired('not-a-jwt')).toBe(true)
    })

    it('returns true for empty string', () => {
      expect(isTokenExpired('')).toBe(true)
    })
  })

  describe('getTokenWithExpirationCheck', () => {
    it('returns null when no token is set', () => {
      expect(getTokenWithExpirationCheck()).toBeNull()
    })

    it('returns token when it is not expired', () => {
      const futureExp = Math.floor(Date.now() / 1000) + 3600
      const header = btoa(JSON.stringify({ alg: 'H256', typ: 'JWT' }))
      const payload = btoa(JSON.stringify({ sub: '123', exp: futureExp }))
      const token = `${header}.${payload}.signature`

      setToken(token)
      expect(getTokenWithExpirationCheck()).toBe(token)
    })

    it('returns null and removes token when it is expired', () => {
      const pastExp = Math.floor(Date.now() / 1000) - 3600
      const header = btoa(JSON.stringify({ alg: 'H256', typ: 'JWT' }))
      const payload = btoa(JSON.stringify({ sub: '123', exp: pastExp }))
      const token = `${header}.${payload}.signature`

      setToken(token)
      expect(getTokenWithExpirationCheck()).toBeNull()
      expect(getToken()).toBeNull()
    })
  })
})
