// ESM wrapper for react-plotly.js to avoid CJS/ESM interop issues.
// react-plotly.js v2.6.0 is pure CJS with __esModule flag and exports["default"].
// Vite's dev server interop wraps it as { default: { default: Component } },
// so we need to unwrap .default to get the actual component.
import { type ComponentType, type CSSProperties } from 'react'
import type { Config, Data, Layout } from 'react-plotly.js'
import PlotlyDefault from 'react-plotly.js'

interface PlotlyChartProps {
  data: Data | Data[]
  layout?: Partial<Layout>
  config?: Partial<Config>
  style?: CSSProperties
}

// Resolve the actual Plotly component.
// Vite dev interop returns { default: Component } for CJS with __esModule.
// Production build returns Component directly.
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access */
const raw = PlotlyDefault as any
const PlotComponent: ComponentType<PlotlyChartProps> =
  (typeof raw?.default === 'function' ? raw.default : null) ??
  (typeof raw === 'function' ? raw : null)
/* eslint-enable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access */

export function PlotlyChart({
  data,
  layout,
  config,
  style,
}: PlotlyChartProps) {
  if (!PlotComponent) return null

  const chartData = Array.isArray(data) ? data : [data]

  return (
    <PlotComponent
      data={chartData}
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
