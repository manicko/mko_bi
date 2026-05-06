import { PlotlyChart } from './PlotlyChart'
import type { PlotlyData, PlotlyLayout } from '../../../../shared/types/api.types'

interface BarChartProps {
  data: PlotlyData
  layout?: PlotlyLayout
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
  const chartLayout: PlotlyLayout = {
    title: title || '',
    xaxis: { title: xAxisLabel || '', type: 'category' },
    yaxis: { title: yAxisLabel || '' },
    barmode: 'group',
    ...layout,
  }

  return <PlotlyChart data={{ ...data, type: 'bar' }} layout={chartLayout} />
}
