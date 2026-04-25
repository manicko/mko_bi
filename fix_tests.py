import re

with open("tests/test_deps.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace credentials=MagicMock(credentials="...") with token="..."
content = re.sub(
    r'credentials=MagicMock\(credentials="([^"]+)"\)', r'token="\1"', content
)

with open("tests/test_deps.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed")
