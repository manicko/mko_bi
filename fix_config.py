"""Fix config.py to add CORS validator and import."""

with open('c:/py_dev/mkobi/src/mkobi/config.py', encoding='utf-8') as f:
    content = f.read()

# Add field_validator import
content = content.replace(
    'from pydantic import BaseModel, Field, PostgresDsn',
    'from pydantic import BaseModel, Field, PostgresDsn, field_validator'
)

# Add validator after cors_origins field
old_text = '''    # --- CORS ---
    cors_origins: list[str] = []

    # --- Database Migrations ---'''

new_text = '''    # --- CORS ---
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

        return value

    # --- Database Migrations ---'''

content = content.replace(old_text, new_text)

with open('c:/py_dev/mkobi/src/mkobi/config.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Config.py updated successfully')
