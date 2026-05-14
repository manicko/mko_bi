# Task Validation Report — 001

**Generated:** 2026-05-14T16:10:01+05:00
**Validator:** Kilo (System Integrity Agent)
**Scope:** All 12 tasks in `.ai/tasks/todo/`

---

## Executive Summary

| Category | Count |
|---|---|
| Approved | 8 |
| Rejected | 4 |
| Total | 12 |

## Approved Tasks (8)

### TASK_001 — Fix file.size null check in upload endpoint
- File: src/mkobi/api/routes/upload.py
- Semantic Anchor: upload_file_endpoint (function) — VERIFIED at line 46
- Target Line 68: if file.size > config.max_file_size — VERIFIED
- Risk: Low. Isolated null-check addition.
- Tests: tests/test_upload_api.py

### TASK_002 — Fix grant access endpoint to use require_admin_role
- File: src/mkobi/api/routes/dashboards.py
- Semantic Anchor: grant_dashboard_access_endpoint (function) — VERIFIED at line 373
- Target Line 371: dependencies=[Depends(require_viewer_role)] — VERIFIED
- Note: require_admin_role already imported at line 20
- Risk: Low. Authorization tightening (intentional breaking change).
- Tests: tests/test_dashboards_api.py

### TASK_003 — Remove duplicate _graph_repo.update call
- File: src/mkobi/api/routes/graphs.py
- Semantic Anchor: update_graph_endpoint (function) — VERIFIED at line 191
- Target Lines 233-239: Two consecutive identical _graph_repo.update() calls — VERIFIED
- Risk: Low. Clear copy-paste bug removal.
- Tests: tests/test_graphs.py

### TASK_006 — Fix rate limiter to use cached instance
- File: src/mkobi/api/routes/auth.py
- Semantic Anchor: _handle_login (function) — VERIFIED at line 36
- Target Lines 43-44: AsyncRateLimiter instantiation — VERIFIED
- Risk: Low. Uses existing auth_service._rate_limiter.
- Tests: tests/test_auth.py

### TASK_007 — Add missing dashboard access check to data endpoint
- File: src/mkobi/api/routes/data.py
- Semantic Anchor: get_aggregated_data_endpoint (function) — VERIFIED at line 39
- Insert after: deps import block (line 18) and logger.info (line 65) — VERIFIED
- check_dashboard_access verified in core/permissions.py (line 206)
- Risk: Low. Security fix.
- Tests: tests/test_data.py

### TASK_009 — Replace module-level GraphRepository singleton with DI in dashboards.py
- File: src/mkobi/api/routes/dashboards.py
- Semantic Anchor: _graph_repo (variable) — VERIFIED at line 38
- get_graph_repository verified in deps.py (line 201)
- Risk: Low. DI pattern alignment.
- Tests: tests/test_dashboards_api.py, tests/test_graphs.py

### TASK_010 — Replace module-level GraphRepository singleton with DI in graphs.py
- File: src/mkobi/api/routes/graphs.py
- Semantic Anchor: _graph_repo (variable) — VERIFIED at line 33
- get_graph_repository verified in deps.py (line 201)
- CONDITION: Add depends_on [task_003] to order.yaml. Remove duplicate changes_2 entry.
- Risk: Low. DI pattern alignment.
- Tests: tests/test_graphs.py

### TASK_011 — Replace direct RegistrationRequestRepository with DI in admin.py
- File: src/mkobi/api/routes/admin.py
- Semantic Anchor: repo variable and get_registration_requests_admin_endpoint — VERIFIED
- 3 instantiation sites at lines 142, 170, 228 — VERIFIED
- get_registration_request_repository verified in deps.py (line 191)
- Risk: Low. DI pattern alignment.
- Tests: tests/test_admin.py

### TASK_012 — Replace direct ProcessingLogRepository with DI in processing_logs.py
- File: src/mkobi/api/routes/processing_logs.py
- Semantic Anchor: get_log_by_id_endpoint — VERIFIED
- Lines 106-108: ProcessingLogRepository() — VERIFIED
- get_processing_log_repository verified in deps.py (line 181)
- Risk: Low. DI pattern alignment.
- Tests: tests/test_processing_logs.py

---

## Rejected Tasks (4)

### TASK_004 — Fix hardcoded dimension count in data worker
- File: src/mkobi/workers/data_worker.py
- REJECTED: DATA INTEGRITY RISK
- graph.dimensions may be empty/None/contain invalid column names. No validation specified.
- Could silently corrupt aggregated data for all dashboards.
- Fix required: Add dimension validation against df.columns, specify fallback behavior.

### TASK_005 — Extract duplicate ValueError handling
- File: src/mkobi/api/routes/upload.py
- REJECTED: FRAGILE ANCHORING + MISSING LOGGING
- insert_before anchor "        try:" is ambiguous (multiple try blocks) and whitespace-sensitive.
- Proposed helper drops logger.warning calls present in original code.
- Fix required: Add logging inside helper; use stable anchor.

### TASK_008 — Add email domain blocklist validation
- File: src/mkobi/services/auth_service.py
- REJECTED: LOGIC BUG + CONFIG COUPLING
- Domain comparison is case-sensitive, contradicting case-insensitive acceptance criteria.
- email.split('@')[1] has no guard against missing '@'.
- get_config() direct call is inconsistent with injection pattern.
- Fix required: .lower() on domain; add malformed-email guard; inject config.

### TASK_010 — Dependency conflict (conditionally re-approvable)
- File: src/mkobi/api/routes/graphs.py
- REJECTED: UNDECLARED DEPENDENCY ON TASK_003
- Task 003 removes duplicate .update() call that this task also targets.
- Second changes_2 entry will fail text-match after task_003 runs.
- Fix required: Add depends_on [task_003]; reduce changes_2 entries by 1.

---

## Dependency Graph

task_001 []
task_002 []
task_003 []
task_006 []
task_007 []
task_009 []
task_011 []
task_012 []
task_010 [task_003]  — MISSING IN CURRENT order.yaml

## Layer Integrity — No cross-layer violations detected.

## Semantic Stability — All approved tasks use stable function/variable anchors with unique or correctly-handled targets.

## Rollout Warnings
1. Do NOT execute task_010 before task_003.
2. task_002 and task_007 restrict access — verify with stakeholders.
3. All approved tasks require passing referenced test suites.
ENDREPORT