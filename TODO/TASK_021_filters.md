# Task: Filters Component

## Goal
Implement global filters for dashboards

## Implementation Details

### Files to Modify
- `src/mko_bi/dashboards/components/filters.py`

### Functions to Implement

#### apply_filters(df: pl.DataFrame, filters: List[Dict]) -> pl.DataFrame
- **Input**: DataFrame, list of filter configurations
- **Output**: Filtered DataFrame
- **Logic**:
  1. For each filter in list:
     - column = filter["column"]
     - operator = filter["operator"] (==, !=, >, <, >=, <=)
     - value = filter["value"]
  2. Apply filter using polars
  3. Chain filters with AND logic
  4. Return filtered DataFrame

### Supported Operators
- == (equals)
- != (not equals)
- > (greater than)
- < (less than)
- >= (greater or equal)
- <= (less or equal)
- contains (for strings)
- in (for list values)

### Filter Configuration
```python
[
    {"column": "year", "operator": "==", "value": 2023},
    {"column": "category", "operator": "in", "value": ["A", "B"]},
    {"column": "sales", "operator": ">", "value": 1000}
]
```

### Testing
- Test single filter
- Test multiple filters
- Test different operators
- Test with string/numeric/datetime columns
- Test empty filter list
- Test invalid operator