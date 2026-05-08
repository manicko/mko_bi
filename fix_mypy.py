"""Fix mypy error in config.py cors_origins validator."""
with open('c:/py_dev/mkobi/src/mkobi/config.py', encoding='utf-8') as f:
    content = f.read()

# Fix the validator to always return list[str]
old_validator = '''    @field_validator("cors_origins", mode="before")
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

        return value'''

new_validator = '''    @field_validator("cors_origins", mode="before")
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

content = content.replace(old_validator, new_validator)

with open('c:/py_dev/mkobi/src/mkobi/config.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed mypy error in config.py')
