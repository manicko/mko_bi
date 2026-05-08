# =============================================================================
# Optimized Multi-stage Dockerfile for mkobi
# FASTER builds: stable base, minimal layers, optimized caching
# Targets: dev (hot reload), test, prod (default)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage: base - Stable Python 3.12 on Debian Bookworm (FAST mirrors)
# -----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Configure fast mirror (Yandex for CIS regions)
RUN rm -f /etc/apt/sources.list.d/*.sources && \
    echo "deb http://mirror.yandex.ru/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian-security bookworm-security main" >> /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian bookworm-updates main" >> /etc/apt/sources.list

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv via official installer (latest version, no version pinning)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Create non-root user with proper home directory
RUN addgroup --system app && adduser --system --group app --home /app/app_home
# Ensure home directory exists and is writable
RUN mkdir -p /app/app_home/.cache/uv && chown -R app:app /app/app_home
ENV HOME=/app/app_home
ENV UV_CACHE_DIR=/app/app_home/.cache/uv

# Use system Python for uv (skip venv creation)
ENV UV_SYSTEM_PYTHON=1

# -----------------------------------------------------------------------------
# Stage: dev - Development with HOT RELOAD (--reload flag)
# -----------------------------------------------------------------------------
FROM base AS dev

# Copy dependency files and source code (uv sync needs src/ to build package)
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install all dependencies including dev (system Python, no venv)
RUN uv sync --frozen

# Copy remaining files
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Create data directories
RUN mkdir -p /app/data/uploads /app/data/logs /app/data/tmp_uploads && \
    chown -R app:app /app/data

USER app

EXPOSE 8000

# Hot reload enabled for development
CMD ["uv", "run", "uvicorn", "src.mkobi.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# -----------------------------------------------------------------------------
# Stage: test - Testing environment
# -----------------------------------------------------------------------------
FROM base AS test

COPY pyproject.toml uv.lock ./
COPY src/ ./src/
RUN uv sync --frozen

COPY tests/ ./tests/
COPY alembic/ ./alembic/
COPY alembic.ini ./

RUN mkdir -p /app/data/uploads /app/data/logs /app/data/tmp_uploads && \
    chown -R app:app /app/data

USER app

ENV ENV=test \
    DATABASE__DBNAME=bidb_test

CMD ["uv", "run", "pytest", "tests/", "-v"]

# -----------------------------------------------------------------------------
# Stage: prod - Production (DEFAULT target - faster rebuilds)
# -----------------------------------------------------------------------------
FROM base AS prod

# Copy dependency files and source code (uv sync needs src/ to build package)
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install only production dependencies (system Python, no venv)
RUN uv sync --frozen --no-dev

# Copy remaining files
COPY alembic/ ./alembic/
COPY alembic.ini ./

RUN mkdir -p /app/data/uploads /app/data/logs /app/data/tmp_uploads && \
    chown -R app:app /app/data

USER app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.mkobi.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
