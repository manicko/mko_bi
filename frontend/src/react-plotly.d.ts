declare module 'react-plotly.js' {
  import { ComponentType } from 'react'
  import type { Config, Data, Layout } from 'plotly.js'

  interface PlotParams {
    data: Data[]
    layout?: Partial<Layout>
    config?: Partial<Config>
    style?: React.CSSProperties
    [key: string]: unknown
  }

  const Plot: ComponentType<PlotParams>
  export default Plot

  // Re-export plotly.js types for convenience
  export type { Config, Data, Layout }
}
