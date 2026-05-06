import { Typography } from '@mui/material'

interface PlaceholderPageProps {
  title: string
}

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <div style={{ padding: '20px' }}>
      <Typography variant="h4">{title}</Typography>
      <Typography>This page will be implemented in a future task.</Typography>
    </div>
  )
}
