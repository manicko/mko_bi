# Task: Dashboard API Endpoints

## Goal
REST API for dashboard management and data retrieval

## Implementation Details

### Files to Modify
- `src/mko_bi/api/routes/dashboards.py`

### Endpoints

#### GET /dashboards
- **Authentication**: Required (JWT)
- **Authorization**: Only dashboards user has access to
- **Output**: List of DashboardResponse (id, name, config)
- **Logic**:
  1. Get user_id from JWT
  2. Call `list_dashboards(user_id)`
  3. Return filtered list

#### POST /dashboards
- **Authentication**: Required
- **Authorization**: Admin or can create own
- **Input**: DashboardCreateRequest (name, config)
- **Output**: DashboardCreateResponse (id, name)
- **Logic**:
  1. Get user_id from JWT
  2. Call `create_dashboard()`
  3. Return created dashboard info

#### GET /dashboards/{id}
- **Authentication**: Required
- **Authorization**: Must have access to dashboard
- **Output**: DashboardResponse with config
- **Logic**:
  1. Get user_id from JWT
  2. Call `get_dashboard(dashboard_id, user_id)`
  3. Return 404 if None
  4. Return dashboard info

#### DELETE /dashboards/{id}
- **Authentication**: Required
- **Authorization**: Admin only
- **Input**: dashboard_id path parameter
- **Output**: 204 No Content
- **Logic**:
  1. Verify admin
  2. Call `delete_dashboard()`
  3. Return 204

### Request/Response Models
- DashboardResponse: id, name, config
- DashboardCreateRequest: name, config
- DashboardCreateResponse: id, name

### Error Handling
- 401 for invalid/missing JWT
- 403 for insufficient permissions
- 404 for non-existent dashboard
- 400 for invalid config

### Testing
- Test authenticated access
- Test authorization filters
- Test CRUD operations
- Test config validation