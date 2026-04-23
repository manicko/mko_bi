# Task: Chart Components

## Goal
Render charts using Plotly

## Implementation Details

### Files to Modify
- `src/mko_bi/dashboards/components/charts/bar.py`
- `src/mko_bi/dashboards/components/charts/dot.py`

### Functions to Implement

#### build_bar_chart(data: DataFrame, x_col: str, y_col: str, title: str = "") -> plotly.graph_objects.Figure
- **Input**: DataFrame, x column name, y column name, optional title
- **Output**: Plotly Figure object
- **Logic**:
  1. Create bar trace with x and y data
  2. Configure layout (title, axis labels)
  3. Return figure

#### build_dot_chart(data: DataFrame, x_col: str, y_col: str, size_col: str = None, title: str = "") -> plotly.graph_objects.Figure
- **Input**: DataFrame, x column, y column, optional size column, optional title
- **Output**: Plotly Figure object
- **Logic**:
  1. Create scatter plot with mode='markers'
  2. Configure marker size if size_col provided
  3. Set layout with title and labels
  4. Return figure

### Plotly Configuration
- Use `go.Bar()` for bar chart
- Use `go.Scatter()` with mode='markers' for dot chart
- Support optional size encoding
- Configure axes and labels
- Support custom title

### Testing
- Test with sample data
- Test with different column types
- Test layout configuration
- Test with empty data
- Test error handling