import { PlotlyChart } from './PlotlyChart'
import type { PlotlyData, PlotlyLayout } from '../../../../shared/types/api.types'

interface PieChartProps {
  data: PlotlyData
  layout?: PlotlyLayout
  title?: string
}

export function PieChart({ data, layout, title }: PieChartProps) {
  const chartLayout: Partial<PlotlyLayout> = {
    title: { text: title || '' },
    ...layout,
  }

  return <PlotlyChart data={{ ...data, type: 'pie' } as PlotlyData} layout={chartLayout as PlotlyLayout} />
}
