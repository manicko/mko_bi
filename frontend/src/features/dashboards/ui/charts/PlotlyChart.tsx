import Plot from 'react-plotly.js'
import type { PlotlyData, PlotlyLayout } from '../../../../shared/types/api.types'

interface PlotlyChartProps {
  data: PlotlyData | PlotlyData[]
  layout?: PlotlyLayout
  config?: PlotlyReactConfig
  style?: React.CSSProperties
}

interface PlotlyReactConfig {
  responsive?: boolean
  displayModeBar?: boolean | 'hover'
  [key: string]: unknown
}

export function PlotlyChart({
  data,
  layout,
  config,
  style,
}: PlotlyChartProps) {
  const chartData = Array.isArray(data) ? data : [data]

  return (
    <Plot
      data={chartData as any[]}
      layout={{
        autosize: true,
        margin: { t: 40, r: 20, b: 40, l: 40 },
        ...layout,
      }}
      config={{
        responsive: true,
        displayModeBar: 'hover',
        ...config,
      }}
      style={{ width: '100%', height: '100%', ...style }}
    />
  )
}
