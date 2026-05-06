declare module 'react-plotly.js' {
  import { ComponentType } from 'react'

  interface PlotParams {
    data: Array<Record<string, unknown>>
    layout?: Record<string, unknown>
    config?: Record<string, unknown>
    style?: React.CSSProperties
    [key: string]: unknown
  }

  const Plot: ComponentType<PlotParams>
  export default Plot
}
