import { PlotlyChart } from './PlotlyChart'
import type { Data, Layout } from 'react-plotly.js'

interface BarChartProps {
  data: Data
  layout?: Layout
  title?: string
  xAxisLabel?: string
  yAxisLabel?: string
}

export function BarChart({
  data,
  layout,
  title,
  xAxisLabel,
  yAxisLabel,
}: BarChartProps) {
  const chartLayout: Partial<Layout> = {
    title: { text: title || '' },
    xaxis: { title: { text: xAxisLabel || '' }, type: 'category' },
    yaxis: { title: { text: yAxisLabel || '' } },
    barmode: 'group',
    ...layout,
  }

  return <PlotlyChart data={[data]} layout={chartLayout} />
}
