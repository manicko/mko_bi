"""Simple test script to verify CORS configuration works."""
import os
import sys
from importlib import reload

# Add src to path
sys.path.insert(0, 'c:/py_dev/mkobi/src')

import mkobi.config
from mkobi.config import Settings


def test_default_cors() -> None:
    """Test 1: Default CORS origins from YAML."""
    print("Test 1: Default CORS origins from YAML")
    os.environ.pop('CORS_ORIGINS', None)
    # Reload config to pick up env changes
    reload(mkobi.config)
    settings = Settings()
    print(f"  Default CORS origins: {settings.cors_origins}")
    assert "https://example.com" in settings.cors_origins
    assert "https://app.example.com" in settings.cors_origins
    print("  PASSED")


def test_cors_from_json_env() -> None:
    """Test 2: CORS from JSON string env var."""
    print("\nTest 2: CORS from JSON string env var")
    os.environ['CORS_ORIGINS'] = '["http://localhost:3000"]'
    reload(mkobi.config)
    settings = Settings()
    print(f"  CORS origins: {settings.cors_origins}")
    assert settings.cors_origins == ["http://localhost:3000"]
    print("  PASSED")


def test_cors_from_comma_separated() -> None:
    """Test 3: CORS from comma-separated string."""
    print("\nTest 3: CORS from comma-separated string")
    os.environ['CORS_ORIGINS'] = "http://localhost:3000,http://example.com"
    reload(mkobi.config)
    settings = Settings()
    print(f"  CORS origins: {settings.cors_origins}")
    assert "http://localhost:3000" in settings.cors_origins
    assert "http://example.com" in settings.cors_origins
    print("  PASSED")


def test_cors_from_single_string() -> None:
    """Test 4: CORS from single string."""
    print("\nTest 4: CORS from single string")
    os.environ['CORS_ORIGINS'] = "http://localhost:3000"
    reload(mkobi.config)
    settings = Settings()
    print(f"  CORS origins: {settings.cors_origins}")
    assert settings.cors_origins == ["http://localhost:3000"]
    print("  PASSED")


def test_cors_env_overrides_yaml() -> None:
    """Test 5: CORS env overrides YAML."""
    print("\nTest 5: CORS env overrides YAML")
    os.environ['CORS_ORIGINS'] = '["http://from-env:3000"]'
    reload(mkobi.config)
    settings = Settings()
    print(f"  CORS origins: {settings.cors_origins}")
    assert settings.cors_origins == ["http://from-env:3000"]
    assert "https://example.com" not in settings.cors_origins
    print("  PASSED")


if __name__ == "__main__":
    test_default_cors()
    test_cors_from_json_env()
    test_cors_from_comma_separated()
    test_cors_from_single_string()
    test_cors_env_overrides_yaml()

    print("\n" + "="*50)
    print("All CORS tests PASSED!")
    print("="*50)
