# Audit Fix Plan — Prioritized Development Roadmap

**Date:** 2026-06-17
**Source:** All audit phases (01–90, 99-validation) + bug reports (00-bug_report)
**Scope:** Mandatory fixes + high-value advisory fixes. Excludes rejected/already-fixed findings.

---

## How to Read This Plan

- **Priority**: P0 (critical, fix first) → P3 (low, fix when convenient)
- **Effort**: Trivial (<5 min) / Small (<30 min) / Medium (<2 h)
- Each item references the original finding ID(s) and affected files
- Findings already fixed in the codebase are noted and skipped

---

## P0 — Critical / Production-Blocking

### P0-1: Fix Frontend `getAggregatedData` Filters (INT-011)

**Severity:** HIGH | **Effort:** Trivial | **Type:** RUNTIME-ERROR

**Problem:** Frontend passes `filters` as an object to Axios, which serializes it as `?filters[key]=value`. Backend expects `filters` as a JSON string (`json.loads(filters)`). Filters are completely non-functional.

**File:** `frontend/src/features/dashboards/api/dashboardApi.ts:23-29`

**Fix:** Stringify filters before passing as query param:
```typescript
// In useAggregatedData, change the queryFn:
queryFn: () =>
  dashboardApi.getAggregatedData({
    dashboard_id: dashboardId,
    graph_id: graphId,
    filters: filters ? JSON.stringify(filters) : undefined,
  }),
```

Also update `AggregatedDataRequest` type in `api.types.ts` to make `filters` a `string` instead of an object.

---

## P1 — High Priority (Mandatory Fixes)

### P1-1: Fix Dockerfile Frontend Build (INF-001)

**Severity:** CRITICAL | **Effort:** Trivial | **Type:** RUNTIME-ERROR

**Problem:** BuildKit cache mount (`--mount=type=cache,target=/app/frontend/node_modules`) prevents `node_modules` from being written to the image layer. `npm run build` fails with `tsc: not found`. Production Docker image has no frontend.

**File:** `docker/Dockerfile:17-19`

**Fix:** Remove the cache mount:
```dockerfile
# Before:
RUN --mount=type=cache,target=/app/frontend/node_modules \
    npm ci

# After:
RUN npm ci
```

### P1-2: Fix Nginx IPv6 Healthcheck (INF-002)

**Severity:** HIGH | **Effort:** Trivial | **Type:** RUNTIME-ERROR

**Problem:** Nginx binds to IPv4 only (`listen 80;`) but healthcheck resolves `localhost` to IPv6 `[::1]`. Healthcheck permanently fails (458+ consecutive failures).

**File:** `docker/nginx/nginx.conf:14`

**Fix:** Change to dual-stack:
```nginx
listen [::]:80;
```

### P1-3: Fix `SecretsFileSource` Empty `_FILE` Values (INF-003)

**Severity:** MEDIUM | **Effort:** Trivial | **Type:** SPEC-DEVIATION

**Problem:** `LOGGING__LOG_FILE=""` in docker-compose.override.yml is matched by `SecretsFileSource` (which looks for all `*_FILE` vars). Empty string resolves to `.` (current directory), causing `Is a directory` error on every startup.

**File:** `src/mkobi/config.py:66-74`

**Fix:** Add empty-value guard:
```python
if env_var_name.endswith("_FILE"):
    file_path_str = os.environ[env_var_name]
    if not file_path_str.strip():
        continue
```

### P1-4: Fix `test_none_jwt_secret_accepted` for Containerized Env (BE-001 / TST-001)

**Severity:** HIGH | **Effort:** Small | **Type:** RUNTIME-ERROR

**Problem:** Test deletes `JWT__SECRET_KEY` and expects `.env` file fallback, but `.env` is not mounted in Docker test container. Test fails in Docker.

**File:** `tests/test_config.py:379-384`

**Fix:** Replace with environment-agnostic test:
```python
def test_env_jwt_secret_accepted(self, monkeypatch):
    monkeypatch.setenv("JWT__SECRET_KEY", "test-jwt-secret-key-for-unit-tests-32-chars!")
    settings = Settings()
    assert settings.jwt.secret_key == "test-jwt-secret-key-for-unit-tests-32-chars!"
```

### P1-5: Fix `test_validate_file_invalid_extension` for MIME-First Validation (BE-002 / TST-002)

**Severity:** MEDIUM | **Effort:** Small | **Type:** SPEC-DEVIATION

**Problem:** Test expects extension check to fail first, but with `python-magic` installed, MIME detection runs first and rejects `.txt` files as `text/plain`.

**File:** `tests/test_data_service.py:552-577`

**Fix:** Update expected regex to match MIME-first error:
```python
with pytest.raises(ValueError, match="Detected MIME type.*not allowed"):
```

### P1-6: Fix Ruff Cache Permission Errors in Docker Tests (BE-003 / TST-003)

**Severity:** MEDIUM | **Effort:** Trivial | **Type:** RUNTIME-ERROR

**Problem:** Non-root `app` user can't write to `.ruff_cache` in Docker container. Tests fail.

**File:** `tests/test_dev_seeders.py:193, 218`

**Fix:** Add `--no-cache` to ruff subprocess calls:
```python
result = subprocess.run(
    [ruff_path, "check", "--no-cache", "src/mkobi/db/seeders/test_media_dash.py"],
    capture_output=True, text=True,
)
```

### P1-7: Align Nginx `X-Frame-Options` with Application (DC-001)

**Severity:** MEDIUM | **Effort:** Trivial | **Type:** SPEC-DEVIATION

**Problem:** Application sets `X-Frame-Options: DENY` but Nginx overrides with `SAMEORIGIN`. Security intent is silently weakened.

**File:** `docker/nginx/nginx.conf:21`

**Fix:** Remove `X-Frame-Options` from Nginx (let the application middleware handle it), or change to `DENY` to match application intent.

### P1-8: Prevent Admin User Creation with Placeholder Password (DC-006)

**Severity:** HIGH | **Effort:** Small | **Type:** BEST-PRACTICE

**Problem:** If `ADMIN_PASSWORD` is not set, `ensure_admin_user()` creates admin with known default `"CHANGE_ME_ADMIN_PASSWORD"`.

**File:** `src/mkobi/db/starter.py:317-352`

**Fix:** Add check in `ensure_admin_user()`:
```python
if config.admin_password.lower() in {p.lower() for p in WEAK_PASSWORDS}:
    logger.error("Refusing to create admin user with a known weak/placeholder password. Set ADMIN_PASSWORD.")
    return
```

---

## P2 — Medium Priority (Advisory Fixes with Significant Impact)

### P2-1: Remove Redundant `cast()` Calls (BE-004)

**Severity:** LOW | **Effort:** Trivial | **Type:** BEST-PRACTICE

**File:** `src/mkobi/services/processing_log_service.py:78,85,224,249,255`

Remove 5 redundant `cast()` calls. Keep casts on lines 72/153 (where `create_log` returns `Any`).

### P2-2: Remove Dead `DataPipeline` Class (DP-01)

**Severity:** MEDIUM | **Effort:** Trivial | **Type:** BEST-PRACTICE

**File:** `src/mkobi/data/processing/registry.py:33-221`

Delete the entire `DataPipeline` class. Update comment in `processing_log_service.py:51`.

### P2-3: Tighten `find_task_file` Glob Pattern (DP-03)

**Severity:** MEDIUM | **Effort:** Trivial | **Type:** BEST-PRACTICE

**File:** `src/mkobi/services/file_processing.py:295`

```python
# Before:
task_files = list(upload_dir.glob(f"*{task_id}*.csv*"))
# After:
task_files = list(upload_dir.glob(f"{task_id}.csv*"))
if len(task_files) > 1:
    raise ValueError(f"Multiple files found for task {task_id}: {[f.name for f in task_files]}")
```

### P2-4: Lower Stale Processing Timeout + Orphaned UPLOADED Check (DP-07)

**Severity:** HIGH | **Effort:** Small | **Type:** SPEC-DEVIATION

**File:** `src/mkobi/workers/data_worker.py`

1. Change `DEFAULT_STALE_PROCESSING_TIMEOUT_MINUTES = 30` → `5`
2. Add `mark_orphaned_uploaded_logs_failed()` function and call it at startup

### P2-5: Fix `getProfile()` Duplication (FE-003)

**Severity:** MEDIUM | **Effort:** Trivial | **Type:** BEST-PRACTICE

**Problem:** `getProfile()` duplicated in `authApi.ts` and `userApi.ts`.

**Fix:** Remove from `userApi.ts`, update `UserProfile.tsx` to import from `authApi`.

### P2-6: Wire LogViewer Dashboard Filter (FE-008)

**Severity:** MEDIUM | **Effort:** Small | **Type:** BEST-PRACTICE

**File:** `frontend/src/features/admin/ui/LogViewer.tsx:78-85`

Wire the empty Dashboard dropdown to `getDashboardsAdmin()`.

### P2-7: Fix `updateDashboard` Return Type Mismatch (INT-010)

**Severity:** MEDIUM | **Effort:** Trivial | **Type:** SPEC-DEVIATION

**File:** `frontend/src/features/admin/api/adminApi.ts:116-118`

Change `Promise<DashboardAdmin>` → `Promise<DashboardDetail>` to match backend's `DashboardRead` response.

### P2-8: Align `GraphDataWithConfig.layout` Type (INT-012)

**Severity:** MEDIUM | **Effort:** Small | **Type:** SPEC-DEVIATION

**File:** `frontend/src/shared/types/api.types.ts`

Define explicit `ChartLayoutConfig` interface matching backend, replace `Layout` from `react-plotly.js` in `GraphDataWithConfig`.

### P2-9: Fix `LayoutRead` and `UserRead` Nullable Timestamps (INT-015, INT-016)

**Severity:** LOW | **Effort:** Trivial | **Type:** SPEC-DEVIATION

**Files:** `src/mkobi/models/layout.py`, `src/mkobi/models/user.py`

Change `created_at: datetime | None = None` → `created_at: datetime` in both models (DB columns are non-nullable).

### P2-10: Add `updated_at` to `UserRead` (INT-017)

**Severity:** LOW | **Effort:** Trivial | **Type:** SPEC-DEVIATION

**File:** `src/mkobi/models/user.py`

Add `updated_at: datetime` to `UserRead` (column exists in DB but is not exposed).

### P2-11: Add `response_model` to Endpoints Missing It (INT-007, INT-008, INT-009)

**Severity:** LOW | **Effort:** Small | **Type:** BEST-PRACTICE

Add `response_model=SuccessResponse` or appropriate model to:
- `POST /auth/change-password` (auth.py)
- `POST /register-request` (auth.py)
- `POST /admin/registration-requests/{id}/reject` (admin.py)

### P2-12: Deputize Redundant Role Update Endpoint (INT-020)

**Severity:** MEDIUM | **Effort:** Trivial | **Type:** BEST-PRACTICE

**File:** `src/mkobi/api/routes/users.py:184`

Add `deprecated=True` to `PUT /users/{user_id}` endpoint. Frontend already uses `PATCH /admin/users/{user_id}/role`.

### P2-13: Remove Misleading Empty Body from `refreshToken()` (INT-019)

**Severity:** LOW | **Effort:** Trivial | **Type:** BEST-PRACTICE

**File:** `frontend/src/features/auth/api/authApi.ts:12`

Change `post<Token>('/auth/refresh', {})` → `post<Token>('/auth/refresh')`.

### P2-14: Align `logout()` Return Type (INT-006)

**Severity:** LOW | **Effort:** Trivial | **Type:** BEST-PRACTICE

**File:** `frontend/src/features/auth/api/authApi.ts:26-28`

Change `Promise<void>` → `Promise<SuccessResponse>` to match backend.

### P2-15: Fix `error_code` Type Alignment (INT-004)

**Severity:** MEDIUM | **Effort:** Trivial | **Type:** SPEC-DEVIATION

**File:** `src/mkobi/models/data.py:98`

Change `error_code: str | None = None` → `error_code: ErrorCode | None = None`.

### P2-16: Standardize `rq-worker` Command (INF-005 / DC-005)

**Severity:** HIGH | **Effort:** Trivial | **Type:** RUNTIME-ERROR

**File:** `docker/docker-compose.yml:162`

Change `["uv", "run", "rq", "worker", ...]` → `["/app/.venv/bin/rqworker", ...]` to match override file.

### P2-17: Add Production Credential Guard (INF-004 / DC-004)

**Severity:** MEDIUM | **Effort:** Small | **Type:** BEST-PRACTICE

**File:** `src/mkobi/config.py`

Add `model_validator` to `Settings` that rejects known-weak database passwords and JWT secrets when `ENV=production`.

### P2-18: Fix Nginx Config Documentation (DC-002, DC-010)

**Severity:** LOW | **Effort:** Trivial | **Type:** DOC-UPDATE

- Add `/health/detailed` proxy to nginx.conf (or combine with `/health` using regex)
- Review unconditional CSP header impact on development

### P2-19: Fix Configuration Documentation (DC-003, DC-008, DC-009)

**Severity:** LOW | **Effort:** Trivial | **Type:** DOC-UPDATE

**File:** `docs/06-backend/configuration.md`

- `DATABASE__USER` default is `mkobi_app` (not `postgres`)
- `JWT__ACCESS_TOKEN_EXPIRE_MINUTES` default is `15` (not `30`)
- `RATE_LIMITER_FAIL_CLOSED` default is `true` (not `false`)
- Note that test env sets `RECREATE_TEST_DB=true`

### P2-20: Add Warning to Override File + Bind DB Port to localhost (INF-006)

**Severity:** LOW | **Effort:** Trivial | **Type:** BEST-PRACTICE

**File:** `docker/docker-compose.override.yml`

- Add warning comment about not using in production
- Change db port from `"5432:5432"` → `"127.0.0.1:5432:5432"`

### P2-21: Fix PostgreSQL Healthcheck (INF-007)

**Severity:** LOW | **Effort:** Trivial | **Type:** RUNTIME-ERROR

**Files:** `docker/docker-compose.yml`, `docker/docker-compose.test.yml`

Add `-d bidb` to healthcheck and `start_period: 10s`.

---

## P3 — Low Priority (Minor Improvements)

### P3-1: Remove `generateShortId()` Dead Function (FE-002)

**Severity:** LOW | **Effort:** Trivial

**File:** `frontend/src/shared/utils/shortUuid.ts:25`

Remove unused function or add comment explaining future use.

### P3-2: Remove Disabled "Access" Button (FE-005)

**Severity:** LOW | **Effort:** Trivial

**File:** `frontend/src/features/admin/ui/DashboardManagement.tsx:187-189`

Remove the permanently disabled "Access (coming soon)" button.

### P3-3: Standardize `useAuth` Import Paths (FE-006)

**Severity:** LOW | **Effort:** Trivial

**File:** `frontend/src/features/auth/ui/RegisterForm.tsx:4`

Change `from '../'` → `from '../model/useAuth'`.

### P3-4: Fix `ErrorPage` Unnecessary `useAuth()` Call (FE-007)

**Severity:** MEDIUM | **Effort:** Small

**File:** `frontend/src/shared/components/ErrorPage.tsx:12`

Replace `useAuth()` with synchronous token check.

### P3-5: Guard `onUploadComplete` Double-Invocation (FE-009)

**Severity:** MEDIUM | **Effort:** Small

**File:** `frontend/src/features/upload/ui/UploadModal.tsx:74-78`

Add `hasCompletedRef` guard to ensure callback fires exactly once.

### P3-6: Preserve Native Dim Types in Aggregation (DP-05)

**Severity:** MEDIUM | **Effort:** Small

**File:** `src/mkobi/services/aggregation_service.py:83`

Replace `str(row[col])` with `_coerce_dim_value()` helper that preserves int/float/bool.

### P3-7: Remove `round(4)` from Storage Calculations (DP-06)

**Severity:** LOW | **Effort:** Trivial

**File:** `src/mkobi/data/processing/aggregate_transforms.py:205,248,257`

Remove `.round(4)` from YoY and share calculations. Round at presentation layer instead.

### P3-8: Re-raise in `_update_processing_log_status` Test Mode (DP-04)

**Severity:** LOW | **Effort:** Trivial

**File:** `src/mkobi/workers/data_worker.py:226-228`

Change silent swallow to `raise` after logging.

### P3-9: Add `created_by` to `DashboardRead` (INT-018)

**Severity:** LOW | **Effort:** Small

**File:** `src/mkobi/models/dashboard.py`

Add `created_by: UUID | None` to `DashboardRead` and populate in service layer.

### P3-10: Document `DashboardRead.permission` Injection Pattern (INT-002)

**Severity:** MEDIUM | **Effort:** Trivial

**File:** `src/mkobi/models/dashboard.py`

Add docstring explaining `permission` is service-layer injected, not a DB column.

### P3-11: Add `SuccessResponse` Type to Frontend (INT-006)

**Severity:** LOW | **Effort:** Trivial

**File:** `frontend/src/shared/types/api.types.ts`

Add `SuccessResponse` interface if not present.

### P3-12: Normalize Null/Undefined at API Boundary (INT-013)

**Severity:** LOW | **Effort:** Small

**File:** `frontend/src/shared/utils/` (new file)

Create `normalizeNullable` utility for API response mapping.

### P3-13: Add Coverage File Path for Docker (TST-007)

**Severity:** MEDIUM | **Effort:** Trivial

Set `COVERAGE_FILE=/tmp/.coverage` in test container environment.

### P3-14: Fix Migration Downgrade Comment (DB-003)

**Severity:** LOW | **Effort:** Trivial

**File:** `alembic/versions/f47ac18b5b9e_...py`

Add comment explaining the redundant index was created outside migration chain.

### P3-15: Add Rollback to Service Methods (DB-004)

**Severity:** MEDIUM | **Effort:** Small

**Files:** `auth_service.py`, `graph_service.py`, `user_service.py`

Wrap `db.commit()` in try/except with `db.rollback()` in service methods that manage their own transactions.

### P3-16: Use Enum in Starter Cleanup (DB-005)

**Severity:** LOW | **Effort:** Trivial

**File:** `src/mkobi/db/starter.py:380-382`

Replace hardcoded `'failed'` with `ProcessingStatus.FAILED.value`.

### P3-17: Add Timing Attack Mitigation to Login (SEC-01)

**Severity:** MEDIUM | **Effort:** Small

**File:** `src/mkobi/services/auth_service.py:201-206`

Add dummy `bcrypt.checkpw` call in "user not found" path to prevent timing-based enumeration.

### P3-18: Unify Registration Error Messages (SEC-02)

**Severity:** MEDIUM | **Effort:** Small

**File:** `src/mkobi/services/auth_service.py:416-438`

Return generic message for all registration conflict cases to prevent user enumeration.

### P3-19: Make `cookie_secure` Environment-Aware (SEC-04)

**Severity:** LOW | **Effort:** Trivial

**File:** `src/mkobi/config.py:227`

Add validator that sets `cookie_secure=False` in development.

---

## Already Fixed (No Action Needed)

| Finding | Description | Status |
|---------|-------------|--------|
| DP-02 | APPEND mode filter values | Already fixed — both test and production paths clear unconditionally |
| DP-08 | Error path status rollback | Already fixed — production path uses independent session |
| INT-001 | `metric_agg` persistence | Rejected — field is persisted in JSONB `settings` column |
| INT-003 | `AdminUser.force_password_change` | Rejected — field exists in frontend type |
| INT-005 | `ProcessingLogRead.dashboard_name` | Rejected — service layer injects correctly |
| FE-001 | `PlaceholderPage` dead code | Rejected — documented architectural pattern per SPEC.md |

---

## Bug Reports — Resolution

### 02-missing-websocket-implementation.md
**Status:** Tasks TASK_054 and TASK_057 reference non-existent WebSocket functionality.
**Resolution:** Close both tasks. The application correctly uses HTTP polling via TanStack Query (`refetchInterval: 2000`). WebSocket is not in the spec. If real-time push is needed in the future, it should be a new feature request, not a test task for unimplemented functionality.

### 03-task-057-upload-progress-websocket-mismatch.md
**Status:** Same root cause as above.
**Resolution:** Close TASK_057. No WebSocket implementation exists or is planned.

---

## Implementation Order Summary

| Phase | Items | Estimated Effort |
|-------|-------|-----------------|
| **P0** | INT-011 (filters fix) | 5 min |
| **P1** | 8 items (Docker, Nginx, tests, security) | ~2 hours |
| **P2** | 14 items (code quality, types, docs) | ~4 hours |
| **P3** | 19 items (minor improvements) | ~4 hours |
| **Close** | 2 bug reports + 6 rejected findings | 10 min |

**Total estimated effort:** ~10 hours

---

## Validation Checklist

After implementing all fixes, verify:

- [ ] `docker compose -f docker/docker-compose.yml build` succeeds (frontend builds)
- [ ] `docker compose -f docker/docker-compose.test.yml exec test-app pytest tests/ -v` passes
- [ ] `uv run ruff check src/` passes
- [ ] `uv run mypy src/` passes (0 errors)
- [ ] `cd frontend && npm run build` passes
- [ ] `cd frontend && npm run lint` passes
- [ ] `cd frontend && npm run test` passes
- [ ] Nginx healthcheck shows `healthy` in `docker ps`
- [ ] Filter functionality works end-to-end (upload CSV → view dashboard → apply filter)
