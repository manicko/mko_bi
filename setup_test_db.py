"""Script to set up test database with proper migrations."""

import os
import sys

# Set environment variables for test database
os.environ["DATABASE__HOST"] = "localhost"
os.environ["DATABASE__PORT"] = "5432"
os.environ["DATABASE__DBNAME"] = "bidb_test"
os.environ["DATABASE__USER"] = "postgres"
os.environ["DATABASE__PASSWORD"] = "1234"

# Now import and run migrations
from alembic import command
from alembic.config import Config

# Create alembic config
alembic_cfg = Config("alembic.ini")

# Get the database URL from our config
from mkobi.config import get_config
config = get_config()
db_url = str(config.DATABASE_URL)

# Set the URL directly in alembic config (bypassing interpolation issues)
alembic_cfg.set_main_option("sqlalchemy.url", db_url)

print(f"Running migrations on: {db_url}")
try:
    command.upgrade(alembic_cfg, "head")
    print("Migrations completed successfully!")
except Exception as e:
    print(f"Error running migrations: {e}")
    sys.exit(1)
