"""Fix test files - remove config={} and update AggregationFunctionEnum usages."""

import re
import os

def fix_test_file(filepath):
    """Fix a test file by removing config={} and updating enum usages."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove config={} from Dashboard creations
    content = re.sub(r',\s*config=\{\}', '', content)
    
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
    content = re.sub(r'type="(select|multiselect|range|date)"', r'type=FilterType.\U\1', content)
    content = re.sub(r'permission="(view|edit|admin)"', r'permission=DashboardPermission.\U\1', content)
    content = re.sub(r'status="(started|uploaded|processing|success|failed|completed)"', r'status=ProcessingStatus.\U\1', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed: {filepath}")

# Find all test files
test_dir = 'tests'
for root, dirs, files in os.walk(test_dir):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            fix_test_file(filepath)

print("Done!")
