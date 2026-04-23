# Task: Login Endpoint

## Goal
Implement user authentication via JWT

## Implementation Details

### Files to Modify
- `src/mko_bi/api/routes/auth.py`

### Endpoints

#### POST /login
- **Input**: LoginRequest (email, password)
- **Output**: LoginResponse (access_token)
- **Logic**:
  1. Get user by email using `get_user_by_email()`
  2. Verify password using `verify_password()`
  3. If invalid, raise HTTPException 401
  4. Create JWT token with user ID
  5. Return token

#### POST /register
- **Input**: RegisterRequest (email, password, role)
- **Output**: LoginResponse (access_token)
- **Logic**:
  1. Validate input data
  2. Create user using `create_user()`
  3. Generate JWT token
  4. Return token

### Request/Response Models
- LoginRequest: email (str), password (str)
- LoginResponse: access_token (str)
- RegisterRequest: email (str), password (str), role (str, default "viewer")

### Error Handling
- 401 for invalid credentials
- 400 for duplicate email/validation errors
- Generic error messages (don't reveal which field is wrong)

### Testing
- Test successful login
- Test invalid credentials
- Test registration
- Test duplicate email handling