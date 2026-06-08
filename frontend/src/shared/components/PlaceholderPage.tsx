import { Typography } from '@mui/material'

interface PlaceholderPageProps {
  title: string
}

/**
 * Placeholder page for features that are planned but not yet implemented.
 *
 * Use this component as a stub for routes that are in the navigation but
 * don't have their full implementation yet. Provides a consistent "coming soon"
 * experience across the application.
 *
 * @param title - The page title to display
 *
 * @example
 * // In routes.tsx for a feature in development:
 * <Route path="/reports" element={<PlaceholderPage title="Reports" />} />
 *
 * @see PLAN_02.md for recommended usage patterns and roadmap integration.
 */
export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <div style={{ padding: '20px' }}>
      <Typography variant="h4">{title}</Typography>
      <Typography>This page will be implemented in a future task.</Typography>
    </div>
  )
}