---
id: deployment
domain: deployment
tags:
  - deployment
  - docker
  - production
  - nginx
  - health-checks
  - migrations
  - dash-migration
related:
  - backend-architecture
  - configuration
  - health-api
  - security-overview
---

# Deployment

## Overview

This guide covers deployment options for the mkobi BI Dashboard system, from local development to production. The application consists of a FastAPI backend, React 18 frontend, PostgreSQL database, and optional Redis for task queues.

**Related documentation:**
- [Backend Architecture](../06-backend/architecture.md) — System architecture and layer responsibilities
- [Configuration](../06-backend/configuration.md) — Config sources, secrets, and environment variables
- [Security Overview](../08-security/security-overview.md) — Production credential enforcement
- [Health API](../05-health/health-api.md) — Health check endpoints for monitoring

---

## Development Deployment

### Prerequisites

- Python 3.12+
- Node.js 20+
- uv (Python package manager)
- PostgreSQL 16+ (local or Docker)

### Local Setup

1. **Clone and configure:**
   ```bash
   git clone <repository-url>
   cd mkobi
   cp .env.example .env
   # Edit .env with your local settings
   ```

2. **Backend:**
   ```bash
   uv sync
   uv run uvicorn mkobi.main:app --reload --port 8000
   ```

3. **Frontend (separate terminal):**
   ```bash
   cd frontend
   npm install
   npm run dev
   # Server runs at http://localhost:5173 (Vite default)
   ```

4. **Database:**
```bash
docker compose -f docker/docker-compose.yml up -d db
uv run alembic upgrade head
```

The React dev server runs on port 5173 (Vite) and proxies API requests to FastAPI on port 8000. Hot reload is enabled for both servers. CORS is configured to allow cross-origin requests between the dev servers.

### Environment Configuration

Development uses `.env` files for convenience (lowest priority in the config source hierarchy). See [Configuration](../06-backend/configuration.md) for the full priority chain.

---

## Production Deployment

### Production Principals

- **No overengineering:** Use proven, simple deployment patterns. The application does not require Kubernetes or complex orchestration for typical workloads.
- **Single responsibility:** Each container serves one purpose — app, database, or cache.
- **Security by default:** No default secrets, non-root containers, secrets via environment or Docker secrets.

### Option A — FastAPI Serves Static Files (Recommended)

FastAPI serves the built React static files directly. This is the simplest production deployment with a single entry point.

```
Client → FastAPI (port 8000)
              ├── /api/*    → REST API handlers
              ├── /static/ → React SPA build output (frontend/dist/)
              └── /         → React SPA index.html
```

**Steps:**

1. **Build frontend:**
   ```bash
   cd frontend
   npm run build
   # Output: frontend/dist/
   ```

2. **FastAPI configuration:**

   The backend mounts `frontend/dist/` as static files. All non-API routes fall through to the React `index.html` for client-side routing.

3. **Environment variables required:**
   ```
   ENV=production
   DATABASE__HOST=<production-db-host>
   DATABASE__PASSWORD=<strong-password>
   JWT__SECRET_KEY=<random-256-bit-secret>
   CORS_ORIGINS=["https://your-domain.com"]
   LOGGING__LEVEL=WARNING
   ```

### Option B — Nginx Reverse Proxy

Nginx proxies API requests to FastAPI and serves the React SPA static files. This adds a layer of control (SSL termination, caching, load balancing) at the cost of additional complexity.

```
Client → Nginx (port 80/443)
              ├── /api/*  → FastAPI (port 8000)
              └── /*      → React SPA static (frontend/dist/)
```

**nginx.conf snippet:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
```

To enable, start the nginx service from `docker-compose.yml`:
```bash
docker compose -f docker/docker-compose.yml --profile production up -d
```

---

## Docker Deployment

The project uses a multi-stage Dockerfile supporting dev, test, and prod targets. See [Docker Guide](../11-guides/docker.md) for the full Docker specification.

### Quick Start

```bash
# Production (default target)
docker compose -f docker/docker-compose.yml up -d

# Development with hot reload and frontend dev server
docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml up -d
```

**Note:** Development mode includes the frontend service running on port 5173 (Vite dev server with hot reload). Access the application at http://localhost:5173.

### Dockerfile Targets

| Target | Base | Dependencies | Workers | Use Case |
|--------|------|-------------|---------|----------|
| `base` | python:3.12-slim-bookworm | System only | — | Shared base |
| `dev` | base | All (incl. dev) | 1 (--reload) | Local dev |
| `test` | base | All (incl. dev) | 1 (pytest) | CI/CD |
| `prod` | base | Production only | 4 | Production |

### Required Production Variables

The following environment variables **must** be set explicitly. Docker Compose will refuse to start the `app` service without them:

```
DATABASE__PASSWORD=<production-password>
JWT__SECRET_KEY=<production-secret>
```

### Database Migrations

- `AUTO_MIGRATE=true` — runs `alembic upgrade head` on container startup (default in docker-compose.yml)
- **Migration advisory lock** — In multi-instance deployments (K8s replicas, multiple Gunicorn workers), parallel migrations can corrupt the schema. The `_apply_migrations()` method acquires a PostgreSQL advisory lock (`pg_advisory_lock(42)`) before running migrations, ensuring only one instance runs migrations at a time. The lock is released after completion, even on failure.
- **Migration job pattern** — For production Docker Compose deployments, a dedicated `migrate` service runs `alembic upgrade head` before the app service starts. The app service depends on the migration service completing successfully (`depends_on: migrate: condition: service_completed_successfully`). This separates migration concerns from application startup and allows `AUTO_MIGRATE=false` in the app config.
- Manual migration:
```bash
docker compose -f docker/docker-compose.yml exec app uv run alembic upgrade head
# Check status:
docker compose -f docker/docker-compose.yml exec app uv run alembic current
```

### Database Role (Least-Privilege)

The application uses a dedicated database role (`mkobi_app`) with limited privileges instead of the superuser `postgres` role:

| Role | Purpose | Privileges |
| --- | --- | --- |
| `postgres` | Migrations (DDL) | Superuser |
| `mkobi_app` | Runtime operations | `CONNECT`, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on tables; `USAGE` on sequences |

This follows the least-privilege principle: any SQL injection or application bug is limited to the `mkobi_app` role's permissions and cannot execute superuser operations. The `postgres` role is used only for migrations that require DDL.

The role is created via an initialization SQL script mounted to `/docker-entrypoint-initdb.d/` in the PostgreSQL container. The application's `DATABASE__USER` and `DATABASE__PASSWORD` point to the `mkobi_app` role.

### Volumes

| Volume | Container Path | Purpose |
|--------|---------------|---------|
| `postgres_data` | `/var/lib/postgresql/data` | Database persistence |
| `app_data` | `/app/data` | Uploads, logs, temp files |
| `redis_data` | `/data` | Task queue (if used) |

### Health Checks

- **db**: `pg_isready` — verifies PostgreSQL is accepting connections
- **app**: HTTP GET `/health` — verifies the application responds
- **redis**: `redis-cli ping` — verifies Redis availability

### Common Operations

```bash
# View logs
docker compose -f docker/docker-compose.yml logs -f app

# Open shell
docker compose -f docker/docker-compose.yml exec app /bin/bash

# Run tests
docker compose -f docker/docker-compose.test.yml exec test-app uv run pytest tests/ -v

# Stop and remove everything (including volumes)
docker compose -f docker/docker-compose.yml down -v

# Rebuild after code changes
docker compose -f docker/docker-compose.yml up -d --build
```

---

## Design Principles

This project intentionally avoids overengineering. The following decisions reflect that philosophy:

- **No Redux/Zustand:** TanStack Query handles all server state. React local state (`useState`, `useReducer`) handles UI state.
- **No unnecessary abstraction layers:** API calls go through a thin Axios instance (with JWT interceptors). No additional service wrappers or API gateway abstractions.
- **No duplicated logic:** Pydantic models from the backend are the single source of truth for data shapes. Frontend types are derived from the OpenAPI spec.
- **No premature scaling:** A single FastAPI instance with 4 workers handles typical BI workloads. Scale horizontally only when metrics justify it.
- **No framework churn:** The stack (FastAPI, React, PostgreSQL, Polars) is stable and well-supported. Avoid adding new frameworks without strong operational justification.

---

## Dash Migration Path

The system may need to coexist with an existing Dash application during migration. Two strategies are supported:

### Strategy 1 — iframe Fallback (Gradual Migration)

Embed existing Dash charts within the React SPA via `<iframe>`. This allows incremental migration of individual dashboards without a full rewrite.

```tsx
// React component wrapping a Dash chart
<DashEmbed url="http://dash-server:8050/chart-name" />
```

**Pros:** Zero risk to existing Dash dashboards. Teams can migrate one chart at a time.
**Cons:** iframe isolation limits interactivity. Two runtimes to maintain.

### Strategy 2 — Full Replacement (Preferred)

Replace Dash charts with Plotly.js React components. The backend API serves the same aggregated data format to both frontends during the transition period.

```tsx
// Plotly.js React chart
import Plot from 'react-plotly.js';
<Plot data={chartData} layout={layout} />
```

**Pros:** Single runtime, full interactivity, consistent UX, no iframe limitations.
**Cons:** Requires rewriting each Dash chart as a React component.

### Recommendation

Use Strategy 1 for complex, stable charts that rarely change. Use Strategy 2 for new development and charts that need tight integration with the React SPA. Over time, migrate all charts to Strategy 2.

---

## Cross-References

- [Backend Architecture](../06-backend/architecture.md) — System architecture and startup lifecycle
- [Configuration](../06-backend/configuration.md) — Config sources, secrets, and environment variables
- [Security Overview](../08-security/security-overview.md) — Production credential enforcement and security constraints
- [Health API](../05-health/health-api.md) — Health check endpoints for load balancers and Kubernetes
- [Task Queue](../03-processing/task-queue.md) — Redis/RQ migration for production background processing
- [Logging](../06-backend/logging.md) — Structured JSON logging in production
