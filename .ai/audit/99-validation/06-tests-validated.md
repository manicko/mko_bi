---
name: 06-tests-validated
description: Validation report for Phase 06 test quality findings
agent: validator
alwaysApply: false
---

# Phase 06 Validation Report — Test Quality

**Executor:** validator  
**Status:** complete  
**Validated:** yes

---

## Rejected Findings

**None** — All findings are verified and remain valid.

---

## Merged Findings

**None** — Findings are distinct and address separate issues.

---

## Reclassified Findings

**None** — All classifications are appropriate for the issues identified.

---

## Cross-Phase Conflicts

**No conflicts detected between test findings and other audit phases.**

### Infrastructure Dependency Analysis

The findings in this phase (TST-001 through TST-004) are code-level issues that exist independently of the Docker infrastructure problems documented in Phase 05. However, there are important cross-phase relationships:

- **TST-001** validation requires container execution to confirm the subprocess failure on `uv` binary. The Dockerfile shows uv is installed at `/root/.local/bin` (line 52) via curl installer. The test stage runs as `USER app` (line 142), but `/root` directory in Debian images has mode `700`, preventing access to `/root/.local/bin`. When `subprocess.run(["uv", ...])` is called, it fails because the binary is not accessible. This is a valid mandatory finding that prevents containerized test execution.

- **TST-002** (xdist crashes) — Code issue: shared mutable state in `test_graphs.py:360,368` (`async_client.headers` mutation) creates race conditions under parallel execution. The conftest.py properly implements SavePoint isolation (lines 467-486) and xdist worker database suffixes (lines 139-169), but test code that mutates shared fixtures remains unsafe.

- **TST-003** (missing coverage flag) — Configuration issue: coverage thresholds defined in frontend/vite.config.ts (lines 52-64) but package.json test script (line 10) runs `vitest run` without `--coverage` flag.

- **TST-004** (temp file cleanup) — Code issue: cleanup placement after assertions; temp file may persist on test failure.

### Cross-Phase Dependency Note

The **INF-001** finding (init script SQL syntax error) affects PostgreSQL database initialization and would prevent test container database startup in production-like environments. However, INF-001 addresses a different component (PostgreSQL role creation) than TST-001 (test uv binary access). These are orthogonal issues requiring separate fixes.

---

## Rollout Safety Issues

No rollout safety issues identified for test fixes. Test modifications are isolated and do not affect production code paths.

---

## Validated Counts Per Phase

| Finding | Classification | Validation Status |
|---------|----------------|-----------------|
| TST-001 | mandatory | **VERIFIED** — `uv run` subprocess calls in test_dev_seeders.py:188,208 fail in container due to non-root user lacking access to root-owned `/root/.local/bin/uv` binary |
| TST-002 | advisory | **VERIFIED** — Shared mutable state in `test_graphs.py:360,368` (`async_client.headers` modification) creates race conditions under xdist parallel execution |
| TST-003 | advisory | **VERIFIED** — vite.config.ts defines coverage thresholds (lines 52-64) but package.json test script (line 10) runs `vitest run` without `--coverage` flag |
| TST-004 | advisory | **VERIFIED** — `test_e2e_upload.py:343` cleanup occurs after assertions; file remains if earlier assertions fail |

---

## Required Fixes

**TST-001: Tests calling external subprocess commands fail in container environment**

Change from:
```python
result = subprocess.run(["uv", "run", "ruff", "check", ...])
```

To:
```python
result = subprocess.run(["/app/.venv/bin/ruff", "check", ...])
```

Or use environment-aware path resolution:
```python
import shutil
ruff_path = shutil.which("ruff") or "/app/.venv/bin/ruff"
mypy_path = shutil.which("mypy") or "/app/.venv/bin/mypy"
```

This fix is mandatory because containerized tests cannot execute in CI/test pipeline.

---

## Advisory Recommendations

All original advisory recommendations are validated:

- **TST-002**: Consider removing `-n auto` from pytest addopts until shared state issues are resolved. The shared state at `test_graphs.py:360,368` mutates `async_client.headers` without proper isolation.

- **TST-003**: Update package.json test script to `"test": "vitest run --coverage"` to enforce coverage thresholds and provide visibility into untested frontend code.

- **TST-004**: Wrap temp file creation/deletion in try/finally block for guaranteed cleanup. The `multi_file` temp file at line 307 should use the same pattern as `e2e_csv_file` fixture (lines 39-45).

---

## Evidence Summary

### TST-001 Evidence
- `tests/test_dev_seeders.py:188-200`: `subprocess.run(["uv", "run", "ruff", "check", ...])`
- `tests/test_dev_seeders.py:208-220`: `subprocess.run(["uv", "run", "mypy", ...])`
- `docker/Dockerfile:52`: uv installed to `/root/.local/bin/uv` via curl installer
- `docker/Dockerfile:142`: Test stage runs as `USER app`
- `docker/Dockerfile:133`: PATH set to `/app/.venv/bin` but `/root/.local/bin` is inaccessible due to `/root` permissions (mode 700)

**Note on Error Type:** The actual error may be either `FileNotFoundError` (most likely, when subprocess cannot find `uv` in accessible PATH) or `PermissionError` (if binary exists but user lacks execute rights). Both stem from the inaccessibility of `/root/.local/bin` to non-root users.

### TST-002 Evidence
- `pyproject.toml:196`: `addopts = "--import-mode=importlib -ra -v --strict-markers --cov-fail-under=65 -n auto"`
- `tests/test_graphs.py:360`: `async_client.headers = {"Authorization": f"Bearer {token_b}"}` (mutates shared client)
- `tests/test_graphs.py:368-369`: Same pattern, modifies headers without cleanup between tests

### TST-003 Evidence
- `frontend/vite.config.ts:52-64`: Coverage thresholds defined
- `frontend/package.json:10`: `"test": "vitest run"` (no --coverage flag)

### TST-004 Evidence
- `tests/test_e2e_upload.py:305-307`: Temp file created inside test method
- `tests/test_e2e_upload.py:343`: `multi_file.unlink(missing_ok=True)` placed after all assertions

---

## Implementation Notes

### Recommended Fix for TST-001

The most robust fix is to use `shutil.which()` to find tools in PATH, falling back to the venv path:

```python
# tests/test_dev_seeders.py

def _get_tool_path(tool_name: str) -> str:
    """Get path to linting tool, using venv fallback for container environments."""
    import shutil
    return shutil.which(tool_name) or f"/app/.venv/bin/{tool_name}"

async def test_seed_script_ruff_mypy():
    """Verify seed script passes linting and type checks."""
    ruff_path = _get_tool_path("ruff")
    mypy_path = _get_tool_path("mypy")

    result = subprocess.run(
        [ruff_path, "check", "src/mkobi/db/seeders/test_media_dash.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Ruff check failed: {result.stdout}"

    result = subprocess.run(
        [mypy_path, "src/mkobi/db/seeders/test_media_dash.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Mypy check failed: {result.stdout}"
```

---

**Report generated:** 2026-06-11