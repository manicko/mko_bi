# Docker Quick Start - mkobi BI Dashboard

**Date**: 2026-05-06  
**Version**: 1.0  

---

## Prerequisites

- Docker installed
- Docker Compose installed (or docker compose plugin)

---

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd mkobi
```

### 2. Configure environment (optional)

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

**Important changes for production:**
- Set `DATABASE__PASSWORD` to a secure password
- Set `JWT__SECRET_KEY` to a strong secret (generate with `openssl rand -hex 32`)
- Update `CORS_ORIGINS` to your domain for production

### 3. Start the application

```bash
docker-compose up -d
```

This will:
- Start PostgreSQL 16 database in a container
- Build and start the mkobi application
- Create persistent Docker volumes for data
- Run database migrations automatically
- **Create and migrate test database** (if `RECREATE_TEST_DB=true`)

### 3.1 Test Database (Optional)

To enable automatic test database creation on first launch, add to `docker-compose.yml`:

```yaml
# In app service environment:
ENV: test  # or development
DATABASE__TEST_DBNAME: bidb_test
RECREATE_TEST_DB: "true"
```

This ensures `uv run pytest tests/` can run against a properly migrated test database.

### 4. Access the application

- **API**: http://localhost:8000
- **API Docs (Swagger UI)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Data Storage

All data is stored in Docker volumes:

| Volume | Container Path | Purpose |
|--------|----------------|---------|
| `app_data` | `/app/data` | App data (uploads, logs, temp files) |
| `postgres_data` | `/var/lib/postgresql/data` | PostgreSQL database files |

### View data volumes:

```bash
docker volume ls
docker volume inspect mkobi_app_data
docker volume inspect mkobi_postgres_data
```

### Access uploaded files:

```bash
docker exec -it mkobi-app-1 ls -la /app/data/uploads
```

---

## Common Commands

### View logs

```bash
# All services
docker-compose logs -f

# App only
docker-compose logs -f app

# Database only
docker-compose logs -f db
```

### Stop the application

```bash
docker-compose down
```

### Stop and remove volumes (⚠️ deletes all data)

```bash
docker-compose down -v
```

### Rebuild after code changes

```bash
docker-compose up -d --build
```

### Run migrations manually

```bash
docker exec -it mkobi-app-1 uv run alembic upgrade head
```

### Access PostgreSQL database

```bash
docker exec -it mkobi-db-1 psql -U postgres -d bidb
```

---

## Environment Variables

Key variables in `.env` (or set in environment):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE__PASSWORD` | `1234` | PostgreSQL password |
| `JWT__SECRET_KEY` | (auto-generated) | JWT signing key |
| `JWT__ALGORITHM` | `HS256` | JWT algorithm |
| `CORS_ORIGINS` | `["http://localhost"]` | CORS allowed origins |
| `AUTO_MIGRATE` | `true` | Auto-run migrations on startup |
| `RECREATE_TEST_DB` | `false` | Auto-create test DB on startup |
| `DATABASE__TEST_DBNAME` | `bidb_test` | Test database name |
| `LOGGING__LEVEL` | `INFO` | Logging level |
| `LOGGING__LOG_FILE` | `/app/data/logs/app.log` | Log file path |

---

## Production Deployment

### 1. Update `.env` for production:

```bash
ENV=production
DATABASE__PASSWORD=<strong-password>
JWT__SECRET_KEY=<strong-secret>
CORS_ORIGINS='["https://yourdomain.com"]'
LOGGING__LEVEL=WARNING
```

### 2. Use Docker secrets (recommended):

```bash
# Instead of putting passwords in .env, use Docker secrets:
DATABASE__PASSWORD_FILE=/run/secrets/db_password
JWT__SECRET_KEY_FILE=/run/secrets/jwt_secret
```

### 3. Run production checklist:

See `PRODUCTION_CHECKLIST.md` for full pre-deployment verification.

---

## Troubleshooting

### Database connection error

Wait for database to be healthy:
```bash
docker-compose ps
# Look for "health: starting" -> wait until "healthy"
```

### Port already in use

Change the port mapping in `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Maps host port 8080 to container 8000
```

### Migration errors

Check logs and run manually:
```bash
docker-compose logs app
docker exec -it mkobi-app-1 uv run alembic upgrade head
```

### Test database not created

Ensure these variables are set in `docker-compose.yml`:
```yaml
ENV: development  # or test
RECREATE_TEST_DB: "true"
DATABASE__TEST_DBNAME: bidb_test
```

Then restart:
```bash
docker-compose down && docker-compose up -d
```

### Run tests in Docker

```bash
docker exec -it mkobi-app-1 uv run pytest tests/
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              HOST MACHINE                │
│                                   │
│  ┌──────────────┐    ┌──────────────┐ │
│  │   Docker     │    │   Docker     │ │
│  │   Volume:    │    │   Volume:    │ │
│  │   app_data   │    │   postgres_  │ │
│  │              │    │   data       │ │
│  └──────┬───────┘    └──────┬───────┘ │
│         │                    │          │
│         ▼                    ▼          │
│  ┌─────────────────────────────────┐  │
│  │         DOCKER NETWORK         │  │
│  │  ┌──────────┐  ┌──────────┐ │  │
│  │  │   app    │  │    db    │ │  │
│  │  │  :8000   │  │  :5432   │ │  │
│  │  └────┬─────┘  └────┬─────┘ │  │
│  │       │              │       │  │
│  │       └──────┬───────┘       │  │
│  │              │                  │  │
│  │         localhost:8000         │  │
│  │                              │  │
│  │  On startup:                 │  │
│  │  • Check DB exists           │  │
│  │  • Run Alembic migrations    │  │
│  │  • Create test DB (optional) │  │
│  └─────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

**Key points:**
- App and database run in isolated Docker containers
- Data persists in Docker volumes (survives container restarts)
- On first launch: migrations auto-run via `DatabaseStarter`
- Test database created/migrated if `RECREATE_TEST_DB=true`
- No need to install Python, PostgreSQL, or dependencies on host
- Same setup works on any machine with Docker

---

## Next Steps

1. Run `docker-compose up -d`
2. Open http://localhost:8000/docs
3. Create first admin user (see API docs)
4. Start uploading data and creating dashboards!
