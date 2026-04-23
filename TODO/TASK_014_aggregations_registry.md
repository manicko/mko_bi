# Task: Aggregations Registry

## Goal
Implement various aggregation operations for data analysis

## Implementation Details

### Files to Modify
- `src/mko_bi/data/processing/registry.py`

### Functions/Classes to Implement

#### Aggregation Registry
Maintain a registry of available aggregation operations.

#### Aggregation Operations

##### group_by(df: pl.DataFrame, columns: List[str]) -> pl.DataFrame
- Group DataFrame by specified columns

##### sum_agg(df: pl.DataFrame, column: str, alias: str) -> pl.DataFrame
- Calculate sum of column

##### mean_agg(df: pl.DataFrame, column: str, alias: str) -> pl.DataFrame
- Calculate mean of column

##### count_agg(df: pl.DataFrame, alias: str) -> pl.DataFrame
- Count rows

##### min_agg(df: pl.DataFrame, column: str, alias: str) -> pl.DataFrame
- Find minimum value

##### max_agg(df: pl.DataFrame, column: str, alias: str) -> pl.DataFrame
- Find maximum value

##### yoy_agg(df: pl.DataFrame, column: str, period: str = "year") -> pl.DataFrame
- Calculate Year-over-Year growth
- Compare current period with previous period

##### share_agg(df: pl.DataFrame, value_col: str, total_col: str) -> pl.DataFrame
- Calculate percentage/share
- value_col / total_col * 100

### Configuration Format
```python
{
    "aggregations": [
        {"column": "sales", "operation": "sum", "alias": "total_sales"},
        {"column": "quantity", "operation": "mean", "alias": "avg_qty"},
        {"column": "id", "operation": "count", "alias": "count"}
    ],
    "group_by": ["category", "region"]
}
```

### Testing
- Test each aggregation operation
- Test with different data types
- Test group by combinations
- Test YoY calculation
- Test share calculation