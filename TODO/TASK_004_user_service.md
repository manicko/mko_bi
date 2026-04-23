# Task: User Registration Service

## Goal
Create new users with hashed passwords and role management

## Implementation Details

### Files to Modify
- `src/mko_bi/services/user_service.py`
- `src/mko_bi/db/repositories/user_repo.py` (may need updates)

### Function to Implement

#### create_user(email: str, password: str, role: str = "viewer") -> UserModel
- **Input**: Email, plain password, role (admin/editor/viewer)
- **Output**: Created User model
- **Logic**:
  1. Validate email uniqueness (check via repository)
  2. Validate role is one of: admin, editor, viewer
  3. Hash password using `hash_password()`
  4. Create user via repository
  5. Return created user (without password hash in response)

### Validation
- Email format validation
- Unique email constraint
- Role must be one of: admin, editor, viewer
- Password strength requirements

### Repository Updates
- May need to add method for checking email uniqueness
- Ensure password_hash is never returned in queries

### Testing
- Test successful user creation
- Test duplicate email rejection
- Test invalid role handling
- Test password hashing
- Test user retrieval without password hash