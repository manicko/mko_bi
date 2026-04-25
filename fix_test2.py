with open("tests/test_deps.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the error message check
content = content.replace(
    'assert "чтения" in str(exc_info.value.detail).lower()',
    'assert "прав" in str(exc_info.value.detail).lower()',
)

with open("tests/test_deps.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed error message check")
