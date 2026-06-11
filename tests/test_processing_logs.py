"""Tests for processing logs functionality."""

import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4

from mkobi.models.enums import ProcessingStatus
from mkobi.models.processing_logs import ProcessingLogFilter, ProcessingLogRead, ProcessingLogCreate
from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository
from mkobi.services.processing_log_service import ProcessingLogService, _validate_transition
from mkobi.workers.data_worker import cleanup_stale_processing_logs
from mkobi.db.models.processing_logs import ProcessingLog
from mkobi.utils.exceptions import AppException, ErrorCode


class TestProcessingLogFilter:
    """Tests for ProcessingLogFilter model."""

    def test_filter_defaults(self):
        """Test default values for filter."""
        filter_obj = ProcessingLogFilter()
        assert filter_obj.dashboard_id is None
        assert filter_obj.status is None
        assert filter_obj.date_from is None
        assert filter_obj.date_to is None
        assert filter_obj.skip == 0
        assert filter_obj.limit == 100

    def test_filter_with_values(self):
        """Test filter with values."""
        dashboard_id = uuid4()
        filter_obj = ProcessingLogFilter(
            dashboard_id=dashboard_id,
            status=ProcessingStatus.STARTED,
            skip=10,
            limit=50,
        )
        assert filter_obj.dashboard_id == dashboard_id
        assert filter_obj.status == ProcessingStatus.STARTED
        assert filter_obj.skip == 10
        assert filter_obj.limit == 50


class TestProcessingLogModels:
    """Tests for ProcessingLog models."""

    def test_create_model(self):
        """Test ProcessingLogCreate model."""
        create_obj = ProcessingLogCreate(
            status=ProcessingStatus.STARTED,
            message="Test message",
        )
        assert create_obj.dashboard_id is None
        assert create_obj.status == ProcessingStatus.STARTED
        assert create_obj.message == "Test message"

    def test_read_model(self):
        """Test ProcessingLogRead model."""
        log_id = uuid4()
        read_obj = ProcessingLogRead(
            id=log_id,
            status=ProcessingStatus.COMPLETED,
            message="Completed",
            started_at=datetime.now(),
            finished_at=datetime.now(),
        )
        assert read_obj.id == log_id
        assert read_obj.status == ProcessingStatus.COMPLETED


class TestProcessingLogRepository:
    """Tests for ProcessingLogRepository."""

    @pytest.mark.asyncio
    async def test_create_log(self, async_db_session):
        """Test creating a log entry."""
        repo = ProcessingLogRepository()

        log = await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.STARTED,
            message="Test log",
            db=async_db_session,
        )

        assert log.dashboard_id is None
        assert log.status == ProcessingStatus.STARTED
        assert log.message == "Test log"
        assert log.started_at is not None

    @pytest.mark.asyncio
    async def test_update_status(self, async_db_session):
        """Test updating log status."""
        repo = ProcessingLogRepository()

        log = await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.STARTED,
            message="Test",
            db=async_db_session,
        )

        await repo.update_status(
            log_id=log.id,
            status=ProcessingStatus.COMPLETED,
            message="Completed",
            db=async_db_session,
        )

        # Verify update
        updated = await repo.get_by_id(log.id, db=async_db_session)
        assert updated is not None
        assert updated.status == ProcessingStatus.COMPLETED
        assert updated.message == "Completed"
        assert updated.finished_at is not None

    @pytest.mark.asyncio
    async def test_get_by_dashboard(self, async_db_session):
        """Test getting logs by dashboard."""
        repo = ProcessingLogRepository()

        # Clean up any existing logs with None dashboard_id for test isolation
        from sqlalchemy import delete
        from mkobi.db.models.processing_logs import ProcessingLog
        await async_db_session.execute(
            delete(ProcessingLog).where(ProcessingLog.dashboard_id.is_(None))
        )
        await async_db_session.commit()

        # Create multiple logs with None dashboard_id
        log1 = await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.STARTED,
            message="Test1",
            db=async_db_session,
        )
        log2 = await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.COMPLETED,
            message="Test2",
            db=async_db_session,
        )
        await async_db_session.commit()

        logs = await repo.get_by_dashboard(None, db=async_db_session)
        # Filter to only count our test logs (other tests may have added data)
        test_logs = [log for log in logs if log.id in (log1.id, log2.id)]
        assert len(test_logs) == 2

    @pytest.mark.asyncio
    async def test_get_filtered(self, async_db_session):
        """Test filtered log retrieval."""
        repo = ProcessingLogRepository()

        # Clean up any existing COMPLETED logs with None dashboard_id for test isolation
        from sqlalchemy import delete
        from mkobi.db.models.processing_logs import ProcessingLog
        await async_db_session.execute(
            delete(ProcessingLog).where(
                ProcessingLog.status == ProcessingStatus.COMPLETED,
                ProcessingLog.dashboard_id.is_(None),
            )
        )
        await async_db_session.commit()

        log2 = await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.COMPLETED,
            message="Test2",
            db=async_db_session,
        )
        await async_db_session.commit()

        filters = ProcessingLogFilter(
            status=ProcessingStatus.COMPLETED,
        )

        logs = await repo.get_filtered(filters, db=async_db_session)
        # Verify our log2 is in the results
        assert any(log.id == log2.id for log in logs)
        assert any(log.status == ProcessingStatus.COMPLETED for log in logs)


class TestProcessingLogService:
    """Tests for ProcessingLogService."""

    @pytest.fixture
    def service(self, async_db_session):
        """Create service with repository."""
        from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository
        repo = ProcessingLogRepository()
        return ProcessingLogService(repo)

    @pytest.mark.asyncio
    async def test_create_started_log(self, service, async_db_session):
        """Test creating started log via service."""
        result = await service.create_started_log(None, async_db_session)

        assert isinstance(result, ProcessingLogRead)
        assert result.dashboard_id is None
        assert result.status == ProcessingStatus.STARTED

    @pytest.mark.asyncio
    async def test_update_to_completed(self, service, async_db_session):
        """Test updating log to completed via valid state transitions."""
        # Create a log and follow proper state transitions
        log = await service.create_started_log(None, async_db_session)

        # Follow proper flow: STARTED -> UPLOADED -> PROCESSING -> COMPLETED
        await service.update_to_uploaded(log.id, async_db_session)
        await service.update_to_processing(log.id, async_db_session)

        # Update to completed
        result = await service.update_to_completed(
            log.id, "All good", async_db_session,
        )

        assert result is not None
        assert result.status == ProcessingStatus.COMPLETED
        assert result.message == "All good"

    @pytest.mark.asyncio
    async def test_update_to_failed(self, service, async_db_session):
        """Test updating log to failed."""
        # First create a log
        log = await service.create_started_log(None, async_db_session)

        # Update to failed
        result = await service.update_to_failed(
            log.id, "Error occurred", async_db_session
        )

        assert result is not None
        assert result.status == ProcessingStatus.FAILED
        assert result.message == "Error occurred"

    @pytest.mark.asyncio
    async def test_get_filtered(self, service, async_db_session):
        """Test getting filtered logs via service."""
        # Clean up any existing COMPLETED logs with None dashboard_id for test isolation
        from sqlalchemy import delete
        from mkobi.db.models.processing_logs import ProcessingLog
        await async_db_session.execute(
            delete(ProcessingLog).where(
                ProcessingLog.status == ProcessingStatus.COMPLETED,
                ProcessingLog.dashboard_id.is_(None),
            )
        )
        await async_db_session.commit()

        # Create logs
        log1 = await service.create_started_log(None, async_db_session)
        await service.update_to_uploaded(log1.id, async_db_session)
        await service.update_to_processing(log1.id, async_db_session)
        await service.update_to_completed(
            log1.id,
            "Done",
            async_db_session,
        )
        await service.create_started_log(None, async_db_session)

        filters = ProcessingLogFilter(
            status=ProcessingStatus.COMPLETED,
        )

        logs = await service.get_filtered(filters, async_db_session)
        # Verify log1 is in the results - filter to only check our test log
        test_logs = [log for log in logs if log.id == log1.id]
        assert len(test_logs) == 1
        assert test_logs[0].status == ProcessingStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_update_processing_log_with_finished_at(self, service, async_db_session):
        """Test update_processing_log with custom finished_at timestamp."""
        # Create a log and set to PROCESSING status for valid transition to COMPLETED
        log = await service.create_started_log(None, async_db_session)
        await service.update_to_uploaded(log.id, async_db_session)
        await service.update_to_processing(log.id, async_db_session)

        # Update with custom finished_at (UTC-aware for consistency)
        custom_finished = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        result = await service.update_processing_log(
            log_id=log.id,
            status="completed",
            message="Custom finished",
            finished_at=custom_finished,
            db=async_db_session,
        )

        assert result is not None
        assert result.status == ProcessingStatus.COMPLETED
        assert result.message == "Custom finished"
        # finished_at should be close to our custom time (within 1 second tolerance)
        assert result.finished_at is not None
        expected_time = datetime.fromisoformat(custom_finished)
        diff = abs((result.finished_at - expected_time).total_seconds())
        assert diff < 1.0, "finished_at should be close to the custom timestamp"

    @pytest.mark.asyncio
    async def test_update_processing_log_invalid_finished_at(self, service, async_db_session):
        """Test update_processing_log with invalid finished_at format."""
        # Create a log and set to PROCESSING status for valid transition to COMPLETED
        log = await service.create_started_log(None, async_db_session)
        await service.update_to_uploaded(log.id, async_db_session)
        await service.update_to_processing(log.id, async_db_session)

        # Update with invalid finished_at - should fall back to None/default behavior
        result = await service.update_processing_log(
            log_id=log.id,
            status="completed",
            message="Invalid timestamp",
            finished_at="not-a-valid-timestamp",
            db=async_db_session,
        )

        assert result is not None
        assert result.status == ProcessingStatus.COMPLETED
        # finished_at should be set automatically for COMPLETED
        assert result.finished_at is not None


class TestStaleProcessingCleanup:
    """Tests for stale processing cleanup functionality."""

    @pytest.mark.asyncio
    async def test_cleanup_stale_processing_logs(self, async_db_session):
        """Test that stale PROCESSING entries are marked as FAILED."""
        repo = ProcessingLogRepository()

        # Clean up any existing PROCESSING logs with None dashboard_id for test isolation
        from sqlalchemy import delete
        await async_db_session.execute(
            delete(ProcessingLog).where(
                ProcessingLog.status == ProcessingStatus.PROCESSING,
                ProcessingLog.dashboard_id.is_(None),
            )
        )
        await async_db_session.commit()

        # Create a stale PROCESSING log (started 40 minutes ago - older than default 30 min timeout)
        old_time = datetime.now(UTC) - timedelta(minutes=40)
        stale_log = await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.PROCESSING,
            message="Processing started",
            db=async_db_session,
        )
        # Manually set started_at to simulate old entry
        from sqlalchemy import update as sa_update
        stmt = sa_update(ProcessingLog).where(ProcessingLog.id == stale_log.id).values({"started_at": old_time})
        await async_db_session.execute(stmt)
        await async_db_session.commit()

        # Create a fresh PROCESSING log (should not be affected)
        fresh_log = await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.PROCESSING,
            message="Fresh processing",
            db=async_db_session,
        )

        # Create a COMPLETED log (should not be affected)
        completed_log = await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.COMPLETED,
            message="Completed",
            db=async_db_session,
        )

        # Run cleanup with 30 minute timeout, passing the test session
        await cleanup_stale_processing_logs(timeout_minutes=30, session=async_db_session)

        # Verify stale log is now FAILED
        updated_stale = await repo.get_by_id(stale_log.id, db=async_db_session)
        assert updated_stale is not None
        assert updated_stale.status == ProcessingStatus.FAILED
        assert "Worker timeout" in updated_stale.message or updated_stale.message is not None

        # Verify fresh log is still PROCESSING
        fresh = await repo.get_by_id(fresh_log.id, db=async_db_session)
        assert fresh is not None
        assert fresh.status == ProcessingStatus.PROCESSING

        # Verify COMPLETED log is unchanged
        completed = await repo.get_by_id(completed_log.id, db=async_db_session)
        assert completed is not None
        assert completed.status == ProcessingStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_cleanup_no_stale_entries(self, async_db_session):
        """Test cleanup when there are no stale entries."""
        repo = ProcessingLogRepository()

        # Delete any stale entries from previous runs to ensure test isolation
        from sqlalchemy import delete
        from mkobi.db.models.processing_logs import ProcessingLog
        await async_db_session.execute(
            delete(ProcessingLog).where(
                ProcessingLog.status == ProcessingStatus.PROCESSING,
                ProcessingLog.started_at < datetime.now(UTC) - timedelta(minutes=1),
            )
        )
        await async_db_session.commit()

        # Create only fresh entries
        await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.PROCESSING,
            message="Fresh processing",
            db=async_db_session,
        )

        # Run cleanup with test session
        count = await cleanup_stale_processing_logs(timeout_minutes=30, session=async_db_session)

        assert count == 0, "Should have marked 0 entries as FAILED"


class TestStateTransitionValidation:
    """Tests for processing status state machine validation."""

    def test_valid_transition_started_to_uploaded(self):
        """Test valid transition from STARTED to UPLOADED."""
        _validate_transition(
            ProcessingStatus.STARTED, ProcessingStatus.UPLOADED
        )

    def test_valid_transition_started_to_failed(self):
        """Test valid transition from STARTED to FAILED."""
        _validate_transition(
            ProcessingStatus.STARTED, ProcessingStatus.FAILED
        )

    def test_valid_transition_uploaded_to_processing(self):
        """Test valid transition from UPLOADED to PROCESSING."""
        _validate_transition(
            ProcessingStatus.UPLOADED, ProcessingStatus.PROCESSING
        )

    def test_valid_transition_uploaded_to_failed(self):
        """Test valid transition from UPLOADED to FAILED."""
        _validate_transition(
            ProcessingStatus.UPLOADED, ProcessingStatus.FAILED
        )

    def test_valid_transition_processing_to_completed(self):
        """Test valid transition from PROCESSING to COMPLETED."""
        _validate_transition(
            ProcessingStatus.PROCESSING, ProcessingStatus.COMPLETED
        )

    def test_valid_transition_processing_to_failed(self):
        """Test valid transition from PROCESSING to FAILED."""
        _validate_transition(
            ProcessingStatus.PROCESSING, ProcessingStatus.FAILED
        )

    def test_same_status_transition_allowed(self):
        """Test that same status transition is allowed (no-op)."""
        _validate_transition(
            ProcessingStatus.STARTED, ProcessingStatus.STARTED
        )

    def test_invalid_transition_completed_to_processing(self):
        """Test that COMPLETED -> PROCESSING is blocked."""
        with pytest.raises(AppException) as exc_info:
            _validate_transition(
                ProcessingStatus.COMPLETED, ProcessingStatus.PROCESSING
            )
        assert exc_info.value.code == ErrorCode.INVALID_TRANSITION
        assert "completed -> processing" in exc_info.value.detail

    def test_invalid_transition_completed_to_failed(self):
        """Test that COMPLETED -> FAILED is blocked."""
        with pytest.raises(AppException) as exc_info:
            _validate_transition(
                ProcessingStatus.COMPLETED, ProcessingStatus.FAILED
            )
        assert exc_info.value.code == ErrorCode.INVALID_TRANSITION

    def test_invalid_transition_failed_to_completed(self):
        """Test that FAILED -> COMPLETED is blocked."""
        with pytest.raises(AppException) as exc_info:
            _validate_transition(
                ProcessingStatus.FAILED, ProcessingStatus.COMPLETED
            )
        assert exc_info.value.code == ErrorCode.INVALID_TRANSITION

    def test_invalid_transition_started_to_processing(self):
        """Test that STARTED -> PROCESSING is blocked (must go through UPLOADED)."""
        with pytest.raises(AppException) as exc_info:
            _validate_transition(
                ProcessingStatus.STARTED, ProcessingStatus.PROCESSING
            )
        assert exc_info.value.code == ErrorCode.INVALID_TRANSITION

    def test_invalid_transition_started_to_completed(self):
        """Test that STARTED -> COMPLETED is blocked (must go through PROCESSING)."""
        with pytest.raises(AppException) as exc_info:
            _validate_transition(
                ProcessingStatus.STARTED, ProcessingStatus.COMPLETED
            )
        assert exc_info.value.code == ErrorCode.INVALID_TRANSITION

    @pytest.mark.asyncio
    async def test_service_invalid_transition_raises_error(self, async_db_session):
        """Test that service method raises error for invalid transitions."""
        service = ProcessingLogService(ProcessingLogRepository())
        # Create log in COMPLETED state
        log = await service.create_started_log(None, async_db_session)
        await service.update_to_uploaded(log.id, async_db_session)
        await service.update_to_processing(log.id, async_db_session)
        await service.update_to_completed(log.id, "Done", async_db_session)

        # Try to transition from COMPLETED to PROCESSING (invalid)
        with pytest.raises(AppException) as exc_info:
            await service.update_to_processing(log.id, async_db_session)
        assert exc_info.value.code == ErrorCode.INVALID_TRANSITION
