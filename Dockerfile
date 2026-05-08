# =============================================================================
# Optimized Multi-stage Dockerfile for mkobi
# FASTER builds: stable base, minimal layers, optimized caching
# Targets: dev (hot reload), test, prod (default)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage: frontend-builder - Build React SPA inside Docker
# -----------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files first for layer caching
COPY frontend/package*.json ./

# Install dependencies (use npm install as package-lock.json may be excluded)
RUN npm install

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

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

# Install uv via official installer
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Create non-root user
RUN addgroup --system app && adduser --system --group app

# -----------------------------------------------------------------------------
# Stage: dev - Development with HOT RELOAD (--reload flag)
# -----------------------------------------------------------------------------
FROM base AS dev

# Copy dependency files FIRST for layer caching
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install all dependencies including dev (creates .venv)
RUN uv sync --frozen

# Add venv to PATH so uvicorn/uvicorn are found
ENV PATH="/app/.venv/bin:${PATH}"

# Copy remaining files
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Create data directories with proper permissions
RUN mkdir -p /app/data/uploads /app/data/logs /app/data/tmp_uploads && \
    chown -R app:app /app/data

# Run as root in dev mode (needed for writable mounted volumes with egg-info)
# This allows setuptools to create src/mkobi.egg-info

EXPOSE 8000

# Hot reload enabled for development
CMD ["uvicorn", "src.mkobi.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# -----------------------------------------------------------------------------
# Stage: test - Testing environment
# -----------------------------------------------------------------------------
FROM base AS test

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
RUN uv sync --frozen
ENV PATH="/app/.venv/bin:${PATH}"

COPY tests/ ./tests/
COPY alembic/ ./alembic/
COPY alembic.ini ./

RUN mkdir -p /app/data/uploads /app/data/logs /app/data/tmp_uploads && \
    chown -R app:app /app/data

USER app

ENV ENV=test \
    DATABASE__DBNAME=bidb_test

CMD ["pytest", "tests/", "-v"]

# -----------------------------------------------------------------------------
# Stage: prod - Production (DEFAULT target - faster rebuilds)
# -----------------------------------------------------------------------------
FROM base AS prod

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install only production dependencies
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:${PATH}"

# Copy frontend build artifacts from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copy remaining files
COPY alembic/ ./alembic/
COPY alembic.ini ./

RUN mkdir -p /app/data/uploads /app/data/logs /app/data/tmp_uploads && \
    chown -R app:app /app/data

USER app

EXPOSE 8000

CMD ["uvicorn", "src.mkobi.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
