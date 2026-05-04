#!/usr/bin/env python
"""Fix incorrect await session.execute(...).method() patterns in test_models.py."""

import re

filepath = "tests/test_models.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find: variable = await async_db_session.execute(...) followed by ).method()
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
        method_line = -1
        
        while j < len(lines):
            collect.append(lines[j])
            # Check if this line has ).method( or ).method followed by something
            if re.search(r'\)\.\w+\(', lines[j]) or re.search(r'\)\.\w+\s*$', lines[j]):
                found_method = True
                method_line = j
                break
            j += 1
        
        if found_method:
            # We need to fix this block
            # The pattern is:
            # variable = await async_db_session.execute(...)
            #     ... (arguments)
            # ).method()
            
            # Should be:
            # result = await async_db_session.execute(...)
            #     ... (arguments)
            # variable = result.method()
            
            # Find the variable name (before =)
            first_line = collect[0]
            var_match = re.search(r'(\w+)\s*=\s*await async_db_session\.execute\(', first_line)
            if var_match:
                var_name = var_match.group(1)
                # Get the method name from the last line
                method_line_text = collect[-1]
                method_match = re.search(r'\)\.(\w+)\(', method_line_text)
                if not method_match:
                    method_match = re.search(r'\)\.(\w+)\s*$', method_line_text)
                
                if method_match:
                    method_name = method_match.group(1)
                    
                    # Rebuild the block
                    # First line: result = await async_db_session.execute(
                    new_first = first_line.replace(f'{var_name} = await', 'result = await')
                    new_lines.append(new_first)
                    
                    # Middle lines (arguments) - unchanged
                    for k in range(1, len(collect) - 1):
                        new_lines.append(collect[k])
                    
                    # Last line: ).method() -> result.method()
                    last_line = collect[-1]
                    # Remove the closing ) and .method()
                    # The execute arguments end, and we need to call method on result
                    new_last = last_line.replace(').' + method_name + '(', f'result.{method_name}(')
                    new_last = new_last.replace(').' + method_name, f'result.{method_name}')
                    
                    # Actually, let's be more careful
                    # The last line might be: ).scalars().all()
                    # We need to extract what's after ). and call it on result
                    last_line_stripped = last_line.strip()
                    if last_line_stripped.startswith(').'):
                        # Extract the method chain
                        method_chain = last_line_stripped[2:]  # Remove ').'
                        new_lines.append(f'    {var_name} = result.{method_chain}')
                    else:
                        new_lines.append(last_line)
                    
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
