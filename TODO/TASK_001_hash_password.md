# Task: Password Hashing with Bcrypt

## Goal
Securely hash and verify passwords using bcrypt

## Implementation Details

### Files to Modify
- `src/mko_bi/core/security.py`

### Functions to Implement

#### hash_password(password: str) -> str
- **Input**: Plain text password string
- **Output**: BCrypt hashed password string
- **Logic**:
  1. Generate salt using `bcrypt.gensalt()`
  2. Hash password with salt using `bcrypt.hashpw()`
  3. Return decoded string

#### verify_password(password: str, hash_value: str) -> bool
- **Input**: Plain text password, hashed password string
- **Output**: Boolean indicating match
- **Logic**:
  1. Use `bcrypt.checkpw()` to compare
  2. Return True/False

### Constraints
- Must use bcrypt library
- Never store plain text passwords
- Salt generation must be automatic

### Testing
- Test with various password lengths
- Test hash verification with correct/incorrect passwords
- Verify hashes are different for same password (salt)