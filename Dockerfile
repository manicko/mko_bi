# syntax=docker/dockerfile:1.4
# =============================================================================
# Optimized Multi-stage Dockerfile for mkobi
# FASTER builds: BuildKit caching, pinned versions, optimized layers
# Targets: dev (hot reload), test, prod (default)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage: base - Stable Python 3.12 on Debian Bookworm (FAST apt)
# -----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/root/.cache/uv

# Install system deps with BuildKit cache mount for faster rebuilds
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (PINNED version for better layer caching)
ARG UV_VERSION=0.5.21
RUN curl -LsSf https://astral.sh/uv/${UV_VERSION}/install.sh | sh

WORKDIR /app

# Create non-root user early (rarely changes)
RUN addgroup --system app && adduser --system --group app

# -----------------------------------------------------------------------------
# Stage: dev - Development with HOT RELOAD (--reload flag)
# -----------------------------------------------------------------------------
FROM base AS dev

# Copy dependency files FIRST for layer caching
COPY --link pyproject.toml uv.lock ./

# Install all dependencies including dev with uv cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Copy source code with --link for better layer sharing
COPY --link src/ ./src/
COPY --link alembic/ ./alembic/
COPY --link alembic.ini ./

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

COPY --link pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

COPY --link src/ ./src/
COPY --link tests/ ./tests/
COPY --link alembic/ ./alembic/
COPY --link alembic.ini ./

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

# Copy dependency files FIRST for layer caching
COPY --link pyproject.toml uv.lock ./

# Install only production dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Copy source code with --link for better layer sharing
COPY --link src/ ./src/
COPY --link alembic/ ./alembic/
COPY --link alembic.ini ./

RUN mkdir -p /app/data/uploads /app/data/logs /app/data/tmp_uploads && \
    chown -R app:app /app/data

USER app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.mkobi.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
