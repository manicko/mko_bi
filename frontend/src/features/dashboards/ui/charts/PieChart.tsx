import { PlotlyChart } from './PlotlyChart'
import type { Data, Layout } from 'react-plotly.js'

interface PieChartProps {
  data: Data
  layout?: Layout
  title?: string
}

export function PieChart({ data, layout, title }: PieChartProps) {
  const chartLayout: Partial<Layout> = {
    title: { text: title || '' },
    ...layout,
  }

  return <PlotlyChart data={[data]} layout={chartLayout} />
}
