"""Tests for data worker background functions."""
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import polars as pl

from mkobi.models.enums import AggregationFunctionEnum, ProcessingStatus
from mkobi.models.data import ProcessingConfig
from mkobi.utils.exceptions import AppException, ErrorCode
from mkobi.workers.data_worker import (
    _update_processing_log_status,
    cleanup_stale_processing_logs,
    mark_orphaned_uploaded_logs_failed,
    _store_aggregates,
    _validate_processing_config,
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
        """Test updating status to COMPLETED sets finished_at.

        In test mode (session provided), no commit happens - caller manages transaction.
        """
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
        # No commit in test mode - caller (SAVEPOINT) manages transaction
        mock_session.commit.assert_not_called()

    async def test_update_processing_log_status_failed(
        self, mock_session
    ):
        """Test updating status to FAILED sets finished_at.

        In test mode (session provided), no commit happens - caller manages transaction.
        """
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
        # No commit in test mode - caller (SAVEPOINT) manages transaction
        mock_session.commit.assert_not_called()

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

    # --- mark_orphaned_uploaded_logs_failed tests ---

    async def test_mark_orphaned_uploaded_logs_failed_finds_orphaned(
        self, mock_session
    ):
        """Test marking orphaned UPLOADED entries as FAILED."""
        mock_result = MagicMock()
        mock_result.rowcount = 2
        mock_session.execute.return_value = mock_result

        count = await mark_orphaned_uploaded_logs_failed(session=mock_session)

        assert count == 2
        mock_session.execute.assert_called_once()

    async def test_mark_orphaned_uploaded_logs_failed_no_entries(
        self, mock_session
    ):
        """Test marking returns 0 when no orphaned entries found."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        count = await mark_orphaned_uploaded_logs_failed(session=mock_session)

        assert count == 0


# --- _validate_processing_config tests ---


class TestValidateProcessingConfig:
    """Tests for _validate_processing_config function.

    Note: Pydantic models already validate required fields. These tests focus on
    custom validation for empty string values that pass Pydantic but are invalid
    for processing logic.
    """

    def test_valid_config_no_fields(self):
        """Test that config with no optional fields passes validation."""
        config = ProcessingConfig()
        _validate_processing_config(config)  # Should not raise

    def test_valid_config_with_valid_fields(self):
        """Test that config with valid fields passes validation."""
        config = ProcessingConfig(
            groupby=["category", "region"],
            sort_by=["year"],
            aggregations=[
                {"column": "revenue", "function": AggregationFunctionEnum.SUM},
            ],
            yoy_config={"year_column": "year", "value_column": "revenue_sum"},
            share_config={"value_column": "revenue_sum"},
            custom_metrics=[{"name": "profit", "expr": "revenue - cost"}],
        )
        _validate_processing_config(config)  # Should not raise

    def test_valid_config_with_dict_aggregations(self):
        """Test that config with dict-style aggregations passes validation."""
        config = ProcessingConfig(
            aggregations=[
                {"column": "revenue", "function": AggregationFunctionEnum.SUM},
            ],
        )
        _validate_processing_config(config)  # Should not raise

    def test_invalid_groupby_empty_string(self):
        """Test that groupby with empty string raises error."""
        config = ProcessingConfig(
            groupby=["category", ""],
        )
        with pytest.raises(AppException) as exc_info:
            _validate_processing_config(config)
        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR
        assert "groupby" in exc_info.value.detail.lower()

    def test_invalid_sort_by_empty_string(self):
        """Test that sort_by with empty string raises error."""
        config = ProcessingConfig(
            sort_by=["year", ""],
        )
        with pytest.raises(AppException) as exc_info:
            _validate_processing_config(config)
        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR
        assert "sort_by" in exc_info.value.detail.lower()

    def test_valid_metrics(self):
        """Test that metrics with valid entries passes validation."""
        config = ProcessingConfig(
            metrics=[{"name": "revenue", "type": "sum"}],
        )
        _validate_processing_config(config)  # Should not raise

    def test_invalid_metrics_empty_value(self):
        """Test that metrics with empty values raises error."""
        config = ProcessingConfig(
            metrics=[{"name": "", "type": "sum"}],
        )
        with pytest.raises(AppException) as exc_info:
            _validate_processing_config(config)
        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR


# --- _store_aggregates tests ---

@pytest.mark.asyncio
class TestStoreAggregates:
    """Tests for _store_aggregates function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    async def test_store_aggregates_no_graphs(
        self, mock_session
    ):
        """Test _store_aggregates returns early when no graphs found."""
        df = pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        dashboard_id = uuid4()
        task_id = str(uuid4())

        # Mock result with no graphs
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await _store_aggregates(
            df=df,
            dashboard_id=dashboard_id,
            task_id=task_id,
            mode="overwrite",
            db_session=mock_session,
        )

        mock_session.execute.assert_called()

    async def test_store_aggregates_with_graphs(
        self, mock_session
    ):
        """Test _store_aggregates processes data when graphs exist."""
        from mkobi.models.enums import GraphType, FilterType

        df = pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        dashboard_id = uuid4()
        task_id = str(uuid4())

        # Create mock Graph with valid type
        mock_graph = MagicMock()
        mock_graph.id = uuid4()
        mock_graph.name = "Test Graph"
        mock_graph.type = GraphType.BAR
        mock_graph.dashboard_id = dashboard_id
        mock_graph.config = {}
        mock_graph.dimensions = []
        mock_graph.metrics = []

        # Create mock Filter with valid type
        mock_filter = MagicMock()
        mock_filter.id = uuid4()
        mock_filter.name = "Test Filter"
        mock_filter.type = FilterType.SELECT
        mock_filter.config = {}
        mock_filter.created_at = datetime.now(UTC)

        # Create two mock results for the two execute calls (graph query, filter query)
        mock_graph_result = MagicMock()
        mock_graph_result.scalars.return_value.all.return_value = [mock_graph]

        mock_filter_result = MagicMock()
        mock_filter_result.scalars.return_value.all.return_value = [mock_filter]

        mock_session.execute.side_effect = [mock_graph_result, mock_filter_result]

        # Patch the classes that are imported inside the function
        with patch(
            "mkobi.services.aggregation_service.AggregationService"
        ) as mock_agg_service, patch(
            "mkobi.data.storage.manager.StorageManager"
        ) as mock_storage, patch(
            "mkobi.db.repositories.dashboard_filter_values_repo.DashboardFilterValuesRepository"
        ) as mock_repo:
            mock_service_instance = AsyncMock()
            mock_service_instance.aggregate_for_dashboard = AsyncMock(
                return_value=[{"graph_id": mock_graph.id, "dims": {}, "metrics": {}}]
            )
            mock_service_instance.extract_filter_values = AsyncMock(return_value={})
            mock_agg_service.return_value = mock_service_instance

            mock_manager_instance = AsyncMock()
            mock_manager_instance.save_aggregates = AsyncMock(return_value=5)
            mock_storage.return_value = mock_manager_instance

            mock_repo_instance = AsyncMock()
            mock_repo_instance.save_filter_values = AsyncMock()
            mock_repo_instance.clear_dashboard_values = AsyncMock()
            mock_repo.return_value = mock_repo_instance

            await _store_aggregates(
                df=df,
                dashboard_id=dashboard_id,
                task_id=task_id,
                mode="overwrite",
                db_session=mock_session,
            )

            assert mock_session.execute.call_count == 2
            mock_manager_instance.save_aggregates.assert_called_once()

    async def test_store_aggregates_append_mode(
        self, mock_session
    ):
        """Test _store_aggregates uses append mode correctly (clear_old=False).

        Per SPEC.md, filter values are rebuilt on each upload (idempotent overwrite),
        so clear_dashboard_values must be called regardless of mode.
        """
        from mkobi.models.enums import GraphType, FilterType

        df = pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        dashboard_id = uuid4()
        task_id = str(uuid4())

        mock_graph = MagicMock()
        mock_graph.id = uuid4()
        mock_graph.name = "Test Graph"
        mock_graph.type = GraphType.BAR
        mock_graph.dashboard_id = dashboard_id
        mock_graph.config = {}
        mock_graph.dimensions = []
        mock_graph.metrics = []

        mock_filter = MagicMock()
        mock_filter.id = uuid4()
        mock_filter.name = "Test Filter"
        mock_filter.type = FilterType.SELECT
        mock_filter.config = {}
        mock_filter.created_at = datetime.now(UTC)

        mock_graph_result = MagicMock()
        mock_graph_result.scalars.return_value.all.return_value = [mock_graph]

        mock_filter_result = MagicMock()
        mock_filter_result.scalars.return_value.all.return_value = [mock_filter]

        mock_session.execute.side_effect = [mock_graph_result, mock_filter_result]

        with patch(
            "mkobi.services.aggregation_service.AggregationService"
        ) as mock_agg_service, patch(
            "mkobi.data.storage.manager.StorageManager"
        ) as mock_storage, patch(
            "mkobi.db.repositories.dashboard_filter_values_repo.DashboardFilterValuesRepository"
        ) as mock_repo:
            mock_service_instance = AsyncMock()
            mock_service_instance.aggregate_for_dashboard = AsyncMock(
                return_value=[{"graph_id": mock_graph.id, "dims": {}, "metrics": {}}]
            )
            mock_service_instance.extract_filter_values = AsyncMock(return_value={})
            mock_agg_service.return_value = mock_service_instance

            mock_manager_instance = AsyncMock()
            mock_manager_instance.save_aggregates = AsyncMock(return_value=3)
            mock_storage.return_value = mock_manager_instance

            mock_repo_instance = AsyncMock()
            mock_repo_instance.save_filter_values = AsyncMock()
            mock_repo_instance.clear_dashboard_values = AsyncMock()
            mock_repo.return_value = mock_repo_instance

            await _store_aggregates(
                df=df,
                dashboard_id=dashboard_id,
                task_id=task_id,
                mode="append",
                db_session=mock_session,
            )

            # Check that clear_old was False (append mode)
            call_kwargs = mock_manager_instance.save_aggregates.call_args
            assert call_kwargs[1]["clear_old"] is False

            # Verify filter values are cleared in append mode (idempotent rebuild per SPEC.md)
            mock_repo_instance.clear_dashboard_values.assert_called_once()

    async def test_store_aggregates_logs_processed_count(
        self, mock_session
    ):
        """Test _store_aggregates saves filter values when present."""
        from mkobi.models.enums import GraphType, FilterType

        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        dashboard_id = uuid4()
        task_id = str(uuid4())

        mock_graph = MagicMock()
        mock_graph.id = uuid4()
        mock_graph.name = "Test Graph"
        mock_graph.type = GraphType.BAR
        mock_graph.dashboard_id = dashboard_id
        mock_graph.config = {}
        mock_graph.dimensions = []
        mock_graph.metrics = []

        mock_filter = MagicMock()
        mock_filter.id = uuid4()
        mock_filter.name = "Test Filter"
        mock_filter.type = FilterType.SELECT
        mock_filter.config = {}
        mock_filter.created_at = datetime.now(UTC)

        mock_graph_result = MagicMock()
        mock_graph_result.scalars.return_value.all.return_value = [mock_graph]

        mock_filter_result = MagicMock()
        mock_filter_result.scalars.return_value.all.return_value = [mock_filter]

        mock_session.execute.side_effect = [mock_graph_result, mock_filter_result]

        with patch(
            "mkobi.services.aggregation_service.AggregationService"
        ) as mock_agg_service, patch(
            "mkobi.data.storage.manager.StorageManager"
        ) as mock_storage, patch(
            "mkobi.db.repositories.dashboard_filter_values_repo.DashboardFilterValuesRepository"
        ) as mock_repo:
            mock_service_instance = AsyncMock()
            mock_service_instance.aggregate_for_dashboard = AsyncMock(
                return_value=[{"graph_id": mock_graph.id, "dims": {"a": [1]}, "metrics": {"b": 1}}]
            )
            mock_service_instance.extract_filter_values = AsyncMock(
                return_value={"b": ["x", "y"]}
            )
            mock_agg_service.return_value = mock_service_instance

            mock_manager_instance = AsyncMock()
            mock_manager_instance.save_aggregates = AsyncMock(return_value=3)
            mock_storage.return_value = mock_manager_instance

            mock_repo_instance = AsyncMock()
            mock_repo_instance.save_filter_values = AsyncMock()
            mock_repo_instance.clear_dashboard_values = AsyncMock()
            mock_repo.return_value = mock_repo_instance

            await _store_aggregates(
                df=df,
                dashboard_id=dashboard_id,
                task_id=task_id,
                mode="overwrite",
                db_session=mock_session,
            )

            mock_repo_instance.save_filter_values.assert_called_once()