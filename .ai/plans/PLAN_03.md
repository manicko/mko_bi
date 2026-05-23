---
phase: 3
name: Docker Development Environment Improvements
description: Fix gaps in Docker dev setup: missing frontend dev server in Docker, override not enabling hot reload properly, no Vite proxy for API, missing .env handling for dev, and documentation drift between docker.md and actual config.
depends_on: []
files_modified:
  - docker-compose.override.yml
  - Dockerfile
  - docs/11-guides/docker.md
  - docs/10-deployment/deployment.md
autonomous: true
---

# Docker Development Environment Improvements — Phase 3

## Executive Summary

The current Docker development setup has several gaps that degrade developer experience:

1. **No frontend dev server in Docker** — `docker-compose.override.yml` mounts `frontend/dist` (pre-built static files) instead of running the Vite dev server. Developers must manually run `npm run dev` on the host, defeating the purpose of Docker-based dev.
2. **Dev override doesn't enable `--reload`** — The override file overrides the CMD to `uvicorn ...` without `--reload`, so even backend hot reload is broken in Docker dev mode.
3. **No Vite proxy configured** — `vite.config.ts` has no `server.proxy` section, so the Vite dev server can't forward `/api` requests to the FastAPI backend container.
4. **Dev override uses hardcoded passwords** — `DATABASE__PASSWORD: ${DATABASE__PASSWORD:-1234}` and `MKOBI_APP_PASSWORD: ${MKOBI_APP_PASSWORD:-dev_password}` are duplicated from the base compose instead of being sourced from `.env`.
5. **Documentation drift** — `docs/11-guides/docker.md` references non-existent `prod-base` and `prod-slim` stages, and cross-links point to wrong paths.
6. **No `docker-compose.dev.yml` convention** — The project uses `docker-compose.override.yml` (auto-loaded by Docker Compose), but the docs and README reference explicit `-f` flags. The override should be the default dev experience.

## Waves Structure

### Wave 1: Backend Dev Hot Reload Fix 🔧
*Dependencies: None — standalone fix*
*Tasks: 1-2*

### Wave 2: Frontend Dev Server in Docker ⚛️
*Dependencies: None — independent of Wave 1*
*Tasks: 3-5*

### Wave 3: Documentation Alignment 📖
*Dependencies: Waves 1-2 (must reflect actual state)*
*Tasks: 6-7*

## Dependency Graph

```
Wave 1 (Backend hot reload) ──┐
                               ├─> Wave 3 (Docs alignment)
Wave 2 (Frontend dev server) ──┘
```

Waves 1 and 2 are **independent** and can run in parallel. Wave 3 depends on both.

## Tasks

### Wave 1: Backend Dev Hot Reload Fix

#### Task 1: Fix Dev Override CMD to Enable Hot Reload
- **ID**: TASK_03_01_fix_dev_reload
- **Title**: Restore --reload flag in dev override command
- **Description**: The `docker-compose.override.yml` overrides the app CMD to `uvicorn ...` without `--reload`, breaking hot reload. The Dockerfile `dev` stage already has `--reload` in its CMD, but the override replaces it. Fix the override to include `--reload`.
- **Files affected**: `docker-compose.override.yml:58`
- **Targets**:
  - Change `command: ["uvicorn", "src.mkobi.main:app", "--host", "0.0.0.0", "--port", "8000"]`
  - To `command: ["uvicorn", "src.mkobi.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]`
- **Acceptance criteria**:
  - Backend container restarts code on file changes inside the container
  - `docker compose up -d` (with override auto-loaded) gives hot reload out of the box
- **Tests to run**:
  - `docker compose up -d`
  - Modify a Python file in `src/mkobi/` and verify the container auto-reloads

#### Task 2: Simplify Dev Override Environment (Use .env Defaults)
- **ID**: TASK_03_02_simplify_dev_env
- **Title**: Remove duplicated hardcoded passwords from dev override
- **Description**: The dev override repeats `DATABASE__PASSWORD: ${DATABASE__PASSWORD:-1234}` and `MKOBI_APP_PASSWORD: ${MKOBI_APP_PASSWORD:-dev_password}`. These defaults should come from `.env` file only. The override should only set values that differ from production defaults (like `ENV: development`, `LOGGING__LEVEL: DEBUG`).
- **Files affected**: `docker-compose.override.yml:14-27`, `docker-compose.override.yml:36-48`, `docker-compose.override.yml:63-66`
- **Targets**:
  - Remove `DATABASE__PASSWORD`, `MKOBI_APP_PASSWORD`, `JWT__SECRET_KEY` from `migrate` service environment (let them come from `.env`)
  - Remove `DATABASE__USER`, `DATABASE__PASSWORD`, `JWT__SECRET_KEY` from `app` service environment (let them come from `.env`)
  - Remove `POSTGRES_PASSWORD`, `MKOBI_APP_PASSWORD` from `db` service environment (let them come from `.env`)
  - Keep only dev-specific overrides: `ENV: development`, `LOGGING__LEVEL: DEBUG`, `RECREATE_TEST_DB: "true"`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`
- **Acceptance criteria**:
  - Dev override only contains values that are truly dev-specific
  - All secrets sourced from `.env` file
  - `docker compose up -d` works with the existing `.env` file
- **Tests to run**:
  - `docker compose down -v && docker compose up -d`
  - Verify app starts, connects to DB, and serves API

### Wave 2: Frontend Dev Server in Docker

#### Task 3: Add Frontend Dev Service to Override
- **ID**: TASK_03_03_add_frontend_dev_service
- **Title**: Add a frontend dev server service to docker-compose.override.yml
- **Description**: The current override mounts `frontend/dist` (pre-built static), requiring manual `npm run dev` on the host. Add a `frontend` service that runs the Vite dev server inside Docker with hot reload.
- **Files affected**: `docker-compose.override.yml` (new service addition)
- **Targets**:
  - Add `frontend` service:
    ```yaml
    frontend:
      image: node:20-alpine
      working_dir: /app
      volumes:
        - ./frontend:/app
        - frontend_node_modules:/app/node_modules
      ports:
        - "5173:5173"
      command: ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
      environment:
        - CHOKIDAR_USEPOLLING=true
    ```
  - Add `frontend_node_modules` volume to the `volumes:` section
  - Remove the `frontend/dist` mount from the `app` service (no longer needed in dev)
- **Acceptance criteria**:
  - `docker compose up -d` starts frontend dev server on port 5173
  - Vite hot reload works for frontend file changes
  - Node modules are persisted in a volume (not lost on container restart)
- **Tests to run**:
  - `docker compose up -d`
  - Open `http://localhost:5173` — Vite dev server responds
  - Edit a `.tsx` file and verify browser hot reloads

#### Task 4: Add Vite Proxy for API Requests
- **ID**: TASK_03_04_add_vite_proxy
- **Title**: Configure Vite dev server to proxy API requests to backend
- **Description**: Without a proxy, the Vite dev server on port 5173 can't reach the FastAPI backend on port 8000 (different container, different port). Add `server.proxy` to `vite.config.ts` so `/api` requests are forwarded to `http://app:8000`.
- **Files affected**: `frontend/vite.config.ts:4-11`
- **Targets**:
  - Add `server` config to `defineConfig`:
    ```typescript
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://app:8000',
          changeOrigin: true,
        },
      },
    },
    ```
- **Acceptance criteria**:
  - Frontend dev server proxies `/api/*` to the FastAPI container
  - No CORS errors in browser dev tools when using Vite dev server
  - API calls from the frontend work without absolute URLs
- **Tests to run**:
  - `docker compose up -d`
  - Open `http://localhost:5173` and trigger an API call
  - Verify in browser Network tab that the request goes to `localhost:5173/api/...` and returns data

#### Task 5: Update App Service to Not Depend on Frontend Build in Dev
- **ID**: TASK_03_05_remove_frontend_dist_mount_in_dev
- **Title**: Remove frontend/dist mount from app service in dev override
- **Description**: The dev override currently mounts `./frontend/dist:/app/frontend/dist`, which requires a pre-built frontend. With the Vite dev server running separately, this mount is unnecessary and misleading.
- **Files affected**: `docker-compose.override.yml:57` (the `- ./frontend/dist:/app/frontend/dist` line)
- **Targets**:
  - Remove the `- ./frontend/dist:/app/frontend/dist` volume mount from the `app` service in the override
  - Keep all other mounts (`./src`, `./alembic`, `./tests`, etc.)
- **Acceptance criteria**:
  - App service in dev mode doesn't require `frontend/dist` to exist
  - Backend API works independently of frontend build state
- **Tests to run**:
  - Ensure `frontend/dist/` does NOT exist
  - `docker compose up -d`
  - Verify backend starts and serves API on port 8000

### Wave 3: Documentation Alignment

#### Task 6: Fix Docker Guide (docker.md)
- **ID**: TASK_03_06_fix_docker_guide
- **Title**: Align docker.md with actual Dockerfile and compose state
- **Description**: `docs/11-guides/docker.md` references non-existent `prod-base` and `prod-slim` stages, has wrong cross-link paths, and doesn't document the frontend dev server.
- **Files affected**: `docs/11-guides/docker.md`
- **Targets**:
  - Remove references to `prod-base` and `prod-slim` stages (they don't exist in the Dockerfile)
  - Fix cross-link paths:
    - `../04-run/run-guide.md` → `../99-reference/run-guide.md`
    - `../05-ops/deployment.md` → `../10-deployment/deployment.md`
    - `../05-ops/task-queue-migration.md` → `../11-guides/task-queue-migration.md`
  - Update the "Quick Start → Development" section to reflect the new frontend dev service
  - Update the "File Structure" section to include the frontend service
  - Add a note that `docker compose up -d` (without `-f`) auto-loads the override for dev
- **Acceptance criteria**:
  - All cross-links resolve to existing files
  - All Dockerfile targets mentioned actually exist
  - Dev setup instructions match the actual docker-compose.override.yml
- **Tests to run**:
  - Verify all cross-links resolve
  - Follow the dev setup instructions from scratch

#### Task 7: Fix Deployment Doc (deployment.md)
- **ID**: TASK_03_07_fix_deployment_doc
- **Title**: Update deployment.md to reflect actual Docker dev workflow
- **Description**: `docs/10-deployment/deployment.md` has a "Docker Deployment" section that references the old override workflow and doesn't mention the frontend dev server.
- **Files affected**: `docs/10-deployment/deployment.md:158-247`
- **Targets**:
  - Update the "Quick Start" section to clarify:
    - `docker compose up -d` → production (default)
    - `docker compose up -d` (with override auto-loaded) → development with hot reload for both backend and frontend
  - Add a note about the frontend dev server on port 5173
  - Update the Dockerfile targets table to match actual targets (remove `prod-slim`)
- **Acceptance criteria**:
  - Deployment doc matches actual Docker behavior
  - Developers can follow the doc to set up both local and Docker dev environments
- **Tests to run**:
  - Verify all commands in the doc work as described

## Must Have Requirements

1. **Backend hot reload works in Docker dev** — `--reload` flag is active
2. **Frontend dev server runs in Docker** — Vite dev server with hot reload on port 5173
3. **Vite proxies API to backend** — no CORS issues in dev
4. **No pre-built frontend required for dev** — `frontend/dist` not needed
5. **Dev secrets sourced from .env** — no hardcoded passwords in override
6. **Documentation matches reality** — all cross-links valid, all commands work

## Risk Assessment

### Risk Level: Low
- Changes are confined to `docker-compose.override.yml` and `vite.config.ts`
- Production `docker-compose.yml` and `Dockerfile` are untouched
- Each wave is independently reversible
- No changes to application code or API contracts

### Rollback
- Revert `docker-compose.override.yml` → instant rollback for Waves 1-2
- Revert `vite.config.ts` → instant rollback for Wave 4
- Revert doc files → instant rollback for Wave 3

## Success Metrics

- [ ] `docker compose up -d` starts backend + frontend + db with hot reload
- [ ] Backend auto-reloads on Python file changes
- [ ] Frontend auto-reloads on TSX file changes
- [ ] API calls from frontend reach backend without CORS errors
- [ ] No `frontend/dist` directory needed for dev
- [ ] All doc cross-links resolve
- [ ] All doc commands work as described
- [ ] Production `docker-compose.yml` unchanged

## References

- [Project Structure](C:\py_dev\mkobi\.ai\structure\map.md)
- [Docker Guide](C:\py_dev\mkobi\docs\11-guides\docker.md)
- [Deployment Doc](C:\py_dev\mkobi\docs\10-deployment\deployment.md)
- [Docker Compose Override Docs](https://docs.docker.com/compose/multiple-compose-files/)
- [Vite Server Options](https://vite.dev/config/server-options.html#server-proxy)
