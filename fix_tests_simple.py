"""Fix test files - remove config={} and update AggregationFunctionEnum usages."""

import os

def fix_test_file(filepath):
    """Fix a test file by removing config={} and updating enum usages."""
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    
    # Remove config={} from Dashboard creations
    # Pattern: , config={}\n        )
    lines = content.split('\n')
    new_lines = []
    skip_next = False
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
        if 'config={}' in line and i + 1 < len(lines) and ')' in lines[i + 1]:
            # Skip this line and the next closing paren
            skip_next = True
            continue
        new_lines.append(line)
    content = '\n'.join(new_lines)
    
    # Update AggregationFunctionEnum member names
    replacements = {
        'AggregationFunctionEnum.sum_val': 'AggregationFunctionEnum.SUM',
        'AggregationFunctionEnum.mean': 'AggregationFunctionEnum.MEAN',
        'AggregationFunctionEnum.count_val': 'AggregationFunctionEnum.COUNT',
        'AggregationFunctionEnum.min_val': 'AggregationFunctionEnum.MIN',
        'AggregationFunctionEnum.max_val': 'AggregationFunctionEnum.MAX',
        'AggregationFunctionEnum.median': 'AggregationFunctionEnum.MEDIAN',
        'AggregationFunctionEnum.std': 'AggregationFunctionEnum.STD',
        'AggregationFunctionEnum.var': 'AggregationFunctionEnum.VAR',
        'AggregationFunctionEnum.first': 'AggregationFunctionEnum.FIRST',
        'AggregationFunctionEnum.last': 'AggregationFunctionEnum.LAST',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Update enum string values to enum members
    # Filter type
    content = content.replace('type="select"', 'type=FilterType.SELECT')
    content = content.replace('type="multiselect"', 'type=FilterType.MULTISELECT')
    content = content.replace('type="range"', 'type=FilterType.RANGE')
    content = content.replace('type="date"', 'type=FilterType.DATE')
    
    # DashboardPermission
    content = content.replace('permission="view"', 'permission=DashboardPermission.VIEW')
    content = content.replace('permission="edit"', 'permission=DashboardPermission.EDIT')
    content = content.replace('permission="admin"', 'permission=DashboardPermission.ADMIN')
    
    # ProcessingStatus
    content = content.replace('status="started"', 'status=ProcessingStatus.STARTED')
    content = content.replace('status="uploaded"', 'status=ProcessingStatus.UPLOADED')
    content = content.replace('status="processing"', 'status=ProcessingStatus.PROCESSING')
    content = content.replace('status="success"', 'status=ProcessingStatus.SUCCESS')
    content = content.replace('status="failed"', 'status=ProcessingStatus.FAILED')
    content = content.replace('status="completed"', 'status=ProcessingStatus.COMPLETED')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed: {filepath}")

# Find all test files
test_dir = 'tests'
for root, _dirs, files in os.walk(test_dir):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            fix_test_file(filepath)

print("Done!")
