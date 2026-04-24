# Task: JWT Token Management

## Goal
Implement JWT-based authentication for API endpoints

## Implementation Details

### Files to Modify
- `src/mko_bi/core/security.py`
- `src/mko_bi/config.py` (SECRET_KEY, ALGORITHM)

### Functions to Implement

#### create_access_token(data: dict) -> str
- **Input**: Dictionary with user data (e.g., {"user_id": 1})
- **Output**: JWT token string
- **Logic**:
  1. Add expiration time to payload
  2. Encode using HS256 algorithm
  3. Return token string

#### decode_token(token: str) -> dict
- **Input**: JWT token string
- **Output**: Decoded payload dictionary
- **Logic**:
  1. Decode token using secret key
  2. Validate expiration
  3. Return payload

### Configuration
- SECRET_KEY from environment variable
- ALGORITHM: HS256
- ACCESS_TOKEN_EXPIRE_MINUTES: 30

### Testing
- Test token creation with sample data
- Test token decoding
- Test expired token handling
- Test invalid token rejection