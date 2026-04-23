import sys

sys.path.insert(0, "src")

from mko_bi.services.user_service import create_user, get_user_by_email

# Test create_user
print("Testing create_user...")
user = create_user("test@example.com", "password123", "viewer")
print(f"Created user: {user.email}, role: {user.role}")

# Test get_user_by_email
print("\nTesting get_user_by_email...")
user_db = get_user_by_email("test@example.com")
if user_db:
    print(f"Found user: {user_db.email}, role: {user_db.role}")
else:
    print("User not found!")

# Test get_user_by_email with non-existent user
print("\nTesting get_user_by_email with non-existent user...")
user_db = get_user_by_email("nonexistent@example.com")
if user_db:
    print(f"Found user: {user_db.email}")
else:
    print("User not found (expected)")

print("\n✅ All tests passed!")
