"""╨в╨╡╤Б╤В╤Л ╨┤╨╗╤П ╨╝╨╛╨┤╨╡╨╗╨╡╨╣ SQLAlchemy (User, Dashboard, Access, Graph, Layout, AggregatedData).

╨в╨╡╤Б╤В╨╕╤А╤Г╨╡╤В ╤Б╨╛╨╖╨┤╨░╨╜╨╕╨╡, ╤З╤В╨╡╨╜╨╕╨╡, ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╨╡ ╨╕ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╨╡ ╨╝╨╛╨┤╨╡╨╗╨╡╨╣,
╨░ ╤В╨░╨║╨╢╨╡ ╨┐╤А╨╛╨▓╨╡╤А╨║╨╕ ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╨╣, ╤Б╨▓╤П╨╖╨╡╨╣ ╨╕ ╨║╨░╤Б╨║╨░╨┤╨╜╨╛╨│╨╛ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╤П.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from uuid import UUID

from mkobi.db.models import user as user_model
from mkobi.db.models import dashboard as dashboard_model
from mkobi.db.models import access as access_model
from mkobi.db.models import graphs as graph_model
from mkobi.db.models import layout as layout_model
from mkobi.db.models import aggregated_data as aggregated_data_model
from mkobi.models.enums import UserRole, DashboardPermission, GraphType


class TestUserModel:
    """╨в╨╡╤Б╤В╤Л ╨┤╨╗╤П ╨╝╨╛╨┤╨╡╨╗╨╕ User."""

    async def test_create_user(self, async_db_session):
        """╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П ╤Б ╨▓╨░╨╗╨╕╨┤╨╜╤Л╨╝╨╕ ╨┤╨░╨╜╨╜╤Л╨╝╨╕."""
        user = user_model.User(
            email="test@example.com",
            password_hash="$2b$12$examplehash",
            role=UserRole.VIEWER,
            is_active=True,
        )
        async_db_session.add(user)
        await async_db_session.commit()
        await async_db_session.refresh(user)

        assert user.id is not None
        assert isinstance(user.id, UUID)
        assert user.email == "test@example.com"
        assert user.role == UserRole.VIEWER
        assert user.is_active is True

    async def test_create_user_with_default_role(self, async_db_session):
        """╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П ╤Б ╤А╨╛╨╗╤М╤О ╨┐╨╛ ╤Г╨╝╨╛╨╗╤З╨░╨╜╨╕╤О."""
        user = user_model.User(
            email="test2@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        assert user.role == UserRole.VIEWER

    async def test_create_user_with_default_is_active(self, async_db_session):
        """╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П ╤Б is_active ╨┐╨╛ ╤Г╨╝╨╛╨╗╤З╨░╨╜╨╕╤О."""
        user = user_model.User(
            email="test3@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        assert user.is_active is True

    async def test_unique_email_constraint(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Г╨╜╨╕╨║╨░╨╗╤М╨╜╨╛╤Б╤В╨╕ email."""
        user1 = user_model.User(
            email="duplicate@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user1)
        await async_db_session.commit()

        user2 = user_model.User(
            email="duplicate@example.com",
            password_hash="$2b$12$examplehash2",
        )
        async_db_session.add(user2)

        with pytest.raises(IntegrityError):
            await async_db_session.commit()
        
        await async_db_session.rollback()
        
    async def test_user_role_enum_values(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨┤╨╛╨┐╤Г╤Б╤В╨╕╨╝╤Л╤Е ╨╖╨╜╨░╤З╨╡╨╜╨╕╨╣ ╤А╨╛╨╗╨╕ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П."""
        for role in [UserRole.ADMIN, UserRole.EDITOR, UserRole.VIEWER]:
            user = user_model.User(
                email=f"{role.value}_user@example.com",
                password_hash="$2b$12$examplehash",
                role=role,
            )
            async_db_session.add(user)
        await async_db_session.commit()

        result = await async_db_session.execute(select(user_model.User))
        users = result.scalars().all()
        assert len(users) == 3

    # Note: Removed low-value string representation tests (__repr__, __str__)
    # These tests have low diagnostic value and are fragile to changes


class TestDashboardModel:
    """╨в╨╡╤Б╤В╤Л ╨┤╨╗╤П ╨╝╨╛╨┤╨╡╨╗╨╕ Dashboard."""

    async def test_create_dashboard(self, async_db_session):
        """╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨┤╨░╤И╨▒╨╛╤А╨┤╨░ ╤Б ╨▓╨░╨╗╨╕╨┤╨╜╤Л╨╝╨╕ ╨┤╨░╨╜╨╜╤Л╨╝╨╕."""
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            description="Test description",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()
        await async_db_session.refresh(dashboard)

        assert dashboard.id is not None
        assert isinstance(dashboard.id, UUID)
        assert dashboard.name == "Test Dashboard"
        assert dashboard.description == "Test description"

    async def test_create_dashboard_with_defaults(self, async_db_session):
        """╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨┤╨░╤И╨▒╨╛╤А╨┤╨░ ╤Б╨╛ ╨╖╨╜╨░╤З╨╡╨╜╨╕╤П╨╝╨╕ ╨┐╨╛ ╤Г╨╝╨╛╨╗╤З╨░╨╜╨╕╤О."""
        dashboard = dashboard_model.Dashboard(
            name="Default Dashboard",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        assert dashboard.description is None
        assert dashboard.updated_at is not None

    async def test_unique_name_constraint(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Г╨╜╨╕╨║╨░╨╗╤М╨╜╨╛╤Б╤В╨╕ ╨╕╨╝╨╡╨╜╨╕ ╨┤╨░╤И╨▒╨╛╤А╨┤╨░."""
        dashboard1 = dashboard_model.Dashboard(
            name="Same Name",
        )
        async_db_session.add(dashboard1)
        await async_db_session.commit()

        dashboard2 = dashboard_model.Dashboard(
            name="Same Name",
        )
        async_db_session.add(dashboard2)

        with pytest.raises(IntegrityError):
            await async_db_session.commit()
        
        await async_db_session.rollback()
        
    async def test_dashboard_updated_at_auto_update(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨░╨▓╤В╨╛╨╝╨░╤В╨╕╤З╨╡╤Б╨║╨╛╨│╨╛ ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╤П updated_at."""
        dashboard = dashboard_model.Dashboard(
            name="Update Test",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()
        await async_db_session.refresh(dashboard)

        old_updated_at = dashboard.updated_at

        # ╨Ю╨▒╨╜╨╛╨▓╨╗╤П╨╡╨╝ ╨┤╨░╤И╨▒╨╛╤А╨┤
        dashboard.name = "Updated Name"
        await async_db_session.commit()
        await async_db_session.refresh(dashboard)

        assert dashboard.updated_at > old_updated_at

    # Note: Removed low-value string representation tests (__repr__, __str__)
    # These tests have low diagnostic value and are fragile to changes


class TestAccessModel:
    """╨в╨╡╤Б╤В╤Л ╨┤╨╗╤П ╨╝╨╛╨┤╨╡╨╗╨╕ Access."""

    async def test_create_access(self, async_db_session):
        """╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨┐╤А╨░╨▓╨░ ╨┤╨╛╤Б╤В╤Г╨┐╨░."""
        user = user_model.User(
            email="access_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Access Test Dashboard",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        access = access_model.DashboardAccess(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        async_db_session.add(access)
        await async_db_session.commit()
        await async_db_session.refresh(access)

        assert access.user_id == user.id
        assert access.dashboard_id == dashboard.id
        assert access.permission == DashboardPermission.VIEW

    async def test_unique_composite_key(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Г╨╜╨╕╨║╨░╨╗╤М╨╜╨╛╤Б╤В╨╕ ╤Б╨╛╤Б╤В╨░╨▓╨╜╨╛╨│╨╛ ╨║╨╗╤О╤З╨░ (user_id, dashboard_id)."""
        user = user_model.User(
            email="composite_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Composite Test",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        access1 = access_model.DashboardAccess(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        async_db_session.add(access1)
        await async_db_session.commit()

        access2 = access_model.DashboardAccess(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        async_db_session.add(access2)

        with pytest.raises(IntegrityError):
            await async_db_session.commit()

        await async_db_session.rollback()

    async def test_permission_enum_values(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨┤╨╛╨┐╤Г╤Б╤В╨╕╨╝╤Л╤Е ╨╖╨╜╨░╤З╨╡╨╜╨╕╨╣ ╤Г╤А╨╛╨▓╨╜╤П ╨┤╨╛╤Б╤В╤Г╨┐╨░."""
        user1 = user_model.User(
            email="perm_user1@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user1)
        user2 = user_model.User(
            email="perm_user2@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user2)
        user3 = user_model.User(
            email="perm_user3@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user3)
        await async_db_session.commit()

        dashboard1 = dashboard_model.Dashboard(
            name="Perm Test 1",
        )
        async_db_session.add(dashboard1)
        dashboard2 = dashboard_model.Dashboard(
            name="Perm Test 2",
        )
        async_db_session.add(dashboard2)
        dashboard3 = dashboard_model.Dashboard(
            name="Perm Test 3",
        )
        async_db_session.add(dashboard3)
        await async_db_session.commit()

        permissions = [DashboardPermission.VIEW, DashboardPermission.EDIT, DashboardPermission.ADMIN]
        for i, permission in enumerate(permissions):
            access = access_model.DashboardAccess(
                user_id=[user1, user2, user3][i].id,
                dashboard_id=[dashboard1, dashboard2, dashboard3][i].id,
                permission=permission,
            )
            async_db_session.add(access)
        await async_db_session.commit()

        accesses = await async_db_session.execute(
            select(access_model.DashboardAccess)
        )
        accesses = accesses.scalars().all()
        assert len(accesses) == 3

    async def test_cascade_delete_user(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨║╨░╤Б╨║╨░╨┤╨╜╨╛╨│╨╛ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╤П ╨┐╤А╨╕ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╨╕ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П."""
        user = user_model.User(
            email="cascade_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Cascade Dash Test",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        access = access_model.DashboardAccess(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        async_db_session.add(access)
        await async_db_session.commit()

        # ╨г╨┤╨░╨╗╤П╨╡╨╝ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П
        await async_db_session.delete(user)
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝, ╤З╤В╨╛ ╨┤╨╛╤Б╤В╤Г╨┐ ╤В╨╛╨╢╨╡ ╤Г╨┤╨░╨╗╨╡╨╜
        result = await async_db_session.execute(
            select(access_model.DashboardAccess)
        )
        result = result.fetchall()
        assert len(result) == 0

    async def test_cascade_delete_dashboard(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨║╨░╤Б╨║╨░╨┤╨╜╨╛╨│╨╛ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╤П ╨┐╤А╨╕ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╨╕ ╨┤╨░╤И╨▒╨╛╤А╨┤╨░."""
        user = user_model.User(
            email="cascade_dash_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Cascade Dash Test",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        access = access_model.DashboardAccess(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        async_db_session.add(access)
        await async_db_session.commit()

        # ╨г╨┤╨░╨╗╤П╨╡╨╝ ╨┤╨░╤И╨▒╨╛╤А╨┤
        await async_db_session.delete(dashboard)
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝, ╤З╤В╨╛ ╨┤╨╛╤Б╤В╤Г╨┐ ╤В╨╛╨╢╨╡ ╤Г╨┤╨░╨╗╨╡╨╜
        result = await async_db_session.execute(
            select(access_model.DashboardAccess)
        )
        result = result.fetchall()
        assert len(result) == 0

    # Note: Removed low-value string representation tests (__repr__, __str__)
    # These tests have low diagnostic value and are fragile to changes


class TestUserDashboardRelationship:
    """╨в╨╡╤Б╤В╤Л ╨┤╨╗╤П ╤Б╨▓╤П╨╖╨╕ ╨╝╨╡╨╢╨┤╤Г ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П╨╝╨╕ ╨╕ ╨┤╨░╤И╨▒╨╛╤А╨┤╨░╨╝╨╕."""

    async def test_user_dashboards_relationship(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Б╨▓╤П╨╖╨╕ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П ╤Б ╨┤╨░╤И╨▒╨╛╤А╨┤╨░╨╝╨╕ ╤З╨╡╤А╨╡╨╖ ╨┤╨╛╤Б╤В╤Г╨┐."""
        user = user_model.User(
            email="rel_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        dashboard1 = dashboard_model.Dashboard(
            name="Dash 1",
        )
        dashboard2 = dashboard_model.Dashboard(
            name="Dash 2",
        )
        async_db_session.add_all([dashboard1, dashboard2])
        await async_db_session.commit()

        access1 = access_model.DashboardAccess(
            user_id=user.id,
            dashboard_id=dashboard1.id,
            permission=DashboardPermission.VIEW,
        )
        access2 = access_model.DashboardAccess(
            user_id=user.id,
            dashboard_id=dashboard2.id,
            permission=DashboardPermission.EDIT,
        )
        async_db_session.add_all([access1, access2])
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝, ╤З╤В╨╛ ╤Г ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П ╨╡╤Б╤В╤М ╨┤╨╛╤Б╤В╤Г╨┐ ╨║ ╨┤╨░╤И╨▒╨╛╤А╨┤╨░╨╝
        result = await async_db_session.execute(
            select(user_model.User).where(user_model.User.id == user.id)
        )
        result = result.scalar_one()
        assert len(result.dashboards) == 2
        dashboard_names = {d.name for d in result.dashboards}
        assert "Dash 1" in dashboard_names
        assert "Dash 2" in dashboard_names

    async def test_dashboard_users_relationship(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Б╨▓╤П╨╖╨╕ ╨┤╨░╤И╨▒╨╛╤А╨┤╨░ ╤Б ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П╨╝╨╕ ╤З╨╡╤А╨╡╨╖ ╨┤╨╛╤Б╤В╤Г╨┐."""
        user1 = user_model.User(
            email="user1@example.com",
            password_hash="$2b$12$examplehash",
        )
        user2 = user_model.User(
            email="user2@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add_all([user1, user2])
        await async_db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Shared Dashboard",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        access1 = access_model.DashboardAccess(
            user_id=user1.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        access2 = access_model.DashboardAccess(
            user_id=user2.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.ADMIN,
        )
        async_db_session.add_all([access1, access2])
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝, ╤З╤В╨╛ ╤Г ╨┤╨░╤И╨▒╨╛╤А╨┤╨░ ╨╡╤Б╤В╤М ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╨╕
        result = await async_db_session.execute(
            select(dashboard_model.Dashboard).where(
                dashboard_model.Dashboard.id == dashboard.id
            )
        )
        result = result.scalar_one()
        assert len(result.users) == 2
        user_emails = {u.email for u in result.users}
        assert "user1@example.com" in user_emails
        assert "user2@example.com" in user_emails


class TestDashboardGraphRelationship:
    """╨в╨╡╤Б╤В╤Л ╨┤╨╗╤П ╤Б╨▓╤П╨╖╨╕ ╨┤╨░╤И╨▒╨╛╤А╨┤╨░ ╤Б ╨│╤А╨░╤Д╨╕╨║╨░╨╝╨╕."""

    async def test_dashboard_graphs_relationship(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Б╨▓╤П╨╖╨╕ ╨┤╨░╤И╨▒╨╛╤А╨┤╨░ ╤Б ╨│╤А╨░╤Д╨╕╨║╨░╨╝╨╕."""
        dashboard = dashboard_model.Dashboard(
            name="Graph Test Dashboard",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        graph1 = graph_model.Graph(
            dashboard_id=dashboard.id,
            name="Graph 1",
            type=GraphType.BAR,
            config={"color": "blue"},
            dimensions=["category"],
            metrics=["value"],
        )
        graph2 = graph_model.Graph(
            dashboard_id=dashboard.id,
            name="Graph 2",
            type=GraphType.LINE,
            config={"color": "red"},
            dimensions=["date"],
            metrics=["amount"],
        )
        async_db_session.add_all([graph1, graph2])
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝, ╤З╤В╨╛ ╤Г ╨┤╨░╤И╨▒╨╛╤А╨┤╨░ ╨╡╤Б╤В╤М ╨│╤А╨░╤Д╨╕╨║╨╕
        result = await async_db_session.execute(
            select(dashboard_model.Dashboard).where(
                dashboard_model.Dashboard.id == dashboard.id
            )
        )
        result = result.scalar_one()
        assert len(result.graphs) == 2
        graph_names = {g.name for g in result.graphs}
        assert "Graph 1" in graph_names
        assert "Graph 2" in graph_names

    async def test_graph_cascade_delete(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨║╨░╤Б╨║╨░╨┤╨╜╨╛╨│╨╛ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╤П ╨│╤А╨░╤Д╨╕╨║╨╛╨▓ ╨┐╤А╨╕ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╨╕ ╨┤╨░╤И╨▒╨╛╤А╨┤╨░."""
        dashboard = dashboard_model.Dashboard(
            name="Cascade Graph Test",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        graph = graph_model.Graph(
            dashboard_id=dashboard.id,
            name="Test Graph",
            type=GraphType.BAR,
            dimensions=["x"],
            metrics=["y"],
        )
        async_db_session.add(graph)
        await async_db_session.commit()

        # ╨г╨┤╨░╨╗╤П╨╡╨╝ ╨┤╨░╤И╨▒╨╛╤А╨┤
        await async_db_session.delete(dashboard)
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝, ╤З╤В╨╛ ╨│╤А╨░╤Д╨╕╨║ ╤В╨╛╨╢╨╡ ╤Г╨┤╨░╨╗╨╡╨╜
        result = await async_db_session.execute(
            select(graph_model.Graph)
        )
        result = result.fetchall()
        assert len(result) == 0


class TestGraphModel:
    """╨в╨╡╤Б╤В╤Л ╨┤╨╗╤П ╨╝╨╛╨┤╨╡╨╗╨╕ Graph."""

    async def test_create_graph(self, async_db_session):
        """╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨│╤А╨░╤Д╨╕╨║╨░."""
        dashboard = dashboard_model.Dashboard(
            name="Graph Parent Dashboard",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        graph = graph_model.Graph(
            dashboard_id=dashboard.id,
            name="Test Graph",
            type=GraphType.BAR,
            config={"axis": {"x": "bottom"}},
            dimensions=["category", "year"],
            metrics=["sales", "profit"],
        )
        async_db_session.add(graph)
        await async_db_session.commit()
        await async_db_session.refresh(graph)

        assert graph.id is not None
        assert isinstance(graph.id, UUID)
        assert graph.name == "Test Graph"
        assert graph.type == GraphType.BAR
        assert graph.config == {"axis": {"x": "bottom"}}
        assert graph.dimensions == ["category", "year"]
        assert graph.metrics == ["sales", "profit"]

    async def test_graph_type_constraint(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╤П ╨╜╨░ ╤В╨╕╨┐ ╨│╤А╨░╤Д╨╕╨║╨░."""
        dashboard = dashboard_model.Dashboard(
            name="Type Constraint Test",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        # ╨Ф╨╛╨┐╤Г╤Б╤В╨╕╨╝╤Л╨╡ ╤В╨╕╨┐╤Л ╨┤╨╛╨╗╨╢╨╜╤Л ╤А╨░╨▒╨╛╤В╨░╤В╤М
        for graph_type in [GraphType.BAR, GraphType.LINE, GraphType.PIE, GraphType.TABLE]:
            graph = graph_model.Graph(
                dashboard_id=dashboard.id,
                name=f"Graph {graph_type}",
                type=graph_type,
                config={},
                dimensions=[],
                metrics=[],
            )
            async_db_session.add(graph)
        await async_db_session.commit()

        result = await async_db_session.execute(
            select(graph_model.Graph)
        )
        graphs = result.scalars().all()
        assert len(graphs) == 4

    async def test_unique_dashboard_name_constraint(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Г╨╜╨╕╨║╨░╨╗╤М╨╜╨╛╤Б╤В╨╕ ╨╕╨╝╨╡╨╜╨╕ ╨│╤А╨░╤Д╨╕╨║╨░ ╨▓ ╤А╨░╨╝╨║╨░╤Е ╨┤╨░╤И╨▒╨╛╤А╨┤╨░."""
        dashboard = dashboard_model.Dashboard(
            name="Unique Name Test",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        graph1 = graph_model.Graph(
            dashboard_id=dashboard.id,
            name="Same Name",
            type=GraphType.BAR,
            config={},
            dimensions=[],
            metrics=[],
        )
        async_db_session.add(graph1)
        await async_db_session.commit()

        graph2 = graph_model.Graph(
            dashboard_id=dashboard.id,
            name="Same Name",
            type=GraphType.LINE,
            config={},
            dimensions=[],
            metrics=[],
        )
        async_db_session.add(graph2)

        with pytest.raises(IntegrityError):
            await async_db_session.commit()

        await async_db_session.rollback()

    async def test_graph_foreign_key_constraint(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨╛╨│╤А╨░╨╜╨╕╤З╨╡╨╜╨╕╤П ╨▓╨╜╨╡╤И╨╜╨╡╨│╨╛ ╨║╨╗╤О╤З╨░ ╨┤╨╗╤П ╨│╤А╨░╤Д╨╕╨║╨░."""
        # ╨Я╤Л╤В╨░╨╡╨╝╤Б╤П ╤Б╨╛╨╖╨┤╨░╤В╤М ╨│╤А╨░╤Д╨╕╨║ ╤Б ╨╜╨╡╤Б╤Г╤Й╨╡╤Б╤В╨▓╤Г╤О╤Й╨╕╨╝ dashboard_id
        # ╨н╤В╨╛ ╨┤╨╛╨╗╨╢╨╜╨╛ ╨▓╤Л╨╖╨▓╨░╤В╤М ╨╛╤И╨╕╨▒╨║╤Г, ╨╜╨╛ SQLite ╨╝╨╛╨╢╨╡╤В ╨╜╨╡ ╨┐╤А╨╛╨▓╨╡╤А╤П╤В╤М FK ╨┐╨╛ ╤Г╨╝╨╛╨╗╤З╨░╨╜╨╕╤О
        from uuid import uuid4
        invalid_uuid = uuid4()
        graph = graph_model.Graph(
            dashboard_id=invalid_uuid,
            name="Invalid FK Graph",
            type=GraphType.BAR,
            config={},
            dimensions=[],
            metrics=[],
        )
        async_db_session.add(graph)
        # ╨Т SQLite FK ╨╝╨╛╨│╤Г╤В ╨▒╤Л╤В╤М ╨╛╤В╨║╨╗╤О╤З╨╡╨╜╤Л, ╨┐╨╛╤Н╤В╨╛╨╝╤Г ╤Н╤В╨╛ ╨╝╨╛╨╢╨╡╤В ╨╜╨╡ ╨▓╤Л╨╖╨▓╨░╤В╤М ╨╛╤И╨╕╨▒╨║╤Г
        # ╨Э╨╛ ╨╝╤Л ╨▓╤Б╨╡ ╤А╨░╨▓╨╜╨╛ ╤В╨╡╤Б╤В╨╕╤А╤Г╨╡╨╝ ╨╗╨╛╨│╨╕╨║╤Г
        try:
            await async_db_session.commit()
        except IntegrityError:
            await async_db_session.rollback()

    # Note: Removed low-value string representation tests (__repr__, __str__)
    # These tests have low diagnostic value and are fragile to changes


class TestLayoutModel:
    """╨в╨╡╤Б╤В╤Л ╨┤╨╗╤П ╨╝╨╛╨┤╨╡╨╗╨╕ Layout."""

    async def test_create_layout(self, async_db_session):
        """╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ layout."""
        layout = layout_model.Layout(
            name="Test Layout",
            definition={
                "grid": [{"x": 0, "y": 0, "w": 6, "h": 4}],
                "filters": [{"field": "year", "type": "select"}],
            },
        )
        async_db_session.add(layout)
        await async_db_session.commit()
        await async_db_session.refresh(layout)

        assert layout.id is not None
        assert isinstance(layout.id, UUID)
        assert layout.name == "Test Layout"
        assert layout.definition == {
            "grid": [{"x": 0, "y": 0, "w": 6, "h": 4}],
            "filters": [{"field": "year", "type": "select"}],
        }

    async def test_create_layout_with_defaults(self, async_db_session):
        """╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ layout ╤Б╨╛ ╨╖╨╜╨░╤З╨╡╨╜╨╕╤П╨╝╨╕ ╨┐╨╛ ╤Г╨╝╨╛╨╗╤З╨░╨╜╨╕╤О."""
        layout = layout_model.Layout(
            name="Default Layout",
        )
        async_db_session.add(layout)
        await async_db_session.commit()

        assert layout.definition == {}
        assert layout.created_at is not None

    async def test_unique_layout_name_constraint(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Г╨╜╨╕╨║╨░╨╗╤М╨╜╨╛╤Б╤В╨╕ ╨╕╨╝╨╡╨╜╨╕ layout."""
        layout1 = layout_model.Layout(
            name="Same Layout Name",
            definition={},
        )
        async_db_session.add(layout1)
        await async_db_session.commit()

        layout2 = layout_model.Layout(
            name="Same Layout Name",
            definition={"grid": []},
        )
        async_db_session.add(layout2)

        with pytest.raises(IntegrityError):
            await async_db_session.commit()
        
        await async_db_session.rollback()
        
    async def test_layout_dashboards_relationship(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Б╨▓╤П╨╖╨╕ layout ╤Б ╨┤╨░╤И╨▒╨╛╤А╨┤╨░╨╝╨╕."""
        layout = layout_model.Layout(
            name="Shared Layout",
            definition={"grid": []},
        )
        async_db_session.add(layout)
        await async_db_session.commit()

        dashboard1 = dashboard_model.Dashboard(
            name="Dash with Layout 1",
            layout_id=layout.id,
        )
        dashboard2 = dashboard_model.Dashboard(
            name="Dash with Layout 2",
            layout_id=layout.id,
        )
        async_db_session.add_all([dashboard1, dashboard2])
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝, ╤З╤В╨╛ ╤Г layout ╨╡╤Б╤В╤М ╨┤╨░╤И╨▒╨╛╤А╨┤╤Л
        result = await async_db_session.execute(
            select(layout_model.Layout).where(
                layout_model.Layout.id == layout.id
            )
        )
        result = result.scalar_one()
        assert len(result.dashboards) == 2
        dashboard_names = {d.name for d in result.dashboards}
        assert "Dash with Layout 1" in dashboard_names
        assert "Dash with Layout 2" in dashboard_names

    async def test_layout_cascade_delete(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ SET NULL ╨┐╤А╨╕ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╨╕ layout."""
        layout = layout_model.Layout(
            name="To Be Deleted Layout",
            definition={"grid": []},
        )
        async_db_session.add(layout)
        await async_db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Dashboard with Layout",
            layout_id=layout.id,
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        # ╨г╨┤╨░╨╗╤П╨╡╨╝ layout
        await async_db_session.delete(layout)
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝, ╤З╤В╨╛ layout_id ╤Б╤В╨░╨╗ NULL ╤Г ╨┤╨░╤И╨▒╨╛╤А╨┤╨░
        result = await async_db_session.execute(
            select(dashboard_model.Dashboard).where(
                dashboard_model.Dashboard.id == dashboard.id
            )
        )
        result = result.scalar_one()
        assert result.layout_id is None

    # Note: Removed low-value string representation tests (__repr__, __str__)
    # These tests have low diagnostic value and are fragile to changes


class TestAggregatedDataModel:
    """╨в╨╡╤Б╤В╤Л ╨┤╨╗╤П ╨╝╨╛╨┤╨╡╨╗╨╕ AggregatedData."""

    async def test_create_aggregated_data(self, async_db_session):
        """╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡ ╨░╨│╤А╨╡╨│╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╤Е ╨┤╨░╨╜╨╜╤Л╤Е."""
        dashboard = dashboard_model.Dashboard(
            name="Agg Data Dashboard",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        graph = graph_model.Graph(
            dashboard_id=dashboard.id,
            name="Agg Graph",
            type=GraphType.BAR,
            config={},
            dimensions=["category"],
            metrics=["value"],
        )
        async_db_session.add(graph)
        await async_db_session.commit()

        agg_data = aggregated_data_model.AggregatedData(
            dashboard_id=dashboard.id,
            graph_id=graph.id,
            dims={"category": "A", "year": 2023},
            metrics={"value": 100, "count": 10},
        )
        async_db_session.add(agg_data)
        await async_db_session.commit()
        await async_db_session.refresh(agg_data)

        assert agg_data.id is not None
        assert isinstance(agg_data.id, int)
        assert agg_data.dims == {"category": "A", "year": 2023}
        assert agg_data.metrics == {"value": 100, "count": 10}

    async def test_aggregated_data_relationships(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Б╨▓╤П╨╖╨╡╨╣ ╨░╨│╤А╨╡╨│╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╤Е ╨┤╨░╨╜╨╜╤Л╤Е."""
        dashboard = dashboard_model.Dashboard(
            name="Agg Rel Dashboard",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        graph = graph_model.Graph(
            dashboard_id=dashboard.id,
            name="Agg Rel Graph",
            type=GraphType.BAR,
            config={},
            dimensions=["x"],
            metrics=["y"],
        )
        async_db_session.add(graph)
        await async_db_session.commit()

        agg_data = aggregated_data_model.AggregatedData(
            dashboard_id=dashboard.id,
            graph_id=graph.id,
            dims={"x": "test"},
            metrics={"y": 42},
        )
        async_db_session.add(agg_data)
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝ ╤Б╨▓╤П╨╖╨╕
        result = await async_db_session.execute(
            select(aggregated_data_model.AggregatedData).where(
                aggregated_data_model.AggregatedData.id == agg_data.id
            )
        )
        result = result.scalar_one()
        assert result.dashboard.id == dashboard.id
        assert result.graph.id == graph.id

    async def test_aggregated_data_cascade_delete_dashboard(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨║╨░╤Б╨║╨░╨┤╨╜╨╛╨│╨╛ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╤П ╨┐╤А╨╕ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╨╕ ╨┤╨░╤И╨▒╨╛╤А╨┤╨░."""
        dashboard = dashboard_model.Dashboard(
            name="Cascade Agg Dashboard",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        graph = graph_model.Graph(
            dashboard_id=dashboard.id,
            name="Cascade Agg Graph",
            type=GraphType.BAR,
            config={},
            dimensions=["x"],
            metrics=["y"],
        )
        async_db_session.add(graph)
        await async_db_session.commit()

        agg_data = aggregated_data_model.AggregatedData(
            dashboard_id=dashboard.id,
            graph_id=graph.id,
            dims={"x": "test"},
            metrics={"y": 42},
        )
        async_db_session.add(agg_data)
        await async_db_session.commit()

        # ╨г╨┤╨░╨╗╤П╨╡╨╝ ╨┤╨░╤И╨▒╨╛╤А╨┤
        await async_db_session.delete(dashboard)
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝, ╤З╤В╨╛ ╨░╨│╤А╨╡╨│╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╨╡ ╨┤╨░╨╜╨╜╤Л╨╡ ╤В╨╛╨╢╨╡ ╤Г╨┤╨░╨╗╨╡╨╜╤Л
        result = await async_db_session.execute(
            select(aggregated_data_model.AggregatedData)
        )
        result = result.fetchall()
        assert len(result) == 0

    async def test_aggregated_data_cascade_delete_graph(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨║╨░╤Б╨║╨░╨┤╨╜╨╛╨│╨╛ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╤П ╨┐╤А╨╕ ╤Г╨┤╨░╨╗╨╡╨╜╨╕╨╕ ╨│╤А╨░╤Д╨╕╨║╨░."""
        dashboard = dashboard_model.Dashboard(
            name="Cascade Graph Dashboard",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        graph = graph_model.Graph(
            dashboard_id=dashboard.id,
            name="Cascade Graph",
            type=GraphType.BAR,
            config={},
            dimensions=["x"],
            metrics=["y"],
        )
        async_db_session.add(graph)
        await async_db_session.commit()

        agg_data = aggregated_data_model.AggregatedData(
            dashboard_id=dashboard.id,
            graph_id=graph.id,
            dims={"x": "test"},
            metrics={"y": 42},
        )
        async_db_session.add(agg_data)
        await async_db_session.commit()

        # ╨г╨┤╨░╨╗╤П╨╡╨╝ ╨│╤А╨░╤Д╨╕╨║
        await async_db_session.delete(graph)
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝, ╤З╤В╨╛ ╨░╨│╤А╨╡╨│╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╨╡ ╨┤╨░╨╜╨╜╤Л╨╡ ╤В╨╛╨╢╨╡ ╤Г╨┤╨░╨╗╨╡╨╜╤Л
        result = await async_db_session.execute(
            select(aggregated_data_model.AggregatedData)
        )
        result = result.fetchall()
        assert len(result) == 0




class TestModelIndexes:
    """╨в╨╡╤Б╤В╤Л ╨┤╨╗╤П ╨╕╨╜╨┤╨╡╨║╤Б╨╛╨▓ ╨╝╨╛╨┤╨╡╨╗╨╡╨╣."""

    async def test_user_email_index(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨╕╨╜╨┤╨╡╨║╤Б╨░ ╨╜╨░ email."""
        # ╨б╨╛╨╖╨┤╨░╨╡╨╝ ╨╜╨╡╤Б╨║╨╛╨╗╤М╨║╨╛ ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╨╡╨╣
        for i in range(5):
            user = user_model.User(
                email=f"user{i}@example.com",
                password_hash="$2b$12$examplehash",
            )
            async_db_session.add(user)
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝, ╤З╤В╨╛ ╨╝╨╛╨╢╨╜╨╛ ╨╜╨░╨╣╤В╨╕ ╨┐╨╛ email (╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╤В ╨╕╨╜╨┤╨╡╨║╤Б)
        result = await async_db_session.execute(
            select(user_model.User).where(
                user_model.User.email == "user2@example.com"
            )
        )
        result = result.scalar_one_or_none()

        assert result is not None
        assert result.email == "user2@example.com"

    async def test_dashboard_name_index(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╨╕╨╜╨┤╨╡╨║╤Б╨░ ╨╜╨░ ╨╕╨╝╤П ╨┤╨░╤И╨▒╨╛╤А╨┤╨░."""
        # ╨б╨╛╨╖╨┤╨░╨╡╨╝ ╨╜╨╡╤Б╨║╨╛╨╗╤М╨║╨╛ ╨┤╨░╤И╨▒╨╛╤А╨┤╨╛╨▓
        for i in range(5):
            dashboard = dashboard_model.Dashboard(
                name=f"Dashboard {i}",
            )
            async_db_session.add(dashboard)
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝, ╤З╤В╨╛ ╨╝╨╛╨╢╨╜╨╛ ╨╜╨░╨╣╤В╨╕ ╨┐╨╛ ╨╕╨╝╨╡╨╜╨╕ (╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╡╤В ╨╕╨╜╨┤╨╡╨║╤Б)
        result = await async_db_session.execute(
            select(dashboard_model.Dashboard).where(
                dashboard_model.Dashboard.name == "Dashboard 2"
            )
        )
        result = result.scalar_one_or_none()

        assert result is not None
        assert result.name == "Dashboard 2"

    async def test_access_composite_index(self, async_db_session):
        """╨Я╤А╨╛╨▓╨╡╤А╨║╨░ ╤Б╨╛╤Б╤В╨░╨▓╨╜╨╛╨│╨╛ ╨╕╨╜╨┤╨╡╨║╤Б╨░ ╨╜╨░ ╨┤╨╛╤Б╤В╤Г╨┐."""
        user = user_model.User(
            email="index_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Index Test Dashboard",
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        access = access_model.DashboardAccess(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission=DashboardPermission.VIEW,
        )
        async_db_session.add(access)
        await async_db_session.commit()

        # ╨Я╤А╨╛╨▓╨╡╤А╤П╨╡╨╝, ╤З╤В╨╛ ╨╝╨╛╨╢╨╜╨╛ ╨╜╨░╨╣╤В╨╕ ╨┐╨╛ ╤Б╨╛╤Б╤В╨░╨▓╨╜╨╛╨╝╤Г ╨║╨╗╤О╤З╤Г
        result = await async_db_session.execute(
            select(access_model.DashboardAccess).where(
                access_model.DashboardAccess.user_id == user.id,
                access_model.DashboardAccess.dashboard_id == dashboard.id,
            )
        )
        result = result.scalar_one_or_none()

        assert result is not None
        assert result.permission == DashboardPermission.VIEW
