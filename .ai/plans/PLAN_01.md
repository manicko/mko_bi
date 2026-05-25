# PLAN_01: Standalone Test Compose

**Phase:** 01 — Standalone Test Compose
**Created:** 2026-05-24
**Research:** RESEARCH_01.md (HIGH confidence)
**Decisions:** DECISION_01.md (LOCKED)

---

## Goal

Convert `docker-compose.test.yml` from an overlay/override file into a fully standalone, independent compose configuration. Dev and test environments must run in parallel with zero shared state — separate containers, volumes, and networks.

---

## Dependency DAG

```
TASK_025 (rewrite docker-compose.test.yml)
    │
    ├──► TASK_027 (verify parallel execution)
    │
    └──► TASK_028 (fix conftest.py setdefault)
              │
              └──► TASK_027 (verify parallel execution)

TASK_026 (clean docker-compose.yml)
    │
    └──► TASK_027 (verify parallel execution)
```

- **TASK_025** and **TASK_026** are independent (different target files) → Wave 1 (parallel)
- **TASK_028** depends on TASK_025 (needs compose to know which env vars are set) → Wave 2
- **TASK_027** depends on all three → Wave 3 (verification)

---

## Execution Waves

| Wave | Tasks | Description |
|------|-------|-------------|
| 1 | TASK_025, TASK_026 | Rewrite test compose + clean production compose (parallel-safe) |
| 2 | TASK_028 | Fix conftest.py setdefault for Docker Compose env var compatibility |
| 3 | TASK_027 | Verify both environments run in parallel |

---

## Files Modified

| File | Change | Task |
|------|--------|------|
| `docker-compose.test.yml` | Complete rewrite: standalone with test-db, test-redis, test-migrate, test-app | TASK_025 |
| `docker-compose.yml` | Remove test artifacts: RECREATE_TEST_DB, test-related comments | TASK_026 |
| `tests/conftest.py` | Replace direct os.environ assignment with setdefault for Docker Compose compatibility | TASK_028 |

---

## must_haves (backward-validated against phase goal)

1. `docker-compose.test.yml` is fully standalone — defines ALL services, volumes, networks from scratch
2. All test services prefixed with `test-`: test-db, test-redis, test-migrate, test-app
3. Port mapping: test-app=8001, test-db=5433, test-redis=6380
4. Separate Docker volume: `test_postgres_data`
5. Separate Docker network: `test_network`
6. `test-migrate` is a separate one-shot service (`restart: "no"`)
7. `docker-compose.yml` is clean — no RECREATE_TEST_DB, no test-related comments
8. Dev environment (`docker-compose.yml` + `docker-compose.override.yml`) runs unchanged
9. Both environments run in parallel: `docker compose up -d` AND `docker compose -f docker-compose.test.yml up -d`
10. Tests executable via: `docker compose -f docker-compose.test.yml exec test-app uv run pytest tests/ -v`
11. `tests/conftest.py` uses `os.environ.setdefault()` so Docker Compose environment variables take precedence inside containers

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Port conflicts between dev and test | Explicit fixed port mapping (8001/5433/6380) |
| Shared networks/volumes | Fully separate file + prefixed names |
| Init script not running on test-db | Use postgres superuser (simpler); init script not needed for test-db |
| Test-app healthcheck restart loop | Explicitly disable healthcheck in test-app |
| Migration race condition | `depends_on: test-db: condition: service_healthy` |
| conftest.py overriding Docker Compose env vars | Use `setdefault` so compose values win inside containers, localhost defaults work natively |
