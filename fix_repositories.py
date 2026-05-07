"""Fix repository files by removing @classmethod and changing cls to self."""

import re
from pathlib import Path

repo_dir = Path("C:/py_dev/mkobi/src/mkobi/db/repositories")

for py_file in repo_dir.glob("*.py"):
    content = py_file.read_text(encoding="utf-8")
    
    # Remove @classmethod lines (with possible whitespace)
    content = re.sub(r'\s*@classmethod\s*\n', '\n', content)
    
    # Change cls to self in method signatures
    # Pattern matches: async def method_name(cls, -> async def method_name(self,
    content = re.sub(r'(async def \w+\()cls(,\s*)', r'\1self\2', content)
    
    py_file.write_text(content, encoding="utf-8")
    print(f"Fixed: {py_file.name}")
