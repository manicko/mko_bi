# Task: Dot Chart Component

## Goal
Render dot charts using Plotly

## Implementation Details

### Files to Modify
- `src/mko_bi/dashboards/components/charts/dot.py`

### Functions to Implement

#### build_dot_chart(data: DataFrame, x_col: str, y_col: str, size_col: str = None, title: str = "") -> plotly.graph_objects.Figure
- **Input**: DataFrame, x column, y column, optional size column, optional title
- **Output**: Plotly Figure object
- **Logic**:
  1. Create scatter plot with mode='markers'
  2. Configure marker size if size_col provided
  3. Set layout with title and labels
  4. Return figure

### Plotly Configuration
- Use `go.Scatter()` with mode='markers'
- Support optional size encoding
- Configure axes and labels
- Support custom title

### Testing
- Test basic dot chart
- Test with size encoding
- Test layout
- Test with various data ranges
- Test error cases