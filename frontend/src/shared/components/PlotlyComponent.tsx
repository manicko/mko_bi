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
const raw: unknown = PlotlyDefault
const PlotComponent: ComponentType<PlotlyChartProps> | null =
  typeof raw === "object" && raw !== null
    ? ((raw as { default?: unknown }).default as ComponentType<PlotlyChartProps>) ??
      (raw as ComponentType<PlotlyChartProps>)
    : typeof raw === "function"
      ? (raw as ComponentType<PlotlyChartProps>)
      : null

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
