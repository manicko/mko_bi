from sqlalchemy import create_engine, text
from mko_bi.db.base import Base
from mko_bi.db.models import access, dashboard, user

# Create engine with echo=True to see SQL
engine = create_engine('sqlite:///./test_database.db', echo=True, future=True, connect_args={'check_same_thread': False})

# Check if tables exist
inspector = engine.connect()
try:
    result = inspector.execute(text('SELECT name FROM sqlite_master WHERE type="table" AND name="users"'))
    print('Tables before create_all:', result.fetchall())
except Exception as e:
    print('Error:', e)

# Create tables
Base.metadata.create_all(bind=engine)

# Check if tables exist after create_all
result = inspector.execute(text('SELECT name FROM sqlite_master WHERE type="table" AND name="users"'))
print('Tables after create_all:', result.fetchall())

inspector.close()
engine.dispose()