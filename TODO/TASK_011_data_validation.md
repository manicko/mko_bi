# Task: Data Validation

## Goal
Validate CSV data against expected schema

## Implementation Details

### Files to Modify
- `src/mko_bi/data/loaders/validator.py`

### Function to Implement

#### validate(df: pl.DataFrame, schema: dict) -> bool
- **Input**: Polars DataFrame, schema dictionary
- **Output**: Boolean (True if valid)
- **Logic**:
  1. Check all expected columns exist
  2. Check column data types match schema
  3. Raise ValueError with descriptive message on failure

### Schema Format
```python
{
    "column_name": expected_type,
    "date_column": pl.Datetime,
    "numeric_column": pl.Float64,
    "string_column": pl.Utf8
}
```

### Validation Steps
1. Column existence check
2. Type checking (basic - can be extended)
3. Raise ValueError with specific missing columns

### Error Messages
- "Missing columns: [col1, col2]"
- "Type mismatch for column X: expected Y, got Z"

### Testing
- Test valid schema
- Test missing columns
- Test type mismatches
- Test empty DataFrame
- Test extra columns (should pass)