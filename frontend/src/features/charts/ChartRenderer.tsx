import { PlotlyChart } from './PlotlyChart'
import type { GraphDataWithConfig } from '../../../../shared/types/api.types'

interface ChartRendererProps {
  graph: GraphDataWithConfig
}

export function ChartRenderer({ graph }: ChartRendererProps) {
  return <PlotlyChart data={graph.data} layout={graph.layout} />
}