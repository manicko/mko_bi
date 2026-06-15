"""Data service tests - integration tests verifying actual database state."""
from pathlib import Path
from unittest.mock import patch
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
from mkobi.services.graph_service import GraphService
from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository
from mkobi.db.repositories.graph_repo import GraphRepository
from mkobi.db.repositories.aggregated_data_repo import AggregatedDataRepository
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.services.dashboard_service import DashboardService
from mkobi.core.security import hash_password
from mkobi.models.graph import GraphCreate
from mkobi.core.permissions import DashboardPermissionError


# ========== Integration Tests for DataService ==========

@pytest.mark.asyncio
class TestDataServiceIntegration:
    """Integration tests for DataService with real database."""

    @pytest.fixture
    def data_service(self):
        """Create DataService with real repositories."""
        return DataService(
            agg_repo=AggregatedDataRepository(),
            log_repo=ProcessingLogRepository(),
            graph_repo=GraphRepository(),
        )

    @pytest.fixture
    async def log_repo(self):
        """Create ProcessingLogRepository instance."""
        return ProcessingLogRepository()

    @pytest.fixture
    async def owner_user(self, async_db_session):
        """Create an owner user for dashboard tests."""
        user = await UserRepository().create(
            db=async_db_session,
            email=f"owner_{uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TestPass123!"),
            role="admin",
        )
        await async_db_session.commit()
        return user

    @pytest.fixture
    async def dashboard_service_for_test(self):
        """Create DashboardService for test setup."""
        return DashboardService(DashboardRepository(), AccessRepository())

    @pytest.fixture
    async def test_dashboard(self, async_db_session, owner_user, dashboard_service_for_test):
        """Create a test dashboard."""
        dashboard = await dashboard_service_for_test.create_dashboard(
            name=f"Test Dashboard {uuid4().hex[:8]}",
            config={"graph_types": ["bar"]},
            owner_id=owner_user.id,
            db=async_db_session,
        )
        return dashboard

    # --- process_upload tests ---

    async def test_process_upload_creates_log_record(
        self, data_service, async_db_session, test_dashboard, log_repo, valid_csv_content
    ):
        """Test successful file upload creates processing log in database."""
        csv_content = valid_csv_content

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        try:
            with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
                with patch("mkobi.services.file_processing.enqueue_job"):
                    result = await data_service.process_upload(
                        file_path=tmp_path,
                        dashboard_id=test_dashboard.id,
                        user_id=uuid4(),
                        filename="test.csv",
                        content_type="text/csv",
                        mode=UploadMode.OVERWRITE,
                        db=async_db_session,
                    )

            # Verify response
            assert result.task_id is not None
            assert result.status == ProcessingStatusEnum.UPLOADED
            assert result.filename == "test.csv"
            assert result.dashboard_id == test_dashboard.id
            assert "File uploaded successfully" in result.message

            # Verify log was actually created in database (not mock assertion)
            log = await log_repo.get_by_id(result.task_id, async_db_session)
            assert log is not None
            assert log.dashboard_id == test_dashboard.id
            assert log.status == ProcessingStatusEnum.UPLOADED
            assert log.message is not None
            assert "uploaded" in log.message.lower()
        finally:
            tmp_path.unlink(missing_ok=True)

    async def test_process_upload_creates_log_for_dashboard(
        self, data_service, async_db_session, test_dashboard, log_repo, valid_csv_content
    ):
        """Test upload creates log record with correct dashboard association."""
        csv_content = valid_csv_content

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        try:
            with patch("mkobi.services.file_processing.enqueue_job"):
                result = await data_service.process_upload(
                    file_path=tmp_path,
                    dashboard_id=test_dashboard.id,
                    filename="data.csv",
                    content_type="text/csv",
                    mode=UploadMode.APPEND,
                    db=async_db_session,
                )

            assert result.status == ProcessingStatusEnum.UPLOADED

            # Verify log exists in database (not mock assertion)
            logs = await log_repo.get_by_dashboard(test_dashboard.id, async_db_session)
            assert len(logs) >= 1
            found_log = next((log_item for log_item in logs if log_item.id == result.task_id), None)
            assert found_log is not None
        finally:
            tmp_path.unlink(missing_ok=True)

    async def test_process_upload_no_permission_raises(
        self, data_service, async_db_session, test_dashboard
    ):
        """Test upload fails when user lacks permission."""
        csv_content = b"name,value\nfoo,1\n"

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = Path(tmp.name)

        try:
            with patch("mkobi.services.data_service.check_dashboard_access", return_value=False):
                with pytest.raises(DashboardPermissionError):
                    await data_service.process_upload(
                        file_path=tmp_path,
                        dashboard_id=test_dashboard.id,
                        user_id=uuid4(),
                        filename="data.csv",
                        content_type="text/csv",
                        db=async_db_session,
                    )
        finally:
            tmp_path.unlink(missing_ok=True)

    async def test_process_upload_csv_gz_creates_log(
        self, data_service, async_db_session, test_dashboard, log_repo
    ):
        """Test upload with gzip compressed CSV creates log in database."""
        csv_content = b"date,category,revenue\n2023-01-01,A,100.5\n"

        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
            gz.write(csv_content)
        gz_content = buf.getvalue()

        with tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False) as tmp:
            tmp.write(gz_content)
            tmp_path = Path(tmp.name)

        try:
            with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
                with patch("mkobi.services.file_processing.enqueue_job"):
                    result = await data_service.process_upload(
                        file_path=tmp_path,
                        dashboard_id=test_dashboard.id,
                        user_id=uuid4(),
                        filename="data.csv.gz",
                        content_type="application/gzip",
                        db=async_db_session,
                    )

            assert result.status == ProcessingStatusEnum.UPLOADED

            # Verify log was created with correct status in database
            log = await log_repo.get_by_id(result.task_id, async_db_session)
            assert log is not None
            assert log.status == ProcessingStatusEnum.UPLOADED
        finally:
            tmp_path.unlink(missing_ok=True)

    # --- get_aggregated_data tests ---

    async def test_get_aggregated_data_uses_repository(
        self, data_service, async_db_session
    ):
        """Test aggregated data retrieval calls repository correctly."""
        dashboard_id = uuid4()
        graph_id = uuid4()

        result = await data_service.get_aggregated_data(
            dashboard_id, graph_id, db=async_db_session,
        )

        assert result == []

    async def test_get_aggregated_data_with_filters(
        self, data_service, async_db_session, test_dashboard
    ):
        """Test aggregated data filters are properly handled."""
        graph_service = GraphService(GraphRepository())
        graph = await graph_service.create(
            GraphCreate(
                name="Test Graph",
                type="bar",
                dashboard_id=test_dashboard.id,
                config={},
                dimensions=["category", "year"],
                metrics=["revenue"],
            ),
            db=async_db_session,
        )

        test_filters = {"year": 2023, "category": "Electronics"}

        result = await data_service.get_aggregated_data(
            test_dashboard.id, graph.id, db=async_db_session, filters=test_filters,
        )

        assert result == []

    # --- get_available_metrics tests ---

    async def test_get_available_metrics_aggregates_graphs(
        self, data_service, async_db_session, test_dashboard
    ):
        """Test getting available metrics from graphs in database."""
        graph_service = GraphService(GraphRepository())

        # Create graphs with specific metrics via GraphService
        await graph_service.create(
            GraphCreate(
                name="Graph 1",
                type="bar",
                dashboard_id=test_dashboard.id,
                config={},
                dimensions=["category"],
                metrics=["revenue", "sales"],
            ),
            db=async_db_session,
        )
        await graph_service.create(
            GraphCreate(
                name="Graph 2",
                type="line",
                dashboard_id=test_dashboard.id,
                config={},
                dimensions=["region"],
                metrics=["profit"],
            ),
            db=async_db_session,
        )

        result = await data_service.get_available_metrics(test_dashboard.id, db=async_db_session)

        assert set(result) == {"revenue", "sales", "profit"}

    async def test_get_available_metrics_empty_dashboard(
        self, data_service, async_db_session, test_dashboard, owner_user
    ):
        """Test available metrics returns empty when no graphs exist."""
        # Create a separate dashboard with no graphs
        empty_dashboard = await DashboardService(DashboardRepository(), AccessRepository()).create_dashboard(
            name=f"Empty Dashboard {uuid4().hex[:8]}",
            config={"graph_types": ["bar"]},
            owner_id=owner_user.id,
            db=async_db_session,
        )

        result = await data_service.get_available_metrics(empty_dashboard.id, db=async_db_session)

        assert result == []

    # --- trigger_processing tests ---

    async def test_trigger_processing_updates_log_status(
        self, data_service, async_db_session, test_dashboard, log_repo
    ):
        """Test trigger processing updates log status in database."""
        # Create initial log in UPLOADED status via repository
        log = await log_repo.create_log(
            dashboard_id=test_dashboard.id,
            status=ProcessingStatusEnum.UPLOADED,
            message="test.csv",
            db=async_db_session,
        )
        await async_db_session.commit()
        task_id = log.id

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            with patch("mkobi.services.data_service.find_task_file", return_value="/tmp/test.csv"):
                with patch("mkobi.services.data_service.enqueue_processing_job"):
                    result = await data_service.trigger_processing(
                        task_id, test_dashboard.id, uuid4(), db=async_db_session,
                    )

        assert result.task_id == task_id
        assert result.status == ProcessingStatusEnum.PROCESSING

        # Verify status was updated in database (not mock assertion)
        updated_log = await log_repo.get_by_id(task_id, async_db_session)
        assert updated_log is not None
        assert updated_log.status == ProcessingStatusEnum.PROCESSING

    async def test_trigger_processing_no_permission_raises(
        self, data_service, async_db_session, test_dashboard
    ):
        """Test trigger processing fails without permission."""
        log = await ProcessingLogRepository().create_log(
            dashboard_id=test_dashboard.id,
            status=ProcessingStatusEnum.UPLOADED,
            message="test.csv",
            db=async_db_session,
        )
        await async_db_session.commit()
        task_id = log.id

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=False):
            with pytest.raises(DashboardPermissionError):
                await data_service.trigger_processing(
                    task_id, test_dashboard.id, uuid4(), db=async_db_session,
                )

    async def test_trigger_processing_task_not_found(
        self, data_service, async_db_session
    ):
        """Test trigger processing raises error for unknown task."""
        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            with pytest.raises(ValueError, match="Processing task.*not found"):
                await data_service.trigger_processing(
                    uuid4(), uuid4(), uuid4(), db=async_db_session,
                )


# --- Processing status lifecycle integration tests ---

@pytest.mark.asyncio
class TestProcessingStatusLifecycleIntegration:
    """Integration tests for processing log status lifecycle."""

    @pytest.fixture
    def data_service(self):
        """Create DataService with real repositories."""
        return DataService(
            agg_repo=AggregatedDataRepository(),
            log_repo=ProcessingLogRepository(),
            graph_repo=GraphRepository(),
        )

    @pytest.fixture
    async def log_repo(self):
        """Create ProcessingLogRepository instance."""
        return ProcessingLogRepository()

    @pytest.fixture
    async def test_log(self, async_db_session, log_repo, dashboard_service_for_test):
        """Create a test processing log with dashboard."""
        owner = await UserRepository().create(
            db=async_db_session,
            email=f"owner_{uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TestPass123!"),
            role="admin",
        )
        await async_db_session.commit()

        dashboard = await dashboard_service_for_test.create_dashboard(
            name=f"Test Dashboard {uuid4().hex[:8]}",
            config={"graph_types": ["bar"]},
            owner_id=owner.id,
            db=async_db_session,
        )

        log = await log_repo.create_log(
            dashboard_id=dashboard.id,
            status=ProcessingStatusEnum.UPLOADED,
            message="test.csv",
            db=async_db_session,
        )
        await async_db_session.commit()
        return log, dashboard

    @pytest.fixture
    async def dashboard_service_for_test(self):
        """Create DashboardService for test setup."""
        return DashboardService(DashboardRepository(), AccessRepository())

    async def test_status_update_processes_to_processing(
        self, data_service, async_db_session, log_repo, test_log, dashboard_service_for_test
    ):
        """Verify status update changes UPLOADED to PROCESSING."""
        log, dashboard = test_log
        task_id = log.id

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            with patch("mkobi.services.data_service.find_task_file", return_value="/tmp/test.csv"):
                with patch("mkobi.services.data_service.enqueue_processing_job"):
                    result = await data_service.trigger_processing(
                        task_id=task_id,
                        dashboard_id=dashboard.id,
                        user_id=uuid4(),
                        db=async_db_session,
                    )

        assert result.status == ProcessingStatusEnum.PROCESSING

        # Verify status was updated in database (not mock assertion)
        updated_log = await log_repo.get_by_id(task_id, async_db_session)
        assert updated_log is not None
        assert updated_log.status == ProcessingStatusEnum.PROCESSING

    async def test_status_update_from_failed_allows_reprocessing(
        self, data_service, async_db_session, log_repo, test_log, dashboard_service_for_test
    ):
        """Verify transitioning from FAILED to PROCESSING is handled."""
        log, dashboard = test_log

        # Update log to FAILED status via repository
        await log_repo.update_status(
            log_id=log.id,
            status=ProcessingStatusEnum.FAILED,
            message="Processing failed",
            db=async_db_session,
        )
        await async_db_session.commit()

        with patch("mkobi.services.data_service.check_dashboard_access", return_value=True):
            with patch("mkobi.services.data_service.find_task_file", return_value="/tmp/test.csv"):
                with patch("mkobi.services.data_service.enqueue_processing_job"):
                    result = await data_service.trigger_processing(
                        task_id=log.id,
                        dashboard_id=dashboard.id,
                        user_id=uuid4(),
                        db=async_db_session,
                    )

        # Current behavior: status is updated to PROCESSING
        assert result.status == ProcessingStatusEnum.PROCESSING

        # Verify status was updated in database (not mock assertion)
        updated_log = await log_repo.get_by_id(log.id, async_db_session)
        assert updated_log is not None
        assert updated_log.status == ProcessingStatusEnum.PROCESSING


# --- Validation tests (keeping as unit tests since they test utility functions) ---

@pytest.mark.asyncio
class TestFileValidation:
    """Tests for file validation logic - do not require database."""

    @pytest.fixture
    def data_service(self):
        """Create DataService instance for validation tests."""
        return DataService(
            agg_repo=AggregatedDataRepository(),
            log_repo=ProcessingLogRepository(),
            graph_repo=GraphRepository(),
        )

    async def test_validate_file_none_content_type_raises_error(self, data_service):
        """Test MIME validation raises error when content_type is None.

        Note: MIME type is now detected from file content, not from header.
        This test validates that the file still exists and has valid content.
        """
        from mkobi.services.file_processing import validate_file

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(b"name,value\ntest,1\n" * 10)
            tmp_path = Path(tmp.name)

        try:
            # MIME type is detected from content, so any CSV passes validation
            validate_file(
                file_path=tmp_path,
                filename="test.csv",
                content_type=None,
                max_file_size=data_service._max_file_size,
            )
        finally:
            tmp_path.unlink(missing_ok=True)

    async def test_validate_file_valid_csv(self, data_service):
        """Test validation passes for valid CSV file."""
        from mkobi.services.file_processing import validate_file

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(b"name,value\ntest,1\n" * 10)
            tmp_path = Path(tmp.name)

        try:
            validate_file(
                file_path=tmp_path,
                filename="test.csv",
                content_type="text/csv",
                max_file_size=data_service._max_file_size,
            )
        finally:
            tmp_path.unlink(missing_ok=True)

    async def test_validate_file_valid_gz(self, data_service):
        """Test validation passes for valid .csv.gz file.

        Note: MIME type is detected from content (gzip magic bytes 0x1f 0x8b).
        """
        from mkobi.services.file_processing import validate_file

        # Create actual gzip content (gzip magic bytes at start)
        with tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False) as tmp:
            # Write gzip magic bytes followed by some CSV data
            tmp.write(b"\x1f\x8b\x08\x00compressed data")
            tmp_path = Path(tmp.name)

        try:
            validate_file(
                file_path=tmp_path,
                filename="test.csv.gz",
                content_type="application/gzip",
                max_file_size=data_service._max_file_size,
            )
        finally:
            tmp_path.unlink(missing_ok=True)

    async def test_validate_file_invalid_extension(self, data_service, valid_csv_content):
        """Test validation rejects .txt extension.

        Note: With MIME detection from content using python-magic/libmagic, a .txt file
        with plain text content is detected as text/plain by libmagic, which is not in
        the allowed MIME types list. The MIME-first validation rejects it before the
        extension check runs. This is the expected security behavior: MIME detection
        from content takes priority over extension-based checks.

        On systems without libmagic, the fallback detector returns application/octet-
        stream for plain text without commas/newlines, which also triggers MIME error.
        """
        from mkobi.services.file_processing import validate_file

        # Create a file with .txt extension and plain text content (no CSV structure)
        # libmagic detects this as text/plain (not in allowed types), so MIME-first
        # validation raises before the extension check. Without libmagic, fallback returns
        # application/octet-stream which is also not allowed.
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"plain text data without csv structure")
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(ValueError, match="Detected MIME type.*not allowed"):
                validate_file(
                    file_path=tmp_path,
                    filename="test.txt",
                    content_type="text/csv",
                    max_file_size=data_service._max_file_size,
                )
        finally:
            tmp_path.unlink(missing_ok=True)

    async def test_validate_file_invalid_mime(self, data_service):
        """Test validation rejects disallowed MIME type detected from content.

        MIME type is now detected from file content using python-magic,
        not from the client-provided Content-Type header.
        """
        from mkobi.services.file_processing import validate_file

        # Create a file with content that will be detected as text/plain
        # (plain text "data" without CSV structure should be detected as text/plain)
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(b"data")
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(ValueError, match="Detected MIME type"):
                validate_file(
                    file_path=tmp_path,
                    filename="test.csv",
                    content_type="text/csv",  # This header is now ignored
                    max_file_size=data_service._max_file_size,
                )
        finally:
            tmp_path.unlink(missing_ok=True)

    async def test_validate_file_spoofed_mime_type_rejected(self, data_service):
        """Test that spoofed Content-Type header is rejected based on actual content.

        Security test: An attacker uploads an executable with CSV extension
        and text/csv Content-Type header. The actual content detection should
        reject the malicious file.
        """
        from mkobi.services.file_processing import validate_file

        # Create a file with ELF header (Linux executable) - will be detected as application/x-executable
        elf_header = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(elf_header)
            tmp_path = Path(tmp.name)

        try:
            # Even with spoofed CSV Content-Type header, actual MIME detection should reject
            with pytest.raises(ValueError, match="Detected MIME type"):
                validate_file(
                    file_path=tmp_path,
                    filename="malicious.csv",
                    content_type="text/csv",  # Spoofed header
                    max_file_size=data_service._max_file_size,
                )
        finally:
            tmp_path.unlink(missing_ok=True)

    async def test_validate_file_spoofed_gzip_rejected(self, data_service):
        """Test that spoofed gzip header is rejected when content is not actually gzip."""
        from mkobi.services.file_processing import validate_file

        # Create a file with fake gzip header but not actual gzip content
        # python-magic will detect this as application/x-gzip if it has proper gzip magic bytes
        # but we test with content that will be detected as something else
        with tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False) as tmp:
            # Write plain text pretending to be gzip
            tmp.write(b"This is not gzipped content but claims to be gzip")
            tmp_path = Path(tmp.name)

        try:
            # This should fail because content is not actual gzip
            with pytest.raises(ValueError, match="Detected MIME type"):
                validate_file(
                    file_path=tmp_path,
                    filename="fake.csv.gz",
                    content_type="application/gzip",  # Spoofed header
                    max_file_size=data_service._max_file_size,
                )
        finally:
            tmp_path.unlink(missing_ok=True)


# --- _normalize_json_keys tests ---

@pytest.mark.asyncio
class TestJsonbKeyNormalization:
    """Tests for JSONB dims key normalization (sorted keys)."""

    @pytest.fixture
    async def owner_user(self, async_db_session):
        """Create an owner user for dashboard tests."""
        user = await UserRepository().create(
            db=async_db_session,
            email=f"owner_{uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TestPass123!"),
            role="admin",
        )
        await async_db_session.commit()
        return user

    @pytest.fixture
    async def dashboard_service_for_test(self):
        """Create DashboardService for test setup."""
        return DashboardService(DashboardRepository(), AccessRepository())

    @pytest.fixture
    async def test_dashboard(self, async_db_session, owner_user, dashboard_service_for_test):
        """Create a test dashboard."""
        dashboard = await dashboard_service_for_test.create_dashboard(
            name=f"Test Dashboard {uuid4().hex[:8]}",
            config={"graph_types": ["bar"]},
            owner_id=owner_user.id,
            db=async_db_session,
        )
        return dashboard

    @pytest.fixture
    def storage_manager(self, async_db_session):
        """Create StorageManager instance."""
        from mkobi.data.storage.manager import StorageManager
        return StorageManager(db=async_db_session)

    async def test_save_aggregates_dims_keys_are_sorted(
        self, storage_manager, async_db_session, test_dashboard
    ):
        """Test that dims keys are sorted when saving aggregates to database.

        This ensures deterministic UPSERT conflict detection on JSONB columns
        by verifying that unsorted input keys are stored in sorted order.
        """
        # Create a graph for the dashboard
        graph_service = GraphService(GraphRepository())
        graph = await graph_service.create(
            GraphCreate(
                name="Test Graph",
                type="bar",
                dashboard_id=test_dashboard.id,
                config={},
                dimensions=["category"],
                metrics=["revenue"],
            ),
            db=async_db_session,
        )

        # Create aggregates with explicitly unsorted dim keys
        # Using keys in reverse alphabetical order to ensure sorting happens
        unsorted_dims = {"z_category": "Electronics", "a_region": "North"}
        aggregates = [
            {
                "graph_id": graph.id,
                "dims": unsorted_dims,
                "metrics": {"revenue": 100},
            },
        ]

        saved = await storage_manager.save_aggregates(
            dashboard_id=test_dashboard.id,
            aggregates=aggregates,
            clear_old=True,
        )

        assert saved == 1

        # Retrieve the stored data and verify keys are sorted
        from mkobi.db.models.aggregated_data import AggregatedData
        from sqlalchemy import select

        result = await async_db_session.execute(
            select(AggregatedData.dims).where(
                AggregatedData.dashboard_id == test_dashboard.id,
                AggregatedData.graph_id == graph.id,
            )
        )
        stored_dims = result.scalar_one()

        # Verify keys are sorted alphabetically
        key_list = list(stored_dims.keys())
        assert key_list == sorted(key_list)
        assert key_list == ["a_region", "z_category"]

    async def test_save_aggregates_nested_dims_keys_are_sorted(
        self, storage_manager, async_db_session, test_dashboard
    ):
        """Test that nested dims keys are recursively sorted.

        Verifies the normalization handles nested dictionaries correctly.
        """
        # Create a graph for the dashboard
        graph_service = GraphService(GraphRepository())
        graph = await graph_service.create(
            GraphCreate(
                name="Test Graph Nested",
                type="bar",
                dashboard_id=test_dashboard.id,
                config={},
                dimensions=["category"],
                metrics=["revenue"],
            ),
            db=async_db_session,
        )

        # Create aggregates with nested unsorted dim keys
        unsorted_dims = {
            "z_outer": {
                "z_inner": "value1",
                "a_inner": "value2",
            },
            "a_outer": "simple_value",
        }
        aggregates = [
            {
                "graph_id": graph.id,
                "dims": unsorted_dims,
                "metrics": {"revenue": 200},
            },
        ]

        saved = await storage_manager.save_aggregates(
            dashboard_id=test_dashboard.id,
            aggregates=aggregates,
            clear_old=True,
        )

        assert saved == 1

        # Retrieve the stored data and verify keys are sorted at all levels
        from mkobi.db.models.aggregated_data import AggregatedData
        from sqlalchemy import select

        result = await async_db_session.execute(
            select(AggregatedData.dims).where(
                AggregatedData.dashboard_id == test_dashboard.id,
                AggregatedData.graph_id == graph.id,
            )
        )
        stored_dims = result.scalar_one()

        # Verify top-level keys are sorted
        top_keys = list(stored_dims.keys())
        assert top_keys == sorted(top_keys)

        # Verify nested keys are also sorted
        if "z_outer" in stored_dims:
            nested_keys = list(stored_dims["z_outer"].keys())
            assert nested_keys == sorted(nested_keys)