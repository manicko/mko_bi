"""Simple test script to verify CORS configuration works."""
import os
import sys

# Add src to path
sys.path.insert(0, 'c:/py_dev/mkobi/src')

# Test 1: Default CORS origins from YAML
print("Test 1: Default CORS origins from YAML")
os.environ.pop('CORS_ORIGINS', None)
from mkobi.config import Settings
settings = Settings()
print(f"  Default CORS origins: {settings.cors_origins}")
assert "https://example.com" in settings.cors_origins
assert "https://app.example.com" in settings.cors_origins
print("  PASSED")

# Test 2: CORS from JSON string env var
print("\nTest 2: CORS from JSON string env var")
os.environ['CORS_ORIGINS'] = '["http://localhost:3000"]'
# Need to reload settings
from importlib import reload
import mkobi.config
reload(mkobi.config)
from mkobi.config import Settings
settings = Settings()
print(f"  CORS origins: {settings.cors_origins}")
assert settings.cors_origins == ["http://localhost:3000"]
print("  PASSED")

# Test 3: CORS from comma-separated string
print("\nTest 3: CORS from comma-separated string")
os.environ['CORS_ORIGINS'] = "http://localhost:3000,http://example.com"
reload(mkobi.config)
from mkobi.config import Settings
settings = Settings()
print(f"  CORS origins: {settings.cors_origins}")
assert "http://localhost:3000" in settings.cors_origins
assert "http://example.com" in settings.cors_origins
print("  PASSED")

# Test 4: CORS from single string
print("\nTest 4: CORS from single string")
os.environ['CORS_ORIGINS'] = "http://localhost:3000"
reload(mkobi.config)
from mkobi.config import Settings
settings = Settings()
print(f"  CORS origins: {settings.cors_origins}")
assert settings.cors_origins == ["http://localhost:3000"]
print("  PASSED")

# Test 5: CORS env overrides YAML
print("\nTest 5: CORS env overrides YAML")
os.environ['CORS_ORIGINS'] = '["http://from-env:3000"]'
reload(mkobi.config)
from mkobi.config import Settings
settings = Settings()
print(f"  CORS origins: {settings.cors_origins}")
assert settings.cors_origins == ["http://from-env:3000"]
assert "https://example.com" not in settings.cors_origins
print("  PASSED")

print("\n" + "="*50)
print("All CORS tests PASSED!")
print("="*50)
