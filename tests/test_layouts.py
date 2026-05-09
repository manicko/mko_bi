"""Tests for layouts API."""

from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.db.repositories.layout_repo import LayoutRepository


class TestLayoutsAPI:
    """Test cases for layouts API endpoints."""

    async def test_create_layout_admin_required(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient
    ) -> None:
        """Test that creating layout requires admin role."""
        # Create viewer user
        from mkobi.db.repositories.user_repo import UserRepository
        user_repo = UserRepository()
        user = await user_repo.create(
            db=async_db_session,
            email="viewer_layout@example.com",
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
            "/layouts",
            json={"name": "test_layout", "definition": {"grid": []}},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_create_layout_admin_success(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient, test_user: dict
    ) -> None:
        """Test creating layout as admin (success)."""
        response = await authenticated_client.post(
            "/layouts",
            json={"name": "admin_layout", "definition": {"grid": []}},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "admin_layout"

    async def test_get_layouts_list(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient, test_user: dict
    ) -> None:
        """Test getting list of layouts."""
        # Create test layout
        repo = LayoutRepository()
        await repo.create(
            db=async_db_session,
            name="list_test_layout",
            definition={"grid": []},
        )
        await async_db_session.flush()

        response = await authenticated_client.get("/layouts")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_layout_by_id(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient, test_user: dict
    ) -> None:
        """Test getting layout by ID."""
        repo = LayoutRepository()
        layout = await repo.create(
            db=async_db_session,
            name="detail_test_layout",
            definition={"grid": []},
        )
        await async_db_session.flush()

        response = await authenticated_client.get(f"/layouts/{layout.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(layout.id)
        assert data["name"] == "detail_test_layout"

    async def test_update_layout_admin_required(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient
    ) -> None:
        """Test that updating layout requires admin role."""
        # Create viewer user and layout
        from mkobi.db.repositories.user_repo import UserRepository
        user_repo = UserRepository()
        user = await user_repo.create(
            db=async_db_session,
            email="viewer_layout2@example.com",
            password_hash="hash",
            role="viewer",
        )
        await async_db_session.flush()

        repo = LayoutRepository()
        layout = await repo.create(
            db=async_db_session,
            name="update_test_layout",
            definition={"grid": []},
        )
        await async_db_session.flush()

        # Login as viewer
        from mkobi.core.security import create_access_token
        token = create_access_token({"user_id": str(user.id), "email": user.email})
        viewer_client = authenticated_client
        viewer_client.headers["Authorization"] = f"Bearer {token}"

        response = await viewer_client.put(
            f"/layouts/{layout.id}",
            json={"name": "hacked_layout"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_layout_admin_success(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient, test_user: dict
    ) -> None:
        """Test updating layout as admin (success)."""
        repo = LayoutRepository()
        layout = await repo.create(
            db=async_db_session,
            name="update_success_layout",
            definition={"grid": []},
        )
        await async_db_session.flush()

        response = await authenticated_client.put(
            f"/layouts/{layout.id}",
            json={"name": "updated_layout_name"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "updated_layout_name"

    async def test_delete_layout_admin_required(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient
    ) -> None:
        """Test that deleting layout requires admin role."""
        # Create viewer user and layout
        from mkobi.db.repositories.user_repo import UserRepository
        user_repo = UserRepository()
        user = await user_repo.create(
            db=async_db_session,
            email="viewer_layout3@example.com",
            password_hash="hash",
            role="viewer",
        )
        await async_db_session.flush()

        repo = LayoutRepository()
        layout = await repo.create(
            db=async_db_session,
            name="delete_test_layout",
            definition={"grid": []},
        )
        await async_db_session.flush()

        # Login as viewer
        from mkobi.core.security import create_access_token
        token = create_access_token({"user_id": str(user.id), "email": user.email})
        viewer_client = authenticated_client
        viewer_client.headers["Authorization"] = f"Bearer {token}"

        response = await viewer_client.delete(f"/layouts/{layout.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_layout_admin_success(
        self, async_db_session: AsyncSession, authenticated_client: AsyncClient, test_user: dict
    ) -> None:
        """Test deleting layout as admin (success)."""
        repo = LayoutRepository()
        layout = await repo.create(
            db=async_db_session,
            name="delete_success_layout",
            definition={"grid": []},
        )
        await async_db_session.flush()

        response = await authenticated_client.delete(f"/layouts/{layout.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
