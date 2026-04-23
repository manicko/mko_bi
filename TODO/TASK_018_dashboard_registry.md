# Task: Dashboard Registry

## Goal
Register and manage dashboard types

## Implementation Details

### Files to Modify
- `src/mko_bi/dashboards/registry.py`

### Class to Implement

#### DashboardRegistry

**Methods**:

##### register(cls, dashboard_class)
- Register a dashboard class
- Store in class-level dictionary
- Key: dashboard name or type
- Value: dashboard class

##### get(cls, dashboard_id) -> BaseDashboard
- Retrieve dashboard instance by ID
- Look up dashboard type from database
- Instantiate appropriate dashboard class
- Return dashboard instance

##### list_all() -> List[Dict]
- Return list of all registered dashboards
- Include: id, name, type, config

### Internal Structure
- Class-level dict: `_registry = {}`
- Database table: `dashboards` (already exists)

### Testing
- Test registration
- Test retrieval
- Test listing
- Test with multiple dashboard types