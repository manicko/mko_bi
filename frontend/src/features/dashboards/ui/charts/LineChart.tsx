import { PlotlyChart } from './PlotlyChart'
import type { PlotlyData, PlotlyLayout } from '../../../../shared/types/api.types'

interface LineChartProps {
  data: PlotlyData
  layout?: PlotlyLayout
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
  const chartLayout: Partial<PlotlyLayout> = {
    title: { text: title || '' },
    xaxis: { title: { text: xAxisLabel || '' } },
    yaxis: { title: { text: yAxisLabel || '' } },
    ...layout,
  }

  return <PlotlyChart data={{ ...data, type: 'scatter', mode: 'lines+markers' } as PlotlyData} layout={chartLayout as PlotlyLayout} />
}
