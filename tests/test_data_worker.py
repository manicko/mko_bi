"""Tests for data worker background functions."""
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from mkobi.models.enums import ProcessingStatus
from mkobi.workers.data_worker import (
    _update_processing_log_status,
    cleanup_stale_processing_logs,
)


@pytest.mark.asyncio
class TestDataWorker:
    """Tests for data worker background functions."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    # --- _update_processing_log_status tests ---

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

    async def test_update_processing_log_status_completed(
        self, mock_session
    ):
        """Test updating status to COMPLETED sets finished_at."""
        task_id = str(uuid4())
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        await _update_processing_log_status(
            task_id=task_id,
            status=ProcessingStatus.COMPLETED,
            message="Processing completed",
            session=mock_session,
        )

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_update_processing_log_status_failed(
        self, mock_session
    ):
        """Test updating status to FAILED sets finished_at."""
        task_id = str(uuid4())
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        await _update_processing_log_status(
            task_id=task_id,
            status=ProcessingStatus.FAILED,
            message="Processing failed",
            session=mock_session,
        )

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_update_processing_log_status_with_provided_finished_at(
        self, mock_session
    ):
        """Test finished_at can be explicitly provided."""
        task_id = str(uuid4())
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        explicit_time = datetime(2024, 1, 1, 12, 0, 0)
        await _update_processing_log_status(
            task_id=task_id,
            status=ProcessingStatus.COMPLETED,
            message="Done",
            finished_at=explicit_time,
            session=mock_session,
        )

        mock_session.execute.assert_called_once()

    # --- cleanup_stale_processing_logs tests ---

    async def test_cleanup_stale_processing_logs_finds_stale_entries(
        self, mock_session
    ):
        """Test cleanup finds and marks stale PROCESSING entries."""
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_session.execute.return_value = mock_result

        count = await cleanup_stale_processing_logs(
            timeout_minutes=30,
            session=mock_session,
        )

        assert count == 3
        mock_session.execute.assert_called_once()

    async def test_cleanup_stale_processing_logs_no_entries(
        self, mock_session
    ):
        """Test cleanup returns 0 when no stale entries found."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        count = await cleanup_stale_processing_logs(session=mock_session)

        assert count == 0

    async def test_cleanup_stale_processing_logs_custom_timeout(
        self, mock_session
    ):
        """Test cleanup with custom timeout value."""
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_session.execute.return_value = mock_result

        count = await cleanup_stale_processing_logs(
            timeout_minutes=60,
            session=mock_session,
        )

        assert count == 5