# Task: Layout Component

## Goal
Create flexible layout for combining charts

## Implementation Details

### Files to Modify
- `src/mko_bi/dashboards/components/layout.py`

### Functions to Implement

#### create_layout(charts: List[Figure], layout_type: str = "grid") -> Dict
- **Input**: List of Plotly figures, layout type
- **Output**: Layout configuration dict
- **Logic**:
  1. Configure layout based on type
  2. Support: grid, vertical, horizontal, tabs
  3. Return layout config for Dash/Dash Bootstrap

### Layout Types
- **grid**: Multiple charts in grid format
- **vertical**: Charts stacked vertically
- **horizontal**: Charts side by side
- **tabs**: Charts in separate tabs

### Configuration
- Support responsive design
- Configure spacing and sizing
- Support different screen sizes

### Testing
- Test different layout types
- Test with various numbers of charts
- Test responsive behavior
- Test with empty chart list