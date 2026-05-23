# Task Validation Report — PLAN_03 + Docker Hardening + Validated Audit Findings

**Date:** 2026-05-23
**Scope:** All 26 tasks in `.ai/tasks/todo/` (TASK_001 through TASK_022, minus non-existent TASK_022 duplicate)
**Source Plan:** `.ai/plans/PLAN_03.md`
**Source Audit:** `.ai/audit/validated/audit_validated_findings_001.md`
**Validator:** validator agent

---

## Validation Summary

| Category | Count |
|----------|-------|
| Total tasks in todo | 26 |
| Approved | 21 |
| Rejected | 5 |
| Gate tasks (informational) | 4 |

---

## Approved Tasks

| Task ID | Title | Risk | Notes |
|---------|-------|------|-------|
| TASK_001_03_01_fix_dev_reload | Fix Dev Override CMD to Enable Hot Reload | Low | Confirmed: line 60 of override has no `--reload`. Semantic anchor is the command directive. Safe standalone change. |
| TASK_002_03_02_simplify_dev_env | Remove Duplicated Hardcoded Passwords from Dev Override | Medium | Confirmed: override repeats hardcoded fallback values. All secrets should come from `.env`. `.env.example` exists. Standalone. |
| TASK_003_03_03_add_frontend_dev_service | Add Frontend Dev Server Service to Docker Compose Override | Low | No frontend service exists in current override. Clean addition. Well-scoped. |
| TASK_004_03_04_add_vite_proxy | Configure Vite Dev Server to Proxy API Requests | Low | `vite.config.ts` has no server.proxy block. Single-file, single-purpose change. Depends on TASK_003 (correct). |
| TASK_005_03_05_remove_frontend_dist_mount | Remove frontend/dist Mount from App Service | Low | Current override line 59 mounts `./frontend/dist`. Clean removal. Depends on TASK_003 (correct). |
| TASK_006_03_06_fix_docker_guide | Align docker.md with Actual Dockerfile and Compose | Low | Confirmed: docker.md references non-existent `prod-base`/`prod-slim` stages, has wrong cross-links. Doc-only. |
| TASK_007_03_07_fix_deployment_doc | Update deployment.md | Low | Confirmed: deployment.md references `prod-slim`, has outdated Dockerfile targets table. Doc-only. |
| TASK_008_D01_fix_root_user_dev | Fix Root User in Dev Stage and Override | Medium | Confirmed: Dockerfile dev stage has no `USER app` directive (line 76 comment says "Run as root"). Override line 32 sets `user: root`. Both need fixing. Volume permission risk noted in rollout_notes. |
| TASK_009_D04_add_rq_worker | Add rq-worker Service to Docker Compose | Medium | Redis service exists in base compose but no rq-worker. Worker code at `src/mkobi/workers/data_worker.py` exists. Uses `profiles: [production]` — correct pattern. |
| TASK_010_D11_remove_exposed_ports | Remove DB and Redis Ports Exposed to Host | Low | Confirmed: base compose lines 25 and 109-110 expose ports 5432 and 6379. Dev override already exposes 5432. Safe removal from base. |
| TASK_011_D12_fix_test_compose_passwords | Remove Hardcoded Password Fallback from Test Compose | Low | Confirmed: test compose uses `${MKOBI_APP_PASSWORD:-1234}` and `${DATABASE__PASSWORD:-1234}`. Safe removal of fallbacks. |
| TASK_012_D13_make_mirror_configurable | Make Debian Mirror Configurable via ARG | Low | Confirmed: Dockerfile line 33 hardcodes `mirror.yandex.ru`. Clean ARG-based fix. |
| TASK_013_D10_add_nginx_api_comment | Add Comment Documenting Nginx /api Prefix | Low | Confirmed: nginx.conf line 18 has `location /api` with no explaining comment. Doc-only. |
| TASK_014_D16_remove_redundant_mounts | Remove Redundant Alembic Volume Mounts | Low | Confirmed: base compose mounts `./alembic` and `./alembic.ini` as read-only, but these are already copied in Dockerfile at build time (lines 69-70 prod, 124-125). |
| TASK_015_D14_document_env_tradeoff | Document .env Weak Credentials as Known Trade-off | Low | `.env.example` already exists with placeholder values (confirmed). `.gitignore` line 151 has `.env`. `.dockerignore` line 72 has `.env`. Task is to document the trade-off, not create new files. Scope needs clarification — see Execution Warning below. |
| TASK_016_D15_document_superuser_migration | Document Postgres Superuser for Migrations | Low | Doc-only comment addition to docker-compose.yml near migrate service. Safe. |
| TASK_018_VF001_fix_token_payload_key | Fix token payload key mismatch in refresh endpoint | Low | Confirmed bug: `auth.py:308` uses `"sub"` while `deps.py:429` reads `"user_id"`. Single-key rename fix. Blocking production bug. |
| TASK_019_VF002_use_set_secure_cookie_in_login | Use set_secure_cookie utility in login endpoint | Low | Confirmed: `auth.py:31-41` imports `delete_secure_cookie` but not `set_secure_cookie`. `set_secure_cookie()` exists at `security.py:381-404`. Pure refactoring. |
| TASK_020_VF003_remove_duplicate_login_cookie_test | Remove duplicate login cookie test in test_auth.py | Low | Confirmed: `test_auth.py:63-88` and `test_auth_api.py:35-60` test the same behavior. Remove from test_auth.py. |
| TASK_021_VF004_remove_redundant_removeToken | Remove redundant removeToken() in useAuth.logout | Low | Confirmed: `useAuth.ts:45` calls `removeToken()` then `logoutClient()` at line 46 which also calls `removeToken()` internally (`authApi.ts:30`). Idempotent, zero-risk. |
| TASK_022_VF005_make_cookie_secure_configurable | Make COOKIE_SECURE configurable via env var | Low | Confirmed: `security.py:47` hardcodes `COOKIE_SECURE: bool = True`. Needs to become config-driven. Low priority / optional. |

## Rejected Tasks

| Task ID | Title | Rejection Reason |
|---------|-------|-----------------|
| TASK_017_D17_fix_test_db_creation_dev | Fix Test Database Creation in Dev Environment | **REJECTED** — Stale semantic anchor / Already fixed in starter.py |

---

## Detailed Rejection Analysis

### TASK_017_D17 — Fix Test Database Creation in Dev Environment

**Rejection Reason:** The task's core fix (replacing admin URL derivation in `db/starter.py`) is **already implemented** in the current codebase.

**Evidence:**
- `src/mkobi/db/starter.py:155-189` — The `recreate_test_database()` method already uses `self._config.test_admin_database_url or get_config().test_admin_database_url` at line 158.
- `src/mkobi/config.py:417-435` — The `TEST_ADMIN_DATABASE_URL` property already exists and constructs the admin URL using `self.database.admin_user` and `self.database.admin_password`.
- `src/mkobi/config.py:86-87` — The `DatabaseSettings` class already has `admin_user: str = "postgres"` and `admin_password: str | None = None`.
- `docker-compose.override.yml:41-42` — The dev override already provides `DATABASE__ADMIN_USER: postgres` and `DATABASE__ADMIN_PASSWORD: ${DATABASE__PASSWORD:-1234}`.

The task proposes replacing code at `starter.py:53-61` (old `base_url` derivation from `test_url`) with code using `TEST_ADMIN_DATABASE_URL`. But the current `starter.py` at lines 155-189 already uses `test_admin_database_url` from config. The old code the task references (`base_url = test_url.rsplit("/", 1)[0] + "/postgres"`) does not exist in the current file.

**Secondary Issue:** The task's `docker-compose.override.yml` change (adding `DATABASE__ADMIN_USER` and `DATABASE__ADMIN_PASSWORD`) is also already present at override lines 41-42.

**Verdict:** The entire task is stale. Both the code fix and the override changes are already implemented. The task should be rejected and can be considered DONE.

**Required Action:** Rename to `_REJECTED.yaml`, mark as stale.

---

## Dependency Validation

### Dependency Graph Integrity: PASS (with corrections)

The `order.yaml` dependency graph is **valid** — no circular dependencies detected. Topological ordering is correct.

### Dependency Corrections Needed

1. **TASK_017_D17** is listed in `order.yaml` with `depends_on: []` and is a dependency of `TASK_GATE_03_hardening_complete`. Since TASK_017 is rejected (already implemented), the gate's dependency on it is satisfied by default — the gate can still verify the functionality.

2. **TASK_006 and TASK_007** (Wave 3 docs) depend on `TASK_GATE_01_wave1_complete` and `TASK_GATE_02_wave2_complete` in `order.yaml`. However, the task YAML files themselves list `depends_on` with individual task IDs (TASK_001 through TASK_005). This is **inconsistent** between the task files and the order.yaml. The order.yaml is the authoritative source — it correctly gates Wave 3 behind Gate 1 and Gate 2. The task YAML `depends_on` fields are overly broad but not harmful since the order.yaml controls execution.

### Wave Execution Order

```
Phase 0 (VF-001 to VF-005): All 5 independent, parallel
Phase 1 (Wave 1): TASK_001, TASK_002 — independent, parallel
Phase 2 (Wave 2): TASK_003 → TASK_004 + TASK_005 (parallel after TASK_003)
Phase 3 (Hardening Wave 1): TASK_008, TASK_009, TASK_010, TASK_011 — independent, parallel
  Note: TASK_017 is rejected (already done)
Gate 1: After Wave 1 complete
Gate 2: After Wave 2 complete
Gate 3: After Hardening Wave 1 complete
Phase 4 (Wave 3 docs): TASK_006, TASK_007 — parallel, after Gates 1+2
Phase 5 (Hardening Wave 2): TASK_012-TASK_016 — all independent, parallel
Gate 4: Final, after all above
```

---

## Semantic Target Stability Analysis

### Stable Anchors (APPROVED tasks)

| Task | Anchor Type | Anchor Target | Stability |
|------|------------|---------------|-----------|
| TASK_001 | directive value | `command: ["uvicorn", ...]` in override | Stable — exact string match |
| TASK_002 | service blocks | migrate, app, db in override | Stable — named services |
| TASK_003 | new service | frontend (new) | Stable — new addition |
| TASK_004 | function_call | `defineConfig({` in vite.config.ts | Stable — single call site |
| TASK_005 | volume_mount | `./frontend/dist:/app/frontend/dist` | Stable — exact string |
| TASK_006 | heading/section | docker.md sections | Stable — doc headings |
| TASK_007 | heading/section | deployment.md sections | Stable — doc headings |
| TASK_008 | stage/comment | Dockerfile dev stage, "Run as root" comment | Stable — unique comment |
| TASK_009 | new service | rq-worker (new) | Stable — new addition |
| TASK_010 | service blocks | db, redis in base compose | Stable — named services |
| TASK_011 | service blocks | app, db in test compose | Stable — named services |
| TASK_012 | directive value | `mirror.yandex.ru` in Dockerfile | Stable — exact string |
| TASK_013 | block | `location /api {` in nginx.conf | Stable — unique block |
| TASK_014 | volume_mount | `./alembic`, `./alembic.ini` in base compose | Stable — exact strings |
| TASK_015 | new file | .env.example | Stable — file already exists |
| TASK_016 | service block | migrate in base compose | Stable — named service |
| TASK_018 | dict_key | `"sub"` in `auth.py:308` | Stable — exact string, unique in context |
| TASK_019 | function_call | `response.set_cookie` in `auth.py:99` | Stable — single call site |
| TASK_020 | method | `test_login_sets_refresh_token_cookie` in test_auth.py | Stable — unique method name |
| TASK_021 | function_call | `removeToken` in useAuth.ts:45 | Stable — unique call in logout |
| TASK_022 | constant | `COOKIE_SECURE: bool = True` in security.py:47 | Stable — unique constant |

All semantic anchors are **stable** — they use symbol-level targeting (function names, service names, exact string values, unique constants). No line-based or fragile pattern-based anchors detected.

---

## Scope Isolation Analysis

All approved tasks have **single, coherent responsibilities**:

- Docker override changes: Each task modifies 1-2 specific directives/services
- Dockerfile changes: Each task targets a specific stage or directive
- Documentation changes: Each task updates a single doc file
- Code fixes (VF tasks): Each targets a single function/method
- New services: Each adds one well-defined service

No broad rewrites, mixed responsibilities, or speculative changes detected.

---

## Architectural Safety Analysis

### Architecture Boundaries: PASS

- Docker/compose changes are confined to infrastructure layer — no application code affected
- VF-001 through VF-005 are bug fixes and code quality improvements within existing architecture
- No cross-layer leakage introduced
- Production `docker-compose.yml` is only modified by hardening tasks (security improvements)
- Production `Dockerfile` is only modified by TASK_008 (security: non-root user) and TASK_012 (build portability)

### Backward Compatibility: PASS

- All Docker changes are additive or security-hardening — no breaking API changes
- VF-001 fix corrects a bug — the "old" behavior was broken
- VF-002 is a pure refactoring with identical behavior
- VF-003 removes a duplicate test — no production impact
- VF-004 removes redundant code — idempotent operation
- VF-005 adds configurability — defaults to current behavior (True)

### Dependency Direction: PASS

- No reverse dependencies introduced
- Wave ordering respects logical dependencies (Waves 1-2 before Wave 3 docs)
- Gate tasks correctly enforce wave completion before proceeding

---

## Execution Readiness Warnings

### Warning 1: TASK_015 Scope Ambiguity
**Task:** TASK_015_D14_document_env_tradeoff
**Issue:** The task proposes creating `.env.example` with placeholder values, but `.env.example` already exists at repo root with proper placeholder values. The task's `files` section targets `.env.example (new)` but the file already exists. The task should be reinterpreted as "document the trade-off in a comment or README section" rather than creating a new file. The acceptance criteria mention verifying `.gitignore` and `.dockerignore` entries — these already exist.
**Recommendation:** Clarify scope — either update `.env.example` with better documentation of the trade-off, or add a note to the README/docker.md about the dev credential trade-off. The task is still actionable but needs scope refinement.

### Warning 2: TASK_008 Volume Permissions
**Task:** TASK_008_D01_fix_root_user_dev
**Issue:** The task correctly identifies that removing `user: root` and adding `USER app` may cause volume permission issues (egg-info writes). The rollout_notes mention this risk. The task's acceptance criteria include a health check for writable volumes.
**Recommendation:** Ensure the implementation includes a strategy for handling volume permissions — either build-time `chown` or an entrypoint script. The task is approved but this risk must be addressed during implementation.

### Warning 3: TASK_009 Production Profile
**Task:** TASK_009_D04_add_rq_worker
**Issue:** The rq-worker service uses `profiles: [production]`, meaning it won't start with the default `docker compose up -d`. This is correct for production but means the gate verification (`TASK_GATE_03`) must explicitly use `--profile production` to verify the worker.
**Recommendation:** The gate task already includes this check. No action needed.

### Warning 4: TASK_022 Implementation Approach
**Task:** TASK_022_VF005_make_cookie_secure_configurable
**Issue:** The task's `code_hint` shows replacing a module-level constant with a config-driven value. This requires care — if `COOKIE_SECURE` is imported as a module-level constant by other modules, changing it to a runtime config read could have import-time side effects. The implementation should add a `cookie_secure` field to `AppSettings` (or `JWTSettings`) and access it via `get_config().cookie_secure` at usage sites, rather than changing the module-level constant.
**Recommendation:** Approved with the note that the implementation must handle the transition from compile-time constant to runtime config carefully.

### Warning 5: TASK_006 and TASK_007 Cross-Link Verification
**Tasks:** TASK_006_03_06_fix_docker_guide, TASK_007_03_07_fix_deployment_doc
**Issue:** The tasks list specific cross-link path corrections. The validator confirmed:
- `docs/11-guides/docker.md:262-264` has wrong cross-links (`../04-run/run-guide.md`, `../05-ops/deployment.md`, `../05-ops/task-queue-migration.md`)
- `docs/10-deployment/deployment.md` references `prod-slim` at line 180
**Recommendation:** Approved. The cross-link corrections are clearly specified.

---

## Rollout Consistency Validation

### Rollout Order: SAFE

1. **Phase 0 (VF fixes)** can run first — independent, no Docker dependency
2. **Wave 1 (backend)** and **Wave 2 (frontend)** can run in parallel — independent
3. **Hardening Wave 1** can run in parallel with Waves 1-2 — targets different files
4. **Gates 1-3** verify each wave independently
5. **Wave 3 (docs)** runs after Gates 1-2 — correctly depends on both
6. **Hardening Wave 2** runs independently — low-risk, mostly doc/comment changes
7. **Gate 4** final verification — correctly depends on everything

### Rollback Feasibility: EASY

- Each wave modifies distinct files or distinct sections
- Docker changes are confined to compose files and Dockerfile
- Code fixes (VF) are single-line or single-method changes
- Doc changes are easily reversible
- No database migrations required

---

## Final Verdict

**APPROVED FOR EXECUTION** — 21 of 26 tasks approved. 1 task rejected (TASK_017 — already implemented). 4 gate tasks are informational checkpoints.

**Execution order:** Follow `order.yaml` topological sequence. Waves 1, 2, and Hardening Wave 1 can proceed in parallel. Wave 3 docs must wait for Gates 1+2. Hardening Wave 2 can proceed independently.

**Critical path:** VF-001 (token payload key fix) is blocking for production — should be executed first regardless of wave ordering.

---

## Files Referenced

- `C:\py_dev\mkobi\.ai\plans\PLAN_03.md` — Plan specification
- `C:\py_dev\mkobi\.ai\audit\validated\audit_validated_findings_001.md` — Validated audit findings
- `C:\py_dev\mkobi\.ai\tasks\todo\order.yaml` — Execution order
- `C:\py_dev\mkobi\docker-compose.yml` — Base Docker Compose
- `C:\py_dev\mkobi\docker-compose.override.yml` — Dev override
- `C:\py_dev\mkobi\docker-compose.test.yml` — Test compose
- `C:\py_dev\mkobi\Dockerfile` — Multi-stage Dockerfile
- `C:\py_dev\mkobi\nginx\nginx.conf` — Nginx config
- `C:\py_dev\mkobi\src\mkobi\api\routes\auth.py` — Auth routes (VF-001, VF-002)
- `C:\py_dev\mkobi\src\mkobi\core\security.py` — Security utilities (VF-002, VF-005)
- `C:\py_dev\mkobi\src\mkobi\config.py` — App config (VF-005, TASK_017)
- `C:\py_dev\mkobi\src\mkobi\db\starter.py` — DB starter (TASK_017)
- `C:\py_dev\mkobi\frontend\vite.config.ts` — Vite config (TASK_004)
- `C:\py_dev\mkobi\frontend\src\features\auth\model\useAuth.ts` — Auth hook (VF-004)
- `C:\py_dev\mkobi\frontend\src\features\auth\api\authApi.ts` — Auth API (VF-004)
- `C:\py_dev\mkobi\docs\11-guides\docker.md` — Docker guide (TASK_006)
- `C:\py_dev\mkobi\docs\10-deployment\deployment.md` — Deployment doc (TASK_007)
- `C:\py_dev\mkobi\.env.example` — Env example (TASK_015)
- `C:\py_dev\mkobi\.gitignore` — Git ignore (TASK_015)
- `C:\py_dev\mkobi\.dockerignore` — Docker ignore (TASK_015)
