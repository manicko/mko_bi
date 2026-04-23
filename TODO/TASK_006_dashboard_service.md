# Task: Dashboard CRUD Service

## Goal
Manage dashboards with config-driven architecture

## Implementation Details

### Files to Modify
- `src/mko_bi/services/dashboard_service.py`
- `src/mko_bi/db/models/dashboard.py` (may need updates)

### Functions to Implement

#### create_dashboard(name: str, config: Dict[str, Any], user_id: int) -> DashboardModel
- **Input**: Dashboard name, configuration JSON, creator user_id
- **Output**: Created Dashboard model
- **Logic**:
  1. Validate name is not empty
  2. Validate config structure (basic validation)
  3. Create dashboard record via repository
  4. Return dashboard model

#### get_dashboard(dashboard_id: int, user_id: int) -> Optional[DashboardModel]
- **Input**: Dashboard ID, requesting user_id
- **Output**: Dashboard model or None
- **Logic**:
  1. Query dashboard by ID
  2. If not found, return None
  3. Check access using `check_access(user_id, dashboard_id)`
  4. Return dashboard or None

#### delete_dashboard(dashboard_id: int, user_id: int) -> bool
- **Input**: Dashboard ID, user_id
- **Output**: Success boolean
- **Logic**:
  1. Check admin access (or ownership)
  2. Delete dashboard and associated access records
  3. Return success

#### list_dashboards(user_id: int) -> List[DashboardModel]
- **Input**: Requesting user_id
- **Output**: List of accessible dashboards
- **Logic**:
  1. Get all dashboards
  2. Filter by `check_access(user_id, dashboard.id)`
  3. Return filtered list

### Configuration Structure
- config: JSON string containing:
  - filters: [{column, value}]
  - computed_fields: [{name, expression}]
  - aggregations: [{column, operation, alias}]

### Testing
- Test dashboard creation
- Test access control
- Test listing filtered by access
- Test deletion
- Test config validation