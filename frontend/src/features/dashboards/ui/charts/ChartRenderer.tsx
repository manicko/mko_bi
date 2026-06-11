import { PlotlyChart } from './PlotlyChart'
import { LineChart } from './LineChart'
import { TableChart } from './TableChart'
import type { GraphDataWithConfig } from '../../../../shared/types/api.types'
import type { Data } from 'react-plotly.js'

interface ChartRendererProps {
  graph: GraphDataWithConfig
}

function convertToPlotlyData(
  graph: GraphDataWithConfig,
): Data[] {
  const config = graph.config || {}
  const xCol = config.x || 'x'
  const colorCol = config.color
  const metricCols = config.metrics || ['y']
  const orientation = config.orientation || 'v'

  // If data is already in Plotly format (has x/y fields), return as-is
  if (graph.data.length > 0 && 'x' in graph.data[0] && 'y' in graph.data[0]) {
    return graph.data
  }

  // Convert flat dicts to Plotly Data format
  const metricCol = metricCols[0]

  const makeTrace = (xVals: (string | number)[], yVals: (string | number)[], name?: string): Data => {
    const trace: Record<string, unknown> = {
      x: xVals,
      y: yVals,
      type: graph.type === 'pie' ? 'pie' :
            graph.type === 'line' ? 'scatter' : 'bar',
    }
    if (name) trace.name = name
    if (graph.type === 'bar') {
      trace.orientation = orientation
    }
    if (graph.type === 'line') {
      trace.mode = 'lines'
    }
    return trace
  }

  if (colorCol) {
    // Group by color column for grouped bar chart
    const groups: Record<string, { x: (string | number)[]; y: (string | number)[] }> = {}
    for (const row of graph.data as unknown as Record<string, unknown>[]) {
      const colorVal = row[colorCol]
      const color = colorVal !== undefined && colorVal !== null
        ? (typeof colorVal === 'string' || typeof colorVal === 'number' ? String(colorVal) : 'unknown')
        : 'unknown'
      const xVal = row[xCol]
      const x = xVal !== undefined && xVal !== null
        ? (typeof xVal === 'string' || typeof xVal === 'number' ? xVal : '')
        : ''
      const y = Number(row[metricCol] ?? 0)
      if (!groups[color]) {
        groups[color] = { x: [], y: [] }
      }
      groups[color].x.push(x)
      groups[color].y.push(y)
    }
    return Object.entries(groups).map(([name, trace]) => makeTrace(trace.x, trace.y, name))
  }

  // Single series
  const xVals: (string | number)[] = []
  const yVals: (string | number)[] = []
  for (const row of graph.data as unknown as Record<string, unknown>[]) {
    xVals.push(row[xCol] as string | number)
    yVals.push(Number(row[metricCol] ?? 0))
  }
  return [makeTrace(xVals, yVals)]
}

export function ChartRenderer({ graph }: ChartRendererProps) {
  // Table charts render as native HTML tables (no Plotly conversion)
  if (graph.type === 'table') {
    return <TableChart data={{ rows: graph.data }} />
  }

  // Line charts use LineChart component with scatter type
  if (graph.type === 'line') {
    return <LineChart data={convertToPlotlyData(graph)[0]} layout={graph.layout} />
  }

  // Bar and pie charts use PlotlyChart
  const plotlyData = convertToPlotlyData(graph)

  // Bar charts get default layout (barmode, xaxis type)
  if (graph.type === 'bar') {
    const barLayout = {
      ...graph.layout,
      barmode: (graph.config?.barmode || 'group') as 'group' | 'overlay' | 'relative' | 'stack',
      xaxis: { type: 'category' as const },
    }
    return <PlotlyChart data={plotlyData} layout={barLayout} />
  }

  return <PlotlyChart data={plotlyData} layout={graph.layout} />
}