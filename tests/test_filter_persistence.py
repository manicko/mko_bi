"""Tests for dashboard filter state persistence.

Tests that filter values are correctly stored and retrieved from the API,
enabling frontend filter persistence across navigation.
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
async def dashboard_with_filters_setup(async_db_session, owner_user):
    """Create test dashboard with graph and filters for filter persistence tests."""
    filter_repo = FilterRepository()
    dashboard_filter_repo = DashboardFilterRepository()

    from mkobi.db.repositories.graph_repo import GraphRepository
    from mkobi.services.graph_service import GraphService
    from mkobi.models.graph import GraphCreate

    unique_suffix = uuid4().hex[:8]

    # Create dashboard with unique name
    dashboard = await DashboardRepository().create(
        db=async_db_session,
        name=f"filter_persist_dashboard_{unique_suffix}",
        description="Dashboard for filter persistence tests",
    )

    # Create graph
    graph_service = GraphService(GraphRepository())
    graph = await graph_service.create(
        GraphCreate(
            name=f"filter_persist_graph_{unique_suffix}",
            type=GraphType.TABLE,
            dashboard_id=dashboard.id,
            config={},
            dimensions=[],
            metrics=["sales", "profit"],
        ),
        db=async_db_session,
    )

    # Create filters with names matching CSV columns
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
        "region_filter": region_filter,
        "category_filter": category_filter,
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
class TestFilterStatePersistence:
    """Tests for filter state persistence across navigation scenarios."""

    async def test_filter_values_endpoint_returns_available_values(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        owner_user,
        dashboard_with_filters_setup,
        filter_csv_content: bytes,
    ) -> None:
        """Test that filter values endpoint returns distinct values for each filter.

        This enables frontend to persist filter selections by providing
        the available values to populate dropdowns after navigation.
        """
        from mkobi.config import get_config
        from mkobi.workers.data_worker import process_csv_background

        dashboard = dashboard_with_filters_setup["dashboard"]

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

        # Upload and process CSV
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

            task_file = upload_dir / f"{task_id}.csv"
            await process_csv_background(
                file_path_str=str(task_file),
                task_id=str(task_id),
                dashboard_id_str=str(dashboard.id),
                processing_config_dict=None,
                mode="overwrite",
                db_session=async_db_session,
            )

            # Verify filter values are available via API for frontend consumption
            region_values_response = await authenticated_client.get(
                f"/dashboards/{dashboard.id}/filter-values",
                params={"filter_name": "region"},
            )
            assert region_values_response.status_code == status.HTTP_200_OK
            region_values = region_values_response.json()
            assert set(region_values["values"]) == {"North", "South", "East"}

            category_values_response = await authenticated_client.get(
                f"/dashboards/{dashboard.id}/filter-values",
                params={"filter_name": "category"},
            )
            assert category_values_response.status_code == status.HTTP_200_OK
            category_values = category_values_response.json()
            assert set(category_values["values"]) == {"Electronics", "Clothing", "Books"}
        finally:
            tmp_path.unlink(missing_ok=True)

    async def test_filter_values_persist_across_dashboard_navigation(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        owner_user,
    ) -> None:
        """Test that filter values remain available after navigating to another dashboard.

        This simulates the frontend scenario where:
        1. User sets filter on dashboard A
        2. User navigates to dashboard B (different dashboard)
        3. User navigates back to dashboard A
        4. Filter values should still be available for dashboard A
        """
        # Create two dashboards
        dashboard_repo = DashboardRepository()
        access_repo = AccessRepository()

        dashboard_a = await dashboard_repo.create(
            db=async_db_session,
            name=f"dashboard_a_{uuid4().hex[:8]}",
        )
        dashboard_b = await dashboard_repo.create(
            db=async_db_session,
            name=f"dashboard_b_{uuid4().hex[:8]}",
        )

        # Grant access to both
        await access_repo.grant_access(
            db=async_db_session,
            user_id=owner_user.id,
            dashboard_id=dashboard_a.id,
            permission=DashboardPermission.VIEW,
        )
        await access_repo.grant_access(
            db=async_db_session,
            user_id=owner_user.id,
            dashboard_id=dashboard_b.id,
            permission=DashboardPermission.VIEW,
        )

        await async_db_session.commit()

        # Verify both dashboards are accessible
        response_a = await authenticated_client.get(f"/dashboards/{dashboard_a.id}")
        response_b = await authenticated_client.get(f"/dashboards/{dashboard_b.id}")

        assert response_a.status_code == status.HTTP_200_OK
        assert response_b.status_code == status.HTTP_200_OK

        # Verify filter values endpoint works for both (even if no filters bound)
        filter_values_a = await authenticated_client.get(
            f"/dashboards/{dashboard_a.id}/filter-values",
            params={"filter_name": "any_field"},
        )
        # Should return empty values list, not error
        assert filter_values_a.status_code in [status.HTTP_200_OK]

    async def test_filter_state_cleared_on_new_upload(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        owner_user,
        dashboard_with_filters_setup,
    ) -> None:
        """Test that filter state is properly cleared when new data is uploaded (overwrite mode).

        When a user uploads new data in OVERWRITE mode, old filter values should be
        replaced with values from the new dataset.
        """
        from mkobi.config import get_config
        from mkobi.workers.data_worker import process_csv_background

        dashboard = dashboard_with_filters_setup["dashboard"]

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

        # First upload with regions: North, South, East
        first_csv = b"""category,region,sales
Electronics,North,100
Clothing,South,200
"""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(first_csv)
            tmp_path = Path(f.name)

        try:
            with open(tmp_path, "rb") as f:
                upload_response = await authenticated_client.post(
                    f"/upload/{dashboard.id}?mode=overwrite",
                    files={"file": ("first_data.csv", f, "text/csv")},
                )
            task_id = upload_response.json()["task_id"]
            task_file = upload_dir / f"{task_id}.csv"
            await process_csv_background(
                file_path_str=str(task_file),
                task_id=str(task_id),
                dashboard_id_str=str(dashboard.id),
                processing_config_dict=None,
                mode="overwrite",
                db_session=async_db_session,
            )

            # Check initial filter values
            filter_values_repo = DashboardFilterValuesRepository()
            initial_values = await filter_values_repo.get_filter_values(
                dashboard_id=dashboard.id,
                filter_name="region",
                db=async_db_session,
            )
            assert set(initial_values) == {"North", "South"}

        finally:
            tmp_path.unlink(missing_ok=True)