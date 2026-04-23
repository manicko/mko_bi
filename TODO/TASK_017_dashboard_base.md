# Task: Dashboard Base Class

## Goal
Base class for all dashboard types with config-driven architecture

## Implementation Details

### Files to Modify
- `src/mko_bi/dashboards/base.py`

### Class to Implement

#### BaseDashboard

**Constructor**:
- `__init__(self, config: Dict[str, Any])`
- Store config as instance variable

**Methods**:

##### get_data(self, dashboard_id: int, filters: Dict = None) -> DataFrame
- Retrieve data for dashboard
- Delegate to `data_service.get_data()`
- Apply filters

##### render(self) -> str
- Render dashboard to HTML/JSON
- To be implemented by subclasses

##### update_config(self, new_config: Dict)
- Update dashboard configuration
- Validate new config

### Abstract Methods
- `render()` - Must be implemented by subclasses

### Config Structure
- Stored as JSON string in database
- Contains: filters, computed_fields, aggregations, group_by

### Testing
- Test config storage
- Test data retrieval
- Test config updates
- Test abstract method enforcement