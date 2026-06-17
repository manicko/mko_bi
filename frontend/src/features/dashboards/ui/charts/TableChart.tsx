import { formatDate } from '../../../../shared/utils/formatDate'

interface TableChartData {
  columns?: string[]
  rows: Record<string, unknown>[]
}

interface TableChartProps {
  data: TableChartData
  title?: string
}

function getDisplayValue(value: unknown): string {
  if (value === null || value === undefined) {
    return ''
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  // Handle date strings with consistent formatting
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}/.test(value)) {
    return formatDate(value)
  }
  // At this point value is string | number | boolean | bigint | symbol
  // eslint-disable-next-line @typescript-eslint/no-base-to-string
  return String(value)
}

export function TableChart({ data, title }: TableChartProps) {
  const displayColumns = data.columns || Object.keys(data.rows[0] || {})

  if (!data.rows || data.rows.length === 0) {
    return <p>No data available</p>
  }

  return (
    <div>
      {title && <h3>{title}</h3>}
      <table
        role="grid"
        aria-label={`Data table: ${title || 'chart'}`}
        style={{ width: '100%', borderCollapse: 'collapse' }}
      >
        <caption
          style={{
            position: 'absolute',
            width: '1px',
            height: '1px',
            padding: 0,
            margin: '-1px',
            overflow: 'hidden',
            clip: 'rect(0, 0, 0, 0)',
            whiteSpace: 'nowrap',
            border: 0,
          }}
        >
          {title || 'Data table'}
        </caption>
        <thead>
          <tr>
            {displayColumns.map((col) => (
              <th key={col} scope="col" style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.rows.map((row, idx) => (
            <tr key={idx}>
              {displayColumns.map((col) => (
                <td key={col} style={{ border: '1px solid #ddd', padding: '8px' }}>
                  {getDisplayValue(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}