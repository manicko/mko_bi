# Problem 01: test_media_dash Dashboard Not Automatically Created in Dev Database

**Date:** 2026-06-04
**Severity:** High — blocks Phase 02 verification end-to-end
**Scope:** Backend startup / database seeding

---

## Summary

The `test_media_dash` dashboard does **not** get automatically created in the dev database when the application starts. The seed script (`data/seed_test_media_dash.py`) exists and is correct, but it is **never invoked** — neither at application startup, nor by Docker Compose, nor by any migration. It must be run manually, which means a fresh dev environment has no test dashboard until someone remembers to run `python data/seed_test_media_dash.py`.

---

## Root Cause Analysis

### 1. Seed script exists but is not wired into any startup flow

**File:** `data/seed_test_media_dash.py` (lines 19–185)

The script is a standalone async module with `if __name__ == "__main__": asyncio.run(main())`. It is designed to be run manually. There is **zero** automatic invocation:

- **Not called from `app.py` lifespan** — The `lifespan()` function (lines 77–134) calls `starter.startup()` which runs migrations, ensures admin user, cleans temp files, and cleans old logs. It does **not** call any dashboard seeding.
- **Not called from `DatabaseStarter.startup()`** — The `startup()` method (lines 131–178 of `db/starter.py`) handles: DB connection check, migrations, `ensure_admin_user()`, temp file cleanup, old log cleanup, and optional test DB recreation. No dashboard seeding.
- **Not called from Docker Compose** — Neither `docker-compose.yml` nor `docker-compose.override.yml` has any step that runs the seed script. The `migrate` service only runs `alembic upgrade head`. The `app` service only runs `uvicorn`.
- **Not called from any Alembic migration** — No migration inserts dashboard seed data.
- **Not called from `main.py`** — The entry point (lines 50–55) only checks dependencies and calls `create_app()`.


### 2. No `ensure_test_dashboard()` pattern exists

The codebase has an `ensure_admin_user()` pattern in `DatabaseStarter.startup()` that atomically creates the admin user if missing. An equivalent `ensure_test_dashboard()` or `seed_test_data()` method **does not exist** anywhere.

---

## What Needs to Be Done

### Auto-seed at startup (recommended for dev environment)

Add a `seed_test_media_dash()` call to the application startup flow, gated on the development environment:

1. Convert `C:\py_dev\mkobi\data\seed_test_media_dash.py` to **Create a new seeders structure** in `C:\py_dev\mkobi\src\mkobi\db` 


```text
db/
├── dev_seeders.py      # CLI wrapper
└── seeders/
    └── test_media_dash.py       # actual implementation
```
example
```python
# db/seeders/test_media_dash.py


async def ensure_test_media_dash() -> None: ...
```
example
```python
# db/dev_seeders.py
from db.seeders.test_media_dash import ensure_test_media_dash


async def run_dev_seeders():
    await ensure_test_media_dash()
    # await ensure_demo_layouts()
    # await ensure_demo_reports()
```



2. **Wire it into `DatabaseStarter.startup()`** in `src/mkobi/db/starter.py`отдельный механизм сидов:

```python
# db/starter.py
await run_dev_seeders()

if self._config.env == EnvironmentEnum.DEVELOPMENT:
    await run_dev_seeders()
  ```  
    

3. **Ensure `get_session()` works at that point** — The seed script uses `get_session()` from `mkobi.db.session`, which requires the engine to already be created. Since `DatabaseStarter.startup()` already creates the engine and runs migrations, this is fine if called after `starter.startup()`.

---

## Additional Issues Found During Investigation

### Issue: Seed script uses `get_session()` which depends on engine being initialized

**File:** `data/seed_test_media_dash.py` (line 15)

The script imports `get_session` from `mkobi.db.session`. This requires the async engine to be created first. If called from `DatabaseStarter.startup()` (which already creates `self._main_engine`), the session factory should already be initialized. However, the current `get_session()` implementation uses its own engine — verify that the engine is shared or that `get_session()` picks up the already-created engine.

**Action:** Verify `mkobi/db/session.py` engine initialization is compatible with being called after `DatabaseStarter.startup()`.

### Issue: Seed script deletes filters incorrectly

**File:** `data/seed_test_media_dash.py` (lines 43–44)

```python
for filter_obj in list(existing_dashboard.filters):
    await db.delete(filter_obj)
```

This deletes Filter records that may be referenced by other dashboards. The `Filter` model is a shared entity — multiple dashboards can reference the same filter via the `dashboard_filters` join table. Deleting the Filter record itself (not just the binding) could break other dashboards.

**Action:** On re-seed, only delete the `dashboard_filters` bindings, not the Filter records. Or check if the filter is used elsewhere before deleting.

### Issue: TASK_009 status is "pending"

**File:** `.ai/plans/TASK_009_seed_test_media_dash.yaml` (line 20)

```yaml
status: pending
```

The seed script file exists and appears complete, but the task is still marked as `pending`. This suggests the implementation was done but never verified end-to-end (TASK_010 is also `pending`).

---

## Recommended Fix Priority

1. **Add auto-seed to startup flow** (Option A) — makes dev environment work out of the box
2. **Fix the filter deletion bug** in the seed script — prevents accidental data loss
3. **Update TASK_009 status** to reflect actual implementation state
4. **Run TASK_010 verification** to confirm the full pipeline works

---

## Files Involved

| File | Role |
|------|------|
| `data/seed_test_media_dash.py` | Seed script (exists, correct, not auto-invoked) |
| `src/mkobi/app.py` | FastAPI app factory with lifespan — no seed call |
| `src/mkobi/db/starter.py` | DatabaseStarter.startup() — no seed call |
| `src/mkobi/main.py` | Entry point — no seed call |
| `docker/docker-compose.yml` | Production compose — no seed service |
| `docker/docker-compose.override.yml` | Dev compose — no seed service |
| `.ai/plans/TASK_009_seed_test_media_dash.yaml` | Task spec — says "run manually" |
| `.ai/plans/TASK_010_verify_phase_02.yaml` | Verification — lists seed as manual step |
