import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PlotlyChart } from './PlotlyChart'
import type { Layout, Config } from 'react-plotly.js'

// Mock react-plotly.js
vi.mock('react-plotly.js', () => ({
  default: vi.fn(({ data, layout, config, style }: {
    data: unknown
    layout: Record<string, unknown>
    config: Record<string, unknown>
    style: Record<string, string>
  }) => (
    <div data-testid="plotly-chart" data-layout={JSON.stringify(layout)} data-config={JSON.stringify(config)} data-style={JSON.stringify(style)}>
      <div data-testid="plotly-data">{JSON.stringify(data)}</div>
    </div>
  )),
}))

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

  it('renders with single data object', () => {
    render(<PlotlyChart data={mockBarData} />)

    expect(screen.getByTestId('plotly-chart')).toBeInTheDocument()
    expect(screen.getByTestId('plotly-data')).toHaveTextContent(JSON.stringify([mockBarData]))
  })

  it('renders with array of data objects', () => {
    render(<PlotlyChart data={[mockBarData, mockLineData]} />)

    expect(screen.getByTestId('plotly-chart')).toBeInTheDocument()
    expect(screen.getByTestId('plotly-data')).toHaveTextContent(JSON.stringify([mockBarData, mockLineData]))
  })

  it('applies default layout with autosize', () => {
    render(<PlotlyChart data={mockBarData} />)

    const chart = screen.getByTestId('plotly-chart')
    const layout = JSON.parse(chart.getAttribute('data-layout') || '{}') as Record<string, unknown>

    expect(layout.autosize).toBe(true)
  })

  it('applies default margin to layout', () => {
    render(<PlotlyChart data={mockBarData} />)

    const chart = screen.getByTestId('plotly-chart')
    const layout = JSON.parse(chart.getAttribute('data-layout') || '{}') as Record<string, unknown>

    expect(layout.margin).toEqual({ t: 40, r: 20, b: 40, l: 40 })
  })

  it('merges custom layout with defaults', () => {
    render(<PlotlyChart data={mockBarData} layout={{ title: 'Custom Title' } as Partial<Layout> as Layout} />)

    const chart = screen.getByTestId('plotly-chart')
    const layout = JSON.parse(chart.getAttribute('data-layout') || '{}') as Record<string, unknown>

    expect(layout.title).toBe('Custom Title')
    expect(layout.autosize).toBe(true) // Default preserved
  })

  it('applies default config with responsive', () => {
    render(<PlotlyChart data={mockBarData} />)

    const chart = screen.getByTestId('plotly-chart')
    const config = JSON.parse(chart.getAttribute('data-config') || '{}') as Record<string, unknown>

    expect(config.responsive).toBe(true)
  })

  it('applies default displayModeBar', () => {
    render(<PlotlyChart data={mockBarData} />)

    const chart = screen.getByTestId('plotly-chart')
    const config = JSON.parse(chart.getAttribute('data-config') || '{}') as Record<string, unknown>

    expect(config.displayModeBar).toBe('hover')
  })

  it('merges custom config with defaults', () => {
    render(<PlotlyChart data={mockBarData} config={{ displayModeBar: false }} />)

    const chart = screen.getByTestId('plotly-chart')
    const config = JSON.parse(chart.getAttribute('data-config') || '{}') as Record<string, unknown>

    expect(config.responsive).toBe(true) // Default preserved
    expect(config.displayModeBar).toBe(false) // Custom value
  })

  it('applies default style with width and height', () => {
    render(<PlotlyChart data={mockBarData} />)

    const chart = screen.getByTestId('plotly-chart')
    const style = JSON.parse(chart.getAttribute('data-style') || '{}') as Record<string, string>

    expect(style.width).toBe('100%')
    expect(style.height).toBe('100%')
  })

  it('merges custom styles with defaults', () => {
    render(<PlotlyChart data={mockBarData} style={{ border: '1px solid red' }} />)

    const chart = screen.getByTestId('plotly-chart')
    const style = JSON.parse(chart.getAttribute('data-style') || '{}') as Record<string, string>

    expect(style.width).toBe('100%') // Default preserved
    expect(style.height).toBe('100%') // Default preserved
    expect(style.border).toBe('1px solid red') // Custom value
  })

  it('renders with all props combined', () => {
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

    const chart = screen.getByTestId('plotly-chart')
    const layout = JSON.parse(chart.getAttribute('data-layout') || '{}') as Record<string, unknown>
    const config = JSON.parse(chart.getAttribute('data-config') || '{}') as Record<string, unknown>
    const style = JSON.parse(chart.getAttribute('data-style') || '{}') as Record<string, string>

    expect(layout.title).toBe('Sales Chart')
    expect((layout.xaxis as Record<string, unknown>)?.title).toBe('Months')
    expect(layout.autosize).toBe(true) // Default preserved

    expect(config.responsive).toBe(true) // Default preserved
    expect(config.displayModeBar).toBe(true) // Custom value
    expect(config.scrollZoom).toBe(true) // Custom value

    expect(style.width).toBe('100%') // Default preserved
    expect(style.height).toBe('100%') // Default preserved
    expect(style.backgroundColor).toBe('blue') // Custom value
  })

  it('renders with pie chart data', () => {
    const pieData = {
      values: [30, 20, 50],
      labels: ['A', 'B', 'C'],
      type: 'pie' as const,
    }

    render(<PlotlyChart data={pieData} />)

    expect(screen.getByTestId('plotly-chart')).toBeInTheDocument()
    expect(screen.getByTestId('plotly-data')).toHaveTextContent(JSON.stringify([pieData]))
  })

  it('renders with table data', () => {
    const tableData = {
      type: 'table' as const,
      header: { values: ['A', 'B'] },
      cells: { values: [[1, 2], [3, 4]] },
    }

    render(<PlotlyChart data={tableData} />)

    expect(screen.getByTestId('plotly-chart')).toBeInTheDocument()
  })
})