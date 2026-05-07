import os
os.environ['JWT__SECRET_KEY'] = 'test'
os.environ['DATABASE__HOST'] = 'localhost'
os.environ['DATABASE__PORT'] = '5432'
os.environ['DATABASE__DBNAME'] = 'bidb_test'
os.environ['DATABASE__USER'] = 'postgres'
os.environ['DATABASE__PASSWORD'] = '1234'

from mkobi.app import create_app
app = create_app()

print('All routes:')
for route in app.routes:
    if hasattr(route, 'path'):
        methods = list(route.methods) if hasattr(route, 'methods') else []
        print(f'  {route.path} {methods}')

print('\nFilter routes:')
for route in app.routes:
    if hasattr(route, 'path') and 'filter' in route.path.lower():
        methods = list(route.methods) if hasattr(route, 'methods') else []
        print(f'  {route.path} {methods}')
