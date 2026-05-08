"""Add CORS tests to test_config.py."""
with open('c:/py_dev/mkobi/tests/test_config.py', encoding='utf-8') as f:
    content = f.read()

# Find the end of the file to add new tests
# Add CORS test class before the last line
cors_tests = '''

class TestCORSOrigins(TestSettingsBase):
    """Tests for CORS origins configuration."""

    def test_cors_origins_default_from_yaml(self):
        """Test that CORS origins are loaded from YAML config."""
        settings = Settings()
        # Default from app.yaml
        assert "https://example.com" in settings.cors_origins
        assert "https://app.example.com" in settings.cors_origins

    def test_cors_origins_from_env_json(self, monkeypatch):
        """Test CORS origins parsing from JSON string in env var."""
        monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000"]')
        settings = Settings()
        assert settings.cors_origins == ["http://localhost:3000"]

    def test_cors_origins_from_env_multiple(self, monkeypatch):
        """Test CORS origins parsing from JSON array in env var."""
        monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000", "https://app.example.com"]')
        settings = Settings()
        assert "http://localhost:3000" in settings.cors_origins
        assert "https://app.example.com" in settings.cors_origins

    def test_cors_origins_from_env_comma_separated(self, monkeypatch):
        """Test CORS origins parsing from comma-separated string."""
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://example.com")
        settings = Settings()
        assert "http://localhost:3000" in settings.cors_origins
        assert "http://example.com" in settings.cors_origins

    def test_cors_origins_from_env_single(self, monkeypatch):
        """Test CORS origins parsing from single string."""
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
        settings = Settings()
        assert settings.cors_origins == ["http://localhost:3000"]

    def test_cors_origins_env_overrides_yaml(self, monkeypatch):
        """Test that env var overrides YAML config."""
        monkeypatch.setenv("CORS_ORIGINS", '["http://from-env:3000"]')
        settings = Settings()
        assert settings.cors_origins == ["http://from-env:3000"]
        assert "https://example.com" not in settings.cors_origins
'''

# Append the CORS tests at the end of the file
content = content.rstrip() + cors_tests

with open('c:/py_dev/mkobi/tests/test_config.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('CORS tests added to test_config.py')
