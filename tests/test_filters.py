"""Tests for filters API."""

from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.repositories.filter_repo import FilterRepository
from mkobi.models.enums import FilterType


class TestFiltersAPI:
    """Test cases for filters API endpoints."""

    async def test_create_filter_admin_required(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient
    ) -> None:
        """Test that creating filter requires admin role."""
        # Create viewer user
        from mkobi.db.repositories.user_repo import UserRepository
        user_repo = UserRepository()
        user = await user_repo.create(
            db=async_db_session,
            email="viewer_filter@example.com",
            password_hash="hash",
            role="viewer",
        )
        await async_db_session.flush()

        # Login as viewer
        from mkobi.core.security import create_access_token
        token = create_access_token({"user_id": str(user.id), "email": user.email})
        viewer_client = authenticated_client
        viewer_client.headers["Authorization"] = f"Bearer {token}"

        response = await viewer_client.post(
            "/filters/",
            json={
                "name": "test_filter",
                "type": "select",
                "config": {"field": "year", "source": "dims"},
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_create_filter_admin_success(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient, test_user: dict
    ) -> None:
        """Test creating filter as admin (success)."""
        response = await authenticated_client.post(
            "/filters/",
            json={
                "name": "admin_filter",
                "type": "select",
                "config": {"field": "year"},
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "admin_filter"
        assert data["type"] == FilterType.SELECT

    async def test_get_filters_list(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient, test_user: dict
    ) -> None:
        """Test getting list of filters."""
        # Create test filter first
        repo = FilterRepository()
        await repo.create(
            db=async_db_session,
            name="list_test_filter",
            type=FilterType.SELECT,
            config={"field": "year"},
        )
        await async_db_session.flush()

        response = await authenticated_client.get("/filters/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_filter_by_id(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient, test_user: dict
    ) -> None:
        """Test getting filter by ID."""
        repo = FilterRepository()
        filter_obj = await repo.create(
            db=async_db_session,
            name="detail_test_filter",
            type=FilterType.MULTISELECT,
            config={"field": "category"},
        )
        await async_db_session.flush()

        response = await authenticated_client.get(f"/filters/{filter_obj.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(filter_obj.id)
        assert data["name"] == "detail_test_filter"

    async def test_update_filter_admin_required(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient
    ) -> None:
        """Test that updating filter requires admin role."""
        # Create viewer user and filter
        from mkobi.db.repositories.user_repo import UserRepository
        user_repo = UserRepository()
        user = await user_repo.create(
            db=async_db_session,
            email="viewer_filter2@example.com",
            password_hash="hash",
            role="viewer",
        )
        await async_db_session.flush()

        repo = FilterRepository()
        filter_obj = await repo.create(
            db=async_db_session,
            name="update_test_filter",
            type=FilterType.SELECT,
            config={"field": "year"},
        )
        await async_db_session.flush()

        # Login as viewer
        from mkobi.core.security import create_access_token
        token = create_access_token({"user_id": str(user.id), "email": user.email})
        viewer_client = authenticated_client
        viewer_client.headers["Authorization"] = f"Bearer {token}"

        response = await viewer_client.put(
            f"/filters/{filter_obj.id}",
            json={"name": "hacked_filter"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_filter_admin_success(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient, test_user: dict
    ) -> None:
        """Test updating filter as admin (success)."""
        repo = FilterRepository()
        filter_obj = await repo.create(
            db=async_db_session,
            name="update_success_filter",
            type=FilterType.SELECT,
            config={"field": "year"},
        )
        await async_db_session.flush()

        response = await authenticated_client.put(
            f"/filters/{filter_obj.id}",
            json={"name": "updated_filter_name"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "updated_filter_name"

    async def test_delete_filter_admin_required(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient
    ) -> None:
        """Test that deleting filter requires admin role."""
        # Create viewer user and filter
        from mkobi.db.repositories.user_repo import UserRepository
        user_repo = UserRepository()
        user = await user_repo.create(
            db=async_db_session,
            email="viewer_filter3@example.com",
            password_hash="hash",
            role="viewer",
        )
        await async_db_session.flush()

        repo = FilterRepository()
        filter_obj = await repo.create(
            db=async_db_session,
            name="delete_test_filter",
            type=FilterType.SELECT,
            config={"field": "year"},
        )
        await async_db_session.flush()

        # Login as viewer
        from mkobi.core.security import create_access_token
        token = create_access_token({"user_id": str(user.id), "email": user.email})
        viewer_client = authenticated_client
        viewer_client.headers["Authorization"] = f"Bearer {token}"

        response = await viewer_client.delete(f"/filters/{filter_obj.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_filter_admin_success(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient, test_user: dict
    ) -> None:
        """Test deleting filter as admin (success)."""
        repo = FilterRepository()
        filter_obj = await repo.create(
            db=async_db_session,
            name="delete_success_filter",
            type=FilterType.SELECT,
            config={"field": "year"},
        )
        await async_db_session.flush()

        response = await authenticated_client.delete(f"/filters/{filter_obj.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
