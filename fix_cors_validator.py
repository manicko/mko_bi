"""Fix CORS validator in config.py to handle pydantic-settings JSON parsing."""
with open('c:/py_dev/mkobi/src/mkobi/config.py', encoding='utf-8') as f:
    content = f.read()

# Replace the CORS field and validator
old_cors = '''    # --- CORS ---
    cors_origins: list[str] = []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, value: Any) -> list[str]:
        """Validate and parse CORS origins from various formats.

        Supports:
        - JSON string: '["http://localhost:3000"]'
        - YAML list: ["http://localhost:3000"]
        - Comma-separated string: "http://localhost:3000,http://example.com"
        - Single string: "http://localhost:3000"
        """
        if isinstance(value, str):
            # Try to parse as JSON first
            try:
                import json

                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(origin) for origin in parsed]
            except json.JSONDecodeError:
                pass

            # Try comma-separated
            if "," in value:
                return [origin.strip() for origin in value.split(",")]

            # Single value
            return [value.strip()]

        if isinstance(value, list):
            return [str(origin) for origin in value]

        return []'''

new_cors = '''    # --- CORS ---
    cors_origins: list[str] = []

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: list[str]) -> list[str]:
        """Validate CORS origins.

        Args:
            value: List of CORS origins (already parsed by pydantic-settings).

        Returns:
            list[str]: Validated list of CORS origins.
        """
        if not isinstance(value, list):
            return []
        return [str(origin) for origin in value]'''

content = content.replace(old_cors, new_cors)

with open('c:/py_dev/mkobi/src/mkobi/config.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed CORS validator in config.py')
