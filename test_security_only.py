import sys

sys.path.insert(0, "src")

# Test password hashing
from mko_bi.core.security import hash_password, verify_password

print("Testing password hashing...")
password = "test_password_123"
hashed = hash_password(password)
print("✓ Password hashing works: " + hashed[:50] + "...")

# Test password verification
assert verify_password(password, hashed), "Password verification failed"
print("✓ Password verification works!")

# Test JWT token functions
from mko_bi.core.security import create_access_token, decode_token

print("\nTesting JWT token functions...")
token_data = {"user_id": 1, "email": "test@example.com"}
token = create_access_token(token_data)
print("✓ JWT token created: " + token[:50] + "...")

# Test JWT token decoding
decoded = decode_token(token)
assert decoded["user_id"] == 1, "User ID mismatch"
assert decoded["email"] == "test@example.com", "Email mismatch"
print("✓ JWT token decoding works!")

# Test user service imports
from mko_bi.services.user_service import create_user, get_user_by_email

print("✓ User service imports work!")

print("\n✅ All security module tests passed!")
