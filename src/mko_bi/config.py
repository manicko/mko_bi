import os
from typing import Optional

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/bi_db")

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security
SALT_ROUNDS = 12

# Upload configuration
UPLOAD_TEMP_DIR = "/tmp/mko_bi_uploads"
ALLOWED_FILE_TYPES = [".csv.gz"]
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Application settings
APP_NAME = "mko_bi"
VERSION = "1.0.0"
