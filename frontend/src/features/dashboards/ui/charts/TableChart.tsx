import type { PlotlyData } from '../../../../shared/types/api.types'

interface TableChartProps {
  data: PlotlyData
  title?: string
}

export function TableChart({ data, title }: TableChartProps) {
  const columns = data.columns as string[] | undefined
  const rows = data.rows as Record<string, unknown>[] | undefined

  if (!rows || rows.length === 0) {
    return <p>No data available</p>
  }

  const displayColumns = columns || Object.keys(rows[0] || {})

  return (
    <div>
      {title && <h3>{title}</h3>}
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {displayColumns.map((col) => (
              <th key={col} style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx}>
              {displayColumns.map((col) => (
                <td key={col} style={{ border: '1px solid #ddd', padding: '8px' }}>
                  {String(row[col] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
