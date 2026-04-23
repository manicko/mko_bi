# Task: Access Control System

## Goal
Implement fine-grained access control between users and dashboards

## Implementation Details

### Files to Modify
- `src/mko_bi/core/permissions.py`
- `src/mko_bi/api/deps.py` (for dependency injection)

### Functions to Implement

#### check_access(user_id: int, dashboard_id: int) -> bool
- **Input**: User ID, Dashboard ID
- **Output**: Boolean indicating access
- **Logic**:
  1. If user is admin (role == "admin"), return True
  2. Query AccessRepository for user_id/dashboard_id combination
  3. Return True if record exists, False otherwise

#### grant_access(user_id: int, dashboard_id: int) -> bool
- **Input**: User ID, Dashboard ID
- **Output**: Success boolean
- **Logic**:
  1. Create access record in repository
  2. Return True on success

#### revoke_access(user_id: int, dashboard_id: int) -> bool
- **Input**: User ID, Dashboard ID
- **Output**: Success boolean
- **Logic**:
  1. Delete access record from repository
  2. Return True on success

#### get_user_by_id(user_id: int) -> Optional[UserModel]
- **Input**: User ID
- **Output**: User model or None
- **Logic**: Query user repository

#### get_user_by_email(email: str) -> Optional[UserModel]
- **Input**: Email address
- **Output**: User model or None
- **Logic**: Query user repository

### Repository
- AccessRepository methods: create, delete, get (user_id, dashboard_id)
- UserRepository methods: get, get_by_email

### Testing
- Test admin access (always true)
- Test granted access
- Test revoked access
- Test non-existent combinations
- Test user lookup methods