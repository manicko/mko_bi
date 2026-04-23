import sys

sys.path.insert(0, "src")

from mko_bi.core.security import hash_password, verify_password

print("Security module OK")
hashed = hash_password("test123")
print(f"Hashed: {hashed[:50]}...")
print(f"Verify: {verify_password('test123', hashed)}")
