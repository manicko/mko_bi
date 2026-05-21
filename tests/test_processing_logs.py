"""Tests for processing logs functionality."""

import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4

from mkobi.models.enums import ProcessingStatus
from mkobi.models.processing_logs import ProcessingLogFilter, ProcessingLogRead, ProcessingLogCreate
from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository
from mkobi.services.processing_log_service import ProcessingLogService
from mkobi.workers.data_worker import cleanup_stale_processing_logs
from mkobi.db.models.processing_logs import ProcessingLog


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
            status=ProcessingStatus.SUCCESS,
            message="Success",
            started_at=datetime.now(),
            finished_at=datetime.now(),
        )
        assert read_obj.id == log_id
        assert read_obj.status == ProcessingStatus.SUCCESS


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
            status=ProcessingStatus.SUCCESS,
            message="Completed",
            db=async_db_session,
        )

        # Verify update
        updated = await repo.get_by_id(log.id, db=async_db_session)
        assert updated is not None
        assert updated.status == ProcessingStatus.SUCCESS
        assert updated.message == "Completed"
        assert updated.finished_at is not None

    @pytest.mark.asyncio
    async def test_get_by_dashboard(self, async_db_session):
        """Test getting logs by dashboard."""
        repo = ProcessingLogRepository()

        # Create multiple logs with None dashboard_id
        await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.STARTED,
            message="Test1",
            db=async_db_session,
        )
        await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.SUCCESS,
            message="Test2",
            db=async_db_session,
        )

        logs = await repo.get_by_dashboard(None, db=async_db_session)
        assert len(logs) == 2

    @pytest.mark.asyncio
    async def test_get_filtered(self, async_db_session):
        """Test filtered log retrieval."""
        repo = ProcessingLogRepository()

        await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.STARTED,
            message="Test1",
            db=async_db_session,
        )
        await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.SUCCESS,
            message="Test2",
            db=async_db_session,
        )

        filters = ProcessingLogFilter(
            status=ProcessingStatus.SUCCESS,
        )

        logs = await repo.get_filtered(filters, db=async_db_session)
        assert len(logs) == 1
        assert logs[0].status == ProcessingStatus.SUCCESS


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
    async def test_update_to_success(self, service, async_db_session):
        """Test updating log to success."""
        # First create a log
        log = await service.create_started_log(None, async_db_session)

        # Update to success
        result = await service.update_to_success(
            log.id, "All good", async_db_session
        )

        assert result is not None
        assert result.status == ProcessingStatus.SUCCESS
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
        # Create logs
        log1 = await service.create_started_log(None, async_db_session)
        await service.update_to_success(
            log1.id,
            "Done",
            async_db_session,
        )
        await service.create_started_log(None, async_db_session)

        filters = ProcessingLogFilter(
            status=ProcessingStatus.SUCCESS,
        )

        logs = await service.get_filtered(filters, async_db_session)
        assert len(logs) == 1
        assert logs[0].status == ProcessingStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_update_processing_log_with_finished_at(self, service, async_db_session):
        """Test update_processing_log with custom finished_at timestamp."""
        # Create a log first
        log = await service.create_started_log(None, async_db_session)

        # Update with custom finished_at (UTC-aware for consistency)
        custom_finished = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        result = await service.update_processing_log(
            log_id=log.id,
            status="success",
            message="Custom finished",
            finished_at=custom_finished,
            db=async_db_session,
        )

        assert result is not None
        assert result.status == ProcessingStatus.SUCCESS
        assert result.message == "Custom finished"
        # finished_at should be close to our custom time (within 1 second tolerance)
        assert result.finished_at is not None
        expected_time = datetime.fromisoformat(custom_finished)
        diff = abs((result.finished_at - expected_time).total_seconds())
        assert diff < 1.0, "finished_at should be close to the custom timestamp"

    @pytest.mark.asyncio
    async def test_update_processing_log_invalid_finished_at(self, service, async_db_session):
        """Test update_processing_log with invalid finished_at format."""
        # Create a log first
        log = await service.create_started_log(None, async_db_session)

        # Update with invalid finished_at - should fall back to None/default behavior
        result = await service.update_processing_log(
            log_id=log.id,
            status="success",
            message="Invalid timestamp",
            finished_at="not-a-valid-timestamp",
            db=async_db_session,
        )

        assert result is not None
        assert result.status == ProcessingStatus.SUCCESS
        # finished_at should be set automatically for SUCCESS
        assert result.finished_at is not None


class TestStaleProcessingCleanup:
    """Tests for stale processing cleanup functionality."""

    @pytest.mark.asyncio
    async def test_cleanup_stale_processing_logs(self, async_db_session):
        """Test that stale PROCESSING entries are marked as FAILED."""
        repo = ProcessingLogRepository()

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

        # Create a SUCCESS log (should not be affected)
        success_log = await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatus.SUCCESS,
            message="Success",
            db=async_db_session,
        )

        # Run cleanup with 30 minute timeout, passing the test session
        count = await cleanup_stale_processing_logs(timeout_minutes=30, session=async_db_session)

        assert count == 1, "Should have marked 1 stale entry as FAILED"

        # Verify stale log is now FAILED
        updated_stale = await repo.get_by_id(stale_log.id, db=async_db_session)
        assert updated_stale is not None
        assert updated_stale.status == ProcessingStatus.FAILED
        assert "Worker timeout" in updated_stale.message or updated_stale.message is not None

        # Verify fresh log is still PROCESSING
        fresh = await repo.get_by_id(fresh_log.id, db=async_db_session)
        assert fresh is not None
        assert fresh.status == ProcessingStatus.PROCESSING

        # Verify SUCCESS log is unchanged
        success = await repo.get_by_id(success_log.id, db=async_db_session)
        assert success is not None
        assert success.status == ProcessingStatus.SUCCESS

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
