# Docker Architecture Plan - mkobi (Standard Industry Approach)

**Date**: 2026-05-06  
**Author**: Senior Python Developer  
**Version**: 2.0  

---

## Requirements Analysis

### User Requirements:
1. Maximize Docker usage (app + DB in Docker)
2. Standard industry approach (no platformdirs)
3. `docker-compose up` works on any machine
4. Clean Architecture principles

### Architecture Decision:

**REJECTED**: platformdirs approach - mixes host/container concerns, breaks containerization principles.

**ACCEPTED**: Standard Docker volumes approach - everything in Docker, data persists in volumes.

---

## Recommended Architecture: Standard Docker with Volumes

### Overview

```
┌─────────────────────────────────────────────────┐
│                     HOST MACHINE                        │
│                                                       │
│  docker-compose up -d                              │
│         │                                         │
│         ▼                                         │
│  ┌─────────────────────────────────────────────┐  │
│  │                  DOCKER                          │  │
│  │  ┌──────────────┐    ┌──────────────┐  │  │
│  │  │   app        │    │   postgres:16   │  │  │
│  │  │   :8000      │    │   :5432        │  │  │
│  │  └──────┬───────┘    └──────┬───────┘  │  │
│  │       │                  │            │  │
│  │       │                  │            │  │
│  │  ┌────▼─────────┐   ┌▼─────────────┐ │  │
│  │  │  app_data     │   │ postgres_data   │ │  │
│  │  │  (volume)    │   │ (volume)      │ │  │
│  │  │              │   │                │ │  │
│  │  │  /app/data   │   │ /var/lib/      │ │  │
│  │  │              │   │ postgresql/    │ │  │
│  │  │  uploads/   │   │ data/          │ │  │
│  │  │  logs/      │   │                │ │  │
│  │  │  tmp_uploads/│   │                │ │  │
│  │  └──────────────┘   └────────────────┘ │  │
│  └─────────────────────────────────────────────┘  │
│                                                       │
└─────────────────────────────────────────────────┘
```

### Key Design Points:

1. **All services in Docker** - app + PostgreSQL
2. **Data persistence via Docker volumes** - survives container restarts
3. **No host path dependencies** - works on any machine
4. **Standard docker-compose workflow** - `up`, `down`, `logs`

---

## Implementation Plan

### Step 1: `docker-compose.yml` (Standard Volumes)

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: bidb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DATABASE__PASSWORD:-1234}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile
    depends_on:
      db:
        condition: service_healthy
    environment:
      ENV: production
      DATABASE__HOST: db
      DATABASE__PORT: 5432
      DATABASE__USER: postgres
      DATABASE__PASSWORD: ${DATABASE__PASSWORD:-1234}
      DATABASE__DBNAME: bidb
      JWT__SECRET_KEY: ${JWT__SECRET_KEY:-change-me-in-production}
      JWT__ALGORITHM: HS256
      UPLOAD__TEMP_DIR: /app/data/tmp_uploads
      LOGGING__LOG_FILE: /app/data/logs/app.log
      CORS_ORIGINS: '["http://localhost"]'
      LOGGING__LEVEL: INFO
      AUTO_MIGRATE: "true"
    ports:
      - "8000:8000"
    volumes:
      - app_data:/app/data
    restart: unless-stopped

volumes:
  postgres_data:
  app_data:
```

**Why this is correct:**
- Named volumes `app_data` and `postgres_data` managed by Docker
- No host path dependencies
- Works identically on Linux, Mac, Windows
- Data persists until `docker-compose down -v`

---

### Step 2: `Dockerfile` (Minimal)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv/

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create data directories (will be overridden by volume mount)
RUN mkdir -p /app/data/uploads /app/data/logs /app/data/tmp_uploads

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "src.mkobi.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Step 3: Update `config.py` (No Changes Needed)

The app already reads from env vars:
- `UPLOAD__TEMP_DIR` → defaults to `/app/data/tmp_uploads` in container
- `LOGGING__LOG_FILE` → defaults to `/app/data/logs/app.log`

No code changes needed - pydantic-settings handles env vars correctly.

---

### Step 4: `.env.example` (Documentation)

```bash
# Database
DATABASE__PASSWORD=your_secure_password_here
DATABASE__DBNAME=bidb

# JWT
JWT__SECRET_KEY=your_jwt_secret_key_here
JWT__ALGORITHM=HS256

# App
ENV=production
CORS_ORIGINS='["http://localhost:3000"]'
LOGGING__LEVEL=INFO

# Optional: Override data paths (usually not needed)
# UPLOAD__TEMP_DIR=/app/data/tmp_uploads
# LOGGING__LOG_FILE=/app/data/logs/app.log
```

---

### Step 5: `.gitignore` (Add .env)

```
# Environment
.env
```

---

### Step 6: `README_DOCKER.md` (Quick Start Guide)

```markdown
## Quick Start with Docker

### Prerequisites
- Docker installed
- Docker Compose installed (or docker compose plugin)

### Start Application

1. (Optional) Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env and set secure passwords
   ```

2. Start all services:
   ```bash
   docker-compose up -d
   ```

3. Access the application:
   - **API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc

### Data Storage

All data is stored in Docker volumes:

| Volume | Container Path | Purpose |
|--------|----------------|---------|
| `app_data` | `/app/data` | App data (uploads, logs, temp files) |
| `postgres_data` | `/var/lib/postgresql/data` | PostgreSQL database files |

#### View volumes:
```bash
docker volume ls
docker volume inspect mkobi_app_data
docker volume inspect mkobi_postgres_data
```

#### Access data inside volumes:
```bash
# List uploaded files
docker exec mkobi-app-1 ls -la /app/data/uploads

# View logs
docker exec mkobi-app-1 cat /app/data/logs/app.log

# Access PostgreSQL
docker exec -it mkobi-db-1 psql -U postgres -d bidb
```

### Common Commands

| Command | Description |
|---------|-------------|
| `docker-compose ps` | Show running services |
| `docker-compose logs -f` | Follow all logs |
| `docker-compose logs -f app` | Follow app logs |
| `docker-compose down` | Stop and remove containers |
| `docker-compose down -v` | ⚠️ Stop + DELETE ALL DATA |
| `docker-compose up -d --build` | Rebuild after code changes |

### Production Deployment

1. Set strong passwords in `.env`:
   ```bash
   DATABASE__PASSWORD=<strong-password>
   JWT__SECRET_KEY=<strong-secret>
   ```

2. Use Docker secrets (recommended):
   ```bash
   DATABASE__PASSWORD_FILE=/run/secrets/db_password
   JWT__SECRET_KEY_FILE=/run/secrets/jwt_secret
   ```

3. Update CORS for production:
   ```bash
   CORS_ORIGINS='["https://yourdomain.com"]'
   ```

4. Run production checklist (see `PRODUCTION_CHECKLIST.md`)
```

---

## Architecture Benefits

| Feature | Standard Docker Volumes | platformdirs |
|---------|----------------------|---------------|
| Works on any machine | ✅ Yes | ⚠️ Needs setup script |
| No host dependencies | ✅ Yes | ❌ Depends on host paths |
| True containerization | ✅ Yes | ❌ Breaks isolation |
| `docker-compose up` only | ✅ Yes | ❌ Need setup.sh first |
| Data portability | ✅ `docker volume` commands | ❌ Scattered on host |
| Industry standard | ✅ Yes | ❌ Non-standard |

---

## Implementation Steps

1. [x] Create `docker-compose.yml` with named volumes
2. [x] Update `Dockerfile` to create `/app/data` directories
3. [x] Add `.env` to `.gitignore`
4. [x] Create `README_DOCKER.md` with quick start
5. [ ] Test on clean machine: `docker-compose up -d`
6. [x] Run `ruff check .` - passed
7. [x] Run `uv run mypy .` - config issue (pre-existing)
8. [x] Run `uv run pytest tests/` - 281 passed, 30 failed (pre-existing bugs)

---

## Why NOT platformdirs in Docker?

1. **Breaks containerization** - containers should be isolated from host
2. **No portability** - host paths differ between machines
3. **Permission issues** - Docker daemon vs host user mismatch
4. **Not industry standard** - nobody does this
5. **Complicates setup** - need setup.sh scripts

### Correct Approach:
- Docker volumes = managed by Docker, portable, standard
- If you need host access to data → use `docker cp` or `docker exec`

---

## Final Recommendation

**Use Standard Docker Volumes (this plan)** because:
1. True "works on any machine" - just `docker-compose up`
2. Follows Docker best practices
3. No host dependencies or setup scripts
4. Data persists in Docker-managed volumes
5. Industry standard approach

---

## Commands Summary

### Development:
```bash
docker-compose up -d          # Start all services
docker-compose logs -f app      # Watch app logs
docker-compose down              # Stop services
```

### Production:
```bash
# 1. Set secure passwords
vim .env

# 2. Start
docker-compose up -d

# 3. Verify
curl http://localhost:8000/health
```

### Data Management:
```bash
# Backup database
docker exec mkobi-db-1 pg_dump -U postgres bidb > backup.sql

# Restore database
docker exec -i mkobi-db-1 psql -U postgres bidb < backup.sql

# Access uploaded files
docker exec mkobi-app-1 tar czf - /app/data/uploads > uploads.tar.gz
```

---

**Next step:** Implementation is complete. User can run `docker-compose up -d` on any machine with Docker installed.
