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
  const chartLayout: Partial<PlotlyLayout> = {
    title: { text: title || '' },
    xaxis: { title: { text: xAxisLabel || '' }, type: 'category' },
    yaxis: { title: { text: yAxisLabel || '' } },
    barmode: 'group',
    ...layout,
  }

  return <PlotlyChart data={{ ...data, type: 'bar' } as PlotlyData} layout={chartLayout as PlotlyLayout} />
}
