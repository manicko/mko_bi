---
id: docker-guide
domain: guides
tags:
  - docker
  - deployment
  - devops
related:
  - run-guide
  - deployment
  - task-queue-migration
  - file-cleanup
---

# Docker Guide for mkobi BI Dashboard System

## Purpose

This document provides comprehensive Docker setup instructions for the mkobi BI Dashboard System, including multi-stage builds, development environment configuration, testing procedures, and production deployment guidelines.

## Architecture Overview

### Containers

| Container | Purpose | Ports |
|-----------|---------|-------|
| `app` | FastAPI backend with hot reload (dev) or multi-workers (prod) | 8000 |
| `frontend` | Vite development server (dev only) | 5173 |
| `db` | PostgreSQL 18 database | 5432 |
| `redis` | Redis for task queue (production profile) | 6379 |
| `nginx` | Reverse proxy for production (production profile) | 80 |

### Networks

- Default: `app_network` (bridge)
- Test: `test_network` (isolated)

### Volumes

- `postgres_data` — PostgreSQL data persistence (mounted at `/var/lib/postgresql` for PG18+ compatibility)
- `app_data` — Application data (uploads, logs, temp files)
- `redis_data` — Redis data (if using task queue)

### Profiles

- Default: Starts `app`, `frontend`, `db`, `migrate`
- `production`: Adds `rq-worker`, `nginx`, `redis`

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- uv (for local development)

## Quick Start

### Development

```bash
# Start development environment with hot reload
docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml --env-file .env up -d

# Frontend dev server runs at http://localhost:5173 (Vite hot reload)
# Backend API runs at http://localhost:8000

# View logs
docker compose -f docker/docker-compose.yml --env-file .env logs -f app
docker compose -f docker/docker-compose.yml --env-file .env logs -f frontend
```

> **Note on Cookie Security:** The `AppSettings.cookie_secure` setting defaults to `true`, which requires HTTPS for cookies to be sent. Since the development environment runs over HTTP, `docker-compose.override.yml` sets `APP__COOKIE_SECURE=false` to allow authentication cookies to work correctly. Do not use `true` in production — the default value is secure.

> **Note on Port 8000 Access in Development:** Port 8000 serves the backend API and the production React build. The production frontend build uses secure cookies and memory-only token storage, which cannot authenticate over HTTP. **The intended development entry point is http://localhost:5173**, which runs the Vite development server with hot reload. The frontend dev server proxies `/api` requests to the backend at port 8000, enabling proper authentication flow in development.

> **Note on Frontend Profile:** The frontend service requires the `frontend` profile. To start it explicitly:
> ```bash
> docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml --env-file .env --profile frontend up -d
> ```

### Testing

```bash
# Start test environment (standalone compose, no production overlap)
docker compose -f docker/docker-compose.test.yml up -d --build

# Run tests
docker compose -f docker/docker-compose.test.yml exec test-app /app/.venv/bin/pytest tests/ -v

# Stop test environment
docker compose -f docker/docker-compose.test.yml down
```

> **Test Compose is Standalone:** `docker-compose.test.yml` defines its own isolated services (`test-db`, `test-redis`, `test-migrate`, `test-app`), volumes (`test_postgres_data`, `test_redis_data`), and network (`test_network`). It uses shifted host ports (**5433**, **6380**, **8001**) so it can run in parallel with the production compose without conflicts.

> **Test Port Security Note:** Host ports are intentionally exposed for development workflow convenience:
> - **Rationale:** Running `pytest` directly from the host terminal is faster for iterative development than `docker compose exec`. The shifted ports enable running both dev and test environments simultaneously.
> - **Security risk is LOW** — the test database contains no production data and uses default test passwords.
> - **For shared machines:** Consider binding to `127.0.0.1` instead of the default `0.0.0.0` to prevent cross-talk between developers.
> - **For CI/CD:** Run tests inside the container (`docker compose exec test-app uv run pytest`) to avoid exposing ports entirely.

### Production

```bash
# Build and start production environment
docker compose -f docker/docker-compose.yml --env-file .env up -d

# Or with specific target
DOCKER_TARGET=prod docker compose -f docker/docker-compose.yml --env-file .env up -d

# Start with production services (RQ worker, nginx)
docker compose -f docker/docker-compose.yml --profile production up -d
```

## Daily Operations

### Start Services

```bash
docker compose -f docker/docker-compose.yml --env-file .env up -d
```

### Stop Services

```bash
docker compose -f docker/docker-compose.yml --env-file .env down
```

### Stop and Remove Volumes

```bash
docker compose -f docker/docker-compose.yml --env-file .env down -v
```

### View Logs

```bash
docker compose -f docker/docker-compose.yml --env-file .env logs -f app
docker compose -f docker/docker-compose.yml --env-file .env logs -f frontend
docker compose -f docker/docker-compose.yml --env-file .env logs db
```

### Execute Commands in Container

```bash
docker compose -f docker/docker-compose.yml --env-file .env exec app /bin/bash
docker compose -f docker/docker-compose.yml --env-file .env exec app /app/.venv/bin/pytest tests/
```

### Rebuild After Changes

```bash
docker compose -f docker/docker-compose.yml --env-file .env up -d --build
```

### View Running Containers

```bash
docker compose -f docker/docker-compose.yml --env-file .env ps
```

## Development Workflow

### Hot Reload

The development environment uses:
- **Backend:** `--reload` flag with uvicorn for automatic reload on code changes
- **Frontend:** Vite dev server with hot module replacement (HMR)

### Frontend Development

- Dev server: http://localhost:5173
- Proxies `/api` to backend at http://localhost:8000
- TypeScript/React with TanStack Query

### Backend Development

- FastAPI with automatic reload
- PostgreSQL with hot reload support
- Shared `app_data` volume for temp files

### Cookie Configuration

The `AppSettings.cookie_secure` setting controls cookie security:
- `true` (default): Requires HTTPS — use in production
- `false`: Works over HTTP — used in development via override

## Testing

### Test Compose

`docker-compose.test.yml` provides an isolated testing environment:
- Shifted ports: 5433 (Postgres), 6380 (Redis), 8001 (API)
- Separate volumes: `test_postgres_data`, `test_redis_data`
- Standalone network: `test_network`

### Running Tests

```bash
# Run all tests
docker compose -f docker/docker-compose.test.yml exec test-app /app/.venv/bin/pytest tests/ -v

# Run specific test file
docker compose -f docker/docker-compose.test.yml exec test-app /app/.venv/bin/pytest tests/test_auth.py -v

# Run with coverage
docker compose -f docker/docker-compose.test.yml exec test-app /app/.venv/bin/pytest tests/ --cov=src/mkobi
```

### Test Isolation

The test environment is completely isolated from development:
- No port conflicts
- No shared volumes
- Separate database instance

## Production Deployment

### Production Profile

Start with the production profile to include `rq-worker` and `nginx`:

```bash
docker compose -f docker/docker-compose.yml --profile production up -d
```

### RQ Worker

Runs the Redis Queue worker for background task processing (CSV uploads, data aggregation).

```bash
# Start production environment with RQ worker
docker compose -f docker/docker-compose.yml --profile production up -d
```

- **Command:** `uv run rq worker --url redis://redis:6379/0`
- **Depends on:** `redis` (healthy), `migrate` (completed successfully)
- **Environment:** Same as `app` service but with `AUTO_MIGRATE: "false"` (migrations handled by the `migrate` service)
- **Shares volume:** `app_data` (access to the same upload/temp files as the app)
- **Shares alembic config:** Mounted read-only for migration rollback capability

> **Note:** The RQ worker is the production implementation of the task queue. The in-memory `asyncio.Queue` (MVP) is used when the RQ worker is not running. See [Task Queue Migration](./task-queue-migration.md) for the migration plan details.

### Nginx Reverse Proxy

Optional Nginx reverse proxy for production. Serves the React SPA static files and proxies API requests to FastAPI.

- **Depends on:** `app`
- **Ports:** `80:80`
- **Volumes:** `nginx.conf` (read-only), `frontend/dist` (read-only)
- **Security hardening:**
  - `read_only: true` — immutable root filesystem
  - `tmpfs` for runtime-writable paths: `/tmp`, `/var/cache/nginx`, `/var/run`, `/var/log/nginx`
  - All volumes mounted read-only (`:ro`)
  - Healthcheck verifies HTTP response (not just config syntax)

> **Note on `no-new-privileges`:** The official `nginx` image uses `setuid` internally to drop from root to the `nginx` user. Adding `security_opt: no-new-privileges:true` would crash the container. For nginx, the `read_only` filesystem is the primary hardening control.

See [Deployment](../10-deployment/deployment.md) for the nginx configuration details.

## Environment Configuration

### Which .env File to Use

| File | Purpose | Values |
|------|---------|--------|
| `.env` (project root) | Development - ready to use | Contains working development values |
| `docker/.env.development` | Development template | Template with `CHANGE_ME` placeholders - must be copied |
| `docker/.env.production` | Production deployment | Template with comments - must be filled before deployment |

### Development Setup

For new developers, set up your environment:

```bash
# Option 1: Use the root .env (works out of the box for development)
# No setup needed - the .env file contains working development values
docker compose -f docker/docker-compose.yml --env-file .env -f docker/docker-compose.override.yml up -d

# Option 2: Copy the development template to docker/.env
# Fill in your preferred values (not required if using root .env)
cp docker/.env.development docker/.env
# Edit docker/.env and replace CHANGE_ME placeholders
docker compose -f docker/docker-compose.yml --env-file docker/.env -f docker/docker-compose.override.yml up -d
```

### Production Setup

For production deployments, use `docker/.env.production`:

```bash
# Production deployment (correct)
docker compose --env-file docker/.env.production -f docker/docker-compose.yml up -d
```

### Required Variables

**Required in production `.env`:**

| Variable | Description |
|----------|-------------|
| `DATABASE__PASSWORD` | PostgreSQL superuser password |
| `MKOBI_APP_PASSWORD` | Application database role password |
| `JWT__SECRET_KEY` | JWT signing secret |
| `ADMIN_USERNAME` | Initial admin username |
| `ADMIN_PASSWORD` | Initial admin password |

**Key Variables:**

| Variable | Description |
|----------|-------------|
| `ENV` | Environment (development/test/production) |
| `DATABASE__HOST` | Database host |
| `DATABASE__PASSWORD` | Database password |
| `JWT__SECRET_KEY` | JWT secret key |
| `LOGGING__LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `AUTO_MIGRATE` | Auto-run database migrations (true/false) |
| `RECREATE_TEST_DB` | Recreate test database on startup (true/false) |
| `APP__COOKIE_SECURE` | Cookie Secure attribute (true/false). Defaults to `true`. Set to `false` in development when using HTTP. |

> **Security Note:** For production deployments, always set `DATABASE__PASSWORD`, `MKOBI_APP_PASSWORD`, and `JWT__SECRET_KEY` to strong, unique values. The compose file uses `${VAR:?error}` enforcement — services will fail to start without these variables explicitly set.

## Docker Internals

### Multi-Stage Build Architecture

This project uses a multi-stage Dockerfile with the following targets:

| Stage | Description |
|-------|-------------|
| `frontend-builder` | Builds React SPA (intermediate stage) |
| `base` | Common base image with system dependencies (build-essential, libpq-dev, libmagic1) |
| `prod-base` | Minimal runtime base for production (libpq5, libmagic1 only; no build tools) |
| `dev` | Development environment with hot reload |
| `test` | Environment for running tests |
| `prod` (default) | Production image with multiple workers |

**Stage Details:**

**base**
- Python 3.12-slim-bookworm as base
- Installs system dependencies: `build-essential`, `libpq-dev`, `libmagic1`, `curl`
  - `libmagic1` is required for server-side MIME type detection (python-magic library) in the file upload pipeline
- Installs uv for fast dependency management
- Creates non-root user for security

**frontend-builder**
- Uses Node 20 Alpine
- Installs frontend dependencies via `npm ci` with BuildKit `--mount=type=cache` for persistent `node_modules` across builds
- Builds React production bundle
- Output: `frontend/dist/`

**dev**
- Extends base
- Installs ALL dependencies (including dev)
- Copies source code for hot reload
- Runs with `--reload` flag

**test**
- Extends base
- Installs ALL dependencies (including dev)
- Copies tests and source code
- Sets `ENV=test`
- Default command runs pytest

**prod-base**
- Python 3.12-slim-bookworm as base
- Installs only runtime dependencies: `libpq5`, `libmagic1`, `curl`
- No build tools (build-essential, libpq-dev) — smaller attack surface
- Installs uv for dependency management
- Creates non-root user
- Extended by `prod` stage

**prod** (default target)
- Extends **prod-base** (not `base`) for minimal image size
- Installs only production dependencies (`uv sync --no-dev`)
- Copies frontend build artifacts from frontend-builder stage
- Runs with multiple workers (`--workers 4`)
- Includes HEALTHCHECK directive (curl `/health`)

### Layer Caching Optimizations

The Dockerfile is optimized for fast builds:

1. **Copy dependency files first**: `pyproject.toml` and `uv.lock` are copied before source code
2. **Separate frontend build**: Frontend is built in a separate stage using `npm ci` (deterministic, lockfile-enforcing install)
3. **BuildKit cache mount for npm**: `RUN --mount=type=cache,target=/app/frontend/node_modules` persists `node_modules` across rebuilds — dependencies are only re-downloaded when `package.json` changes
4. **Minimal layers**: Related commands are combined to reduce layers
5. **Proper .dockerignore**: Excludes unnecessary files from build context

### Build Examples

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

## Health Checks

| Service | Method |
|---------|--------|
| db | Uses `pg_isready` to check PostgreSQL readiness |
| app | Uses HTTP health endpoint `/health` with `start_period: 40s` (waits for db + migrate) |
| redis | Uses `redis-cli ping` |
| nginx | Uses `wget --spider -q http://localhost/` (verifies nginx is actually serving, not just config-valid) |

## PostgreSQL Locale Configuration

PostgreSQL 18 uses the `builtin` locale provider with `C.UTF-8` collation, configured via `POSTGRES_INITDB_ARGS`:

```yaml
POSTGRES_INITDB_ARGS: "--locale-provider=builtin --locale=C.UTF-8"
```

This provides:
- **Immutable collation version** (fixed at `1`) — no collation mismatch errors on image updates
- **Full UTF-8 support** for both Latin and Cyrillic characters
- **No index corruption risk** from OS locale changes

The `-bookworm` Debian tag is used for stability. When upgrading to `-trixie` in the future, no collation refresh is needed — the builtin provider is immutable.

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

### SIGBUS Error in Frontend Container (Windows)

When running the frontend container on Windows Docker Desktop, you may encounter:

```
npm error signal SIGBUS
npm error command sh -c vite --host 0.0.0.0
```

**Root cause:** This occurs due to cross-OS file system incompatibility. Mounts from Windows NTFS to Linux containers through gRPC FUSE or SMB layers cause memory alignment issues when Node.js/Vite accesses files.

**Solution:** The frontend service now uses a dedicated Docker image (`Dockerfile.frontend.dev`) that:
- Installs `node_modules` inside the container during build (avoiding Windows file system issues)
- Mounts individual source files explicitly for hot reload

**Alternative workaround (if issue persists):**
```powershell
# Clear corrupted frontend cache volume
docker volume rm docker_frontend_node_modules frontend_vite_cache
```

### Frontend not loading

```bash
# Rebuild frontend
docker compose -f docker/docker-compose.yml --env-file .env exec app npm run build --prefix frontend

# Check nginx logs (if using)
docker compose -f docker/docker-compose.yml --env-file .env logs nginx
```

### PostgreSQL 18 Collation Version Error

When starting PostgreSQL 18 containers, you may see repeated errors in the logs like:

```
ERROR:  syntax error at or near "COLLATION_VERSION"
LINE:  ALTER DATABASE template1 REFRESH COLLATION_VERSION
```

**Why this is harmless:** This error is caused by a known incompatibility between the Debian `postgresql-common` package (used in the postgres image) and PostgreSQL 18's stricter parser. The underscore syntax `REFRESH COLLATION_VERSION` was valid in PG16/17 but PostgreSQL 18 requires `REFRESH COLLATION VERSION` (space instead of underscore).

**Why it doesn't affect this project:** The PostgreSQL 18 configuration uses the `builtin` locale provider with `C.UTF-8` collation:

```yaml
POSTGRES_INITDB_ARGS: "--locale-provider=builtin --locale=C.UTF-8"
```

The `builtin` locale provider creates an immutable collation version (always `1`), meaning this refresh operation is never actually needed. The database starts and operates correctly despite these log messages.

**Current status:** The issue is tracked in:
- Debian bug tracker: `postgresql-common` package
- Docker Library GitHub: `docker-library/postgres`

These error messages are cosmetic and do not require any action. You can safely ignore them.

### "required variable X is missing a value" error

This means Docker Compose cannot find your `.env` file. Ensure you:
1. Have a `.env` file in the project root (copy from `.env.example`)
2. Pass `--env-file .env` flag with every `docker compose -f docker/docker-compose.yml` command

## Security

1. **Non-root user**: Application runs as `app` user (not root)
2. **Read-only filesystem**: `app` and `nginx` services use `read_only: true` with explicit `tmpfs` mounts for runtime-writable paths
3. **No privilege escalation**: `app` service uses `security_opt: no-new-privileges:true`, blocking `setuid`/`setgid` binary exploitation
4. **Minimal capabilities**: `app` service drops all Linux capabilities via `cap_drop: ALL` (binds to port 8000, no privileged ports needed)
5. **Secrets**: Use Docker secrets or environment variables for sensitive data
6. **.env file**: Never commit `.env` file to version control
7. **Production**: Change default passwords and JWT secret in production
8. **Image scanning**: Run `docker/scripts/scan-images.ps1` to scan built images for CVEs before deployment

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
│   ├── docker-compose.test.yml       # Test environment (standalone)
│   ├── Dockerfile                    # Multi-stage Dockerfile (backend + frontend-builder)
│   ├── Dockerfile.frontend.dev       # Frontend development Dockerfile (avoids Windows SIGBUS)
│   ├── init-scripts/
│   │   └── 01-create-app-role.sh     # DB initialization (creates mkobi_app role)
│   ├── nginx/
│   │   └── nginx.conf                # Nginx configuration (production profile)
│   └── scripts/
│       └── scan-images.ps1           # Trivy vulnerability scanner for built images
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

## Cross-References

- [Run Guide](../99-reference/run-guide.md) - Complete application run instructions
- [Deployment](../10-deployment/deployment.md) - Production deployment strategies
- [Task Queue Migration](./task-queue-migration.md) - Background task processing setup
- [Temp File Cleanup](../03-processing/file-cleanup.md) - File cleanup architecture

## Reference

### Docker Image Versions

| Service | Image | Version |
|---------|-------|--------|
| db | postgres | 18-bookworm |
| redis | redis | 7.4-alpine |
| nginx | nginx | 1.27-alpine |
| frontend | node | 20-alpine |

To update image versions, visit Docker Hub for latest tags and update in compose files.

## License

MIT