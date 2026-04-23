# Task: Data Transformations

## Goal
Apply transformations to data including filters and computed fields

## Implementation Details

### Files to Modify
- `src/mko_bi/data/processing/transformations.py`

### Functions to Implement

#### apply_transformations(df: pl.DataFrame, config: Dict[str, Any]) -> pl.DataFrame
- **Input**: DataFrame, transformation configuration
- **Output**: Transformed DataFrame
- **Logic**:
  1. Apply filters sequentially
  2. Apply computed fields
  3. Return transformed DataFrame

### Filter Implementation
- Support various operators: ==, !=, >, <, >=, <=
- Handle different data types (string, numeric, datetime)
- Chain multiple filters with AND logic

### Computed Fields
- Support arithmetic operations: +, -, *, /
- Support column references
- Support literal values
- Support built-in functions: sum, mean, count, etc.

### Error Handling
- Validate column existence
- Validate operation compatibility
- Provide clear error messages

### Testing
- Test simple filters
- Test complex filter chains
- Test computed field calculations
- Test with different data types
- Test error cases