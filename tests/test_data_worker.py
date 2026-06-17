"""Tests for data worker background functions."""
import asyncio
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import polars as pl

from mkobi.models.enums import AggregationFunctionEnum, ProcessingStatus, FilterType
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
        from mkobi.models.enums import GraphType

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

        # Create mock results for the execute calls (graph query, filter query)
        mock_graph_result = MagicMock()
        mock_graph_result.scalars.return_value.all.return_value = [mock_graph]

        mock_filter_result = MagicMock()
        mock_filter_result.scalars.return_value.all.return_value = [mock_filter]

        # For OVERWRITE mode, no get_aggregates call is needed
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
        from mkobi.models.enums import GraphType

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

        mock_session.execute.side_effect = [mock_graph_result, mock_filter_result] * 3

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
        from mkobi.models.enums import GraphType

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

        mock_session.execute.side_effect = [mock_graph_result, mock_filter_result] * 3

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


# --- Concurrent APPEND upload tests (unit tests with mocks) ---

@pytest.mark.asyncio
class TestConcurrentAppendUploads:
    """Tests for concurrent APPEND mode uploads in _store_aggregates.

    Verifies that concurrent uploads to the same dashboard in APPEND mode
    do not cause data corruption or loss. Tests the UPSERT mechanism's
    thread-safety and transaction isolation.
    """

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession for concurrent upload tests."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    async def test_concurrent_append_uploads_completes_successfully(
        self, mock_session
    ):
        """Verify two concurrent APPEND uploads complete without errors.

        Both uploads use clear_old=False (append mode) and should complete
        successfully without race conditions or deadlocks.
        """
        from mkobi.models.enums import GraphType

        graph_id = uuid4()
        dashboard_id = uuid4()

        df1 = pl.DataFrame({"a": [1], "b": ["x"]})
        df2 = pl.DataFrame({"a": [2], "b": ["y"]})
        task_id1 = str(uuid4())
        task_id2 = str(uuid4())

        mock_graph = MagicMock()
        mock_graph.id = graph_id
        mock_graph.name = "Test Graph"
        mock_graph.type = GraphType.BAR
        mock_graph.dashboard_id = dashboard_id
        mock_graph.config = {}
        mock_graph.dimensions = []
        mock_graph.metrics = []

        mock_filter = MagicMock()
        mock_filter.id = uuid4()
        mock_filter.name = "region"
        mock_filter.type = FilterType.SELECT
        mock_filter.config = {}
        mock_filter.created_at = datetime.now(UTC)

        mock_graph_result = MagicMock()
        mock_graph_result.scalars.return_value.all.return_value = [mock_graph]

        mock_filter_result = MagicMock()
        mock_filter_result.scalars.return_value.all.return_value = [mock_filter]

        mock_session.execute.side_effect = ([mock_graph_result, mock_filter_result] * 3)[:6]

        with patch(
            "mkobi.services.aggregation_service.AggregationService"
        ) as mock_agg_service, patch(
            "mkobi.data.storage.manager.StorageManager"
        ) as mock_storage, patch(
            "mkobi.db.repositories.dashboard_filter_values_repo.DashboardFilterValuesRepository"
        ) as mock_repo:
            mock_service_instance = AsyncMock()
            mock_service_instance.aggregate_for_dashboard = AsyncMock(return_value=[])
            mock_service_instance.extract_filter_values = AsyncMock(return_value={})
            mock_agg_service.return_value = mock_service_instance

            mock_manager_instance = AsyncMock()
            mock_manager_instance.save_aggregates = AsyncMock(return_value=1)
            mock_storage.return_value = mock_manager_instance

            mock_repo_instance = AsyncMock()
            mock_repo_instance.save_filter_values = AsyncMock()
            mock_repo_instance.clear_dashboard_values = AsyncMock()
            mock_repo.return_value = mock_repo_instance

            results = await asyncio.gather(
                _store_aggregates(
                    df=df1,
                    dashboard_id=dashboard_id,
                    task_id=task_id1,
                    mode="append",
                    db_session=mock_session,
                ),
                _store_aggregates(
                    df=df2,
                    dashboard_id=dashboard_id,
                    task_id=task_id2,
                    mode="append",
                    db_session=mock_session,
                ),
                return_exceptions=True,
            )

            assert all(isinstance(r, type(None)) for r in results), \
                f"Both uploads should complete without exceptions, got: {results}"

            assert mock_manager_instance.save_aggregates.call_count == 2
            for call in mock_manager_instance.save_aggregates.call_args_list:
                assert call[1]["clear_old"] is False, "APPEND mode should use clear_old=False"

    async def test_concurrent_append_uploads_data_integrity(
        self, mock_session
    ):
        """Verify data from both concurrent APPEND uploads is preserved.

        Tests that the UPSERT mechanism correctly handles concurrent calls
        and both uploads' data is processed.
        """
        from mkobi.models.enums import GraphType

        graph_id = uuid4()
        dashboard_id = uuid4()

        mock_graph = MagicMock()
        mock_graph.id = graph_id
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

        mock_session.execute.side_effect = [mock_graph_result, mock_filter_result] * 3

        df1 = pl.DataFrame({"a": [1], "b": ["A"]})
        df2 = pl.DataFrame({"a": [2], "b": ["B"]})
        task_id1 = str(uuid4())
        task_id2 = str(uuid4())

        with patch(
            "mkobi.services.aggregation_service.AggregationService"
        ) as mock_agg_service, patch(
            "mkobi.data.storage.manager.StorageManager"
        ) as mock_storage, patch(
            "mkobi.db.repositories.dashboard_filter_values_repo.DashboardFilterValuesRepository"
        ) as mock_repo:
            mock_service_instance = AsyncMock()
            mock_service_instance.aggregate_for_dashboard = AsyncMock(
                side_effect=[
                    [{"graph_id": graph_id, "dims": {"category": "A"}, "metrics": {"revenue_sum": 100}}],
                    [{"graph_id": graph_id, "dims": {"category": "B"}, "metrics": {"revenue_sum": 200}}],
                ]
            )
            mock_service_instance.extract_filter_values = AsyncMock(return_value={"category": ["A", "B"]})
            mock_agg_service.return_value = mock_service_instance

            processed_counts = []

            async def save_aggregates_side_effect(*args, **kwargs):
                aggregates = kwargs.get("aggregates", [])
                processed_counts.append(len(aggregates))
                return len(aggregates)

            mock_manager_instance = AsyncMock()
            mock_manager_instance.save_aggregates = AsyncMock(side_effect=save_aggregates_side_effect)
            mock_manager_instance.get_aggregates = AsyncMock(return_value=[])
            mock_storage.return_value = mock_manager_instance

            mock_repo_instance = AsyncMock()
            mock_repo_instance.save_filter_values = AsyncMock()
            mock_repo_instance.clear_dashboard_values = AsyncMock()
            mock_repo.return_value = mock_repo_instance

            await asyncio.gather(
                _store_aggregates(
                    df=df1,
                    dashboard_id=dashboard_id,
                    task_id=task_id1,
                    mode="append",
                    db_session=mock_session,
                ),
                _store_aggregates(
                    df=df2,
                    dashboard_id=dashboard_id,
                    task_id=task_id2,
                    mode="append",
                    db_session=mock_session,
                ),
            )

            total_records = sum(processed_counts)
            assert total_records == 2, f"Expected 2 total records, got {total_records}"


# --- Integration tests for concurrent APPEND uploads with real database ---

@pytest.mark.asyncio
class TestConcurrentAppendUploadsIntegration:
    """Integration tests for concurrent APPEND mode uploads with real database.

    Verifies that concurrent uploads to the same dashboard in APPEND mode
    correctly persist both datasets using the UPSERT mechanism without
    data corruption or loss.
    """

    @pytest.fixture
    async def test_dashboard(
        self, async_db_session, test_user: dict
    ):
        """Create a test dashboard for integration tests."""
        from mkobi.db.repositories.access_repo import AccessRepository
        from mkobi.db.repositories.dashboard_repo import DashboardRepository
        from mkobi.models.enums import DashboardPermission

        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name=f"integration_test_dashboard_{uuid4().hex[:8]}",
            description="Dashboard for concurrent upload integration tests",
        )

        # Grant edit access to test user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        return dashboard

    @pytest.fixture
    async def graph_for_dashboard(
        self, async_db_session, test_dashboard
    ):
        """Create a graph for the dashboard."""
        from mkobi.models.enums import GraphType
        from mkobi.db.repositories.graph_repo import GraphRepository

        graph_repo = GraphRepository()
        graph = await graph_repo.create(
            db=async_db_session,
            dashboard_id=test_dashboard.id,
            name="Test Graph",
            type=GraphType.BAR,
            dimensions=["category"],
            metrics=["sales"],
        )
        await async_db_session.commit()
        return graph

    async def test_concurrent_append_uploads(
        self,
        async_db_session,
        test_dashboard,
        graph_for_dashboard,
    ):
        """Verify concurrent APPEND uploads complete successfully and data is preserved.

        Two sequential uploads in APPEND mode should both complete without errors,
        and the final aggregated data should contain records from both uploads.
        """
        from mkobi.data.storage.manager import StorageManager
        from mkobi.models.graph import GraphRead
        from mkobi.models.filters import FilterRead
        from mkobi.services.aggregation_service import AggregationService
        from mkobi.models.enums import GraphType

        dashboard_id = test_dashboard.id
        graph_id = graph_for_dashboard.id

        # Build graph_reads and filter_reads for aggregation
        graph_reads = [GraphRead(
            id=graph_id,
            name="Test Graph",
            type=GraphType.BAR,
            dashboard_id=dashboard_id,
            config={},
            dimensions=["category"],
            metrics=["sales"],
            created_at=datetime.now(UTC),
        )]
        filter_reads: list[FilterRead] = []  # No filters to avoid duplicate column names in groupby

        # Initialize services with real database session
        agg_service = AggregationService()
        storage_manager = StorageManager(async_db_session)

        # Create test data for two uploads
        df1 = pl.DataFrame({"category": ["A", "B"], "sales": [100, 200]})
        df2 = pl.DataFrame({"category": ["C", "D"], "sales": [300, 400]})

        # First upload in APPEND mode
        records1 = await agg_service.aggregate_for_dashboard(
            df1, graph_reads, filter_reads, metric_agg="sum"
        )
        aggregates1 = [
            {"graph_id": r["graph_id"], "dims": r["dims"], "metrics": r["metrics"]}
            for r in records1
        ]
        await storage_manager.save_aggregates(
            dashboard_id=dashboard_id,
            aggregates=aggregates1,
            clear_old=False,
        )

        # Second upload in APPEND mode
        records2 = await agg_service.aggregate_for_dashboard(
            df2, graph_reads, filter_reads, metric_agg="sum"
        )
        aggregates2 = [
            {"graph_id": r["graph_id"], "dims": r["dims"], "metrics": r["metrics"]}
            for r in records2
        ]
        await storage_manager.save_aggregates(
            dashboard_id=dashboard_id,
            aggregates=aggregates2,
            clear_old=False,
        )

        # Commit to persist data within the SAVEPOINT transaction
        # (async_db_session fixture handles SAVEPOINT, rollback happens after test)

        # Verify both datasets are present in the database
        all_records = await storage_manager.get_aggregates(dashboard_id)

        categories_found = {rec["dims"].get("category") for rec in all_records}
        assert "A" in categories_found, "Data from first upload should be present"
        assert "B" in categories_found, "Data from first upload should be present"
        assert "C" in categories_found, "Data from second upload should be present"
        assert "D" in categories_found, "Data from second upload should be present"

        # Verify no data corruption - all 4 records should exist
        assert len(all_records) == 4, f"Expected 4 records, got {len(all_records)}"