import { PlotlyChart } from './PlotlyChart'
import type { Data, Layout } from 'react-plotly.js'

interface LineChartProps {
  data: Data
  layout?: Layout
  title?: string
  xAxisLabel?: string
  yAxisLabel?: string
}

export function LineChart({
  data,
  layout,
  title,
  xAxisLabel,
  yAxisLabel,
}: LineChartProps) {
  const chartLayout: Partial<Layout> = {
    title: { text: title || '' },
    xaxis: { title: { text: xAxisLabel || '' } },
    yaxis: { title: { text: yAxisLabel || '' } },
    ...layout,
  }

  return <PlotlyChart data={[data]} layout={chartLayout} />
}
