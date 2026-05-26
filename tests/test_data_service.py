"""Unit tests for DataService business logic."""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import tempfile
import gzip
import io

import pytest

from mkobi.models.enums import (
    ProcessingStatus as ProcessingStatusEnum,
    UploadMode,
)
from mkobi.services.data_service import DataService


@pytest.mark.asyncio
class TestDataService:
    """Unit tests for DataService business logic."""

    @pytest.fixture
    def mock_repos(self):
        """Create mocked repositories for DataService."""
        agg_repo = AsyncMock()
        log_repo = AsyncMock()
        graph_repo = AsyncMock()
        return agg_repo, log_repo, graph_repo

    @pytest.fixture
    def data_service(self, mock_repos):
        """Create DataService instance with mocked repositories."""
        agg_repo, log_repo, graph_repo = mock_repos
        return DataService(agg_repo, log_repo, graph_repo)

    # --- process_upload tests ---

    async def test_process_upload_success(self, data_service, mock_repos, mock_db):
        """Test successful file upload and processing."""
        agg_repo, log_repo, graph_repo = mock_repos
        dashboard_id = uuid4()
        csv_content = b"date,category,revenue\n2023-01-01,A,100.5\n"
        log_id = uuid4()
        log_repo.create_log.return_value.id = log_id
        log_repo.create_log.return_value.status = ProcessingStatusEnum.UPLOADED

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            with patch("mkobi.services.file_processing.enqueue_job") as mock_enqueue:
                result = await data_service.process_upload(
                    file_path=tmp_path,
                    dashboard_id=dashboard_id,
                    user_id=uuid4(),
                    filename="test.csv",
                    content_type="text/csv",
                    mode=UploadMode.OVERWRITE,
                    db=mock_db,
                )

        assert result.task_id == log_id
        assert result.status == ProcessingStatusEnum.UPLOADED
        assert result.filename == "test.csv"
        assert result.dashboard_id == dashboard_id
        assert "File uploaded successfully" in result.message
        log_repo.create_log.assert_called_once()
        mock_enqueue.assert_called_once()

    async def test_process_upload_with_user(self, data_service, mock_repos, mock_db):
        """Test upload when user_id is provided and has access."""
        agg_repo, log_repo, graph_repo = mock_repos
        dashboard_id = uuid4()
        user_id = uuid4()
        csv_content = b"name,value\nfoo,1\n"
        log_id = uuid4()
        log_repo.create_log.return_value.id = log_id
        log_repo.create_log.return_value.status = ProcessingStatusEnum.UPLOADED

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            with patch("mkobi.services.file_processing.enqueue_job"):
                result = await data_service.process_upload(
                    file_path=tmp_path,
                    dashboard_id=dashboard_id,
                    user_id=user_id,
                    filename="data.csv",
                    content_type="text/csv",
                    mode=UploadMode.APPEND,
                    db=mock_db,
                )

        assert result.status == ProcessingStatusEnum.UPLOADED

    async def test_process_upload_no_permission(self, data_service, mock_repos, mock_db):
        """Test upload fails when user lacks permission."""
        agg_repo, log_repo, graph_repo = mock_repos
        dashboard_id = uuid4()
        user_id = uuid4()
        csv_content = b"name,value\nfoo,1\n"

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=False):
            from mkobi.core.permissions import PermissionError

            with pytest.raises(PermissionError):
                await data_service.process_upload(
                    file_path=tmp_path,
                    dashboard_id=dashboard_id,
                    user_id=user_id,
                    filename="data.csv",
                    content_type="text/csv",
                    db=mock_db,
                )

    async def test_process_upload_no_user_skips_permission(self, data_service, mock_repos, mock_db):
        """Test upload with no user_id skips permission check."""
        agg_repo, log_repo, graph_repo = mock_repos
        dashboard_id = uuid4()
        csv_content = b"name,value\nfoo,1\n"
        log_id = uuid4()
        log_repo.create_log.return_value.id = log_id
        log_repo.create_log.return_value.status = ProcessingStatusEnum.UPLOADED

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        with patch("mkobi.services.file_processing.enqueue_job"):
            result = await data_service.process_upload(
                file_path=tmp_path,
                dashboard_id=dashboard_id,
                user_id=None,
                filename="data.csv",
                content_type="text/csv",
                db=mock_db,
            )

        assert result.task_id == log_id

    async def test_process_upload_invalid_mime_type(self, data_service, mock_repos, mock_db):
        """Test upload rejects invalid MIME type."""
        dashboard_id = uuid4()

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(b"some data")
            tmp_path = Path(tmp.name)

        with pytest.raises(ValueError, match="Invalid MIME-type"):
            await data_service.process_upload(
                file_path=tmp_path,
                dashboard_id=dashboard_id,
                filename="data.csv",
                content_type="application/octet-stream",
                db=mock_db,
            )

    async def test_process_upload_invalid_extension(self, data_service, mock_repos, mock_db):
        """Test upload rejects invalid file extension."""
        dashboard_id = uuid4()

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"some data")
            tmp_path = Path(tmp.name)

        with pytest.raises(ValueError, match="Invalid file format"):
            await data_service.process_upload(
                file_path=tmp_path,
                dashboard_id=dashboard_id,
                filename="data.txt",
                content_type="text/csv",
                db=mock_db,
            )

    async def test_process_upload_file_too_large(self, data_service, mock_repos, mock_db):
        """Test upload rejects file exceeding size limit."""
        dashboard_id = uuid4()
        # Mock Path.stat().st_size to simulate large file without creating one
        # The validation checks file_path.stat().st_size in validate_file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(b"x")  # Small content - will be mocked
            tmp_path = Path(tmp.name)

        try:
            with patch.object(
                Path, "stat",
                # Mock object with st_size set to 101MB (exceeds 100MB limit)
                return_value=MagicMock(st_size=101 * 1024 * 1024),
            ):
                with pytest.raises(ValueError, match="exceeds maximum size"):
                    await data_service.process_upload(
                        file_path=tmp_path,
                        dashboard_id=dashboard_id,
                        filename="large.csv",
                        content_type="text/csv",
                        db=mock_db,
                    )
        finally:
            tmp_path.unlink(missing_ok=True)

    async def test_process_upload_csv_gz(self, data_service, mock_repos, mock_db):
        """Test upload with gzip compressed CSV."""
        agg_repo, log_repo, graph_repo = mock_repos
        dashboard_id = uuid4()
        csv_content = b"date,category,revenue\n2023-01-01,A,100.5\n"
        log_id = uuid4()
        log_repo.create_log.return_value.id = log_id
        log_repo.create_log.return_value.status = ProcessingStatusEnum.UPLOADED

        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
            gz.write(csv_content)
        gz_content = buf.getvalue()

        with tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False) as tmp:
            tmp.write(gz_content)
            tmp_path = Path(tmp.name)

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            with patch("mkobi.services.file_processing.enqueue_job"):
                result = await data_service.process_upload(
                    file_path=tmp_path,
                    dashboard_id=dashboard_id,
                    user_id=uuid4(),
                    filename="data.csv.gz",
                    content_type="application/gzip",
                    db=mock_db,
                )

        assert result.status == ProcessingStatusEnum.UPLOADED

    # --- get_aggregated_data tests ---

    async def test_get_aggregated_data_success(self, data_service, mock_repos, mock_db):
        """Test successful retrieval of aggregated data."""
        agg_repo, log_repo, graph_repo = mock_repos
        dashboard_id = uuid4()
        graph_id = uuid4()
        mock_record = MagicMock()
        mock_record.dims = {"category": "A"}
        mock_record.metrics = {"revenue": 100.0}
        mock_record.dashboard_id = dashboard_id
        agg_repo.get_by_graph_id.return_value = [mock_record]

        result = await data_service.get_aggregated_data(dashboard_id, graph_id, db=mock_db)

        assert len(result) == 1
        assert result[0]["dashboard_id"] == dashboard_id
        agg_repo.get_by_graph_id.assert_called_once()

    async def test_get_aggregated_data_empty(self, data_service, mock_repos, mock_db):
        """Test aggregated data returns empty list when no data."""
        agg_repo, log_repo, graph_repo = mock_repos
        agg_repo.get_by_graph_id.return_value = []

        result = await data_service.get_aggregated_data(uuid4(), uuid4(), db=mock_db)

        assert result == []

    async def test_get_aggregated_data_with_filters(self, data_service, mock_repos, mock_db):
        """Test aggregated data filters are passed to repository."""
        agg_repo, log_repo, graph_repo = mock_repos
        dashboard_id = uuid4()
        graph_id = uuid4()
        test_filters = {"year": 2023, "category": "Electronics"}
        mock_record = MagicMock()
        mock_record.dims = {"category": "Electronics", "year": 2023}
        mock_record.metrics = {"revenue": 100.0}
        mock_record.dashboard_id = dashboard_id
        agg_repo.get_by_graph_id.return_value = [mock_record]

        result = await data_service.get_aggregated_data(
            dashboard_id, graph_id, db=mock_db, filters=test_filters,
        )

        assert len(result) == 1
        agg_repo.get_by_graph_id.assert_called_once_with(
            graph_id, mock_db, dashboard_id=dashboard_id, filters=test_filters,
        )

    # --- get_available_metrics tests ---

    async def test_get_available_metrics_success(self, data_service, mock_repos, mock_db):
        """Test getting available metrics from graphs."""
        agg_repo, log_repo, graph_repo = mock_repos
        dashboard_id = uuid4()
        mock_graph = MagicMock()
        mock_graph.metrics = ["revenue", "sales", "profit"]
        graph_repo.get_by_dashboard_id.return_value = [mock_graph]

        result = await data_service.get_available_metrics(dashboard_id, db=mock_db)

        assert set(result) == {"revenue", "sales", "profit"}

    async def test_get_available_metrics_no_graphs(self, data_service, mock_repos, mock_db):
        """Test available metrics returns empty when no graphs exist."""
        agg_repo, log_repo, graph_repo = mock_repos
        graph_repo.get_by_dashboard_id.return_value = []

        result = await data_service.get_available_metrics(uuid4(), db=mock_db)

        assert result == []

    # --- get_available_dimensions tests ---

    async def test_get_available_dimensions_success(self, data_service, mock_repos, mock_db):
        """Test getting available dimensions from graphs."""
        agg_repo, log_repo, graph_repo = mock_repos
        dashboard_id = uuid4()
        mock_graph = MagicMock()
        mock_graph.dimensions = ["category", "year"]
        graph_repo.get_by_dashboard_id.return_value = [mock_graph]

        result = await data_service.get_available_dimensions(dashboard_id, db=mock_db)

        assert set(result) == {"category", "year"}

    async def test_get_available_dimensions_multiple_graphs(self, data_service, mock_repos, mock_db):
        """Test dimensions aggregated from multiple graphs."""
        agg_repo, log_repo, graph_repo = mock_repos
        dashboard_id = uuid4()
        graph1 = MagicMock()
        graph1.dimensions = ["category", "year"]
        graph2 = MagicMock()
        graph2.dimensions = ["region", "year"]
        graph_repo.get_by_dashboard_id.return_value = [graph1, graph2]

        result = await data_service.get_available_dimensions(dashboard_id, db=mock_db)

        assert set(result) == {"category", "year", "region"}

    # --- trigger_processing tests ---

    async def test_trigger_processing_success(self, data_service, mock_repos, mock_db):
        """Test successful processing trigger."""
        agg_repo, log_repo, graph_repo = mock_repos
        task_id = uuid4()
        dashboard_id = uuid4()
        user_id = uuid4()
        mock_log = MagicMock()
        mock_log.status = ProcessingStatusEnum.UPLOADED
        mock_log.message = "test.csv"
        mock_log.dashboard_id = dashboard_id
        log_repo.get_by_id.return_value = mock_log

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            with patch("mkobi.services.data_service.enqueue_processing_job"):
                with patch("mkobi.services.data_service.find_task_file", return_value="/tmp/test.csv"):
                    result = await data_service.trigger_processing(task_id, dashboard_id, user_id, db=mock_db)

        assert result.task_id == task_id
        assert result.status == ProcessingStatusEnum.PROCESSING
        log_repo.update_status.assert_called_once()

    async def test_trigger_processing_no_permission(self, data_service, mock_repos, mock_db):
        """Test trigger processing fails without permission."""
        agg_repo, log_repo, graph_repo = mock_repos
        task_id = uuid4()
        dashboard_id = uuid4()
        user_id = uuid4()
        mock_log = MagicMock()
        mock_log.dashboard_id = dashboard_id
        log_repo.get_by_id.return_value = mock_log

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=False):
            from mkobi.core.permissions import PermissionError

            with pytest.raises(PermissionError):
                await data_service.trigger_processing(task_id, dashboard_id, user_id, db=mock_db)

    async def test_trigger_processing_task_not_found(self, data_service, mock_repos, mock_db):
        """Test trigger processing raises error for unknown task."""
        agg_repo, log_repo, graph_repo = mock_repos
        log_repo.get_by_id.return_value = None

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            with pytest.raises(ValueError, match="Processing task.*not found"):
                await data_service.trigger_processing(uuid4(), uuid4(), uuid4(), db=mock_db)

    async def test_trigger_processing_file_not_found(self, data_service, mock_repos, mock_db):
        """Test trigger processing raises error when file is missing."""
        agg_repo, log_repo, graph_repo = mock_repos
        task_id = uuid4()
        dashboard_id = uuid4()
        user_id = uuid4()
        mock_log = MagicMock()
        mock_log.dashboard_id = dashboard_id
        log_repo.get_by_id.return_value = mock_log

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            with patch("mkobi.services.data_service.find_task_file", side_effect=ValueError("File for task.*not found")):
                with pytest.raises(ValueError, match="File for task.*not found"):
                    await data_service.trigger_processing(task_id, dashboard_id, user_id, db=mock_db)

    # --- get_processing_status tests ---

    async def test_get_processing_status_success(self, data_service, mock_repos, mock_db):
        """Test getting processing status for an active task."""
        agg_repo, log_repo, graph_repo = mock_repos
        task_id = uuid4()
        user_id = uuid4()
        mock_log = MagicMock()
        mock_log.status = ProcessingStatusEnum.PROCESSING
        mock_log.message = "Processing data"
        mock_log.dashboard_id = uuid4()
        log_repo.get_by_id.return_value = mock_log

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            result = await data_service.get_processing_status(task_id, user_id, db=mock_db)

        assert result.task_id == task_id
        assert result.status == ProcessingStatusEnum.PROCESSING
        assert result.progress == 50

    async def test_get_processing_status_no_permission(self, data_service, mock_repos, mock_db):
        """Test processing status fails without permission."""
        agg_repo, log_repo, graph_repo = mock_repos
        mock_log = MagicMock()
        log_repo.get_by_id.return_value = mock_log

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=False):
            from mkobi.core.permissions import PermissionError

            with pytest.raises(PermissionError):
                await data_service.get_processing_status(uuid4(), uuid4(), db=mock_db)

    async def test_get_processing_status_task_not_found(self, data_service, mock_repos, mock_db):
        """Test processing status for non-existent task."""
        agg_repo, log_repo, graph_repo = mock_repos
        log_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Processing task.*not found"):
            await data_service.get_processing_status(uuid4(), uuid4(), db=mock_db)

    async def test_get_processing_status_completed(self, data_service, mock_repos, mock_db):
        """Test processing status for completed task shows 100%."""
        agg_repo, log_repo, graph_repo = mock_repos
        task_id = uuid4()
        user_id = uuid4()
        mock_log = MagicMock()
        mock_log.status = ProcessingStatusEnum.SUCCESS
        mock_log.message = "completed"
        mock_log.dashboard_id = uuid4()
        log_repo.get_by_id.return_value = mock_log

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            result = await data_service.get_processing_status(task_id, user_id, db=mock_db)

        assert result.progress == 100

    async def test_get_processing_status_failed(self, data_service, mock_repos, mock_db):
        """Test processing status for failed task shows 0%."""
        agg_repo, log_repo, graph_repo = mock_repos
        task_id = uuid4()
        user_id = uuid4()
        mock_log = MagicMock()
        mock_log.status = ProcessingStatusEnum.FAILED
        mock_log.message = "failed"
        mock_log.dashboard_id = uuid4()
        log_repo.get_by_id.return_value = mock_log

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            result = await data_service.get_processing_status(task_id, user_id, db=mock_db)

        assert result.progress == 0

    # --- get_processing_result tests ---

    async def test_get_processing_result_success(self, data_service, mock_repos, mock_db):
        """Test getting processing result for completed task."""
        agg_repo, log_repo, graph_repo = mock_repos
        task_id = uuid4()
        user_id = uuid4()
        dashboard_id = uuid4()
        mock_log = MagicMock()
        mock_log.status = ProcessingStatusEnum.SUCCESS
        mock_log.dashboard_id = dashboard_id
        log_repo.get_by_id.return_value = mock_log
        mock_record = MagicMock()
        agg_repo.get_by_graph_id.return_value = [mock_record]
        mock_graph = MagicMock()
        graph_repo.get_by_dashboard_id.return_value = [mock_graph]

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            result = await data_service.get_processing_result(task_id, user_id, db=mock_db)

        assert result.success is True
        assert result.rows_processed == 1

    async def test_get_processing_result_not_complete(self, data_service, mock_repos, mock_db):
        """Test processing result returns not-success for incomplete task."""
        agg_repo, log_repo, graph_repo = mock_repos
        task_id = uuid4()
        user_id = uuid4()
        mock_log = MagicMock()
        mock_log.status = ProcessingStatusEnum.PROCESSING
        mock_log.dashboard_id = uuid4()
        log_repo.get_by_id.return_value = mock_log

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            result = await data_service.get_processing_result(task_id, user_id, db=mock_db)

        assert result.success is False
        assert "Processing not complete" in result.message

    async def test_get_processing_result_no_permission(self, data_service, mock_repos, mock_db):
        """Test processing result fails without permission."""
        agg_repo, log_repo, graph_repo = mock_repos
        mock_log = MagicMock()
        log_repo.get_by_id.return_value = mock_log

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=False):
            from mkobi.core.permissions import PermissionError

            with pytest.raises(PermissionError):
                await data_service.get_processing_result(uuid4(), uuid4(), db=mock_db)

    async def test_get_processing_result_task_not_found(self, data_service, mock_repos, mock_db):
        """Test processing result raises error for unknown task."""
        agg_repo, log_repo, graph_repo = mock_repos
        log_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Processing task.*not found"):
            await data_service.get_processing_result(uuid4(), uuid4(), db=mock_db)

    async def test_get_processing_result_no_graphs(self, data_service, mock_repos, mock_db):
        """Test processing result when dashboard has no graphs."""
        agg_repo, log_repo, graph_repo = mock_repos
        task_id = uuid4()
        user_id = uuid4()
        mock_log = MagicMock()
        mock_log.status = ProcessingStatusEnum.SUCCESS
        mock_log.message = "done"
        mock_log.dashboard_id = uuid4()
        log_repo.get_by_id.return_value = mock_log
        graph_repo.get_by_dashboard_id.return_value = []

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            result = await data_service.get_processing_result(task_id, user_id, db=mock_db)

        assert result.success is True
        assert result.rows_processed == 0

    # --- validate_file tests ---

    async def test_validate_file_mime_skip(self, data_service):
        """Test MIME validation skips when content_type is None."""
        from mkobi.services.file_processing import validate_file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(b"data")
            tmp_path = Path(tmp.name)
        validate_file(file_path=tmp_path, filename="test.csv", content_type=None, max_file_size=data_service._max_file_size)

    async def test_validate_file_valid_csv(self, data_service):
        """Test validation passes for valid CSV file."""
        from mkobi.services.file_processing import validate_file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(b"name,value\ntest,1\n" * 10)
            tmp_path = Path(tmp.name)
        validate_file(
            file_path=tmp_path,
            filename="test.csv",
            content_type="text/csv",
            max_file_size=data_service._max_file_size,
        )

    async def test_validate_file_valid_gz(self, data_service):
        """Test validation passes for valid .csv.gz file."""
        from mkobi.services.file_processing import validate_file
        with tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False) as tmp:
            tmp.write(b"compressed data")
            tmp_path = Path(tmp.name)
        validate_file(
            file_path=tmp_path,
            filename="test.csv.gz",
            content_type="application/gzip",
            max_file_size=data_service._max_file_size,
        )

    async def test_validate_file_invalid_extension(self, data_service):
        """Test validation rejects .txt extension."""
        from mkobi.services.file_processing import validate_file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"some text")
            tmp_path = Path(tmp.name)
        with pytest.raises(ValueError, match="Invalid file format"):
            validate_file(
                file_path=tmp_path,
                filename="test.txt",
                content_type="text/csv",  # Valid MIME but wrong extension
                max_file_size=data_service._max_file_size,
            )

    async def test_validate_file_invalid_mime(self, data_service):
        """Test validation rejects disallowed MIME type."""
        from mkobi.services.file_processing import validate_file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(b"data")
            tmp_path = Path(tmp.name)
        with pytest.raises(ValueError, match="Invalid MIME-type"):
            validate_file(
                file_path=tmp_path,
                filename="test.csv",
                content_type="application/octet-stream",
                max_file_size=data_service._max_file_size,
            )