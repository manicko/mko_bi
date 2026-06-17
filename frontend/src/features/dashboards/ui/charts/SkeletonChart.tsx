import { Paper, Skeleton, Stack } from '@mui/material'

/**
 * Loading skeleton placeholder for chart rendering.
 *
 * Displays a rectangular skeleton that matches the chart dimensions
 * to prevent layout shift when the actual chart loads.
 */
interface SkeletonChartProps {
  count?: number
}

export function SkeletonChart({ count = 1 }: SkeletonChartProps) {
  return (
    <Stack spacing={2}>
      {Array.from({ length: count }).map((_, index) => (
        <Paper key={index} variant="outlined" sx={{ p: 2 }}>
          <Skeleton variant="text" width={180} height={32} sx={{ mb: 1 }} />
          <Stack sx={{ height: 400 }}>
            <Skeleton variant="rounded" width="100%" height="100%" />
          </Stack>
        </Paper>
      ))}
    </Stack>
  )
}