#!/usr/bin/env python
"""Fix incorrect await session.execute(...).method() patterns in test_models.py."""

import re

filepath = "C:/py_exp/mko_bi/tests/test_models.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find: something = await async_db_session.execute(...) followed by ).method()
# We need to separate the await from the method call

# Find all occurrences of "await async_db_session.execute("
# and fix the following pattern where ).method() is on the next line(s)

lines = content.split('\n')
new_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Check if this line has "await async_db_session.execute("
    if 'await async_db_session.execute(' in line:
        # Collect all lines until we find the closing pattern with ).method()
        collect = [line]
        j = i + 1
        found_method = False
        method_line_idx = -1
        
        while j < len(lines):
            collect.append(lines[j])
            # Check if this line has ).method() pattern
            if re.search(r'^\s*\)\.\w+(\(.*\))?\s*$', lines[j]):
                found_method = True
                method_line_idx = j
                break
            j += 1
        
        if found_method and method_line_idx >= 0:
            # Parse the collected lines
            first_line = collect[0]
            
            # Get the variable name (before =)
            var_match = re.search(r'(\w+)\s*=\s*await async_db_session\.execute\(', first_line)
            var_name = var_match.group(1) if var_match else 'result'
            
            # Get the method call from the last line
            last_line = collect[-1]
            method_match = re.search(r'\)\.(\w+)(.*)$', last_line)
            
            if method_match:
                method_name = method_match.group(1)
                method_args = method_match.group(2) if method_match.group(2) else '()'
                
                # Rebuild: first line without variable assignment
                new_first = re.sub(r'\w+\s*=\s*await', 'result = await', first_line)
                new_lines.append(new_first)
                
                # Middle lines (arguments) - unchanged
                for k in range(1, len(collect) - 1):
                    new_lines.append(collect[k])
                
                # Last line: should be just the closing ) 
                # The method call goes on a new line
                new_lines.append('        )')
                new_lines.append(f'        {var_name} = result.{method_name}{method_args}')
                
                i = j + 1
                continue
        
        # If we didn't fix it, just add the original lines
        new_lines.extend(collect)
        i = j + 1 if found_method else i + 1
    else:
        new_lines.append(line)
        i += 1

new_content = '\n'.join(new_lines)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done fixing test_models.py")
