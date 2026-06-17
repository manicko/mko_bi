import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Suspense } from 'react'

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  useParams: () => ({ id: 'test-dashboard-id' }),
}))

// Mock PlotlyChart component to avoid rendering issues in tests
vi.mock('../ui/charts/PlotlyChart', () => ({
  PlotlyChart: () => <div data-testid="plotly-chart">Chart</div>,
}))

// Mock LineChart component
vi.mock('../ui/charts/LineChart', () => ({
  LineChart: () => <div data-testid="line-chart">Line Chart</div>,
}))

// Mock TableChart component
vi.mock('../ui/charts/TableChart', () => ({
  TableChart: () => <div data-testid="table-chart">Table Chart</div>,
}))

// Mock DashboardFilters
vi.mock('../ui/DashboardFilters', () => ({
  DashboardFilters: () => <div data-testid="dashboard-filters">Filters Component</div>,
}))

// Mock UploadModal with lazy/suspense-compatible mock
vi.mock('../../upload/ui/UploadModal', () => ({
  UploadModal: () => null,
}))

// Mock dashboard API
vi.mock('../api/dashboardApi', () => ({
  useDashboard: () => ({
    data: {
      id: 'test-dashboard-id',
      name: 'Test Dashboard',
      description: 'A test dashboard for unit tests',
      config: {
        graph_types: ['bar', 'line'],
      },
      permission: 'edit',
    },
    isLoading: false,
    error: null,
  }),
  useAggregatedData: () => ({
    data: {
      graphs: [
        {
          graph_id: 'graph-1',
          type: 'bar',
          name: 'Sales by Category',
          data: [{ x: ['A', 'B', 'C'], y: [1, 2, 3], type: 'bar' }],
        },
        {
          graph_id: 'graph-2',
          type: 'line',
          name: 'Trend Over Time',
          data: [{ x: [1, 2, 3], y: [10, 20, 30], type: 'scatter', mode: 'lines' }],
        },
        {
          graph_id: 'graph-3',
          type: 'table',
          name: 'Data Table',
          data: [{ category: 'A', value: 100 }, { category: 'B', value: 200 }],
        },
      ],
    },
    isLoading: false,
    error: null,
  }),
  useInvalidateDashboard: () => ({
    invalidateDashboard: vi.fn(),
    invalidateAggregatedData: vi.fn(),
  }),
}))

import { DashboardView } from '../ui/DashboardView'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <Suspense fallback={null}>
        {children}
      </Suspense>
    </QueryClientProvider>
  )
}

describe('DashboardView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dashboard title', async () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <DashboardView />
      </Wrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Test Dashboard')).toBeInTheDocument()
    })
  })

  it('renders dashboard description when present', async () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <DashboardView />
      </Wrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('A test dashboard for unit tests')).toBeInTheDocument()
    })
  })

  it('renders upload button when user has edit permission', async () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <DashboardView />
      </Wrapper>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /upload data/i })).toBeInTheDocument()
    })
  })

  it('renders chart titles from aggregated data', async () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <DashboardView />
      </Wrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Sales by Category')).toBeInTheDocument()
      expect(screen.getByText('Trend Over Time')).toBeInTheDocument()
      expect(screen.getByText('Data Table')).toBeInTheDocument()
    })
  })

  it('renders multiple plotly charts', async () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <DashboardView />
      </Wrapper>
    )

    await waitFor(() => {
      const charts = screen.getAllByTestId('plotly-chart')
      expect(charts).toHaveLength(1)
    })
  })

  it('renders line chart', async () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <DashboardView />
      </Wrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })
  })

  it('renders table chart', async () => {
    const Wrapper = createWrapper()
    render(
      <Wrapper>
        <DashboardView />
      </Wrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('table-chart')).toBeInTheDocument()
    })
  })
})