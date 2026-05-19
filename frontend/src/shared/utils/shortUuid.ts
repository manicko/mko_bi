/**
 * Short UUID utility functions for consistent ID display.
 * Returns shortened IDs (first 8 characters) for use in UI components like DataGrid tables.
 */

export const SHORT_ID_LENGTH = 8

/**
 * Returns the first 8 characters of any string, typically used for UUID display.
 * @param id - The full UUID string
 * @returns First 8 characters of the ID
 *
 * @example
 * shortUuid('550e8400-e29b-41d4-a716-446655440000') // returns '550e8400'
 */
export function shortUuid(id: string): string {
  return id.slice(0, SHORT_ID_LENGTH)
}

/**
 * Generates a new short ID by creating a UUID v4 and returning first 8 characters.
 * Uses crypto.randomUUID() for secure random generation.
 * @returns An 8-character short ID
 */
export function generateShortId(): string {
  return crypto.randomUUID().slice(0, SHORT_ID_LENGTH)
}