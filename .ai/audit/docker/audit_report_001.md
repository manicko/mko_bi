# Docker & Runtime Environment Audit Report — mkobi BI Dashboard

**Date:** 2026-05-25
**Scope:** Dockerfile, docker-compose files, nginx config, init scripts, .dockerignore, application config
**Auditor:** Architecture Audit Agent

---

## Findings Table

| Severity | File | Line | Problem | Impact | Recommendation |
|----------|------|------|---------|--------|----------------|
| HIGH | docker-compose.yml | 56, 92, 149 | Default JWT__SECRET_KEY hardcoded in compose (`dev-secret-key-for-local-development`) | If env vars are not set externally, production deployments use a known weak secret. No enforcement mechanism (`${VAR:?error}`) in the base compose file. | Use `${JWT__SECRET_KEY:?JWT__SECRET_KEY is required}` syntax in the base `docker-compose.yml` for production-critical secrets, or remove defaults entirely. |
| HIGH | docker-compose.yml | 21, 53, 85 | Default DATABASE__PASSWORD hardcoded (`postgres`) | Same pattern as JWT — if `.env` is not configured, production uses a well-known password. | Use `${DATABASE__PASSWORD:?DATABASE__PASSWORD is required}` syntax. |
| HIGH | docker-compose.yml | 59, 95, 96, 152, 153 | Default admin credentials (`admin@example.com` / `admin@example.com`) in production compose | If not overridden, production starts with known admin credentials. The app config validates against weak credentials in production, but the compose file still provides them as defaults. | Remove admin credential defaults from compose; enforce via `${ADMIN_USERNAME:?} / ${ADMIN_PASSWORD:?}`. |
| HIGH | docker-compose.yml | 101 | `AUTO_MIGRATE: "false"` in production app service | The spec requires `AUTO_MIGRATE=true` for automatic schema migrations. The compose file explicitly disables it, relying on the separate `migrate` service instead. While functional, this deviates from the spec and creates a fragile two-step migration process. | Either set `AUTO_MIGRATE=true` per spec, or document why the separate migrate service pattern is preferred. Ensure the migration service is production-tested. |
| MEDIUM | Dockerfile | 138 | No `HEALTHCHECK` instruction in Dockerfile | The Dockerfile defines no HEALTHCHECK. Health checks are only configured at the compose level (`docker-compose.yml` line 107-112). If the image is run without compose (e.g., Kubernetes, ECS, manual `docker run`), no health check exists. | Add `HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1` to the `prod` stage. |
| MEDIUM | Dockerfile | 138 | No `prod-slim` build target | The spec (`docs/10-deployment/deployment.md`) defines a `prod-slim` target for constrained environments. Only `base`, `dev`, `test`, and `prod` targets exist. | Add a `prod-slim` stage with minimal runtime dependencies and 1 worker, or update the spec to match reality. |
| MEDIUM | Dockerfile | 138 | `prod` stage uses `uvicorn` directly, not `uv run uvicorn` | The spec requires `uv run uvicorn mkobi.main:app`. The Dockerfile CMD is `["uvicorn", "src.mkobi.main:app", ...]`. While the venv PATH is set (line 122), the spec mandates `uv run` for consistency. | Align CMD with spec: `["uv", "run", "uvicorn", "src.mkobi.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]`. |
| MEDIUM | docker-compose.yml | 165-178 | Nginx service uses `profiles: [production]` but is defined in base compose | The nginx service is always parsed but only activated with `--profile production`. This is acceptable but means the base compose file contains production-only services. The nginx.conf mounts `../frontend/dist` which is only available after a frontend build. | Document that nginx requires a prior frontend build, or add a comment in the compose file. Consider moving nginx to a separate `docker-compose.prod.yml`. |
| MEDIUM | docker-compose.override.yml | 60, 83 | Hardcoded `JWT__SECRET_KEY: dev-secret-key-for-local-development` (not templated) | Unlike the base compose which uses `${JWT__SECRET_KEY:-...}`, the override hardcodes the dev secret. This is acceptable for dev-only but means the override always overrides any `.env` value. | Use `${JWT__SECRET_KEY:-dev-secret-key-for-local-development}` for consistency, allowing `.env` to override. |
| MEDIUM | docker-compose.override.yml | 62-63 | Hardcoded admin credentials in dev override | `ADMIN_USERNAME: admin@example.com` and `ADMIN_PASSWORD: admin@example.com` are hardcoded, not templated. | Use `${ADMIN_USERNAME:-admin@example.com}` pattern for consistency. |
| MEDIUM | docker-compose.test.yml | 104 | `RECREATE_TEST_DB: "true"` is correct per spec, but `AUTO_MIGRATE: "true"` is also set | Both `AUTO_MIGRATE` and a separate `test-migrate` service exist. This creates a potential race condition — the migrate service runs alembic, then the app service also runs auto-migrate on startup. | Remove `AUTO_MIGRATE: "true"` from test-app since `test-migrate` already handles it, or remove the `test-migrate` service and rely on `AUTO_MIGRATE`. |
| LOW | Dockerfile | 42-46 | `build-essential` and `libpq-dev` installed in `base` stage (inherited by prod) | These are compile-time dependencies. The prod stage only needs `libpq` (runtime), not `libpq-dev` or `build-essential`. This increases the prod image size. | Move `build-essential` and `libpq-dev` to a separate builder stage or install only `libpq5` in prod. |
| LOW | Dockerfile | 49-50 | `uv` installed via curl pipe to shell | Piping `curl | sh` is an anti-pattern for reproducibility and security. The version is not pinned. | Pin uv version: `curl -LsSf https://astral.sh/uv/0.7.12/install.sh | sh` (or use `pip install uv==0.7.12` in a prior step). |
| LOW | docker-compose.yml | 23-24 | `MKOBI_APP_PASSWORD` defaults to `secure_password_placeholder` | The placeholder name suggests it should be changed, but nothing enforces this in production. | Use `${MKOBI_APP_PASSWORD:?MKOBI_APP_PASSWORD is required}` syntax. |
| LOW | docker-compose.yml | 99 | `CORS_ORIGINS` hardcoded to `["http://localhost:3000", "http://localhost:5173"]` in production compose | Production CORS should be configurable per deployment, not hardcoded to localhost origins. | Use `${CORS_ORIGINS:-[]}` and require explicit configuration in production. |
| LOW | docker-compose.override.yml | 73 | Dev command uses `src.mkobi.main:app` instead of `mkobi.main:app` | The Dockerfile copies source to `./src/` and the PYTHONPATH includes `/app`, so `src.mkobi.main:app` works. But the spec and prod stage use `mkobi.main:app` (via `uv run`). This inconsistency could mask import issues. | Align dev command with prod: use `mkobi.main:app` and ensure `PYTHONPATH=/app/src`. |
| LOW | nginx.conf | 14 | Nginx listens on port 80 only, no HTTPS | The compose maps `443:443` but the nginx.conf has no SSL server block. | Add SSL configuration or remove the 443 port mapping from compose. |

---

## Final Assessment

```text
Deployment Readiness: PARTIALLY READY
```

### Summary

The Docker setup is well-structured with a solid multi-stage build, proper `.dockerignore`, non-root user, health checks at the compose level, dedicated DB migration service, least-privilege DB role, and Docker secrets support. However, several issues prevent a **READY** rating:

1. **No production credential enforcement** in the base `docker-compose.yml` — all secrets have weak defaults with no `:?` enforcement.
2. **No HEALTHCHECK in the Dockerfile** — the image is not self-contained for non-compose orchestrators.
3. **Missing `prod-slim` target** per spec.
4. **`AUTO_MIGRATE: "false"`** in production deviates from spec.
5. **Dev dependencies in prod image** (`build-essential`, `libpq-dev`).

---

## File-Level Recommendations

### File: `docker/Dockerfile`

**Problems:**
- No `HEALTHCHECK` instruction in any stage.
- No `prod-slim` build target (spec requires it).
- `build-essential` and `libpq-dev` inherited by prod stage (unnecessary size).
- `uv` installed via unpinned `curl | sh`.
- Prod CMD uses `uvicorn` directly instead of `uv run uvicorn` per spec.
- `PYTHONUNBUFFERED=1` is set (good) but `PYTHONDONTWRITEBYTECODE=1` is also set (good).

**Recommendations:**
- Add `HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1` to the `prod` stage.
- Add a `prod-slim` stage with minimal runtime (`libpq5` only, no `build-essential`), 1 worker.
- Split system deps: keep `build-essential`/`libpq-dev` only in `base` for dev/test; create a `prod-base` with only `libpq5` and `curl`.
- Pin uv version in the installer command.
- Change prod CMD to `["uv", "run", "uvicorn", "src.mkobi.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]`.

### File: `docker/docker-compose.yml`

**Problems:**
- Default `JWT__SECRET_KEY`, `DATABASE__PASSWORD`, `MKOBI_APP_PASSWORD`, and admin credentials have weak fallback values with no enforcement.
- `AUTO_MIGRATE: "false"` contradicts spec requirement.
- `CORS_ORIGINS` hardcoded to localhost in production compose.
- Nginx service included in base file behind a profile (minor structural issue).

**Recommendations:**
- Use `${JWT__SECRET_KEY:?JWT__SECRET_KEY is required}` for production-critical secrets.
- Use `${DATABASE__PASSWORD:?DATABASE__PASSWORD is required}`.
- Use `${MKOBI_APP_PASSWORD:?MKOBI_APP_PASSWORD is required}`.
- Remove default admin credentials or use `:?` enforcement.
- Set `AUTO_MIGRATE: "true"` per spec, or document the rationale for the separate migrate service pattern.
- Use `CORS_ORIGINS: ${CORS_ORIGINS:?CORS_ORIGINS is required}` for production.
- Consider moving nginx to `docker-compose.prod.yml`.

### File: `docker/docker-compose.override.yml`

**Problems:**
- Hardcoded `JWT__SECRET_KEY` (not templated) always overrides `.env`.
- Hardcoded admin credentials.
- Dev command uses `src.mkobi.main:app` instead of `mkobi.main:app`.

**Recommendations:**
- Use `${JWT__SECRET_KEY:-dev-secret-key-for-local-development}` for consistency.
- Use `${ADMIN_USERNAME:-admin@example.com}` pattern.
- Align dev import path with prod.

### File: `docker/docker-compose.test.yml`

**Problems:**
- Both `test-migrate` service and `AUTO_MIGRATE: "true"` on `test-app` — potential race condition.
- Test DB credentials use simple defaults without enforcement (acceptable for test, but worth noting).

**Recommendations:**
- Remove `AUTO_MIGRATE: "true"` from `test-app` since `test-migrate` handles it, or remove `test-migrate` and rely solely on `AUTO_MIGRATE`.

### File: `docker/nginx/nginx.conf`

**Problems:**
- No SSL configuration despite compose mapping port 443.
- No rate limiting or security headers.

**Recommendations:**
- Add SSL server block or remove 443 port mapping.
- Add security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`).

### File: `.dockerignore`

**Problems:**
- None identified. Well-structured, excludes `.env`, `.git`, caches, and IDE files.

**Recommendations:**
- No changes needed.

### File: `docker/init-scripts/01-create-app-role.sh`

**Problems:**
- None identified. Properly implements least-privilege role creation with `DROP IF EXISTS` for idempotency.

**Recommendations:**
- No changes needed.

---

## Positive Findings

1. **Multi-stage build** with clear separation: `frontend-builder`, `base`, `dev`, `test`, `prod`.
2. **Non-root user** (`app`) configured in all stages that run the application.
3. **No `.env` copied into image** — `.dockerignore` correctly excludes all `.env*` files.
4. **No hardcoded secrets in Dockerfile** — all secrets come from environment/compose.
5. **`uv.lock` copied** for reproducible installs with `uv sync --frozen`.
6. **Docker secrets support** via `SecretsFileSource` in config (`_FILE` env var pattern).
7. **Least-privilege DB role** (`mkobi_app`) created via init script, separate from superuser.
8. **Health check endpoint** implemented in app (`/health` and `/health/detailed`) with DB connectivity verification.
9. **Stale temp file cleanup** via `DatabaseStarter` on startup and background task during runtime.
10. **CORS validation** in app code — rejects wildcard `*` in production (logs warning), requires explicit origins.
11. **Admin credential validation** in config — rejects weak usernames/passwords in production.
12. **Separate migration service** ensures schema is ready before app starts.
13. **Redis persistence** via named volume.
14. **PostgreSQL 16** pinned version (no `latest` tag).
15. **Redis 7-alpine** pinned version.
