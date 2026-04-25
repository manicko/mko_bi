"""Тесты для базовых моделей SQLAlchemy (User, Dashboard, Access).

Тестирует создание, чтение, обновление и удаление моделей,
а также проверки ограничений и связей.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from mko_bi.db.models import user as user_model
from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.db.models import access as access_model


class TestUserModel:
    """Тесты для модели User."""

    def test_create_user(self, db_session):
        """Создание пользователя с валидными данными."""
        user = user_model.User(
            email="test@example.com",
            password_hash="$2b$12$examplehash",
            role="viewer",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert isinstance(user.id, UUID)
        assert user.email == "test@example.com"
        assert user.role == "viewer"
        assert user.is_active is True

    def test_create_user_with_default_role(self, db_session):
        """Создание пользователя с ролью по умолчанию."""
        user = user_model.User(
            email="test2@example.com",
            password_hash="$2b$12$examplehash",
        )
        db_session.add(user)
        db_session.commit()

        assert user.role == "viewer"

    def test_create_user_with_default_is_active(self, db_session):
        """Создание пользователя с is_active по умолчанию."""
        user = user_model.User(
            email="test3@example.com",
            password_hash="$2b$12$examplehash",
        )
        db_session.add(user)
        db_session.commit()

        assert user.is_active is True

    def test_unique_email_constraint(self, db_session):
        """Проверка уникальности email."""
        user1 = user_model.User(
            email="duplicate@example.com",
            password_hash="$2b$12$examplehash",
        )
        db_session.add(user1)
        db_session.commit()

        user2 = user_model.User(
            email="duplicate@example.com",
            password_hash="$2b$12$examplehash2",
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_user_role_constraint(self, db_session):
        """Проверка ограничения на роль."""
        user = user_model.User(
            email="invalid_role@example.com",
            password_hash="$2b$12$examplehash",
            role="invalid_role",
        )
        db_session.add(user)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_user_str_representation(self, db_session):
        """Проверка строкового представления пользователя."""
        user = user_model.User(
            email="str_test@example.com",
            password_hash="$2b$12$examplehash",
        )
        db_session.add(user)
        db_session.commit()

        assert str(user) == "str_test@example.com"
        assert "str_test@example.com" in repr(user)
        assert user.role in repr(user)

    def test_user_relationships(self, db_session):
        """Проверка связей пользователя."""
        user = user_model.User(
            email="rel_test@example.com",
            password_hash="$2b$12$examplehash",
        )
        db_session.add(user)
        db_session.commit()

        # Создаем дашборд
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={},
        )
        db_session.add(dashboard)
        db_session.commit()

        # Создаем доступ
        access = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="view",
        )
        db_session.add(access)
        db_session.commit()

        db_session.refresh(user)
        db_session.refresh(dashboard)

        assert len(user.accesses) == 1
        assert user.accesses[0].permission == "view"
        assert len(user.dashboards) == 1
        assert user.dashboards[0].name == "Test Dashboard"


class TestDashboardModel:
    """Тесты для модели Dashboard."""

    def test_create_dashboard(self, db_session):
        """Создание дашборда с валидными данными."""
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            description="Test description",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        assert dashboard.id is not None
        assert isinstance(dashboard.id, UUID)
        assert dashboard.name == "Test Dashboard"
        assert dashboard.description == "Test description"
        assert dashboard.config == {"graph_types": ["bar"]}

    def test_create_dashboard_with_defaults(self, db_session):
        """Создание дашборда со значениями по умолчанию."""
        dashboard = dashboard_model.Dashboard(
            name="Default Dashboard",
            config={},
        )
        db_session.add(dashboard)
        db_session.commit()

        assert dashboard.description is None
        assert dashboard.config == {}
        assert dashboard.updated_at is not None

    def test_unique_name_constraint(self, db_session):
        """Проверка уникальности имени дашборда."""
        dashboard1 = dashboard_model.Dashboard(
            name="Same Name",
            config={},
        )
        db_session.add(dashboard1)
        db_session.commit()

        dashboard2 = dashboard_model.Dashboard(
            name="Same Name",
            config={},
        )
        db_session.add(dashboard2)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_dashboard_updated_at_auto_update(self, db_session):
        """Проверка автоматического обновления updated_at."""
        dashboard = dashboard_model.Dashboard(
            name="Update Test",
            config={},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        old_updated_at = dashboard.updated_at

        # Обновляем дашборд
        dashboard.name = "Updated Name"
        db_session.commit()
        db_session.refresh(dashboard)

        assert dashboard.updated_at > old_updated_at

    def test_dashboard_str_representation(self, db_session):
        """Проверка строкового представления дашборда."""
        dashboard = dashboard_model.Dashboard(
            name="Str Test",
            config={},
        )
        db_session.add(dashboard)
        db_session.commit()

        assert str(dashboard) == "Str Test"
        assert "Str Test" in repr(dashboard)

    def test_dashboard_relationships(self, db_session):
        """Проверка связей дашборда."""
        # Создаем пользователя
        user = user_model.User(
            email="dash_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        db_session.add(user)
        db_session.commit()

        # Создаем дашборд
        dashboard = dashboard_model.Dashboard(
            name="Relationship Test",
            config={},
        )
        db_session.add(dashboard)
        db_session.commit()

        # Создаем доступ
        access = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="edit",
        )
        db_session.add(access)
        db_session.commit()

        db_session.refresh(dashboard)
        db_session.refresh(user)

        assert len(dashboard.accesses) == 1
        assert dashboard.accesses[0].permission == "edit"
        assert len(dashboard.users) == 1
        assert dashboard.users[0].email == "dash_user@example.com"


class TestAccessModel:
    """Тесты для модели Access."""

    def test_create_access(self, db_session):
        """Создание права доступа."""
        # Создаем пользователя
        user = user_model.User(
            email="access_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        db_session.add(user)
        db_session.commit()

        # Создаем дашборд
        dashboard = dashboard_model.Dashboard(
            name="Access Test Dashboard",
            config={},
        )
        db_session.add(dashboard)
        db_session.commit()

        # Создаем доступ
        access = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="view",
        )
        db_session.add(access)
        db_session.commit()
        db_session.refresh(access)

        assert access.user_id == user.id
        assert access.dashboard_id == dashboard.id
        assert access.permission == "view"

    def test_unique_composite_key(self, db_session):
        """Проверка уникальности составного ключа (user_id, dashboard_id)."""
        user = user_model.User(
            email="composite_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        db_session.add(user)
        db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Composite Test",
            config={},
        )
        db_session.add(dashboard)
        db_session.commit()

        access1 = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="view",
        )
        db_session.add(access1)
        db_session.commit()

        access2 = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="edit",
        )
        db_session.add(access2)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_permission_constraint(self, db_session):
        """Проверка ограничения на уровень доступа."""
        user = user_model.User(
            email="perm_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        db_session.add(user)
        db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Perm Test",
            config={},
        )
        db_session.add(dashboard)
        db_session.commit()

        access = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="invalid",
        )
        db_session.add(access)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_foreign_key_constraints(self, db_session):
        """Проверка ограничений внешних ключей."""
        # Пробуем создать доступ с несуществующим user_id
        dashboard = dashboard_model.Dashboard(
            name="FK Test",
            config={},
        )
        db_session.add(dashboard)
        db_session.commit()

        from uuid import uuid4
        non_existent_user_id = uuid4()

        access = access_model.Access(
            user_id=non_existent_user_id,
            dashboard_id=dashboard.id,
            permission="view",
        )
        db_session.add(access)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_cascade_delete_user(self, db_session):
        """Проверка каскадного удаления при удалении пользователя."""
        user = user_model.User(
            email="cascade_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        db_session.add(user)
        db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Cascade Test",
            config={},
        )
        db_session.add(dashboard)
        db_session.commit()

        access = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="view",
        )
        db_session.add(access)
        db_session.commit()

        # Удаляем пользователя
        db_session.delete(user)
        db_session.commit()

        # Проверяем, что доступ тоже удален
        result = db_session.execute(
            access_model.Access.__table__.select()
        ).fetchall()
        assert len(result) == 0

    def test_cascade_delete_dashboard(self, db_session):
        """Проверка каскадного удаления при удалении дашборда."""
        user = user_model.User(
            email="cascade_dash_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        db_session.add(user)
        db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Cascade Dash Test",
            config={},
        )
        db_session.add(dashboard)
        db_session.commit()

        access = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="view",
        )
        db_session.add(access)
        db_session.commit()

        # Удаляем дашборд
        db_session.delete(dashboard)
        db_session.commit()

        # Проверяем, что доступ тоже удален
        result = db_session.execute(
            access_model.Access.__table__.select()
        ).fetchall()
        assert len(result) == 0

    def test_access_str_representation(self, db_session):
        """Проверка строкового представления права доступа."""
        user = user_model.User(
            email="str_access_user@example.com",
            password_hash="$2b$12$examplehash",
        )
        db_session.add(user)
        db_session.commit()

        dashboard = dashboard_model.Dashboard(
            name="Str Access Test",
            config={},
        )
        db_session.add(dashboard)
        db_session.commit()

        access = access_model.Access(
            user_id=user.id,
            dashboard_id=dashboard.id,
            permission="edit",
        )
        db_session.add(access)
        db_session.commit()

        access_str = repr(access)
        assert str(user.id) in access_str
        assert str(dashboard.id) in access_str
        assert "edit" in access_str


class TestModelIndexes:
    """Тесты для индексов моделей."""

    def test_user_email_index(self, db_session):
        """Проверка индекса на email."""
        # Создаем несколько пользователей
        for i in range(5):
            user = user_model.User(
                email=f"user{i}@example.com",
                password_hash="$2b$12$examplehash",
            )
            db_session.add(user)
        db_session.commit()

        # Проверяем, что можно найти по email (использует индекс)
        result = db_session.execute(
            user_model.User.__table__.select().where(
                user_model.User.email == "user2@example.com"
            )
        ).scalar_one_or_none()

        assert result is not None
        assert result.email == "user2@example.com"

    def test_dashboard_name_index(self, db_session):
        """Проверка индекса на имя дашборда."""
        # Создаем несколько дашбордов
        for i in range(5):
            dashboard = dashboard_model.Dashboard(
                name=f"Dashboard {i}",
                config={},
            )
            db_session.add(dashboard)
        db_session.commit()

        # Проверяем, что можно найти по имени (использует индекс)
        result = db_session.execute(
            dashboard_model.Dashboard.__table__.select().where(
                dashboard_model.Dashboard.name == "Dashboard 2"
            )
        ).scalar_one_or_none()

        assert result is not None
        assert result.name == "Dashboard 2"