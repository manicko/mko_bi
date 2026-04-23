# Task: Bar Chart Component

## Goal
Render bar charts using Plotly

## Implementation Details

### Files to Modify
- `src/mko_bi/dashboards/components/charts/bar.py`

### Functions to Implement

#### build_bar_chart(data: DataFrame, x_col: str, y_col: str, title: str = "") -> plotly.graph_objects.Figure
- **Input**: DataFrame, x column name, y column name, optional title
- **Output**: Plotly Figure object
- **Logic**:
  1. Create bar trace with x and y data
  2. Configure layout (title, axis labels)
  3. Return figure

### Plotly Configuration
- Use `go.Bar()` for bar chart
- Set x and y data from DataFrame columns
- Configure layout with proper labels
- Support custom title

### Testing
- Test with sample data
- Test with different column types
- Test layout configuration
- Test with empty data
- Test error handling