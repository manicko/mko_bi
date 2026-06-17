import { format } from 'date-fns'

/**
 * Standard date format for user-facing displays.
 * Used across tables and filters for consistent date representation.
 */
const DISPLAY_DATE_FORMAT = 'dd/MM/yyyy'

/**
 * Standard datetime format for user-facing displays.
 * Used for timestamps that include time.
 */
const DISPLAY_DATETIME_FORMAT = 'dd/MM/yyyy HH:mm'

/**
 * Format a date string or Date object to the standard display format.
 * @param date - Date string (ISO format) or Date object
 * @returns Formatted date string in dd/MM/yyyy format
 *
 * @example
 * formatDate('2024-06-15T10:30:00Z') // returns '15/06/2024'
 * formatDate(new Date()) // returns current date in dd/MM/yyyy format
 */
export function formatDate(date: string | Date | null | undefined): string {
  if (!date) {
    return ''
  }
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return format(dateObj, DISPLAY_DATE_FORMAT)
}

/**
 * Format a date string or Date object to the standard datetime format.
 * @param date - Date string (ISO format) or Date object
 * @returns Formatted datetime string in dd/MM/yyyy HH:mm format
 *
 * @example
 * formatDateTime('2024-06-15T10:30:00Z') // returns '15/06/2024 10:30'
 * formatDateTime(new Date()) // returns current datetime in dd/MM/yyyy HH:mm format
 */
export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) {
    return ''
  }
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return format(dateObj, DISPLAY_DATETIME_FORMAT)
}

/**
 * Format a date for display with optional time component.
 * Uses datetime format for dates that have a time component.
 * @param date - Date string (ISO format) or Date object
 * @returns Formatted date string
 */
export function formatDateForGrid(date: string | Date | null | undefined): string {
  if (!date) {
    return ''
  }
  const dateObj = typeof date === 'string' ? new Date(date) : date

  // Check if date has a meaningful time component
  const hours = dateObj.getHours()
  const minutes = dateObj.getMinutes()
  const hasTime = hours !== 0 || minutes !== 0

  if (hasTime) {
    return format(dateObj, DISPLAY_DATETIME_FORMAT)
  }
  return format(dateObj, DISPLAY_DATE_FORMAT)
}