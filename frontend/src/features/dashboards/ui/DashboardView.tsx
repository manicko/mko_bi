import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Typography,
  CircularProgress,
  Alert,
  Button,
  Grid,
  Paper,
  Stack,
} from '@mui/material'
import { useDashboard, useAggregatedData, useInvalidateDashboard } from '../api/dashboardApi'
import { UploadModal } from '../../upload/ui/UploadModal'
import { DashboardFilters } from './DashboardFilters'
import { PlotlyChart } from './charts'
import type { GraphDataWithConfig, FilterDetail } from '../../../shared/types/api.types'
import type { FilterType } from '../../../shared/types/enums'

export function DashboardView() {
  const { id } = useParams<{ id: string }>()

  const [filters, setFilters] = useState<
    Record<string, string | string[] | number | number[]>
  >({})
  const [uploadModalOpen, setUploadModalOpen] = useState(false)

  const {
    data: dashboard,
    isLoading: dashboardLoading,
    error: dashboardError,
  } = useDashboard(id || '')
  const {
    data: aggregatedData,
    isLoading: dataLoading,
    error: dataError,
  } = useAggregatedData(id || '', filters)
  const { invalidateAggregatedData } = useInvalidateDashboard()

  // Derive filterDetails from dashboard config
  const filterDetails: FilterDetail[] = dashboard?.config?.filters && dashboard.config.filters.length > 0
    ? dashboard.config.filters.map(
        (filterConfig, index) => ({
          id: `filter-${index}-${filterConfig.field}`,
          name: filterConfig.field,
          type: filterConfig.type as FilterType,
          config: {
            field: filterConfig.field,
            source: filterConfig.source,
            multi: filterConfig.multi,
          },
        })
      )
    : []

  const handleFilterChange = useCallback(
    (newFilters: Record<string, string | string[] | number | number[]>) => {
      setFilters(newFilters)
    },
    []
  )

  useEffect(() => {
    if (id && Object.keys(filters).length > 0) {
      invalidateAggregatedData(id)
    }
  }, [filters, id, invalidateAggregatedData])

  if (dashboardLoading) {
    return (
      <Stack sx={{ alignItems: 'center', p: 4 }}>
        <CircularProgress />
      </Stack>
    )
  }

  if (dashboardError || !dashboard) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load dashboard. Please try again.
      </Alert>
    )
  }

  const canEdit = ['edit', 'admin'].includes(dashboard.permission)

  return (
    <Stack sx={{ p: 3 }} spacing={2}>
      <Stack
        direction="row"
        sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 3 }}
      >
        <Typography variant="h4">{dashboard.name}</Typography>
        {canEdit && (
          <Button
            variant="contained"
            onClick={() => setUploadModalOpen(true)}
          >
            Upload Data
          </Button>
        )}
      </Stack>

      {dashboard.description && (
        <Typography variant="body1" color="text.secondary" component="p" sx={{ mb: 2 }}>
          {dashboard.description}
        </Typography>
      )}

      <Grid container spacing={2}>
        {dashboard.config.filters && dashboard.config.filters.length > 0 && (
          <Grid size={{ xs: 12, md: 3 }}>
            <DashboardFilters
              filters={filterDetails}
              values={filters}
              onChange={handleFilterChange}
            />
          </Grid>
        )}

        <Grid
          size={{
            xs: 12,
            md: dashboard.config.filters?.length > 0 ? 9 : 12,
          }}
        >
          {dataLoading && (
            <Stack sx={{ alignItems: 'center', p: 4 }}>
              <CircularProgress />
            </Stack>
          )}

          {dataError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Failed to load chart data.
            </Alert>
          )}

          {aggregatedData?.graphs && aggregatedData.graphs.length > 0 ? (
            <Stack spacing={2}>
              {aggregatedData.graphs.map((graph: GraphDataWithConfig) => (
                <Paper key={graph.graph_id} variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    {graph.name}
                  </Typography>
                  <Stack sx={{ height: 400 }}>
                    <PlotlyChart data={graph.data} layout={graph.layout} />
                  </Stack>
                </Paper>
              ))}
            </Stack>
          ) : (
            !dataLoading && (
              <Alert severity="info">
                No data available for this dashboard. Upload data to see charts.
              </Alert>
            )
          )}
        </Grid>
      </Grid>

      <UploadModal
        open={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        dashboardId={id || ''}
        onUploadComplete={() => {
          setUploadModalOpen(false)
          if (id) {
            invalidateAggregatedData(id)
          }
        }}
      />
    </Stack>
  )
}