import { useCallback, useEffect, useState } from 'react'
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Typography,
  Slider,
  Button,
  Stack,
  Chip,
  Paper,
  Box,
} from '@mui/material'
import type { FilterDetail, FilterConfig } from '../../../shared/types/api.types'

interface DashboardFiltersProps {
  filters: FilterDetail[]
  values: Record<string, string | string[] | number | number[]>
  onChange: (filters: Record<string, string | string[] | number | number[]>) => void
}

export function DashboardFilters({
  filters,
  values,
  onChange,
}: DashboardFiltersProps) {
  const [localFilters, setLocalFilters] = useState<
    Record<string, string | string[] | number | number[]>
  >(() => values || {})

  // Sync local state when external values prop changes
  // This is required for the filter reset behavior when dashboard data reloads
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLocalFilters(values || {})
  }, [values])

  const handleFilterChange = useCallback(
    (filterName: string, value: string | string[] | number | number[]) => {
      const newFilters = { ...localFilters, [filterName]: value }
      setLocalFilters(newFilters)
    },
    [localFilters]
  )

  const handleApplyFilters = useCallback(() => {
    onChange(localFilters)
  }, [localFilters, onChange])

  const handleResetFilters = useCallback(() => {
    const emptyFilters: Record<string, string | string[] | number | number[]> = {}
    setLocalFilters(emptyFilters)
    onChange(emptyFilters)
  }, [onChange])

  if (!filters || filters.length === 0) {
    return null
  }

  return (
    <Paper elevation={0} variant="outlined" sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Filters
      </Typography>
      <Stack spacing={2}>
        {filters.map((filter) => (
          <FilterField
            key={filter.id}
            filter={filter}
            value={localFilters[filter.name]}
            onChange={(value) => handleFilterChange(filter.name, value)}
          />
        ))}
        <Stack direction="row" spacing={1}>
          <Button variant="contained" onClick={handleApplyFilters} size="small">
            Apply
          </Button>
          <Button variant="outlined" onClick={handleResetFilters} size="small">
            Reset
          </Button>
        </Stack>
      </Stack>
    </Paper>
  )
}

interface FilterFieldProps {
  filter: FilterDetail
  value: string | string[] | number | number[] | undefined
  onChange: (value: string | string[] | number | number[]) => void
}

function FilterField({ filter, value, onChange }: FilterFieldProps) {
  const config = filter.config

  switch (filter.type) {
    case 'select':
      return (
        <FormControl fullWidth size="small">
          <InputLabel>{filter.name}</InputLabel>
          <Select
            value={(value as string) || ''}
            label={filter.name}
            onChange={(e) => onChange(e.target.value)}
          >
            {(config.options || []).map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>
                {opt.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )

    case 'multiselect': {
      const selectedValues = Array.isArray(value) ? value : []
      return (
        <FormControl fullWidth size="small">
          <InputLabel>{filter.name}</InputLabel>
          <Select
            multiple
            value={selectedValues}
            label={filter.name}
            onChange={(e) => onChange(e.target.value)}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {(selected as string[]).map((val) => (
                  <Chip key={val} label={val} size="small" />
                ))}
              </Box>
            )}
          >
            {(config.options || []).map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>
                {opt.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )
    }

    case 'range': {
      const rangeValue = (value as [number, number]) || [
        config.min || 0,
        config.max || 100,
      ]
      return (
        <Box>
          <Typography variant="caption">{filter.name}</Typography>
          <Slider
            value={rangeValue}
            min={config.min || 0}
            max={config.max || 100}
            onChange={(_, newValue) => onChange(newValue)}
            valueLabelDisplay="auto"
          />
        </Box>
      )
    }

    case 'date':
      return (
        <TextField
          fullWidth
          size="small"
          label={filter.name}
          type="date"
          value={(value) || ''}
          onChange={(e) => onChange(e.target.value)}
          slotProps={{ inputLabel: { shrink: true } }}
        />
      )

    default:
      return null
  }
}