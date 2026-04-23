# Task: CSV Loading with Polars

## Goal
Load and parse CSV data using Polars with gzip support

## Implementation Details

### Files to Modify
- `src/mko_bi/data/loaders/loader.py`

### Function to Implement

#### load_csv(path: str) -> pl.DataFrame
- **Input**: File path to CSV (supports .csv.gz)
- **Output**: Polars DataFrame
- **Logic**:
  1. Use `pl.read_csv()` with `compression="gzip"`
  2. Handle file not found errors
  3. Handle parsing errors
  4. Return DataFrame

### Error Handling
- Catch file not found
- Catch invalid CSV format
- Catch compression errors
- Raise descriptive exceptions

### Dependencies
- polars library
- gzip support built into Polars

### Testing
- Test loading regular CSV
- Test loading gzipped CSV
- Test invalid file path
- Test malformed CSV
- Test empty file handling