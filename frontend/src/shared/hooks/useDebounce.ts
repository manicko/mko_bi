import { useRef, useEffect, useState, useCallback } from 'react'

/**
 * Hook for debouncing values that change frequently (e.g., input keystrokes).
 *
 * @param value - The value to debounce
 * @param delay - Debounce delay in milliseconds (default: 300)
 * @returns The debounced value
 *
 * @example
 * ```tsx
 * const [searchTerm, setSearchTerm] = useState('')
 * const debouncedSearchTerm = useDebounce(searchTerm, 300)
 *
 * // debouncedSearchTerm updates 300ms after searchTerm stops changing
 * ```
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

/**
 * Hook for debouncing callback functions.
 *
 * @param callback - The callback function to debounce
 * @param delay - Debounce delay in milliseconds (default: 300)
 * @returns An object with the debounced callback and a cancel method
 *
 * @example
 * ```tsx
 * const { debouncedCallback, cancel } = useDebouncedCallback((value) => {
 *   performSearch(value)
 * }, 300)
 * ```
 */
export function useDebouncedCallback(
  callback: (...args: unknown[]) => void,
  delay: number = 300
): { debouncedCallback: (...args: unknown[]) => void; cancel: () => void } {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const debouncedCallback = useCallback(
    (...args: unknown[]) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      timeoutRef.current = setTimeout(() => {
        callback(...args)
        timeoutRef.current = null
      }, delay)
    },
    [callback, delay]
  )

  const cancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
  }, [])

  return { debouncedCallback, cancel }
}