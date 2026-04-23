import sys

sys.path.insert(0, "src")

# Test all imports
from mko_bi.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)
from mko_bi.services.user_service import create_user, get_user_by_email
from mko_bi.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

print("✓ All imports successful!")

# Test config
print(f"✓ SECRET_KEY: {SECRET_KEY[:10]}...")
print(f"✓ ALGORITHM: {ALGORITHM}")
print(f"✓ ACCESS_TOKEN_EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES}")

# Test password hashing
password = "test_password_123"
hashed = hash_password(password)
print(f"✓ Password hashing works: {hashed[:50]}...")

# Test password verification
assert verify_password(password, hashed), "Password verification failed"
print("✓ Password verification works!")

# Test JWT token creation
token_data = {"user_id": 1, "email": "test@example.com"}
token = create_access_token(token_data)
print(f"✓ JWT token created: {token[:50]}...")

# Test JWT token decoding
decoded = decode_token(token)
assert decoded["user_id"] == 1, "User ID mismatch"
assert decoded["email"] == "test@example.com", "Email mismatch"
print("✓ JWT token decoding works!")

# Test user creation
user = create_user("test_user@example.com", "user_password_123", "viewer")
print(f"✓ User created: {user.email}, role: {user.role}")

# Test get_user_by_email
user_db = get_user_by_email("test_user@example.com")
assert user_db is not None, "User not found"
assert user_db.email == "test_user@example.com", "Email mismatch"
assert user_db.role == "viewer", "Role mismatch"
print(f"✓ User retrieval works: {user_db.email}, role: {user_db.role}")

# Test get_user_by_email with non-existent user
user_db = get_user_by_email("nonexistent@example.com")
assert user_db is None, "Non-existent user should return None"
print("✓ Non-existent user returns None")

print("\n✅ All tests passed!")
