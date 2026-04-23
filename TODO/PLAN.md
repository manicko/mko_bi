# Development Plan for BI Dashboard System

## Project Overview
Based on analysis of SPEC.md and STRUCT.md, this is a BI Dashboard System built with FastAPI, Dash, Polars, and PostgreSQL.

## Development Phases

### Phase 1: Core Security & Authentication (High Priority)
1. **Password Hashing** - Implement bcrypt hashing in `core/security.py`
   - `hash_password(password: str) -> str`
   - `verify_password(password: str, hash_value: str) -> bool`

2. **JWT Token Management** - Implement JWT in `core/security.py`
   - `create_access_token(data: dict) -> str`
   - `decode_token(token: str) -> dict`

3. **Login Endpoint** - Implement in `api/routes/auth.py`
   - POST `/login` - User authentication
   - POST `/register` - User registration

4. **User Service** - Implement in `services/user_service.py`
   - `create_user(email, password, role)`
   - User validation and uniqueness checks

### Phase 2: User Management (High Priority)
5. **Users CRUD API** - Implement in `api/routes/users.py`
   - GET `/users` - List all users (admin only)
   - POST `/users` - Create user (admin only)
   - DELETE `/users/{id}` - Delete user (admin only)

6. **Access Control** - Implement in `core/permissions.py`
   - `check_access(user_id, dashboard_id)`
   - `grant_access(user_id, dashboard_id)`
   - `revoke_access(user_id, dashboard_id)`

### Phase 3: Dashboard Management (High Priority)
7. **Dashboard Service** - Implement in `services/dashboard_service.py`
   - `create_dashboard(name, config, user_id)`
   - `get_dashboard(dashboard_id, user_id)`
   - `delete_dashboard(dashboard_id, user_id)`
   - `list_dashboards(user_id)`

8. **Dashboard API** - Implement in `api/routes/dashboards.py`
   - GET `/dashboards` - List accessible dashboards
   - POST `/dashboards` - Create dashboard
   - GET `/dashboards/{id}` - Get dashboard details
   - DELETE `/dashboards/{id}` - Delete dashboard

9. **Access Control Middleware** - Implement in `api/deps.py`
   - Dependency injection for access validation

### Phase 4: Data Processing Pipeline (High Priority)
10. **CSV Upload** - Implement in `api/routes/upload.py`
    - POST `/upload` - Handle CSV file upload
    - File validation (.csv.gz only)
    - Temporary file management

11. **CSV Loading** - Implement in `data/loaders/loader.py`
    - `load_csv(path: str) -> DataFrame`
    - Support gzip compression

12. **Data Validation** - Implement in `data/loaders/validator.py`
    - `validate(df, schema)`
    - Column and type validation

13. **Data Pipeline** - Implement in `data/processing/base.py`
    - `DataPipeline.run(df, config)`
    - Transform and aggregate methods

14. **Data Transformations** - Implement in `data/processing/transformations.py`
    - Filter application
    - Computed fields

15. **Aggregations Registry** - Implement in `data/processing/registry.py`
    - Group by operations
    - YoY calculations
    - Share calculations

16. **Data Storage** - Implement in `data/storage/manager.py`
    - `save_aggregates(dashboard_id, df)`
    - PostgreSQL integration
    - Table creation

17. **Data Retrieval Service** - Implement in `services/data_service.py`
    - `get_data(dashboard_id, filters)`
    - Filter application
    - Pipeline execution

### Phase 5: Dashboard Components (High Priority)
18. **Dashboard Base Class** - Implement in `dashboards/base.py`
    - Config-driven architecture
    - Data retrieval methods

19. **Dashboard Registry** - Implement in `dashboards/registry.py`
    - Dashboard registration
    - Instance retrieval

20. **Chart Components** - Implement in `dashboards/components/charts/`
    - Bar chart (`bar.py`)
    - Dot chart (`dot.py`)

21. **Filters Component** - Implement in `dashboards/components/filters.py`
    - Year, category, brand filters
    - Backend filter application

22. **Layout Component** - Implement in `dashboards/components/layout.py`
    - Multi-axis support
    - Combined charts

### Phase 6: Testing & Infrastructure (Medium Priority)
23. **Logging Configuration** - Configure in `logging_config.py`
    - INFO/WARNING/ERROR levels
    - Structured logging

24. **Error Handling** - Implement middleware and error handlers
    - Proper HTTP status codes
    - Error response formatting

25. **Database Configuration** - Set up migrations and connection pooling
    - PostgreSQL setup
    - Connection management

26. **Docker Configuration** - Create Dockerfile and docker-compose.yml
    - Containerization
    - Service orchestration

27. **Nginx Configuration** - Set up reverse proxy
    - Load balancing
    - SSL termination

28. **Comprehensive Testing** - Write tests for all features
    - Unit tests
    - Integration tests
    - API tests

## Implementation Order
Following the dependency chain:
1. Core security → User management → Access control
2. Dashboard CRUD → Dashboard API → Data service
3. Data pipeline → Storage → Retrieval
4. Chart components → Filters → Layout
5. Infrastructure → Testing

## Key Dependencies
- FastAPI for REST API
- Polars for data processing
- SQLAlchemy for database
- Plotly for visualization
- Pydantic for validation
- JWT + bcrypt for auth