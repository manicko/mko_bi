"""End-to-end tests for complete file upload workflow.

Tests the full flow: upload -> process -> data flow with overwrite mode.
Processing log verification is included.
"""

from collections.abc import Generator
import tempfile
from pathlib import Path
from uuid import UUID
import uuid

import pytest
from fastapi import status
from httpx import AsyncClient

from mkobi.core.security import hash_password, create_access_token
from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.db.repositories.graph_repo import GraphRepository
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.models.enums import DashboardPermission, GraphType, ProcessingStatus
from mkobi.workers.data_worker import process_csv_background


@pytest.fixture
def e2e_csv_content() -> bytes:
    """CSV content with known values for verification."""
    return b"""category,sales,profit
Alpha,100,25
Beta,200,50
Gamma,150,37
Delta,300,75
Epsilon,75,19
"""


@pytest.fixture
def e2e_csv_file(e2e_csv_content: bytes) -> Generator[Path, None, None]:
    """Create temporary CSV file for E2E tests."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
        f.write(e2e_csv_content)
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)


@pytest.fixture
async def e2e_dashboard(async_db_session) -> dict:
    """Create test dashboard with graph for E2E tests."""
    dashboard_repo = DashboardRepository()
    graph_repo = GraphRepository()

    # Create dashboard with unique name
    unique_suffix = uuid.uuid4().hex[:8]
    dashboard = await dashboard_repo.create(
        db=async_db_session,
        name=f"e2e_test_dashboard_{unique_suffix}",
        description="Dashboard for E2E upload tests",
    )

    # Create graph with only category dimension (simpler aggregation)
    graph = await graph_repo.create(
        db=async_db_session,
        dashboard_id=dashboard.id,
        name=f"e2e_test_graph_{unique_suffix}",
        type=GraphType.TABLE,
        dimensions=["category"],
        metrics=["sales", "profit"],
        config={},
    )
    await async_db_session.commit()

    return {
        "dashboard": dashboard,
        "graph": graph,
    }


@pytest.fixture
async def e2e_user(async_db_session) -> dict:
    """Create test user with edit access for E2E tests."""
    user_repo = UserRepository()
    unique_id = uuid.uuid4().hex[:8]
    user = await user_repo.create(
        db=async_db_session,
        email=f"e2e_user_{unique_id}@example.com",
        password_hash=hash_password("TestPass123!"),
        role="admin",
    )
    await async_db_session.commit()

    token = create_access_token({"user_id": str(user.id), "email": user.email})
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "token": token,
    }


@pytest.mark.asyncio
class TestE2EUploadWorkflow:
    """End-to-end tests for upload -> process -> data flow."""

    async def test_e2e_upload_overwrite_mode(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        e2e_user: dict,
        e2e_dashboard: dict,
        e2e_csv_file: Path,
    ) -> None:
        """Test complete E2E flow with overwrite mode."""
        from mkobi.config import get_config
        from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository

        dashboard = e2e_dashboard["dashboard"]
        graph = e2e_dashboard["graph"]

        # Grant edit access to test user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=e2e_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        config = get_config()
        upload_dir = Path(config.upload_temp_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Upload CSV file
        with open(e2e_csv_file, "rb") as f:
            upload_response = await authenticated_client.post(
                f"/upload/{dashboard.id}?mode=overwrite",
                files={"file": ("test_data.csv", f, "text/csv")},
            )

        assert upload_response.status_code == status.HTTP_201_CREATED
        upload_data = upload_response.json()
        assert "task_id" in upload_data
        task_id = upload_data["task_id"]

        # Step 2: Verify processing log created with UPLOADED status
        log_repo = ProcessingLogRepository()
        log = await log_repo.get_by_id(UUID(task_id), async_db_session)
        assert log is not None
        assert log.status == ProcessingStatus.UPLOADED

        # Step 3: Process the CSV file (simulates background worker)
        task_file = upload_dir / f"{task_id}.csv"
        assert task_file.exists(), f"Task file should exist at {task_file}"

        result = await process_csv_background(
            file_path_str=str(task_file),
            task_id=str(task_id),
            dashboard_id_str=str(dashboard.id),
            processing_config_dict=None,
            mode="overwrite",
            db_session=async_db_session,
        )

        assert result["success"] is True
        assert result["rows_processed"] > 0

        # Step 4: Verify temp file is cleaned up after processing
        assert not task_file.exists(), "Temp file should be cleaned up after processing"

        # Step 5: Verify processing log updated to COMPLETED
        log = await log_repo.get_by_id(UUID(task_id), async_db_session)
        assert log is not None
        assert log.status == ProcessingStatus.COMPLETED
        assert log.finished_at is not None

        # Step 6: Verify aggregated data is available via API
        data_response = await authenticated_client.get(
            "/data/aggregated",
            params={"dashboard_id": str(dashboard.id), "graph_id": str(graph.id)},
        )

        assert data_response.status_code == status.HTTP_200_OK
        data = data_response.json()
        assert "graphs" in data
        assert len(data["graphs"]) == 1

        graph_data = data["graphs"][0]
        assert graph_data["graph_id"] == str(graph.id)
        assert graph_data["type"] == GraphType.TABLE.value
        assert "data" in graph_data
        assert len(graph_data["data"]) > 0

        # Step 7: Verify data contains expected values
        categories_in_data = {row.get("category") for row in graph_data["data"]}
        expected_categories = {"Alpha", "Beta", "Gamma", "Delta", "Epsilon"}
        assert categories_in_data == expected_categories

    async def test_e2e_processing_log_status_transitions(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        e2e_user: dict,
        e2e_dashboard: dict,
        e2e_csv_file: Path,
    ) -> None:
        """Verify processing log reflects correct status transitions."""
        from mkobi.config import get_config
        from mkobi.db.repositories.processing_log_repo import ProcessingLogRepository

        dashboard = e2e_dashboard["dashboard"]

        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=e2e_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        config = get_config()
        upload_dir = Path(config.upload_temp_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        log_repo = ProcessingLogRepository()

        # Upload triggers UPLOADED status
        with open(e2e_csv_file, "rb") as f:
            upload_response = await authenticated_client.post(
                f"/upload/{dashboard.id}?mode=overwrite",
                files={"file": ("test.csv", f, "text/csv")},
            )

        task_id = upload_response.json()["task_id"]

        # Check UPLOADED status after upload
        log = await log_repo.get_by_id(UUID(task_id), async_db_session)
        assert log.status == ProcessingStatus.UPLOADED

        # Process and verify eventual COMPLETED status
        task_file = upload_dir / f"{task_id}.csv"
        await process_csv_background(
            file_path_str=str(task_file),
            task_id=str(task_id),
            dashboard_id_str=str(dashboard.id),
            processing_config_dict=None,
            mode="overwrite",
            db_session=async_db_session,
        )

        log = await log_repo.get_by_id(UUID(task_id), async_db_session)
        assert log.status == ProcessingStatus.COMPLETED
        assert log.started_at is not None
        assert log.finished_at is not None
        assert "rows processed" in log.message

    async def test_e2e_multiple_graphs_same_dashboard(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        e2e_user: dict,
        e2e_dashboard: dict,
        e2e_csv_file: Path,
    ) -> None:
        """Test E2E flow with multiple graphs on same dashboard."""
        from mkobi.config import get_config

        dashboard = e2e_dashboard["dashboard"]
        graph = e2e_dashboard["graph"]
        graph_repo = GraphRepository()

        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=e2e_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        # Create second graph with different dimensions
        unique_suffix = uuid.uuid4().hex[:8]
        second_graph = await graph_repo.create(
            db=async_db_session,
            dashboard_id=dashboard.id,
            name=f"e2e_test_graph2_{unique_suffix}",
            type=GraphType.TABLE,
            dimensions=["region"],
            metrics=["sales"],
            config={},
        )
        await async_db_session.commit()

        config = get_config()
        upload_dir = Path(config.upload_temp_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Upload with data that has both dimensions
        multi_dim_csv = b"""category,region,sales,profit
Alpha,North,100,25
Beta,South,200,50
"""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(multi_dim_csv)
            multi_file = Path(f.name)

        with open(multi_file, "rb") as f:
            upload_response = await authenticated_client.post(
                f"/upload/{dashboard.id}?mode=overwrite",
                files={"file": ("multi.csv", f, "text/csv")},
            )

        task_id = upload_response.json()["task_id"]

        # Process
        task_file = upload_dir / f"{task_id}.csv"
        result = await process_csv_background(
            file_path_str=str(task_file),
            task_id=str(task_id),
            dashboard_id_str=str(dashboard.id),
            processing_config_dict=None,
            mode="overwrite",
            db_session=async_db_session,
        )

        assert result["success"] is True

        # Verify both graphs have data
        data_response = await authenticated_client.get(
            "/data/aggregated",
            params={"dashboard_id": str(dashboard.id)},
        )

        assert data_response.status_code == status.HTTP_200_OK
        data = data_response.json()
        assert len(data["graphs"]) == 2

        graph_ids = {g["graph_id"] for g in data["graphs"]}
        assert str(graph.id) in graph_ids
        assert str(second_graph.id) in graph_ids

        multi_file.unlink(missing_ok=True)