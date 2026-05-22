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
- **prod-slim** - Minimal production image

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- uv (for local development)

## Quick Start

### Production

```bash
# Build and start production environment
docker compose up -d

# Or with specific target
DOCKER_TARGET=prod docker compose up -d
```

### Development

```bash
# Start development environment with hot reload



# View logs
docker compose -f docker-compose.yml -f docker-compose.override.yml logs -f app
```

### Testing

```bash
# Start test environment
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d

# Run tests
docker compose -f docker-compose.yml -f docker-compose.test.yml exec app uv run pytest tests/ -v

# Stop test environment
docker compose -f docker-compose.yml -f docker-compose.test.yml down
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

### Stage: prod-base
- Extends base
- Installs only production dependencies (`--no-dev`)
- Copies source code and frontend build
- Creates data directories

### Stage: prod (default target)
- Extends prod-base
- Runs with multiple workers (`--workers 4`)
- Optimized for production deployment

### Stage: prod-slim
- Even smaller image using python:3.12-slim
- Copies pre-installed venv from prod-base
- Minimal runtime dependencies only

## Layer Caching Optimizations

The Dockerfile is optimized for fast builds:

1. **Copy dependency files first**: `pyproject.toml` and `uv.lock` are copied before source code
2. **Separate frontend build**: Frontend is built in a separate stage
3. **Minimal layers**: Related commands are combined to reduce layers
4. **Proper .dockerignore**: Excludes unnecessary files from build context

## Build Examples

```bash
# Build specific target
docker build --target dev -t mkobi:dev .
docker build --target prod -t mkobi:prod .
docker build --target test -t mkobi:test .

# Build with no cache (force rebuild)
docker build --no-cache --target prod -t mkobi:prod .

# Build with build args
docker build --build-arg UV_VERSION=v0.1.0 --target prod -t mkobi:prod .
```

## Environment Variables

See `docker-compose.yml` for all environment variables.

Key variables:
- `ENV` - Environment (development/test/production)
- `DATABASE__HOST` - Database host
- `DATABASE__PASSWORD` - Database password
- `JWT__SECRET_KEY` - JWT secret key
- `LOGGING__LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)
- `AUTO_MIGRATE` - Auto-run database migrations (true/false)
- `RECREATE_TEST_DB` - Recreate test database on startup (true/false)

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
docker compose ps

# View logs
docker compose logs -f app

# Execute command in running container
docker compose exec app uv run pytest tests/

# Open shell in container
docker compose exec app /bin/bash

# Stop all services
docker compose down

# Stop and remove volumes
docker compose down -v

# Rebuild after changes
docker compose up -d --build
```

## Troubleshooting

### Database connection issues
```bash
# Check if database is ready
docker compose exec db pg_isready -U postgres

# View database logs
docker compose logs db
```

### Migration issues
```bash
# Run migrations manually
docker compose exec app uv run alembic upgrade head

# Check migration status
docker compose exec app uv run alembic current
```

### Frontend not loading
```bash
# Rebuild frontend
docker compose exec app npm run build --prefix frontend

# Check nginx logs (if using)
docker compose logs nginx
```

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
├── Dockerfile                    # Multi-stage Dockerfile
├── docker-compose.yml            # Production compose file
├── docker-compose.override.yml   # Development overrides
├── docker-compose.test.yml       # Test environment
├── .dockerignore                 # Excludes files from build context
├── nginx/
│   └── nginx.conf                # Nginx configuration (optional)
└── frontend/
    ├── dist/                     # Built frontend (generated)
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

- [Run Guide](../04-run/run-guide.md) - Complete application run instructions
- [Deployment](../05-ops/deployment.md) - Production deployment strategies
- [Task Queue Migration](../05-ops/task-queue-migration.md) - Background task processing setup