"""Тесты для базовых моделей SQLAlchemy (User, Dashboard, Access).

Тестирует создание, чтение, обновление и удаление моделей,
а также проверки ограничений и связей.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from uuid import UUID

from mko_bi.db.models import user as user_model
from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.db.models import access as access_model


class TestUserModel:
    """Тесты для модели User."""

    async def test_create_user(self, async_db_session):
        """Создание пользователя с валидными данными."""
        user = user_model.User(
            email="test@example.com",
            password_hash="$2b$12$examplehash",
            role="viewer",
            is_active=True,
        )
        async_db_session.add(user)
        await async_db_session.commit()
        await async_db_session.refresh(user)

        assert user.id is not None
        assert isinstance(user.id, UUID)
        assert user.email == "test@example.com"
        assert user.role == "viewer"
        assert user.is_active is True

    async def test_create_user_with_default_role(self, async_db_session):
        """Создание пользователя с ролью по умолчанию."""
        user = user_model.User(
            email="test2@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        assert user.role == "viewer"

    async def test_create_user_with_default_is_active(self, async_db_session):
        """Создание пользователя с is_active по умолчанию."""
        user = user_model.User(
            email="test3@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        assert user.is_active is True

    async def test_unique_email_constraint(self, async_db_session):
        """Проверка уникальности email."""
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


class TestDashboardModel:
    """Тесты для модели Dashboard."""

    async def test_create_dashboard(self, async_db_session):
        """Создание дашборда с валидными данными."""
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            description="Test description",
            config={"graph_types": ["bar"]},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()
        await async_db_session.refresh(dashboard)

        assert dashboard.id is not None
        assert isinstance(dashboard.id, UUID)
        assert dashboard.name == "Test Dashboard"
        assert dashboard.description == "Test description"
        assert dashboard.config == {"graph_types": ["bar"]}

    async def test_create_dashboard_with_defaults(self, async_db_session):
        """Создание дашборда со значениями по умолчанию."""
        dashboard = dashboard_model.Dashboard(
            name="Default Dashboard",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        assert dashboard.description is None
        assert dashboard.config == {}
        assert dashboard.updated_at is not None

    async def test_unique_name_constraint(self, async_db_session):
        """Проверка уникальности имени дашборда."""
        dashboard1 = dashboard_model.Dashboard(
            name="Same Name",
            config={},
        )
        async_db_session.add(dashboard1)
        await async_db_session.commit()

        dashboard2 = dashboard_model.Dashboard(
            name="Same Name",
            config={},
        )
        async_db_session.add(dashboard2)

        with pytest.raises(IntegrityError):
            await async_db_session.commit()

        await async_db_session.rollback()

    async def test_dashboard_updated_at_auto_update(self, async_db_session):
        """Проверка автоматического обновления updated_at."""
        dashboard = dashboard_model.Dashboard(
            name="Update Test",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()
        await async_db_session.refresh(dashboard)

        old_updated_at = dashboard.updated_at

        # Обновляем дашборд
        dashboard.name = "Updated Name"
        await async_db_session.commit()
        await async_db_session.refresh(dashboard)

        assert dashboard.updated_at > old_updated_at


class TestAccessModel:
    """Тесты для модели Access."""

    async def test_create_access(self, async_db_session):
        """Создание права доступа."""
        # Создаем пользователя
        user = user_model.User(
            email="access_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        # Создаем дашборд
        dashboard = dashboard_model.Dashboard(
            name="Access Test Dashboard",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        # Создаем доступ
        access = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="view",
        )
        async_db_session.add(access)
        await async_db_session.commit()
        await async_db_session.refresh(access)

        assert access.user_id == user.id
        assert access.dashboard_id == dashboard.id
        assert access.permission == "view"

    async def test_unique_composite_key(self, async_db_session):
        """Проверка уникальности составного ключа (user_id, dashboard_id)."""
        user = user_model.User(
            email="composite_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Composite Test",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        access1 = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="view",
        )
        async_db_session.add(access1)
        await async_db_session.commit()

        access2 = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="edit",
        )
        async_db_session.add(access2)

        with pytest.raises(IntegrityError):
            await async_db_session.commit()

        await async_db_session.rollback()

    async def test_cascade_delete_user(self, async_db_session):
        """Проверка каскадного удаления при удалении пользователя."""
        user = user_model.User(
            email="cascade_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Cascade Test",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        access = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="view",
        )
        async_db_session.add(access)
        await async_db_session.commit()

        # Удаляем пользователя
        await async_db_session.delete(user)
        await async_db_session.commit()

        # Проверяем, что доступ тоже удален
        result = await async_db_session.execute(
            select(access_model.Access)
        )
        accesses = result.scalars().all()
        assert len(accesses) == 0

    async def test_cascade_delete_dashboard(self, async_db_session):
        """Проверка каскадного удаления при удалении дашборда."""
        user = user_model.User(
            email="cascade_dash_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        async_db_session.add(user)
        await async_db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Cascade Dash Test",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        access = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="view",
        )
        async_db_session.add(access)
        await async_db_session.commit()

        # Удаляем дашборд
        await async_db_session.delete(dashboard)
        await async_db_session.commit()

        # Проверяем, что доступ тоже удален
        result = await async_db_session.execute(
            select(access_model.Access)
        )
        accesses = result.scalars().all()
        assert len(accesses) == 0


class TestModelIndexes:
    """Тесты для индексов моделей."""

    async def test_user_email_index(self, async_db_session):
        """Проверка индекса на email."""
        # Создаем несколько пользователей
        for i in range(5):
            user = user_model.User(
                email=f"user{i}@example.com",
                password_hash="$2b$12$examplehash",
            )
            async_db_session.add(user)
        await async_db_session.commit()

        # Проверяем, что можно найти по email (использует индекс)
        result = await async_db_session.execute(
            select(user_model.User).where(
                user_model.User.email == "user2@example.com"
            )
        )
        user = result.scalar_one_or_none()

        assert user is not None
        assert user.email == "user2@example.com"

    async def test_dashboard_name_index(self, async_db_session):
        """Проверка индекса на имя дашборда."""
        # Создаем несколько дашбордов
        for i in range(5):
            dashboard = dashboard_model.Dashboard(
                name=f"Dashboard {i}",
                config={},
            )
            async_db_session.add(dashboard)
        await async_db_session.commit()

        # Проверяем, что можно найти по имени (использует индекс)
        result = await async_db_session.execute(
            select(dashboard_model.Dashboard).where(
                dashboard_model.Dashboard.name == "Dashboard 2"
            )
        )
        dashboard = result.scalar_one_or_none()

        assert dashboard is not None
        assert dashboard.name == "Dashboard 2"
