# Task: Data Retrieval Service

## Goal
Retrieve and serve aggregated data to dashboard frontend

## Implementation Details

### Files to Modify
- `src/mko_bi/services/data_service.py`

### Function to Implement

#### get_data(dashboard_id: int, filters: Dict[str, Any] = None) -> list
- **Input**: Dashboard ID, optional filters
- **Output**: List of data records (dicts)
- **Logic**:
  1. Get dashboard config (via repository)
  2. Load aggregated data using `get_aggregates()`
  3. Apply filters if provided
  4. Convert to list of dicts
  5. Return data

### Filter Application
- Support filtering on any column
- Support multiple filter conditions (AND logic)
- Filter types: equals, not equals, greater than, less than

### Data Format
- Convert DataFrame to list of dictionaries
- Each row becomes a dict
- Column names as keys

### Error Handling
- Return empty list if dashboard not found
- Return empty list if no data
- Handle filter parsing errors

### Testing
- Test data retrieval
- Test with filters
- Test without filters
- Test non-existent dashboard
- Test empty result set