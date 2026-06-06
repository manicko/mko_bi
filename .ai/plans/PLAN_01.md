# PLAN_01: Remove CREATEDB Privilege from mkobi_app Role (DC-002)

**Created:** 2026-06-06
**Updated:** 2026-06-06 (after empirical verification)
**Source audit finding:** DC-002 (HIGH severity, SPEC-DEVIATION)
**Confidence:** HIGH (empirically verified)

## Summary

Remove `ALTER ROLE mkobi_app CREATEDB` from the database initialization script and make all associated code changes to ensure no functionality breaks. The `recreate_test_database()` function already uses `postgres` superuser credentials (`DATABASE__ADMIN_USER` / `DATABASE__ADMIN_PASSWORD`) for CREATE/DROP DATABASE operations, making CREATEDB on `mkobi_app` redundant and a security violation of the documented least-privilege model.

**This recommendation was previously rolled back multiple times because "the database was not created." Empirical investigation has identified the root cause: the fallback logic in `recreate_test_database()` silently switches to mkobi_app credentials when admin credentials are missing, and without CREATEDB the operation fails. The fix is NOT to keep CREATEDB — it is to eliminate the dangerous fallback AND ensure admin credentials are always configured.**

---

## Empirical Verification Results

All tests were run on the live system with CREATEDB revoked from mkobi_app:

### Test 1: recreate_test_database() with NOCREATEDB + admin credentials provided

```
Environment: docker-compose.test.yml
mkobi_app role: NO "Create DB" attribute
DATABASE__ADMIN_PASSWORD: test_password (provided)
Result: SUCCESS — bidb_test created, migrations applied
```

### Test 2: recreate_test_database() with NOCREATEDB + admin credentials MISSING (empty)

```
Environment: docker-compose.yml (--env-file .env)
mkobi_app role: NO "Create DB" attribute
DATABASE__ADMIN_PASSWORD: '' (empty string → admin_url = None)
Fallback activates: admin_url or test_url → uses mkobi_app
Result: FAILURE — InsufficientPrivilegeError: permission denied to create database
```

**This is the exact failure that caused previous rollbacks.** The root cause is NOT the removal of CREATEDB — it is the silent fallback from admin credentials to application credentials when `DATABASE__ADMIN_PASSWORD` is empty or unset.

### Test 3: Full test suite with NOCREATEDB (fresh volume, init script without CREATEDB)

```
docker compose -f docker/docker-compose.test.yml up -d --build  (with modified init script)
mkobi_app role: NO "Create DB" attribute
bidb_test database: Created by postgres superuser
Tests: 736 passed, 4 failed (ALL pre-existing failures unrelated to CREATEDB)
Result: SUCCESS
```

### Conclusion

| Scenario | Admin credentials | CREATEDB on mkobi_app | Result |
|----------|-------------------|----------------------|--------|
| All Docker compose envs | Provided | NO | **WORKS** |
| Local dev / misconfig | Missing/empty | YES | Works (CURRENT) |
| Local dev / misconfig | Missing/empty | NO | **FAILS** — this is why rollbacks happened |

The fix: **Eliminate the fallback path so missing admin credentials fail with a clear error message instead of a confusing permission denial.**

---

## Root Cause of Previous Rollbacks

The fallback on line 206 of `starter.py`:

```python
base_url = admin_url or test_url  # ← DANGEROUS
```

When `DATABASE__ADMIN_PASSWORD` is empty/unset, `test_admin_database_url` returns `None`, and the code silently falls back to `test_url` (mkobi_app). Without CREATEDB, this fails with `InsufficientPrivilegeError`.

**The previous rollbacks treated the symptom (add CREATEDB back) instead of the cause (fix the fallback + ensure admin credentials are always configured).**

---

## Impact Analysis

### What uses CREATEDB today

| Component | Uses CREATEDB? | Admin credentials provided? |
|-----------|---------------|-----------------------------|
| `recreate_test_database()` in starter.py | Only via fallback (`admin_url or test_url`) | YES — all Docker Compose environments set `DATABASE__ADMIN_USER`/`DATABASE__ADMIN_PASSWORD` |
| `docker-compose.yml` (production) | N/A | YES — `DATABASE__ADMIN_USER: postgres`, `DATABASE__ADMIN_PASSWORD: ${DATABASE__PASSWORD}` |
| `docker-compose.override.yml` (dev) | N/A | YES — `DATABASE__ADMIN_PASSWORD: ${DATABASE__ADMIN_PASSWORD:?...}` (required, will fail if missing) |
| `docker-compose.test.yml` (test) | N/A | YES — `DATABASE__ADMIN_USER: postgres`, `DATABASE__ADMIN_PASSWORD: ${DATABASE__PASSWORD:-test_password}` |
| Local dev without Docker | Potentially via fallback | Depends on `.env` — `DATABASE__ADMIN_PASSWORD` is in `.env.example` but NOT enforced |

### What will break if CREATEDB is removed (without fixing fallback)

1. **Fallback path in `recreate_test_database()`** — If `test_admin_database_url` is `None`, code falls back to `test_url` (mkobi_app user). Without CREATEDB, CREATE DATABASE fails with `permission denied to create database`. **This is what caused previous rollbacks.**
2. **Existing containers** — `postgres_data` volume preserves the role with CREATEDB. Removing from init script only affects NEW initializations.
3. **Misleading comments** — Line 204 in `starter.py` says "requires CREATEDB privilege" but actually the admin URL uses superuser, not CREATEDB.

### What will NOT break

- All Docker Compose environments — admin credentials are always provided
- Migration service — uses `postgres` superuser directly
- Normal application runtime — only uses SELECT/INSERT/UPDATE/DELETE, never CREATE DATABASE
- Test fixtures — `conftest.py` passes `test_admin_database_url` explicitly

---

## Implementation Steps (ORDER IS CRITICAL)

### Step 1: Fix fallback logic in `recreate_test_database()` — DO THIS FIRST

**File:** `src/mkobi/db/starter.py`

**Problem:** Line 206 has a dangerous fallback: `base_url = admin_url or test_url`. If `admin_url` is None, it falls back to `test_url` which uses `mkobi_app` — a role that should NEVER have CREATEDB. This fallback silently masks a configuration error and is the ROOT CAUSE of previous rollbacks.

**Change:** Replace the fallback with an explicit check that raises a clear error:

```python
# BEFORE (lines 188-206):
test_url = self._config.test_database_url or get_config().test_database_url
admin_url = self._config.test_admin_database_url or get_config().test_admin_database_url
if not test_url:
    logger.warning("Test database URL not configured, skipping")
    return
# ...
base_url = admin_url or test_url

# AFTER:
test_url = self._config.test_database_url or get_config().test_database_url
admin_url = self._config.test_admin_database_url or get_config().test_admin_database_url
if not test_url:
    logger.warning("Test database URL not configured, skipping")
    return
if not admin_url:
    raise ValueError(
        "Admin database URL is required for test database recreation. "
        "Set DATABASE__ADMIN_USER and DATABASE__ADMIN_PASSWORD environment variables."
    )
# ...
base_url = admin_url
```

**Also fix the misleading comment on line 204:**

```python
# BEFORE:
# Use admin URL for database creation (requires CREATEDB privilege)
# Fall back to test_url if admin_url not configured (for backwards compatibility)

# AFTER:
# Use admin URL for database creation (requires superuser privileges)
```

**Rationale:**
- This is the ROOT CAUSE fix. Without this step, removing CREATEDB will break any environment where admin credentials are not provided.
- The "backwards compatibility" fallback was actually a compatibility with the security violation (CREATEDB on mkobi_app). Now that we are fixing the violation, the fallback must go.
- The `ValueError` message tells the operator exactly what to fix, instead of a cryptic `InsufficientPrivilegeError`.

**Verification:** Confirm `recreate_test_database()` raises `ValueError` with a clear message when `admin_url` is None, instead of falling back and failing with a confusing permission error.

---

### Step 2: Ensure `DATABASE__ADMIN_PASSWORD` is always required in Docker Compose

**File:** `docker/docker-compose.override.yml`

**Problem:** The dev override uses `${DATABASE__ADMIN_PASSWORD:?DATABASE__ADMIN_PASSWORD must be set}` for the app service, but the variable name `DATABASE__ADMIN_PASSWORD` maps to the `database.admin_password` setting. Verify that this actually works by checking the live environment (already verified — it does work: `DATABASE__ADMIN_PASSWORD=postgres`).

**No changes needed** — all three compose files already enforce admin credentials:
- `docker-compose.yml`: `DATABASE__ADMIN_PASSWORD: ${DATABASE__PASSWORD:?...}` (shares postgres password)
- `docker-compose.override.yml`: `DATABASE__ADMIN_PASSWORD: ${DATABASE__ADMIN_PASSWORD:?...}` (separate admin password required)
- `docker-compose.test.yml`: `DATABASE__ADMIN_PASSWORD: ${DATABASE__PASSWORD:-test_password}` (with default)

**Verification:** Run `docker compose config` for each compose file and confirm `DATABASE__ADMIN_PASSWORD` is always set.

---

### Step 3: Remove CREATEDB grant from init script

**File:** `docker/init-scripts/01-create-app-role.sh`

**Change:** Replace lines 32-33:

```bash
# BEFORE (lines 32-33):
-- Grant CREATEDB privilege for test database recreation
ALTER ROLE mkobi_app CREATEDB;

# AFTER:
-- CREATEDB privilege NOT granted — admin credentials (postgres superuser)
-- are used for CREATE/DROP DATABASE operations in recreate_test_database()
```

**Verification:** Examine the resulting script. Confirm it only grants: LOGIN, CONNECT, USAGE on schema, SELECT/INSERT/UPDATE/DELETE on tables, USAGE on sequences, and default privileges.

---

### Step 4: Apply dollar-quoting fix for password (DC-004 co-fix)

**File:** `docker/init-scripts/01-create-app-role.sh`

**Change:** Line 14 — apply the DC-004 audit fix simultaneously since the same file is being modified:

```sql
-- BEFORE:
CREATE ROLE mkobi_app WITH LOGIN PASSWORD '${MKOBI_APP_PASSWORD}';

-- AFTER:
CREATE ROLE mkobi_app WITH LOGIN PASSWORD $$${MKOBI_APP_PASSWORD}$$;
```

**Rationale:** Since we are already modifying this file, apply the SQL injection fix (DC-004) to prevent single-quote breaking the SQL literal. This is a related security hardening in the same file.

**Verification:** Test with a password containing special characters (single quote, backslash) to ensure the script doesn't break.

---

### Step 5: Add startup role-privilege verification (defense-in-depth)

**File:** `src/mkobi/db/starter.py`

**Problem:** Existing containers where `mkobi_app` already has CREATEDB (from `postgres_data` volume) will retain it even after the init script is changed. Init scripts in `/docker-entrypoint-initdb.d/` only run on FIRST database initialization.

**Solution:** Add a verification method in `DatabaseStarter` that checks if mkobi_app has excessive privileges and logs a warning:

```python
async def _verify_role_privileges(self) -> None:
    """Verify mkobi_app does not have excessive privileges (defense-in-depth)."""
    assert self._main_engine is not None
    try:
        async with self._main_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT rolcreatedb FROM pg_roles WHERE rolname = 'mkobi_app'")
            )
            row = result.fetchone()
            if row and row[0]:
                logger.warning(
                    "mkobi_app role has CREATEDB privilege — this violates "
                    "least-privilege principle. Run: ALTER ROLE mkobi_app NOCREATEDB;"
                )
    except Exception as e:
        logger.debug("Could not verify role privileges: %s", e)
```

Call in `startup()` after connectivity check, before migrations:

```python
# In startup() method, after _check_db_connection():
await self._verify_role_privileges()
```

**Rationale:** This catches:
- Existing volumes where the role still has CREATEDB
- Someone manually granting CREATEDB
- A different init script granting it

**Verification:** Start with an existing volume where mkobi_app has CREATEDB. Confirm the warning is logged.

---

### Step 6: Revoke CREATEDB on existing containers (one-time manual step)

The `postgres_data` Docker volume persists across container restarts. Init scripts only run on first initialization. For existing containers, run:

```bash
# For development environment:
docker compose -f docker/docker-compose.yml --env-file .env exec db psql -U postgres -c "ALTER ROLE mkobi_app NOCREATEDB;"

# For test environment:
docker compose -f docker/docker-compose.test.yml exec test-db psql -U postgres -c "ALTER ROLE mkobi_app NOCREATEDB;"

# Verify revocation:
docker compose -f docker/docker-compose.yml --env-file .env exec db psql -U postgres -c "\du mkobi_app"
# Expected output: mkobi_app with NO "Create DB" in Attributes column
```

**For CI/CD pipelines:** Test env uses `docker compose down -v` which removes volumes, so fresh initialization will use the updated init script. No manual step needed.

---

### Step 7: Verify all three Docker environments work

**7a. Test environment (fresh start with new volumes):**

```bash
docker compose -f docker/docker-compose.test.yml down -v
docker compose -f docker/docker-compose.test.yml up -d --build

# Verify mkobi_app role has NO CREATEDB
docker compose -f docker/docker-compose.test.yml exec test-db psql -U postgres -c "\du mkobi_app"

# Verify bidb_test was created by postgres superuser
docker compose -f docker/docker-compose.test.yml exec test-db psql -U postgres -c "\l"

# Run full test suite
docker compose -f docker/docker-compose.test.yml exec test-app /app/.venv/bin/pytest tests/ -v
```

Expected: `\du mkobi_app` shows no "Create DB". `bidb_test` exists. All tests pass.

**7b. Development environment:**

```bash
# Revoke CREATEDB on existing volume (one-time)
docker compose -f docker/docker-compose.yml --env-file .env exec db psql -U postgres -c "ALTER ROLE mkobi_app NOCREATEDB;"

# Restart app service
docker compose -f docker/docker-compose.yml --env-file .env restart app

# Verify app starts correctly
docker compose -f docker/docker-compose.yml --env-file .env logs app --tail 20
```

Expected: App starts successfully. If `RECREATE_TEST_DB=true`, test database recreation uses admin credentials.

**7c. Production environment (dry-run):**

```bash
docker compose -f docker/docker-compose.yml --env-file docker/.env.production config
```

Expected: Config validates. App service has both `DATABASE__USER: mkobi_app` and `DATABASE__ADMIN_USER: postgres`.

---

### Step 8: Verify config.py comments are correct (no change needed)

**File:** `src/mkobi/config.py`

Lines 107-108 and 495-496 already correctly state that admin operations require CREATEDB privilege that the application user doesn't have. These comments describe the DESIRED state (which we are now implementing). No changes needed.

---

### Step 9: Verify deployment documentation is correct (no change needed)

**File:** `docs/10-deployment/deployment.md`

The "Database Role (Least-Privilege)" section already correctly documents mkobi_app as having only `CONNECT, SELECT, INSERT, UPDATE, DELETE` on tables and `USAGE` on sequences — no CREATEDB. This is already in sync with the desired state.

---

## Rollback Plan

If removing CREATEDB causes unexpected failures:

1. **Re-add CREATEDB on running containers (immediate):**
   ```bash
   docker compose -f docker/docker-compose.yml --env-file .env exec db psql -U postgres -c "ALTER ROLE mkobi_app CREATEDB;"
   ```

2. **Re-add fallback in starter.py:**
   ```python
   base_url = admin_url or test_url
   ```

3. **Re-add CREATEDB to init script (for new containers):**
   ```sql
   ALTER ROLE mkobi_app CREATEDB;
   ```

4. **Rebuild and restart:**
   ```bash
   docker compose -f docker/docker-compose.yml --env-file .env up -d --build
   ```

---

## Summary of All Changes

| Step | File | Change | Risk | Critical? |
|------|------|--------|------|-----------|
| 1 | `src/mkobi/db/starter.py` | Replace `admin_url or test_url` fallback with explicit `admin_url` check + fix comment | LOW | **YES — root cause fix** |
| 2 | `docker-compose.*.yml` | Verify admin credentials always provided (no change needed) | NONE | NO |
| 3 | `docker/init-scripts/01-create-app-role.sh` | Remove `ALTER ROLE mkobi_app CREATEDB;` and update comment | LOW | YES |
| 4 | `docker/init-scripts/01-create-app-role.sh` | Apply dollar-quoting for password (DC-004 co-fix) | LOW | NO |
| 5 | `src/mkobi/db/starter.py` | Add `_verify_role_privileges()` startup check | LOW | NO (defense-in-depth) |
| 6 | Existing containers | Manual `ALTER ROLE mkobi_app NOCREATEDB;` | MEDIUM | YES (one-time) |
| 7 | — | Verification across dev/test/prod environments | NONE | YES |
| 8 | `src/mkobi/config.py` | Verify comments correct (no change needed) | NONE | NO |
| 9 | `docs/` | Verify docs correct (no change needed) | NONE | NO |

---

## Why Previous Rollbacks Happened (And Why They Won't Happen Again)

| Factor | Before (rolled back) | After (this plan) |
|--------|---------------------|-------------------|
| Root cause | Treated as "need CREATEDB" | Identified as "fallback to mkobi_app when admin credentials missing" |
| Fallback `admin_url or test_url` | Present — silently switches to mkobi_app | Removed — raises clear ValueError |
| Error message | `InsufficientPrivilegeError: permission denied to create database` | `ValueError: Admin database URL is required for test database recreation. Set DATABASE__ADMIN_USER and DATABASE__ADMIN_PASSWORD environment variables.` |
| Diagnosis difficulty | Hard — looks like CREATEDB is needed | Easy — tells operator exactly what to configure |
| Actual fix needed | Configure admin credentials | Same, but now the error message says so |

---

## Additional Recommendations Beyond DC-002

### A. Make `DATABASE__ADMIN_PASSWORD` required at config validation time

After removing the fallback (Step 1), `recreate_test_database()` will raise ValueError if admin URL is None. But it would be even better to validate at application startup (in `create_app()` or `lifespan()`) that:
- If `ENV=test` or `RECREATE_TEST_DB=true`, then `DATABASE__ADMIN_USER` and `DATABASE__ADMIN_PASSWORD` must be set
- Fail early with a clear message, before the app even enters the lifespan context

### B. Document the non-Docker local dev workflow

If a developer runs `uvicorn` directly (without Docker) with `RECREATE_TEST_DB=true`, they need:
- `DATABASE__ADMIN_USER=postgres` in `.env`
- `DATABASE__ADMIN_PASSWORD=<their-local-postgres-password>` in `.env`

This should be documented in the run guide or docker guide.

### C. Consider adding `DATABASE__ADMIN_PASSWORD` to `.env.example` with a clearer comment

Currently `.env.example` has `DATABASE__ADMIN_PASSWORD=CHANGE_ME_GENERATE_STRONG_SECRET` but no explanation of what it's for. Add a comment explaining it's needed for test database recreation.
