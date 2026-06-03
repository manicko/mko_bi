import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import type { Layout, Config } from 'react-plotly.js'

// Mock component
function MockPlot(props: {
  data?: unknown
  layout?: Record<string, unknown>
  config?: Record<string, unknown>
  style?: Record<string, string>
}) {
  const { data, layout, config, style } = props
  return (
    <div data-testid="plotly-chart" data-layout={JSON.stringify(layout)} data-config={JSON.stringify(config)} data-style={JSON.stringify(style)}>
      <div data-testid="plotly-data">{JSON.stringify(data)}</div>
    </div>
  )
}

vi.mock('react-plotly.js', () => ({
  default: MockPlot,
}))

// Import AFTER mock
import { PlotlyChart } from './PlotlyChart'

describe('PlotlyChart', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockBarData = {
    x: ['A', 'B', 'C'],
    y: [1, 2, 3],
    type: 'bar' as const,
  }

  const mockLineData = {
    x: [1, 2, 3],
    y: [10, 20, 30],
    type: 'scatter' as const,
    mode: 'lines' as const,
  }

  it('renders with single data object', async () => {
    render(<PlotlyChart data={mockBarData} />)

    await waitFor(() => {
      expect(screen.getByTestId('plotly-chart')).toBeInTheDocument()
    })
  })

  it('renders with array of data objects', async () => {
    render(<PlotlyChart data={[mockBarData, mockLineData]} />)

    await waitFor(() => {
      expect(screen.getByTestId('plotly-chart')).toBeInTheDocument()
      expect(screen.getByTestId('plotly-data')).toHaveTextContent(JSON.stringify([mockBarData, mockLineData]))
    })
  })

  it('applies default layout with autosize', async () => {
    render(<PlotlyChart data={mockBarData} />)

    await waitFor(() => {
      const chart = screen.getByTestId('plotly-chart')
      const layout = JSON.parse(chart.getAttribute('data-layout') || '{}') as Record<string, unknown>
      expect(layout.autosize).toBe(true)
    })
  })

  it('applies default margin to layout', async () => {
    render(<PlotlyChart data={mockBarData} />)

    await waitFor(() => {
      const chart = screen.getByTestId('plotly-chart')
      const layout = JSON.parse(chart.getAttribute('data-layout') || '{}') as Record<string, unknown>
      expect(layout.margin).toEqual({ t: 40, r: 20, b: 40, l: 40 })
    })
  })

  it('merges custom layout with defaults', async () => {
    render(<PlotlyChart data={mockBarData} layout={{ title: { text: 'Custom Title' } }} />)

    await waitFor(() => {
      const chart = screen.getByTestId('plotly-chart')
      const layout = JSON.parse(chart.getAttribute('data-layout') || '{}') as Record<string, unknown>
      expect((layout.title as Record<string, unknown>).text).toBe('Custom Title')
      expect(layout.autosize).toBe(true)
    })
  })

  it('applies default config with responsive', async () => {
    render(<PlotlyChart data={mockBarData} />)

    await waitFor(() => {
      const chart = screen.getByTestId('plotly-chart')
      const config = JSON.parse(chart.getAttribute('data-config') || '{}') as Record<string, unknown>
      expect(config.responsive).toBe(true)
    })
  })

  it('applies default displayModeBar', async () => {
    render(<PlotlyChart data={mockBarData} />)

    await waitFor(() => {
      const chart = screen.getByTestId('plotly-chart')
      const config = JSON.parse(chart.getAttribute('data-config') || '{}') as Record<string, unknown>
      expect(config.displayModeBar).toBe('hover')
    })
  })

  it('merges custom config with defaults', async () => {
    render(<PlotlyChart data={mockBarData} config={{ displayModeBar: false }} />)

    await waitFor(() => {
      const chart = screen.getByTestId('plotly-chart')
      const config = JSON.parse(chart.getAttribute('data-config') || '{}') as Record<string, unknown>
      expect(config.responsive).toBe(true)
      expect(config.displayModeBar).toBe(false)
    })
  })

  it('applies default style with width and height', async () => {
    render(<PlotlyChart data={mockBarData} />)

    await waitFor(() => {
      const chart = screen.getByTestId('plotly-chart')
      const style = JSON.parse(chart.getAttribute('data-style') || '{}') as Record<string, string>
      expect(style.width).toBe('100%')
      expect(style.height).toBe('100%')
    })
  })

  it('merges custom styles with defaults', async () => {
    render(<PlotlyChart data={mockBarData} style={{ border: '1px solid red' }} />)

    await waitFor(() => {
      const chart = screen.getByTestId('plotly-chart')
      const style = JSON.parse(chart.getAttribute('data-style') || '{}') as Record<string, string>
      expect(style.width).toBe('100%')
      expect(style.height).toBe('100%')
      expect(style.border).toBe('1px solid red')
    })
  })

  it('renders with all props combined', async () => {
    const customLayout = { title: 'Sales Chart', xaxis: { title: 'Months' } } as Partial<Layout> as Layout
    const customConfig = { displayModeBar: true, scrollZoom: true } as Partial<Config> as Config
    const customStyle = { backgroundColor: 'blue' }

    render(
      <PlotlyChart
        data={mockBarData}
        layout={customLayout}
        config={customConfig}
        style={customStyle}
      />
    )

    await waitFor(() => {
      const chart = screen.getByTestId('plotly-chart')
      const layout = JSON.parse(chart.getAttribute('data-layout') || '{}') as Record<string, unknown>
      const config = JSON.parse(chart.getAttribute('data-config') || '{}') as Record<string, unknown>
      const style = JSON.parse(chart.getAttribute('data-style') || '{}') as Record<string, string>

      expect(layout.title).toBe('Sales Chart')
      expect((layout.xaxis as Record<string, unknown>)?.title).toBe('Months')
      expect(layout.autosize).toBe(true)

      expect(config.responsive).toBe(true)
      expect(config.displayModeBar).toBe(true)
      expect(config.scrollZoom).toBe(true)

      expect(style.width).toBe('100%')
      expect(style.height).toBe('100%')
      expect(style.backgroundColor).toBe('blue')
    })
  })

  it('renders with pie chart data', async () => {
    const pieData = {
      values: [30, 20, 50],
      labels: ['A', 'B', 'C'],
      type: 'pie' as const,
    }

    render(<PlotlyChart data={pieData} />)

    await waitFor(() => {
      expect(screen.getByTestId('plotly-chart')).toBeInTheDocument()
    })
  })

  it('renders with table data', async () => {
    const tableData = {
      type: 'table' as const,
      header: { values: ['A', 'B'] },
      cells: { values: [[1, 2], [3, 4]] },
    }

    render(<PlotlyChart data={tableData} />)

    await waitFor(() => {
      expect(screen.getByTestId('plotly-chart')).toBeInTheDocument()
    })
  })
})
