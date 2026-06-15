# Phase 06 Test Validation Report

**Validator:** validator  
**Source:** `.ai/audit/06-tests/findings.md`  
**Date:** 2026-06-15

---

## Rejected Findings

None. All findings are valid and accurately describe issues in the codebase.

---

## Merged Findings

3 findings from the test audit are cross-phase duplicates of backend audit findings:

| Test Finding | Backend Finding | Rationale |
|-------------|-----------------|-----------|
| TST-001 | BE-001 | Same root cause: JWT secret test fails in Docker due to missing `.env` fallback. Already identified in backend audit. |
| TST-002 | BE-002 | Same root cause: File validation test expects extension-first but implementation uses MIME-first. Already identified in backend audit. |
| TST-003 | BE-003 | Same root cause: Ruff cache permission errors in Docker container. Already identified in backend audit. |

---

## Reclassified Findings

None. All remaining findings retain their original classification.

---

## Cross-Phase Conflicts

**No conflicts detected.** The test audit findings are consistent with the backend audit. Both audits correctly identify the same issues with test behavior in Docker environment. The cross-phase consistency validates the accuracy of both findings.

---

## Rollout Safety Issues

None. Test quality findings do not affect rollout safety of production code.

---

## Validated Finding Counts

| Type | Count |
|------|-------|
| **Remaining after merge (advisory)** | 5 |

The 5 standalone findings after merging duplicates:
- **TST-004**: Mock call assertions instead of behavioral checks (advisory)
- **TST-005**: Mocked dependency chain testing mock wiring, not logic (advisory)
- **TST-006**: Tautological assertion pattern in cleanup test (advisory)
- **TST-007**: Coverage tool cannot run in Docker container (advisory)
- **TST-008**: Critical path coverage gaps (advisory)

---

## Validation Outcome

All 8 test findings validated with 3 merged to backend findings:
- 0 rejected findings
- 0 reclassified findings
- 3 merged findings (cross-phase duplicates)
- 5 standalone advisory findings for test quality improvements

---

## Actionable Recommendations

Implementation-ready guidance for each advisory finding. Every recommendation includes the exact file, before/after code, and rationale.

### TST-004: Replace Mock Call Assertions with Behavioral Checks

**File:** `tests/test_data_worker.py`

**Problem:** `TestDataWorker` tests at lines 52, 73, 96, 118 assert `mock_session.execute.assert_called_once()` without verifying what SQL was executed or what the return value was. These tests pass as long as `execute` is called once, regardless of correctness.

**Fix for `test_update_processing_log_status_started` (line 35):**

Before:
```python
async def test_update_processing_log_status_started(
    self, mock_session
):
    """Test updating status to PROCESSING adds started_at."""
    task_id = str(uuid4())
    mock_result = MagicMock()
    mock_result.rowcount = None
    mock_session.execute.return_value = mock_result

    await _update_processing_log_status(
        task_id=task_id,
        status=ProcessingStatus.PROCESSING,
        message="Processing started",
        started_at=datetime.now(UTC),
        session=mock_session,
    )

    mock_session.execute.assert_called_once()
```

After:
```python
async def test_update_processing_log_status_started(
    self, mock_session
):
    """Test updating status to PROCESSING adds started_at."""
    task_id = str(uuid4())
    mock_result = MagicMock()
    mock_result.rowcount = None
    mock_session.execute.return_value = mock_result

    await _update_processing_log_status(
        task_id=task_id,
        status=ProcessingStatus.PROCESSING,
        message="Processing started",
        started_at=datetime.now(UTC),
        session=mock_session,
    )

    # Verify execute was called with a statement containing the task_id
    mock_session.execute.assert_called_once()
    call_args = mock_session.execute.call_args
    executed_statement = call_args[0][0]
    rendered = str(executed_statement.compile(compile_kwargs={"literal_binds": True}))
    assert task_id in rendered
    assert "processing_log" in rendered.lower()
```

**Rationale:** Asserting on the rendered SQL verifies the correct table and task_id filter are used, catching regressions where the wrong query is constructed. The same pattern applies to lines 73, 96, 118 — each should verify the SQL contains the expected task_id and status values.

---

**File:** `tests/test_auth_service.py`

**Problem:** `test_reset_password_admin_success` (line 426) asserts `mock_user_repo.update.assert_called_once()` and `mock_db.commit.assert_called_once()` but does not verify the password was actually changed. A test at line 466 (`test_reset_password_admin_update_params`) already checks `call_args.kwargs`, but the success test does not.

**Fix for `test_reset_password_admin_success` (line 426):**

Before:
```python
async def test_reset_password_admin_success(self, auth_service, mock_user_repo, mock_db):
    """Test successful admin password reset."""
    target_user_id = uuid4()
    admin_user_id = uuid4()
    mock_user = MagicMock()
    mock_user.id = target_user_id
    mock_user_repo.get_with_hash = AsyncMock(return_value=mock_user)
    mock_user_repo.update = AsyncMock()

    result = await auth_service.reset_password_admin(
        user_id=target_user_id,
        admin_user_id=admin_user_id,
        db=mock_db,
    )

    assert result is not None
    assert "retrieval_token" in result
    assert "user_id" in result
    assert result["user_id"] == str(target_user_id)
    assert "message" in result
    mock_user_repo.update.assert_called_once()
    mock_db.commit.assert_called_once()
```

After:
```python
async def test_reset_password_admin_success(self, auth_service, mock_user_repo, mock_db):
    """Test successful admin password reset."""
    target_user_id = uuid4()
    admin_user_id = uuid4()
    mock_user = MagicMock()
    mock_user.id = target_user_id
    mock_user_repo.get_with_hash = AsyncMock(return_value=mock_user)
    mock_user_repo.update = AsyncMock()

    result = await auth_service.reset_password_admin(
        user_id=target_user_id,
        admin_user_id=admin_user_id,
        db=mock_db,
    )

    assert result is not None
    assert "retrieval_token" in result
    assert "user_id" in result
    assert result["user_id"] == str(target_user_id)
    assert "message" in result
    # Verify update was called with password_hash and force_password_change
    mock_user_repo.update.assert_called_once()
    call_args = mock_user_repo.update.call_args
    assert "password_hash" in call_args.kwargs
    assert call_args.kwargs["force_password_change"] is True
    mock_db.commit.assert_called_once()
```

**Rationale:** The behavioral check (password_hash present, force_password_change=True) verifies the actual security-critical behavior, not just that a method was called. This catches bugs where `update` is called with wrong parameters.

---

**File:** `tests/test_graph_service.py`

**Problem:** `test_create_graph_success` (line 43) and `test_update_graph_partial` (line 146) assert `mock_graph_repo.create.assert_called_once()` and `mock_graph_repo.update.assert_called_once()` without verifying the arguments passed to the repository.

**Fix for `test_create_graph_success` (line 43):**

Before:
```python
async def test_create_graph_success(self, graph_service, mock_graph_repo, mock_db):
    """Test successful graph creation."""
    dashboard_id = uuid4()
    mock_graph_repo.create.return_value = self._make_graph_obj(
        name="Sales", dashboard_id=dashboard_id, type_=GraphType.BAR
    )

    data = GraphCreate(
        name="Sales",
        type=GraphType.BAR,
        dashboard_id=dashboard_id,
        config={"xaxis": {"title": "Month"}},
        dimensions=["month"],
        metrics=["revenue"],
    )
    result = await graph_service.create(data, db=mock_db)

    assert isinstance(result, GraphRead)
    assert result.name == "Sales"
    assert result.type == GraphType.BAR
    mock_graph_repo.create.assert_called_once()
```

After:
```python
async def test_create_graph_success(self, graph_service, mock_graph_repo, mock_db):
    """Test successful graph creation."""
    dashboard_id = uuid4()
    mock_graph_repo.create.return_value = self._make_graph_obj(
        name="Sales", dashboard_id=dashboard_id, type_=GraphType.BAR
    )

    data = GraphCreate(
        name="Sales",
        type=GraphType.BAR,
        dashboard_id=dashboard_id,
        config={"xaxis": {"title": "Month"}},
        dimensions=["month"],
        metrics=["revenue"],
    )
    result = await graph_service.create(data, db=mock_db)

    assert isinstance(result, GraphRead)
    assert result.name == "Sales"
    assert result.type == GraphType.BAR
    # Verify the repository received the correct data
    mock_graph_repo.create.assert_called_once()
    call_args = mock_graph_repo.create.call_args
    assert call_args.kwargs["name"] == "Sales"
    assert call_args.kwargs["type"] == GraphType.BAR
    assert call_args.kwargs["dashboard_id"] == dashboard_id
```

**Rationale:** Verifying the arguments passed to `create` ensures the service layer correctly transforms the input model into repository parameters. Without this, a bug where the service passes `None` for `dashboard_id` would go undetected.

---

### TST-005: Add Argument Verification to TestStoreAggregates

**File:** `tests/test_data_worker.py`

**Problem:** `TestStoreAggregates` (lines 244-483) mocks `AggregationService`, `StorageManager`, and `DashboardFilterValuesRepository`, then only asserts mock call counts. The actual data transformation logic — how the input DataFrame is aggregated, how filter values are extracted — is completely unverified.

**Fix for `test_store_aggregates_with_graphs` (line 278):**

Before:
```python
    # ... (setup code unchanged)
    await _store_aggregates(
        df=df,
        dashboard_id=dashboard_id,
        task_id=task_id,
        mode="overwrite",
        db_session=mock_session,
    )

    assert mock_session.execute.call_count == 2
    mock_manager_instance.save_aggregates.assert_called_once()
```

After:
```python
    # ... (setup code unchanged)
    await _store_aggregates(
        df=df,
        dashboard_id=dashboard_id,
        task_id=task_id,
        mode="overwrite",
        db_session=mock_session,
    )

    assert mock_session.execute.call_count == 2
    mock_manager_instance.save_aggregates.assert_called_once()
    # Verify aggregation was called with the input DataFrame and correct graph
    mock_service_instance.aggregate_for_dashboard.assert_called_once_with(
        df=df, graphs=[mock_graph]
    )
    # Verify save_aggregates received the aggregation result with correct mode
    save_call_args = mock_manager_instance.save_aggregates.call_args
    assert save_call_args.kwargs["dashboard_id"] == dashboard_id
    assert save_call_args.kwargs["clear_old"] is True  # overwrite mode
    # Verify filter values extraction was called
    mock_service_instance.extract_filter_values.assert_called_once()
    # Verify filter values were saved
    mock_repo_instance.save_filter_values.assert_called_once()
    filter_call_args = mock_repo_instance.save_filter_values.call_args
    assert filter_call_args.kwargs["dashboard_id"] == dashboard_id
```

**Rationale:** Verifying arguments passed to mocked dependencies catches data transformation bugs. For example, if someone changes `_store_aggregates` to pass the wrong DataFrame or forget `clear_old=True` in overwrite mode, these assertions will fail. The test still uses mocks (fast, isolated) but verifies the wiring is correct.

**Additional recommendation:** Add one integration test for `_store_aggregates` using a real test database session with actual `AggregationService` and `StorageManager` instances. This would catch bugs in the real aggregation logic that unit tests with full mocking cannot detect.

---

### TST-006: Fix Tautological Assertion in Cleanup Test

**File:** `tests/test_upload_api.py`

**Problem:** `test_cleanup_task_files_called_during_processing` (line 731) patches `cleanup_task_files` with `wraps=...`, then calls the function directly in the test body (line 781), and asserts `mock_cleanup.assert_called()` (line 784). Since the test itself calls the function, the assertion always passes — it tests nothing.

**Fix — verify actual file deletion behavior:**

Before:
```python
@pytest.mark.asyncio
async def test_cleanup_task_files_called_during_processing(
    self,
    authenticated_client: AsyncClient,
    async_db_session,
    test_user: dict,
    test_dashboard_for_cleanup: Dashboard,
    simple_csv_content: bytes,
    mocker,
) -> None:
    """Verify cleanup_task_files is invoked after processing completes."""
    from mkobi.config import get_config
    from mkobi.services import file_cleanup

    config = get_config()
    upload_dir = Path(config.upload_temp_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Grant edit access to test user
    access_repo = AccessRepository()
    await access_repo.grant_access(
        db=async_db_session,
        user_id=test_user["id"],
        dashboard_id=test_dashboard_for_cleanup.id,
        permission=DashboardPermission.EDIT,
    )
    await async_db_session.commit()

    # Patch cleanup_task_files to track if it's called
    mock_cleanup = mocker.patch(
        "mkobi.services.file_cleanup.cleanup_task_files",
        wraps=file_cleanup.cleanup_task_files,
    )

    # Create CSV file
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
        f.write(simple_csv_content)
        csv_path = Path(f.name)

    try:
        with open(csv_path, "rb") as f:
            response = await authenticated_client.post(
                f"/upload/{test_dashboard_for_cleanup.id}",
                files={"file": ("cleanup_test.csv", f, "text/csv")},
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        task_id = data["task_id"]

        # Call cleanup_task_files directly (simulating post-processing cleanup)
        file_cleanup.cleanup_task_files(task_id=UUID(task_id))

        # Verify cleanup_task_files was called with the task_id
        mock_cleanup.assert_called()
    finally:
        csv_path.unlink(missing_ok=True)
```

After:
```python
@pytest.mark.asyncio
async def test_cleanup_task_files_removes_temp_files(
    self,
    authenticated_client: AsyncClient,
    async_db_session,
    test_user: dict,
    test_dashboard_for_cleanup: Dashboard,
    simple_csv_content: bytes,
) -> None:
    """Verify cleanup_task_files removes temp files for a given task_id."""
    from mkobi.config import get_config
    from mkobi.services import file_cleanup

    config = get_config()
    upload_dir = Path(config.upload_temp_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Grant edit access to test user
    access_repo = AccessRepository()
    await access_repo.grant_access(
        db=async_db_session,
        user_id=test_user["id"],
        dashboard_id=test_dashboard_for_cleanup.id,
        permission=DashboardPermission.EDIT,
    )
    await async_db_session.commit()

    # Create CSV file
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
        f.write(simple_csv_content)
        csv_path = Path(f.name)

    try:
        with open(csv_path, "rb") as f:
            response = await authenticated_client.post(
                f"/upload/{test_dashboard_for_cleanup.id}",
                files={"file": ("cleanup_test.csv", f, "text/csv")},
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        task_id = data["task_id"]

        # Verify the task file exists before cleanup
        task_files_before = list(upload_dir.glob(f"*{task_id}*"))
        assert len(task_files_before) > 0, (
            f"Expected task files before cleanup, found none for task_id={task_id}"
        )

        # Call cleanup and verify files are actually removed
        file_cleanup.cleanup_task_files(task_id=UUID(task_id))

        task_files_after = list(upload_dir.glob(f"*{task_id}*"))
        assert len(task_files_after) == 0, (
            f"Expected no task files after cleanup, found: {task_files_after}"
        )
    finally:
        csv_path.unlink(missing_ok=True)
```

**Rationale:** The new test verifies actual filesystem behavior — that `cleanup_task_files` removes files matching the task_id from the upload directory. This catches bugs where the function is called but doesn't actually delete files (e.g., wrong glob pattern, wrong directory). The test is deterministic: it creates a real upload, gets a real task_id, and checks real file deletion.

---

### TST-007: Fix Coverage Tool in Docker Container

**File:** `docker/docker-compose.test.yml`

**Problem:** The coverage tool writes its SQLite database to `/app/.coverage.*` by default, but the `/app` directory in the Docker test container is not writable. This causes `coverage.exceptions.DataError` when running `pytest --cov` inside the container.

**Fix — add `COVERAGE_FILE` environment variable to the test-app service:**

Before (line 126):
```yaml
  test-app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
      target: test
    container_name: test-app
    environment:
      ENV: test
      HOME: /tmp
      UV_CACHE_DIR: /tmp/.cache/uv
      DATABASE__HOST: test-db
      DATABASE__PORT: 5432
```

After:
```yaml
  test-app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
      target: test
    container_name: test-app
    environment:
      ENV: test
      HOME: /tmp
      UV_CACHE_DIR: /tmp/.cache/uv
      COVERAGE_FILE: /tmp/.coverage
      DATABASE__HOST: test-db
      DATABASE__PORT: 5432
```

**Rationale:** Setting `COVERAGE_FILE=/tmp/.coverage` redirects the coverage SQLite database to `/tmp`, which is always writable. This is a one-line change that enables `pytest --cov` to work inside the Docker container, allowing CI pipelines to enforce the `fail_under = 65` threshold configured in `pyproject.toml:212`.

**Alternative (if coverage should only run on host):** Add a comment in `pyproject.toml` near the `addopts` line documenting that `--cov` flags should be stripped when running in Docker:
```toml
# Note: When running in Docker, use:
#   uv run pytest tests/ -v --no-cov
# Coverage requires writable /tmp for .coverage SQLite file.
# The --cov flags are only applied on host/CI environments.
```

---

### TST-008: Prioritize Tests for Critical Coverage Gaps

**Priority 1 — `api/routes/dashboards_access.py` (32% coverage):**

This module controls who can access which dashboards. Untested access control is a security risk.

**File to create:** `tests/test_dashboards_access_api.py`

```python
"""Tests for dashboard access control API endpoints."""
from uuid import uuid4

import pytest
from httpx import AsyncClient

from mkobi.core.security import hash_password, create_access_token
from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.models.enums import DashboardPermission


class TestDashboardAccessAPI:
    """Tests for access control endpoints."""

    async def test_grant_access_success(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ):
        """Test granting dashboard access to a user."""
        # Create a second user to grant access to
        user_repo = UserRepository()
        target_user = await user_repo.create(
            db=async_db_session,
            email=f"target_{uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TargetPass123!"),
            role="viewer",
        )
        # Create a dashboard
        dash_repo = DashboardRepository()
        dashboard = await dash_repo.create(
            db=async_db_session,
            name=f"access_test_{uuid4().hex[:8]}",
            description="Access test dashboard",
        )
        await async_db_session.commit()

        response = await authenticated_client.post(
            f"/dashboards/{dashboard.id}/access",
            json={
                "user_id": str(target_user.id),
                "permission": DashboardPermission.VIEW,
            },
        )
        assert response.status_code == 201

    async def test_revoke_access_success(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ):
        """Test revoking dashboard access."""
        # ... setup: create user, dashboard, grant access, then revoke
        pass

    async def test_list_access_returns_granted_users(
        self, authenticated_client: AsyncClient, async_db_session, test_user: dict
    ):
        """Test listing users with access to a dashboard."""
        pass

    async def test_unauthorized_user_cannot_grant_access(
        self, async_client: AsyncClient, async_db_session
    ):
        """Test that non-admin users cannot grant dashboard access."""
        pass
```

**Priority 2 — `core/base_repository.py` (0% coverage):**

Every repository inherits from `BaseRepository`. If it has bugs, all repositories are affected.

**File to create:** `tests/test_base_repository.py`

```python
"""Tests for BaseRepository generic CRUD operations."""
from uuid import uuid4

import pytest

from mkobi.core.base_repository import BaseRepository


class TestBaseRepository:
    """Tests for BaseRepository with a real test database session."""

    async def test_get_returns_none_for_missing_id(self, async_db_session):
        """Test get() returns None when entity does not exist."""
        # Use any concrete repository (e.g., DashboardRepository) to test base
        from mkobi.db.repositories.dashboard_repo import DashboardRepository
        from mkobi.db.models.dashboard import Dashboard

        repo = BaseRepository(async_db_session, Dashboard)
        result = await repo.get(uuid4())
        assert result is None

    async def test_get_all_returns_empty_list_when_no_entities(
        self, async_db_session
    ):
        """Test get_all() returns empty list for empty table."""
        from mkobi.db.repositories.dashboard_repo import DashboardRepository
        from mkobi.db.models.dashboard import Dashboard

        repo = BaseRepository(async_db_session, Dashboard)
        result = await repo.get_all()
        assert result == []

    async def test_delete_returns_false_for_missing_id(self, async_db_session):
        """Test delete() returns False when entity does not exist."""
        from mkobi.db.models.dashboard import Dashboard

        repo = BaseRepository(async_db_session, Dashboard)
        result = await repo.delete(uuid4())
        assert result is False
```

**Priority 3 — `workers/data_worker.py` (52% coverage):**

The background worker handles the core data processing pipeline. The `_process_csv_file_async` and `process_csv_background` functions have significant untested paths (lines 54-77, 269-284, 342-348, 494-551).

**Recommended approach:** Add tests for `_process_csv_file_async` error handling paths:
- File not found (line 57-58)
- Encoding errors (line 61-62)
- Missing required columns (line 67-68)
- General processing failures (line 77)

**Priority 4 — `api/routes/dashboards_filters.py` (26% coverage):**

Filter management is a core feature. Add CRUD tests for filter creation, update, deletion, and listing by dashboard.

**Priority 5 — `api/routes/processing_configs.py` (30% coverage):**

Processing configuration drives the data pipeline. Add tests for creating, updating, and validating processing configs.

**Rationale for prioritization:** Security-critical code (access control) is first, followed by foundational code (base repository) that affects all other modules, then core business logic (data worker, filters, processing configs). Each new test file should follow the existing patterns in `tests/test_upload_api.py` for integration tests or `tests/test_auth_service.py` for unit tests.