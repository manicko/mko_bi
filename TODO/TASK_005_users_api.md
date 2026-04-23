# Task: Users CRUD API

## Goal
Manage users with role-based access control (admin only)

## Implementation Details

### Files to Modify
- `src/mko_bi/api/routes/users.py`

### Endpoints

#### GET /users
- **Authentication**: Required (JWT in header)
- **Authorization**: Admin only
- **Output**: List of UserResponse (id, email, role)
- **Logic**:
  1. Verify JWT and extract user_id
  2. Check if user is admin using `check_access()` or role check
  3. Query all users via repository
  4. Filter out password hashes
  5. Return list

#### POST /users
- **Authentication**: Required
- **Authorization**: Admin only
- **Input**: User creation data (email, password, role)
- **Output**: Created user response
- **Logic**:
  1. Verify JWT and admin status
  2. Call `create_user()` service
  3. Return created user (without password)

#### DELETE /users/{id}
- **Authentication**: Required
- **Authorization**: Admin only (cannot delete self)
- **Input**: user_id path parameter
- **Output**: Success message
- **Logic**:
  1. Verify JWT and admin status
  2. Prevent self-deletion
  3. Call repository delete method
  4. Return success

### Request/Response Models
- UserResponse: id, email, role (no password_hash)
- User creation: email, password, role

### Error Handling
- 401 if not authenticated
- 403 if not admin
- 404 if user not found
- 400 for validation errors

### Testing
- Test admin access
- Test non-admin rejection
- Test user listing
- Test creation and deletion
- Test self-deletion prevention