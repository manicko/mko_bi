#!/usr/bin/env python
"""Fix incorrect await session.execute(...).method() patterns in test_models.py."""

import re

filepath = "C:/py_exp/mko_bi/tests/test_models.py"

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if this line has "await async_db_session.execute("
    if 'await async_db_session.execute(' in line:
        # Collect all lines until we find the pattern ).method() or ).method(
        collect = [line]
        j = i + 1
        closing_found = False
        
        while j < len(lines):
            collect.append(lines[j])
            # Check if this line has ).method( or ).method at end
            stripped = lines[j].strip()
            if re.match(r'^\)\.\w+(\(.*\))?\s*$', stripped):
                closing_found = True
                break
            j += 1
        
        if closing_found:
            # Parse the collected lines to extract:
            # 1. The variable name (before =)
            # 2. The method call at the end
            
            first_line = collect[0]
            last_line = collect[-1]
            
            # Get variable name
            var_match = re.search(r'(\w+)\s*=\s*await async_db_session\.execute\(', first_line)
            if var_match:
                var_name = var_match.group(1)
            else:
                var_name = 'result'
            
            # Get method name from last line
            method_match = re.search(r'^\)\.(\w+)(.*)$', last_line.strip())
            if method_match:
                method_name = method_match.group(1)
                method_args = method_match.group(2) if method_match.group(2) else '()'
                
                # Rebuild: first part is execute call without the final ).method()
                # The execute call ends with the line before the last line
                
                # Write the execute call (all except last line)
                for k in range(len(collect) - 1):
                    if k == 0:
                        # Fix first line - remove variable assignment
                        new_line = re.sub(r'\w+\s*=\s*await', 'result = await', collect[k])
                        new_lines.append(new_line.rstrip('\n'))
                    else:
                        new_lines.append(collect[k].rstrip('\n'))
                
                # Add the closing ) for execute
                new_lines.append('        )')
                
                # Add the method call on result
                new_lines.append(f'        {var_name} = result.{method_name}{method_args}'.rstrip('\n'))
                
                i = j + 1
                continue
        
        # If we didn't fix it, just add the original lines
        new_lines.extend([l.rstrip('\n') for l in collect])
        i = j + 1 if closing_found else i + 1
    else:
        new_lines.append(line.rstrip('\n'))
        i += 1

with open(filepath, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print("Done fixing test_models.py")
