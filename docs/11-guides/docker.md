---
id: docker-domain
domain: guides
tags:
  - docker
  - deployment
  - devops
related:
  - run-guide
  - deployment
  - task-queue-migration
---

## Purpose

This document provides comprehensive Docker setup instructions for the mkobi BI Dashboard System, including multi-stage builds, development environment configuration, testing procedures, and production deployment guidelines.

# Docker Setup for mkobi BI Dashboard System

## Overview

This project uses a multi-stage Dockerfile with the following targets:
- **base** - Common base image with system dependencies
- **dev** - Development environment with hot reload
- **test** - Environment for running tests
- **prod** - Production image with multiple workers (default)
- **frontend-builder** - Builds React SPA (intermediate stage)

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- uv (for local development)

## Quick Start

### Production

```bash
# Build and start production environment
docker compose -f docker/docker-compose.yml --env-file .env up -d

# Or with specific target
DOCKER_TARGET=prod docker compose -f docker/docker-compose.yml --env-file .env up -d
```

### Development

```bash
# Start development environment with hot reload
# Note: docker-compose.override.yml is auto-loaded by Docker Compose
docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml --env-file .env up -d

# Frontend dev server runs at http://localhost:5173 (Vite hot reload)
# Backend API runs at http://localhost:8000

# View logs
docker compose -f docker/docker-compose.yml --env-file .env logs -f app
docker compose -f docker/docker-compose.yml --env-file .env logs -f frontend
```

### Testing

```bash
# Start test environment
docker compose -f docker/docker-compose.test.yml up -d

# Run tests
docker compose -f docker/docker-compose.test.yml exec test-app uv run pytest tests/ -v

# Stop test environment
docker compose -f docker/docker-compose.test.yml down
```

## Multi-Stage Builds Explained

### Stage: base
- Python 3.12-slim as base
- Installs system dependencies (build-essential, libpq-dev)
- Installs uv for fast dependency management
- Creates non-root user for security

### Stage: frontend-builder
- Uses Node 20 Alpine
- Installs frontend dependencies
- Builds React production bundle
- Output: `frontend/dist/`

### Stage: dev
- Extends base
- Installs ALL dependencies (including dev)
- Copies source code for hot reload
- Runs with `--reload` flag

### Stage: test
- Extends base
- Installs ALL dependencies (including dev)
- Copies tests and source code
- Sets `ENV=test`
- Default command runs pytest

### Stage: prod (default target)
- Extends base
- Installs only production dependencies
- Copies frontend build artifacts from frontend-builder stage
- Runs with multiple workers (`--workers 4`)

## Layer Caching Optimizations

The Dockerfile is optimized for fast builds:

1. **Copy dependency files first**: `pyproject.toml` and `uv.lock` are copied before source code
2. **Separate frontend build**: Frontend is built in a separate stage
3. **Minimal layers**: Related commands are combined to reduce layers
4. **Proper .dockerignore**: Excludes unnecessary files from build context

## Build Examples

```bash
# Build specific target
docker build -f docker/Dockerfile --target dev -t mkobi:dev .
docker build -f docker/Dockerfile --target prod -t mkobi:prod .
docker build -f docker/Dockerfile --target test -t mkobi:test .

# Build with no cache (force rebuild)
docker build -f docker/Dockerfile --no-cache --target prod -t mkobi:prod .

# Build with build args
docker build -f docker/Dockerfile --build-arg UV_VERSION=v0.1.0 --target prod -t mkobi:prod .
```

## Environment Variables

Environment variables are loaded from `.env` in the project root. All Docker Compose commands require `--env-file .env` flag to load them, because `docker-compose.yml` uses `${VAR:?error}` enforcement patterns that prevent startup without explicit values.

**Required variables in `.env`:**
- `DATABASE__PASSWORD` — PostgreSQL superuser password
- `MKOBI_APP_PASSWORD` — Application database role password
- `JWT__SECRET_KEY` — JWT signing secret
- `ADMIN_USERNAME` — Initial admin username
- `ADMIN_PASSWORD` — Initial admin password

For local development, `docker-compose.override.yml` provides sensible defaults for non-sensitive variables.

Key variables:
- `ENV` — Environment (development/test/production)
- `DATABASE__HOST` — Database host
- `DATABASE__PASSWORD` — Database password
- `JWT__SECRET_KEY` — JWT secret key
- `LOGGING__LEVEL` — Logging level (DEBUG/INFO/WARNING/ERROR)
- `AUTO_MIGRATE` — Auto-run database migrations (true/false)
- `RECREATE_TEST_DB` — Recreate test database on startup (true/false)

**Security Note:** For production deployments, always set `DATABASE__PASSWORD`, `MKOBI_APP_PASSWORD`, and `JWT__SECRET_KEY` to strong, unique values. The compose file uses `${VAR:?error}` enforcement — services will fail to start without these variables explicitly set.

## Volumes

- `postgres_data` - PostgreSQL data persistence
- `app_data` - Application data (uploads, logs, temp files)
- `redis_data` - Redis data (if using task queue)

## Health Checks

- **db**: Uses `pg_isready` to check PostgreSQL readiness
- **app**: Uses HTTP health endpoint `/health`
- **redis**: Uses `redis-cli ping`

## Common Commands

```bash
# View running containers
docker compose -f docker/docker-compose.yml --env-file .env ps

# View logs
docker compose -f docker/docker-compose.yml --env-file .env logs -f app

# Execute command in running container
docker compose -f docker/docker-compose.yml --env-file .env exec app uv run pytest tests/

# Open shell in container
docker compose -f docker/docker-compose.yml --env-file .env exec app /bin/bash

# Stop all services
docker compose -f docker/docker-compose.yml --env-file .env down

# Stop and remove volumes
docker compose -f docker/docker-compose.yml --env-file .env down -v

# Rebuild after changes
docker compose -f docker/docker-compose.yml --env-file .env up -d --build
```

## Troubleshooting

### Database connection issues
```bash
# Check if database is ready
docker compose -f docker/docker-compose.yml --env-file .env exec db pg_isready -U postgres

# View database logs
docker compose -f docker/docker-compose.yml --env-file .env logs db
```

### Migration issues
```bash
# Run migrations manually
docker compose -f docker/docker-compose.yml --env-file .env exec app uv run alembic upgrade head

# Check migration status
docker compose -f docker/docker-compose.yml --env-file .env exec app uv run alembic current
```

### Frontend not loading
```bash
# Rebuild frontend
docker compose -f docker/docker-compose.yml --env-file .env exec app npm run build --prefix frontend

# Check nginx logs (if using)
docker compose -f docker/docker-compose.yml --env-file .env logs nginx
```

### "required variable X is missing a value" error
This means Docker Compose cannot find your `.env` file. Ensure you:
1. Have a `.env` file in the project root (copy from `.env.example`)
2. Pass `--env-file .env` flag with every `docker compose -f docker/docker-compose.yml` command

## Security Notes

1. **Non-root user**: Application runs as `app` user (not root)
2. **Secrets**: Use Docker secrets or environment variables for sensitive data
3. **.env file**: Never commit `.env` file to version control
4. **Production**: Change default passwords and JWT secret in production

## Performance Tips

1. **Use layer caching**: Order Dockerfile commands from least to most frequently changing
2. **Multi-stage builds**: Reduces final image size by excluding build dependencies
3. **uv package manager**: Faster than pip for dependency installation
4. **--no-dev flag**: Excludes development dependencies in production

## File Structure

```
.
├── .dockerignore                   # Build context file (at root)
├── .env                            # Environment variables (gitignored, required for --env-file)
├── .env.example                    # Template for .env
├── docker/
│   ├── docker-compose.yml            # Production compose file
│   ├── docker-compose.override.yml   # Development overrides
│   ├── docker-compose.test.yml       # Test environment
│   ├── Dockerfile                  # Multi-stage Dockerfile
│   ├── init-scripts/
│   │   └── 01-create-app-role.sh     # DB initialization
│   └── nginx/
│       └── nginx.conf                # Nginx configuration (optional)
└── frontend/
    ├── dist/                         # Built frontend (generated)
    ...
```
.
├── .dockerignore                   # Build context file (at root)
├── docker/
│   ├── docker-compose.yml            # Production compose file
│   ├── docker-compose.override.yml   # Development overrides
│   ├── docker-compose.test.yml       # Test environment
│   ├── Dockerfile                  # Multi-stage Dockerfile
│   ├── init-scripts/
│   │   └── 01-create-app-role.sh     # DB initialization
│   └── nginx/
│       └── nginx.conf                # Nginx configuration (optional)
└── frontend/
    ├── dist/                         # Built frontend (generated)
    └── ...
```

## Migration from Old Setup

If migrating from a single-stage Dockerfile:

1. Review the new multi-stage Dockerfile
2. Update `docker-compose.yml` to specify build target
3. Test each environment (dev/test/prod)
4. Update CI/CD pipelines to use new targets

## License

MIT

## Cross-References

- [Run Guide](../99-reference/run-guide.md) - Complete application run instructions
- [Deployment](../10-deployment/deployment.md) - Production deployment strategies
- [Task Queue Migration](./task-queue-migration.md) - Background task processing setup