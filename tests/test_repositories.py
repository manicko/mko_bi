"""Tests for database repositories."""


from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.db.repositories.filter_repo import FilterRepository
from mkobi.db.repositories.graph_repo import GraphRepository
from mkobi.db.repositories.layout_repo import LayoutRepository
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.models.enums import DashboardPermission, FilterType, GraphType, UserRole


class TestUserRepository:
    """Tests for UserRepository CRUD operations."""

    async def test_create_user(self, async_db_session) -> None:
        """Test creating a new user."""
        user = await UserRepository.create(
            db=async_db_session,
            email="repo_test@example.com",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        assert user.id is not None
        assert user.email == "repo_test@example.com"
        assert user.role == UserRole.VIEWER

    async def test_get_by_id(self, async_db_session) -> None:
        """Test getting user by ID."""
        user = await UserRepository.create(
            db=async_db_session,
            email="repo_get@example.com",
            password_hash="hashed_password",
            role=UserRole.EDITOR,
        )
        await async_db_session.commit()

        retrieved = await UserRepository.get(user.id, async_db_session)
        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.email == "repo_get@example.com"

    async def test_get_by_email(self, async_db_session) -> None:
        """Test getting user by email."""
        await UserRepository.create(
            db=async_db_session,
            email="repo_email@example.com",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
        )
        await async_db_session.commit()

        retrieved = await UserRepository.get_by_email("repo_email@example.com", async_db_session)
        assert retrieved is not None
        assert retrieved.email == "repo_email@example.com"

    async def test_update_user(self, async_db_session) -> None:
        """Test updating a user."""
        user = await UserRepository.create(
            db=async_db_session,
            email="repo_update@example.com",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        updated = await UserRepository.update(
            user.id, db=async_db_session, role=UserRole.EDITOR
        )
        await async_db_session.commit()

        assert updated.role == UserRole.EDITOR

    async def test_delete_user(self, async_db_session) -> None:
        """Test deleting a user."""
        user = await UserRepository.create(
            db=async_db_session,
            email="repo_delete@example.com",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )
        await async_db_session.commit()

        result = await UserRepository.delete(user.id, async_db_session)
        await async_db_session.commit()

        assert result is True
        deleted = await UserRepository.get(user.id, async_db_session)
        assert deleted is None


class TestDashboardRepository:
    """Tests for DashboardRepository CRUD operations."""

    async def test_create_dashboard(self, async_db_session, test_user: dict) -> None:
        """Test creating a new dashboard."""
        dashboard = await DashboardRepository.create(
            db=async_db_session,
            name="repo_test_dashboard",
            description="Test dashboard for repo tests",
            created_by=test_user["id"],
        )
        await async_db_session.commit()

        assert dashboard.id is not None
        assert dashboard.name == "repo_test_dashboard"
        assert dashboard.created_by == test_user["id"]

    async def test_get_by_id(self, async_db_session, test_user: dict) -> None:
        """Test getting dashboard by ID."""
        dashboard = await DashboardRepository.create(
            db=async_db_session,
            name="repo_get_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.commit()

        retrieved = await DashboardRepository.get(dashboard.id, async_db_session)
        assert retrieved is not None
        assert retrieved.id == dashboard.id

    async def test_get_user_dashboards(self, async_db_session, test_user: dict) -> None:
        """Test getting dashboards accessible by user."""
        dashboard = await DashboardRepository.create(
            db=async_db_session,
            name="repo_user_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.commit()

        # Add access for test user
        await AccessRepository.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        await async_db_session.commit()

        dashboards = await DashboardRepository.get_user_dashboards(
            async_db_session, test_user["id"]
        )
        assert len(dashboards) >= 1
        assert any(d.id == dashboard.id for d in dashboards)


class TestGraphRepository:
    """Tests for GraphRepository CRUD operations."""

    async def test_create_graph(self, async_db_session, test_user: dict) -> None:
        """Test creating a new graph."""
        # First create a dashboard
        dashboard = await DashboardRepository.create(
            db=async_db_session,
            name="graph_test_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.commit()

        # Create graph
        graph = await GraphRepository.create(
            db=async_db_session,
            dashboard_id=dashboard.id,
            name="test_graph",
            type=GraphType.BAR,
            config={},
            dimensions=[],
            metrics=[],
        )
        await async_db_session.commit()

        assert graph.id is not None
        assert graph.name == "test_graph"
        assert graph.type == GraphType.BAR


class TestFilterRepository:
    """Tests for FilterRepository CRUD operations."""

    async def test_create_filter(self, async_db_session) -> None:
        """Test creating a new filter."""
        filter_obj = await FilterRepository.create(
            db=async_db_session,
            name="test_filter",
            type=FilterType.SELECT,
            config={"field": "year"},
        )
        await async_db_session.commit()

        assert filter_obj.id is not None
        assert filter_obj.name == "test_filter"
        assert filter_obj.type == FilterType.SELECT


class TestLayoutRepository:
    """Tests for LayoutRepository CRUD operations."""

    async def test_create_layout(self, async_db_session) -> None:
        """Test creating a new layout."""
        layout = await LayoutRepository.create(
            db=async_db_session,
            name="test_layout",
            definition={"grid": []},
        )
        await async_db_session.commit()

        assert layout.id is not None
        assert layout.name == "test_layout"


class TestAccessRepository:
    """Tests for AccessRepository operations."""

    async def test_grant_access(self, async_db_session, test_user: dict) -> None:
        """Test granting dashboard access."""
        # Create dashboard first
        dashboard = await DashboardRepository.create(
            db=async_db_session,
            name="access_test_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.commit()

        # Grant access
        await AccessRepository.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.ADMIN,
        )
        await async_db_session.commit()

        # Verify access was granted (check via get_user_dashboards)
        dashboards = await DashboardRepository.get_user_dashboards(
            async_db_session, test_user["id"]
        )
        assert any(d.id == dashboard.id for d in dashboards)
