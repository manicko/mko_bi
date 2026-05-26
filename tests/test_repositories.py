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
        repo = UserRepository()
        user = await repo.create(
            db=async_db_session,
            email="repo_test@example.com",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )
        await async_db_session.flush()

        assert user.id is not None
        assert user.email == "repo_test@example.com"
        assert user.role == UserRole.VIEWER

    async def test_get_by_id(self, async_db_session) -> None:
        """Test getting user by ID."""
        repo = UserRepository()
        user = await repo.create(
            db=async_db_session,
            email="repo_get@example.com",
            password_hash="hashed_password",
            role=UserRole.EDITOR,
        )
        await async_db_session.flush()

        retrieved = await repo.get(user.id, async_db_session)
        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.email == "repo_get@example.com"

    async def test_get_by_email(self, async_db_session) -> None:
        """Test getting user by email."""
        repo = UserRepository()
        await repo.create(
            db=async_db_session,
            email="repo_email@example.com",
            password_hash="hashed_password",
            role=UserRole.ADMIN,
        )
        await async_db_session.flush()

        retrieved = await repo.get_by_email("repo_email@example.com", async_db_session)
        assert retrieved is not None
        assert retrieved.email == "repo_email@example.com"

    async def test_update_user(self, async_db_session) -> None:
        """Test updating a user."""
        repo = UserRepository()
        user = await repo.create(
            db=async_db_session,
            email="repo_update@example.com",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )
        await async_db_session.flush()

        updated = await repo.update(
            user.id, db=async_db_session, role=UserRole.EDITOR
        )
        await async_db_session.flush()

        assert updated.role == UserRole.EDITOR

    async def test_delete_user(self, async_db_session) -> None:
        """Test deleting a user."""
        repo = UserRepository()
        user = await repo.create(
            db=async_db_session,
            email="repo_delete@example.com",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )
        await async_db_session.flush()

        result = await repo.delete(user.id, async_db_session)
        await async_db_session.flush()

        assert result is True
        deleted = await repo.get(user.id, async_db_session)
        assert deleted is None


class TestDashboardRepository:
    """Tests for DashboardRepository CRUD operations."""

    async def test_create_dashboard(self, async_db_session, test_user: dict) -> None:
        """Test creating a new dashboard."""
        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name="repo_test_dashboard",
            description="Test dashboard for repo tests",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        assert dashboard.id is not None
        assert dashboard.name == "repo_test_dashboard"
        assert dashboard.created_by == test_user["id"]

    async def test_get_by_id(self, async_db_session, test_user: dict) -> None:
        """Test getting dashboard by ID."""
        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name="repo_get_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        retrieved = await repo.get(dashboard.id, async_db_session)
        assert retrieved is not None
        assert retrieved.id == dashboard.id

    async def test_get_user_dashboards(self, async_db_session, test_user: dict) -> None:
        """Test getting dashboards accessible by user."""
        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name="repo_user_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        # Add access for test user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        await async_db_session.flush()

        # Verify access was granted (check via get_user_dashboards)
        dashboards = await access_repo.get_user_dashboards(
            test_user["id"], async_db_session
        )
        assert len(dashboards) >= 1
        assert any(d.id == dashboard.id for d in dashboards)


class TestGraphRepository:
    """Tests for GraphRepository CRUD operations."""

    async def test_create_graph(self, async_db_session, test_user: dict) -> None:
        """Test creating a new graph."""
        # First create a dashboard
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="graph_test_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        # Create graph
        graph_repo = GraphRepository()
        graph = await graph_repo.create(
            db=async_db_session,
            dashboard_id=dashboard.id,
            name="test_graph",
            type=GraphType.BAR,
            config={},
            dimensions=[],
            metrics=[],
        )
        await async_db_session.flush()

        assert graph.id is not None
        assert graph.name == "test_graph"
        assert graph.type == GraphType.BAR

    async def test_get_graph(self, async_db_session, test_user: dict) -> None:
        """Test getting graph by ID."""
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="graph_get_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        graph_repo = GraphRepository()
        graph = await graph_repo.create(
            db=async_db_session,
            dashboard_id=dashboard.id,
            name="test_get_graph",
            type=GraphType.LINE,
            config={},
            dimensions=[],
            metrics=[],
        )
        await async_db_session.flush()

        retrieved = await graph_repo.get(graph.id, async_db_session)
        assert retrieved is not None
        assert retrieved.id == graph.id
        assert retrieved.name == "test_get_graph"

    async def test_update_graph(self, async_db_session, test_user: dict) -> None:
        """Test updating a graph."""
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="graph_update_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        graph_repo = GraphRepository()
        graph = await graph_repo.create(
            db=async_db_session,
            dashboard_id=dashboard.id,
            name="test_update_graph",
            type=GraphType.BAR,
            config={},
            dimensions=[],
            metrics=[],
        )
        await async_db_session.flush()

        updated = await graph_repo.update(
            graph.id, db=async_db_session, type=GraphType.LINE
        )
        await async_db_session.flush()

        assert updated is not None
        assert updated.type == GraphType.LINE

    async def test_delete_graph(self, async_db_session, test_user: dict) -> None:
        """Test deleting a graph."""
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="graph_delete_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        graph_repo = GraphRepository()
        graph = await graph_repo.create(
            db=async_db_session,
            dashboard_id=dashboard.id,
            name="test_delete_graph",
            type=GraphType.BAR,
            config={},
            dimensions=[],
            metrics=[],
        )
        await async_db_session.flush()

        result = await graph_repo.delete(graph.id, async_db_session)
        await async_db_session.flush()

        assert result is True
        deleted = await graph_repo.get(graph.id, async_db_session)
        assert deleted is None

    async def test_get_by_dashboard_id(self, async_db_session, test_user: dict) -> None:
        """Test getting all graphs for a dashboard."""
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="graph_by_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        graph_repo = GraphRepository()
        graph1 = await graph_repo.create(
            db=async_db_session,
            dashboard_id=dashboard.id,
            name="graph1",
            type=GraphType.BAR,
            config={},
            dimensions=[],
            metrics=[],
        )
        graph2 = await graph_repo.create(
            db=async_db_session,
            dashboard_id=dashboard.id,
            name="graph2",
            type=GraphType.LINE,
            config={},
            dimensions=[],
            metrics=[],
        )
        await async_db_session.flush()

        graphs = await graph_repo.get_by_dashboard_id(dashboard.id, async_db_session)
        assert len(graphs) == 2
        graph_ids = {g.id for g in graphs}
        assert graph1.id in graph_ids
        assert graph2.id in graph_ids

    async def test_get_by_name_and_dashboard(self, async_db_session, test_user: dict) -> None:
        """Test getting graph by name and dashboard ID."""
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="graph_by_name_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        graph_repo = GraphRepository()
        graph = await graph_repo.create(
            db=async_db_session,
            dashboard_id=dashboard.id,
            name="unique_graph_name",
            type=GraphType.BAR,
            config={},
            dimensions=[],
            metrics=[],
        )
        await async_db_session.flush()

        retrieved = await graph_repo.get_by_name_and_dashboard(
            "unique_graph_name", dashboard.id, async_db_session
        )
        assert retrieved is not None
        assert retrieved.id == graph.id


class TestFilterRepository:
    """Tests for FilterRepository CRUD operations."""

    async def test_create_filter(self, async_db_session) -> None:
        """Test creating a new filter."""
        filter_repo = FilterRepository()
        filter_obj = await filter_repo.create(
            db=async_db_session,
            name="test_filter",
            type=FilterType.SELECT,
            config={"field": "year"},
        )
        await async_db_session.flush()

        assert filter_obj.id is not None
        assert filter_obj.name == "test_filter"
        assert filter_obj.type == FilterType.SELECT

    async def test_get_filter(self, async_db_session) -> None:
        """Test getting filter by ID."""
        filter_repo = FilterRepository()
        filter_obj = await filter_repo.create(
            db=async_db_session,
            name="test_get_filter",
            type=FilterType.SELECT,
            config={"field": "month"},
        )
        await async_db_session.flush()

        retrieved = await filter_repo.get(filter_obj.id, async_db_session)
        assert retrieved is not None
        assert retrieved.id == filter_obj.id
        assert retrieved.name == "test_get_filter"

    async def test_update_filter(self, async_db_session) -> None:
        """Test updating a filter."""
        filter_repo = FilterRepository()
        filter_obj = await filter_repo.create(
            db=async_db_session,
            name="test_update_filter",
            type=FilterType.SELECT,
            config={"field": "year"},
        )
        await async_db_session.flush()

        updated = await filter_repo.update(
            filter_obj.id, db=async_db_session, type=FilterType.DATE
        )
        await async_db_session.flush()

        assert updated is not None
        assert updated.type == FilterType.DATE

    async def test_delete_filter(self, async_db_session) -> None:
        """Test deleting a filter."""
        filter_repo = FilterRepository()
        filter_obj = await filter_repo.create(
            db=async_db_session,
            name="test_delete_filter",
            type=FilterType.SELECT,
            config={"field": "year"},
        )
        await async_db_session.flush()

        result = await filter_repo.delete(filter_obj.id, async_db_session)
        await async_db_session.flush()

        assert result is True
        deleted = await filter_repo.get(filter_obj.id, async_db_session)
        assert deleted is None

    async def test_get_by_name(self, async_db_session) -> None:
        """Test getting filter by name."""
        filter_repo = FilterRepository()
        filter_obj = await filter_repo.create(
            db=async_db_session,
            name="unique_filter_name",
            type=FilterType.SELECT,
            config={"field": "quarter"},
        )
        await async_db_session.flush()

        retrieved = await filter_repo.get_by_name("unique_filter_name", async_db_session)
        assert retrieved is not None
        assert retrieved.id == filter_obj.id
        assert retrieved.name == "unique_filter_name"


class TestLayoutRepository:
    """Tests for LayoutRepository CRUD operations."""

    async def test_create_layout(self, async_db_session) -> None:
        """Test creating a new layout."""
        layout_repo = LayoutRepository()
        layout = await layout_repo.create(
            db=async_db_session,
            name="test_layout",
            definition={"grid": []},
        )
        await async_db_session.flush()

        assert layout.id is not None
        assert layout.name == "test_layout"

    async def test_get_layout(self, async_db_session) -> None:
        """Test getting layout by ID."""
        layout_repo = LayoutRepository()
        layout = await layout_repo.create(
            db=async_db_session,
            name="test_get_layout",
            definition={"grid": []},
        )
        await async_db_session.flush()

        retrieved = await layout_repo.get(layout.id, async_db_session)
        assert retrieved is not None
        assert retrieved.id == layout.id
        assert retrieved.name == "test_get_layout"

    async def test_update_layout(self, async_db_session) -> None:
        """Test updating a layout."""
        layout_repo = LayoutRepository()
        layout = await layout_repo.create(
            db=async_db_session,
            name="test_update_layout",
            definition={"grid": []},
        )
        await async_db_session.flush()

        updated = await layout_repo.update(
            layout.id, db=async_db_session, name="updated_layout_name"
        )
        await async_db_session.flush()

        assert updated is not None
        assert updated.name == "updated_layout_name"

    async def test_delete_layout(self, async_db_session) -> None:
        """Test deleting a layout."""
        layout_repo = LayoutRepository()
        layout = await layout_repo.create(
            db=async_db_session,
            name="test_delete_layout",
            definition={"grid": []},
        )
        await async_db_session.flush()

        result = await layout_repo.delete(layout.id, async_db_session)
        await async_db_session.flush()

        assert result is True
        deleted = await layout_repo.get(layout.id, async_db_session)
        assert deleted is None

    async def test_get_by_name(self, async_db_session) -> None:
        """Test getting layout by name."""
        layout_repo = LayoutRepository()
        layout = await layout_repo.create(
            db=async_db_session,
            name="unique_layout_name",
            definition={"grid": []},
        )
        await async_db_session.flush()

        retrieved = await layout_repo.get_by_name("unique_layout_name", async_db_session)
        assert retrieved is not None
        assert retrieved.id == layout.id
        assert retrieved.name == "unique_layout_name"


class TestAccessRepository:
    """Tests for AccessRepository operations."""

    async def test_grant_access(self, async_db_session, test_user: dict) -> None:
        """Test granting dashboard access."""
        # Create dashboard first
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="access_test_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        # Grant access
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.ADMIN,
        )
        await async_db_session.flush()

        # Verify access was granted (check via get_user_dashboards)
        dashboards = await access_repo.get_user_dashboards(
            test_user["id"], async_db_session
        )
        assert any(d.id == dashboard.id for d in dashboards)

    async def test_check_access(self, async_db_session, test_user: dict) -> None:
        """Test checking user access level to dashboard."""
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="check_access_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.flush()

        permission = await access_repo.check_access(
            test_user["id"], dashboard.id, async_db_session
        )
        assert permission == DashboardPermission.EDIT

    async def test_check_access_no_access(self, async_db_session, test_user: dict) -> None:
        """Test checking access when user has no access to dashboard."""
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="no_access_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        # Create another user without access
        other_user_repo = UserRepository()
        other_user = await other_user_repo.create(
            db=async_db_session,
            email="other_check@example.com",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )
        await async_db_session.flush()

        access_repo = AccessRepository()
        permission = await access_repo.check_access(
            other_user.id, dashboard.id, async_db_session
        )
        assert permission is None

    async def test_revoke_access(self, async_db_session, test_user: dict) -> None:
        """Test revoking user access to dashboard."""
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="revoke_access_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        await async_db_session.flush()

        # Verify access exists
        permission_before = await access_repo.check_access(
            test_user["id"], dashboard.id, async_db_session
        )
        assert permission_before == DashboardPermission.VIEW

        # Revoke access
        result = await access_repo.revoke_access(
            test_user["id"], dashboard.id, async_db_session
        )
        await async_db_session.flush()

        assert result is True

        # Verify access was revoked
        permission_after = await access_repo.check_access(
            test_user["id"], dashboard.id, async_db_session
        )
        assert permission_after is None

    async def test_revoke_access_not_found(self, async_db_session, test_user: dict) -> None:
        """Test revoking access when no access record exists."""
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="revoke_not_found_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        access_repo = AccessRepository()
        result = await access_repo.revoke_access(
            test_user["id"], dashboard.id, async_db_session
        )

        assert result is False

    async def test_get_by_dashboard(self, async_db_session, test_user: dict) -> None:
        """Test getting all access records for a dashboard."""
        dashboard_repo = DashboardRepository()
        dashboard = await dashboard_repo.create(
            db=async_db_session,
            name="get_by_dashboard",
            created_by=test_user["id"],
        )
        await async_db_session.flush()

        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        await async_db_session.flush()

        access_records = await access_repo.get_by_dashboard(
            dashboard.id, async_db_session
        )
        assert len(access_records) == 1
        assert access_records[0].user_id == test_user["id"]
        assert access_records[0].dashboard_id == dashboard.id
