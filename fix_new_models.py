#!/usr/bin/env python
"""Fix test_new_models.py issues."""

import re

filepath = "C:/py_exp/mko_bi/tests/test_new_models.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Remove await from session.add() calls
content = re.sub(r'await async_db_session\.add\(', 'async_db_session.add(', content)

# Fix 2: Fix AggregationFunctionEnum values
content = re.sub(r'AggregationFunctionEnum\.sum\b', 'AggregationFunctionEnum.sum_val', content)
content = re.sub(r'AggregationFunctionEnum\.min\b', 'AggregationFunctionEnum.min_val', content)
content = re.sub(r'AggregationFunctionEnum\.max\b', 'AggregationFunctionEnum.max_val', content)

# Fix 3: Fix await session.execute(...).method() patterns
# This is complex, let's handle it carefully

lines = content.split('\n')
new_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Check if this line has "= await async_db_session.execute("
    if '= await async_db_session.execute(' in line:
        # Collect until we find ").method()"
        collect = [line]
        j = i + 1
        method_found = False
        method_name = None
        
        while j < len(lines):
            collect.append(lines[j])
            # Check if this line has ").method(" or ").method at end
            stripped = lines[j].strip()
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
            var_match = re.search(r'(\w+)\s*=\s*await async_db_session\.execute\(', first_line)
            var_name = var_match.group(1) if var_match else 'result'
            
            # Write: result = await async_db_session.execute(
            new_first = re.sub(r'\w+\s*=\s*await', 'result = await', first_line)
            new_lines.append(new_first.rstrip('\n'))
            
            # Write middle lines (arguments)
            for k in range(1, len(collect) - 1):
                new_lines.append(collect[k].rstrip('\n'))
            
            # Write closing ) and method call
            new_lines.append('        )')
            new_lines.append(f'        {var_name} = result.{method_name}{method_args}'.rstrip('\n'))
            
            i = j + 1
            continue
    
    new_lines.append(line.rstrip('\n'))
    i += 1

new_content = '\n'.join(new_lines)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done fixing test_new_models.py")
