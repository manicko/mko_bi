# Task: Data Pipeline Processing

## Goal
Orchestrate data transformation and aggregation pipeline

## Implementation Details

### Files to Modify
- `src/mko_bi/data/processing/base.py`

### Class to Implement

#### DataPipeline

**Methods**:

##### run(df: pl.DataFrame, config: Dict[str, Any]) -> pl.DataFrame
- **Input**: Input DataFrame, processing configuration
- **Output**: Processed DataFrame
- **Logic**:
  1. Call `transform(df, config)`
  2. Call `aggregate(transformed_df, config)`
  3. Return final result

##### transform(df: pl.DataFrame, config: Dict[str, Any]) -> pl.DataFrame
- **Input**: DataFrame, transformation config
- **Output**: Transformed DataFrame
- **Logic**:
  1. Apply filters if present in config
  2. Apply computed fields if present
  3. Return transformed DataFrame

###### Filter Logic
- For each filter in config["filters"]:
  - column = filter["column"]
  - value = filter["value"]
  - df = df.filter(pl.col(column) == value)

###### Computed Fields Logic
- For each field in config["computed_fields"]:
  - name = field["name"]
  - expression = field["expression"]
  - df = df.with_columns([expression.alias(name)])

##### aggregate(df: pl.DataFrame, config: Dict[str, Any]) -> pl.DataFrame
- **Input**: Transformed DataFrame, aggregation config
- **Output**: Aggregated DataFrame
- **Logic**:
  1. Check if aggregations exist in config
  2. Apply group_by if specified
  3. Apply aggregation operations
  4. Return result

### Configuration Structure
```python
{
    "filters": [{"column": "year", "value": 2023}],
    "computed_fields": [
        {"name": "growth_rate", "expression": (col("value") / col("prev_value")) - 1}
    ],
    "aggregations": [
        {"column": "sales", "operation": "sum", "alias": "total_sales"}
    ],
    "group_by": ["category", "region"]
}
```

### Testing
- Test filter application
- Test computed fields
- Test aggregations
- Test group by
- Test pipeline end-to-end