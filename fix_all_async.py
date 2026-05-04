#!/usr/bin/env python
"""Fix ALL async/sync issues in test files."""

import re
import os

def fix_file(filepath):
    """Fix common async/sync issues in a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix 1: Remove await from session.add() calls
    content = re.sub(r'await (async_db_session\.add\()', r'\1', content)
    
    # Fix 2: Fix AggregationFunctionEnum values
    content = re.sub(r'AggregationFunctionEnum\.sum\b', 'AggregationFunctionEnum.sum_val', content)
    content = re.sub(r'AggregationFunctionEnum\.min\b', 'AggregationFunctionEnum.min_val', content)
    content = re.sub(r'AggregationFunctionEnum\.max\b', 'AggregationFunctionEnum.max_val', content)
    
    # Fix 3: Fix await session.execute(...).method() patterns
    # This is complex - need to find and fix multi-line patterns
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line has "= await async_db_session.execute(" or "= await self.db.execute("
        if re.search(r'=\s*await (async_db_session|self\.db)\.execute\(', line):
            # Collect until we find ").method()"
            collect = [line]
            j = i + 1
            method_found = False
            method_name = None
            method_args = None
            
            while j < len(lines):
                collect.append(lines[j])
                stripped = lines[j].strip()
                # Check if this line has ").method(" or ").method at end
                match = re.match(r'^\)\.(\w+)(.*)$', stripped)
                if match:
                    method_found = True
                    method_name = match.group(1)
                    method_args = match.group(2) if match.group(2) else '()'
                    break
                j += 1
            
            if method_found and method_name:
                # Rebuild: first line without variable assignment
                first_line = collect[0]
                # Get variable name
                var_match = re.search(r'(\w+)\s*=\s*await', first_line)
                var_name = var_match.group(1) if var_match else 'result'
                
                # Write the execute call (without the ).method())
                # First line: result = await session.execute(
                new_first = re.sub(r'\w+\s*=\s*await', 'result = await', first_line)
                new_lines.append(new_first.rstrip('\n'))
                
                # Middle lines (arguments)
                for k in range(1, len(collect) - 1):
                    new_lines.append(collect[k].rstrip('\n'))
                
                # Last line: should be just the closing )
                new_lines.append('        )')
                
                # Add the method call
                new_lines.append(f'        {var_name} = result.{method_name}{method_args}'.rstrip('\n'))
                
                i = j + 1
                continue
        
        new_lines.append(line.rstrip('\n'))
        i += 1
    
    content = '\n'.join(new_lines)
    
    # Fix 4: Replace session.query() with select()
    # This is complex - need to handle the full pattern
    # For now, let's just note that this needs manual fixing
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
    else:
        print(f"No changes: {filepath}")

# Process all test files
test_dir = "C:/py_exp/mko_bi/tests"
for filename in os.listdir(test_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(test_dir, filename)
        try:
            fix_file(filepath)
        except Exception as e:
            print(f"Error fixing {filepath}: {e}")

# Also fix source files if needed
src_dir = "C:/py_exp/mko_bi/src/mko_bi/data/storage"
for filename in ['manager.py']:
    filepath = os.path.join(src_dir, filename)
    if os.path.exists(filepath):
        try:
            fix_file(filepath)
        except Exception as e:
            print(f"Error fixing {filepath}: {e}")

print("\nDone!")
