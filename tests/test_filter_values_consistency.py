"""Filter values consistency tests after upload processing.

Tests that filter values are correctly updated after both OVERWRITE and APPEND uploads.
Filter values are extracted from aggregated data and should reflect all available values
in the dashboard's data.
"""

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient

from mkobi.core.security import hash_password
from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.db.repositories.dashboard_filter_values_repo import DashboardFilterValuesRepository
from mkobi.db.repositories.filter_repo import FilterRepository
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.db.repositories.dashboard_filter_repo import DashboardFilterRepository
from mkobi.models.enums import DashboardPermission, FilterType, GraphType


@pytest.fixture
def filter_csv_content() -> bytes:
    """CSV content with multiple filter dimensions for testing filter values."""
    return b"""category,region,sales,profit
Electronics,North,100,25
Electronics,South,150,37
Clothing,North,200,50
Clothing,South,180,42
Books,East,75,19
"""


@pytest.fixture
async def dashboard_with_filters(async_db_session, owner_user):
    """Create test dashboard with graph and filters for filter values tests."""
    filter_repo = FilterRepository()
    dashboard_filter_repo = DashboardFilterRepository()

    from mkobi.db.repositories.graph_repo import GraphRepository
    from mkobi.services.graph_service import GraphService
    from mkobi.models.graph import GraphCreate

    unique_suffix = uuid4().hex[:8]

    # Create dashboard with unique name
    dashboard = await DashboardRepository().create(
        db=async_db_session,
        name=f"filter_test_dashboard_{unique_suffix}",
        description="Dashboard for filter values tests",
    )

    # Create graph with NO dimensions (filters will provide dimensions)
    graph_service = GraphService(GraphRepository())
    graph = await graph_service.create(
        GraphCreate(
            name=f"filter_test_graph_{unique_suffix}",
            type=GraphType.TABLE,
            dashboard_id=dashboard.id,
            config={},
            dimensions=[],
            metrics=["sales", "profit"],
        ),
        db=async_db_session,
    )

    # Create filters with names matching CSV columns
    # Using names that match the data columns: "region" and "category"
    region_filter = await filter_repo.get_by_name("region", async_db_session)
    if region_filter is None:
        region_filter = await filter_repo.create(
            db=async_db_session,
            name="region",
            type=FilterType.SELECT,
            config={"field": "region"},
        )

    category_filter = await filter_repo.get_by_name("category", async_db_session)
    if category_filter is None:
        category_filter = await filter_repo.create(
            db=async_db_session,
            name="category",
            type=FilterType.SELECT,
            config={"field": "category"},
        )

    # Bind filters to dashboard
    await dashboard_filter_repo.bind_filter(
        dashboard_id=dashboard.id,
        filter_id=region_filter.id,
        db=async_db_session,
    )
    await dashboard_filter_repo.bind_filter(
        dashboard_id=dashboard.id,
        filter_id=category_filter.id,
        db=async_db_session,
    )

    await async_db_session.commit()

    return {
        "dashboard": dashboard,
        "graph": graph,
    }


@pytest.fixture
async def owner_user(async_db_session):
    """Create test user as dashboard owner for tests."""
    user = await UserRepository().create(
        db=async_db_session,
        email=f"owner_{uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPass123!"),
        role="admin",
    )
    await async_db_session.commit()
    return user


@pytest.mark.asyncio
class TestFilterValuesConsistency:
    """Tests for filter values consistency after upload in different modes."""

    async def test_filter_values_after_overwrite(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        owner_user,
        dashboard_with_filters,
        filter_csv_content: bytes,
    ) -> None:
        """Test filter values match uploaded data after OVERWRITE mode upload.

        Verifies that after an OVERWRITE upload:
        1. Filter values are cleared and rebuilt from new data
        2. Only the new data's categories are present in filter values
        """
        from mkobi.config import get_config
        from mkobi.workers.data_worker import process_csv_background

        dashboard = dashboard_with_filters["dashboard"]

        # Grant edit access to test user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=owner_user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        config = get_config()
        upload_dir = Path(config.upload_temp_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Upload CSV file in OVERWRITE mode
        import tempfile
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(filter_csv_content)
            tmp_path = Path(f.name)

        try:
            with open(tmp_path, "rb") as f:
                upload_response = await authenticated_client.post(
                    f"/upload/{dashboard.id}?mode=overwrite",
                    files={"file": ("test_data.csv", f, "text/csv")},
                )

            assert upload_response.status_code == status.HTTP_201_CREATED
            task_id = upload_response.json()["task_id"]

            # Process the CSV file
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

            # Verify filter values after OVERWRITE
            filter_values_repo = DashboardFilterValuesRepository()
            category_values = await filter_values_repo.get_filter_values(
                dashboard_id=dashboard.id,
                filter_name="category",
                db=async_db_session,
            )

            expected_categories = {"Books", "Clothing", "Electronics"}
            assert set(category_values) == expected_categories, (
                f"Expected categories {expected_categories}, got {set(category_values)}"
            )

            region_values = await filter_values_repo.get_filter_values(
                dashboard_id=dashboard.id,
                filter_name="region",
                db=async_db_session,
            )

            expected_regions = {"East", "North", "South"}
            assert set(region_values) == expected_regions, (
                f"Expected regions {expected_regions}, got {set(region_values)}"
            )
        finally:
            tmp_path.unlink(missing_ok=True)

    async def test_filter_values_after_append(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        owner_user,
        dashboard_with_filters,
    ) -> None:
        """Test filter values include all data after APPEND mode upload.

        Verifies that after an APPEND upload:
        1. Filter values are rebuilt from all accumulated data
        2. Values from both uploads are present in filter values
        """
        from mkobi.config import get_config
        from mkobi.workers.data_worker import process_csv_background

        dashboard = dashboard_with_filters["dashboard"]

        # Grant edit access to test user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=owner_user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        config = get_config()
        upload_dir = Path(config.upload_temp_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # First upload - categories Electronics, Clothing; regions North, South
        first_csv = b"""category,region,sales,profit
Electronics,North,100,25
Clothing,South,200,50
"""

        # Second upload - categories Books (new), Electronics (existing); East, West (new regions)
        second_csv = b"""category,region,sales,profit
Books,East,75,19
Electronics,West,150,37
"""

        import tempfile

        # Upload first file in APPEND mode
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(first_csv)
            first_tmp = Path(f.name)

        try:
            with open(first_tmp, "rb") as f:
                upload_response = await authenticated_client.post(
                    f"/upload/{dashboard.id}?mode=append",
                    files={"file": ("first_data.csv", f, "text/csv")},
                )

            task_id_1 = upload_response.json()["task_id"]
            task_file_1 = upload_dir / f"{task_id_1}.csv"
            await process_csv_background(
                file_path_str=str(task_file_1),
                task_id=str(task_id_1),
                dashboard_id_str=str(dashboard.id),
                processing_config_dict=None,
                mode="append",
                db_session=async_db_session,
            )

            # Upload second file in APPEND mode
            with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
                f.write(second_csv)
                second_tmp = Path(f.name)

            try:
                with open(second_tmp, "rb") as f:
                    upload_response = await authenticated_client.post(
                        f"/upload/{dashboard.id}?mode=append",
                        files={"file": ("second_data.csv", f, "text/csv")},
                    )

                task_id_2 = upload_response.json()["task_id"]
                task_file_2 = upload_dir / f"{task_id_2}.csv"
                result = await process_csv_background(
                    file_path_str=str(task_file_2),
                    task_id=str(task_id_2),
                    dashboard_id_str=str(dashboard.id),
                    processing_config_dict=None,
                    mode="append",
                    db_session=async_db_session,
                )

                assert result["success"] is True

                # Verify filter values after APPEND - should have all categories
                filter_values_repo = DashboardFilterValuesRepository()
                category_values = await filter_values_repo.get_filter_values(
                    dashboard_id=dashboard.id,
                    filter_name="category",
                    db=async_db_session,
                )

                expected_categories = {"Books", "Clothing", "Electronics"}
                assert set(category_values) == expected_categories, (
                    f"Expected all categories {expected_categories}, got {set(category_values)}"
                )

                # Verify all regions are present
                region_values = await filter_values_repo.get_filter_values(
                    dashboard_id=dashboard.id,
                    filter_name="region",
                    db=async_db_session,
                )

                expected_regions = {"East", "North", "South", "West"}
                assert set(region_values) == expected_regions, (
                    f"Expected all regions {expected_regions}, got {set(region_values)}"
                )
            finally:
                second_tmp.unlink(missing_ok=True)
        finally:
            first_tmp.unlink(missing_ok=True)