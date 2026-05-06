"""Tests for processing logs functionality."""

import pytest
from uuid import uuid4
from datetime import datetime

from mkobi.models.enums import ProcessingStatusEnum
from mkobi.models.processing_logs import ProcessingLogFilter, ProcessingLogRead, ProcessingLogCreate
from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository
from mkobi.services.processing_log_service import ProcessingLogService


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
            status=ProcessingStatusEnum.STARTED,
            skip=10,
            limit=50,
        )
        assert filter_obj.dashboard_id == dashboard_id
        assert filter_obj.status == ProcessingStatusEnum.STARTED
        assert filter_obj.skip == 10
        assert filter_obj.limit == 50


class TestProcessingLogModels:
    """Tests for ProcessingLog models."""

    def test_create_model(self):
        """Test ProcessingLogCreate model."""
        create_obj = ProcessingLogCreate(
            status=ProcessingStatusEnum.STARTED,
            message="Test message",
        )
        assert create_obj.dashboard_id is None
        assert create_obj.status == ProcessingStatusEnum.STARTED
        assert create_obj.message == "Test message"

    def test_read_model(self):
        """Test ProcessingLogRead model."""
        log_id = uuid4()
        read_obj = ProcessingLogRead(
            id=log_id,
            status=ProcessingStatusEnum.SUCCESS,
            message="Success",
            started_at=datetime.now(),
            finished_at=datetime.now(),
        )
        assert read_obj.id == log_id
        assert read_obj.status == ProcessingStatusEnum.SUCCESS


class TestProcessingLogRepository:
    """Tests for ProcessingLogRepository."""

    @pytest.mark.asyncio
    async def test_create_log(self, async_db_session):
        """Test creating a log entry."""
        repo = ProcessingLogRepository(async_db_session)

        log = await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatusEnum.STARTED,
            message="Test log",
        )

        assert log.dashboard_id is None
        assert log.status == ProcessingStatusEnum.STARTED
        assert log.message == "Test log"
        assert log.started_at is not None

    @pytest.mark.asyncio
    async def test_update_status(self, async_db_session):
        """Test updating log status."""
        repo = ProcessingLogRepository(async_db_session)

        log = await repo.create_log(
            dashboard_id=None,
            status=ProcessingStatusEnum.STARTED,
        )

        await repo.update_status(
            log_id=log.id,
            status=ProcessingStatusEnum.SUCCESS,
            message="Completed",
        )

        # Verify update
        updated = await repo.get_by_id(log.id)
        assert updated is not None
        assert updated.status == ProcessingStatusEnum.SUCCESS
        assert updated.message == "Completed"
        assert updated.finished_at is not None

    @pytest.mark.asyncio
    async def test_get_by_dashboard(self, async_db_session):
        """Test getting logs by dashboard."""
        repo = ProcessingLogRepository(async_db_session)

        # Create multiple logs with None dashboard_id
        await repo.create_log(None, ProcessingStatusEnum.STARTED)
        await repo.create_log(None, ProcessingStatusEnum.SUCCESS)

        logs = await repo.get_by_dashboard(None)
        assert len(logs) == 2

    @pytest.mark.asyncio
    async def test_get_filtered(self, async_db_session):
        """Test filtered log retrieval."""
        repo = ProcessingLogRepository(async_db_session)

        await repo.create_log(None, ProcessingStatusEnum.STARTED)
        await repo.create_log(None, ProcessingStatusEnum.SUCCESS)

        filters = ProcessingLogFilter(
            status=ProcessingStatusEnum.SUCCESS,
        )

        logs = await repo.get_filtered(filters)
        assert len(logs) == 1
        assert logs[0].status == ProcessingStatusEnum.SUCCESS


class TestProcessingLogService:
    """Tests for ProcessingLogService."""

    @pytest.mark.asyncio
    async def test_create_started_log(self, async_db_session):
        """Test creating started log via service."""
        result = await ProcessingLogService.create_started_log(None, async_db_session)

        assert isinstance(result, ProcessingLogRead)
        assert result.dashboard_id is None
        assert result.status == ProcessingStatusEnum.STARTED

    @pytest.mark.asyncio
    async def test_update_to_success(self, async_db_session):
        """Test updating log to success."""
        # First create a log
        log = await ProcessingLogService.create_started_log(None, async_db_session)

        # Update to success
        result = await ProcessingLogService.update_to_success(
            log.id, "All good", async_db_session
        )

        assert result is not None
        assert result.status == ProcessingStatusEnum.SUCCESS
        assert result.message == "All good"

    @pytest.mark.asyncio
    async def test_update_to_failed(self, async_db_session):
        """Test updating log to failed."""
        # First create a log
        log = await ProcessingLogService.create_started_log(None, async_db_session)

        # Update to failed
        result = await ProcessingLogService.update_to_failed(
            log.id, "Error occurred", async_db_session
        )

        assert result is not None
        assert result.status == ProcessingStatusEnum.FAILED
        assert result.message == "Error occurred"

    @pytest.mark.asyncio
    async def test_get_filtered(self, async_db_session):
        """Test getting filtered logs via service."""
        # Create logs
        log1 = await ProcessingLogService.create_started_log(None, async_db_session)
        await ProcessingLogService.update_to_success(
            log1.id,
            "Done",
            async_db_session,
        )
        await ProcessingLogService.create_started_log(None, async_db_session)

        filters = ProcessingLogFilter(
            status=ProcessingStatusEnum.SUCCESS,
        )

        logs = await ProcessingLogService.get_filtered(filters, async_db_session)
        assert len(logs) == 1
        assert logs[0].status == ProcessingStatusEnum.SUCCESS
