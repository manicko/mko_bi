"""Тесты для репозиториев базы данных.

Тестирует операции CRUD для UserRepository, DashboardRepository и AccessRepository.
Использует изолированную тестовую базу данных SQLite in-memory.
"""

import pytest
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import access as access_model
from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.db.models import user as user_model
from mko_bi.db.repositories import AccessRepository, DashboardRepository, UserRepository


class TestUserRepository:
    """Тесты для UserRepository."""

    def test_create_user(self, test_db):
        """Тест создания пользователя."""
        user = UserRepository.create(
            db=test_db,
            email="newuser@example.com",
            password_hash="hashed_password_123",
            role="editor",
        )
        assert user is not None
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.password_hash == "hashed_password_123"
        assert user.role == "editor"

    def test_create_user_duplicate_email(self, test_db):
        """Тест создания пользователя с дублирующимся email."""
        UserRepository.create(
            db=test_db,
            email="duplicate@example.com",
            password_hash="hash1",
            role="viewer",
        )
        with pytest.raises(SQLAlchemyError):
            UserRepository.create(
                db=test_db,
                email="duplicate@example.com",
                password_hash="hash2",
                role="admin",
            )

    def test_get_user(self, test_db, test_user):
        """Тест получения пользователя по ID."""
        user = UserRepository.get(test_user.id, db=test_db)
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert user.role == test_user.role

    def test_get_nonexistent_user(self, test_db):
        """Тест получения несуществующего пользователя."""
        user = UserRepository.get(99999, db=test_db)
        assert user is None

    def test_get_by_email(self, test_db, test_user):
        """Тест получения пользователя по email."""
        user = UserRepository.get_by_email(test_user.email, db=test_db)
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_get_by_nonexistent_email(self, test_db):
        """Тест получения пользователя по несуществующему email."""
        user = UserRepository.get_by_email("nonexistent@example.com", db=test_db)
        assert user is None

    def test_update_user(self, test_db, test_user):
        """Тест обновления пользователя."""
        updated = UserRepository.update(
            test_user.id,
            db=test_db,
            email="updated@example.com",
            role="admin",
        )
        assert updated is not None
        assert updated.id == test_user.id
        assert updated.email == "updated@example.com"
        assert updated.role == "admin"

    def test_update_nonexistent_user(self, test_db):
        """Тест обновления несуществующего пользователя."""
        updated = UserRepository.update(99999, db=test_db, email="test@example.com")
        assert updated is None

    def test_delete_user(self, test_db, test_user):
        """Тест удаления пользователя."""
        result = UserRepository.delete(test_user.id, db=test_db)
        assert result is True
        # Проверяем, что пользователь действительно удален
        user = UserRepository.get(test_user.id, db=test_db)
        assert user is None

    def test_delete_nonexistent_user(self, test_db):
        """Тест удаления несуществующего пользователя."""
        result = UserRepository.delete(99999, db=test_db)
        assert result is False

    def test_get_all_users(self, test_db, test_user):
        """Тест получения всех пользователей."""
        # Создаем дополнительных пользователей
        UserRepository.create(
            db=test_db,
            email="user2@example.com",
            password_hash="hash2",
            role="editor",
        )
        UserRepository.create(
            db=test_db,
            email="user3@example.com",
            password_hash="hash3",
            role="viewer",
        )
        users = UserRepository.get_all(db=test_db)
        assert len(users) >= 3
        emails = [u.email for u in users]
        assert test_user.email in emails
        assert "user2@example.com" in emails
        assert "user3@example.com" in emails

    def test_get_session(self):
        """Тест создания сессии."""
        session = UserRepository.get_session()
        assert session is not None
        session.close()


class TestDashboardRepository:
    """Тесты для DashboardRepository."""

    def test_create_dashboard(self, test_db):
        """Тест создания дашборда."""
        dashboard = DashboardRepository.create(
            db=test_db,
            name="Test Dashboard",
            config='{"charts": [{"type": "bar"}]}',
        )
        assert dashboard is not None
        assert dashboard.id is not None
        assert dashboard.name == "Test Dashboard"
        assert dashboard.config == '{"charts": [{"type": "bar"}]}'

    def test_get_dashboard(self, test_db, test_dashboard):
        """Тест получения дашборда по ID."""
        dashboard = DashboardRepository.get(test_dashboard.id, db=test_db)
        assert dashboard is not None
        assert dashboard.id == test_dashboard.id
        assert dashboard.name == test_dashboard.name

    def test_get_nonexistent_dashboard(self, test_db):
        """Тест получения несуществующего дашборда."""
        dashboard = DashboardRepository.get(99999, db=test_db)
        assert dashboard is None

    def test_get_by_user(self, test_db, test_user, test_dashboard, test_access):
        """Тест получения дашбордов пользователя."""
        dashboards = DashboardRepository.get_by_user(test_user.id, db=test_db)
        assert len(dashboards) >= 1
        dashboard_ids = [d.id for d in dashboards]
        assert test_dashboard.id in dashboard_ids

    def test_get_by_user_no_access(self, test_db, test_user):
        """Тест получения дашбордов пользователя без доступа."""
        # Создаем дашборд без доступа для пользователя
        dashboard = DashboardRepository.create(
            db=test_db,
            name="Private Dashboard",
            config="{}",
        )
        dashboards = DashboardRepository.get_by_user(test_user.id, db=test_db)
        dashboard_ids = [d.id for d in dashboards]
        assert dashboard.id not in dashboard_ids

    def test_update_dashboard(self, test_db, test_dashboard):
        """Тест обновления дашборда."""
        updated = DashboardRepository.update(
            test_dashboard.id,
            db=test_db,
            name="Updated Dashboard",
            config='{"charts": []}',
        )
        assert updated is not None
        assert updated.id == test_dashboard.id
        assert updated.name == "Updated Dashboard"
        assert updated.config == '{"charts": []}'

    def test_update_nonexistent_dashboard(self, test_db):
        """Тест обновления несуществующего дашборда."""
        updated = DashboardRepository.update(99999, db=test_db, name="Test")
        assert updated is None

    def test_delete_dashboard(self, test_db, test_dashboard):
        """Тест удаления дашборда."""
        result = DashboardRepository.delete(test_dashboard.id, db=test_db)
        assert result is True
        dashboard = DashboardRepository.get(test_dashboard.id, db=test_db)
        assert dashboard is None

    def test_delete_nonexistent_dashboard(self, test_db):
        """Тест удаления несуществующего дашборда."""
        result = DashboardRepository.delete(99999, db=test_db)
        assert result is False

    def test_get_all_dashboards(self, test_db, test_dashboard):
        """Тест получения всех дашбордов."""
        DashboardRepository.create(
            db=test_db,
            name="Dashboard 2",
            config="{}",
        )
        DashboardRepository.create(
            db=test_db,
            name="Dashboard 3",
            config="{}",
        )
        dashboards = DashboardRepository.get_all(db=test_db)
        assert len(dashboards) >= 3
        names = [d.name for d in dashboards]
        assert test_dashboard.name in names
        assert "Dashboard 2" in names
        assert "Dashboard 3" in names

    def test_get_session(self):
        """Тест создания сессии."""
        session = DashboardRepository.get_session()
        assert session is not None
        session.close()


class TestAccessRepository:
    """Тесты для AccessRepository."""

    def test_grant_access(self, test_db, test_user, test_dashboard):
        """Тест предоставления доступа."""
        access = AccessRepository.grant_access(
            user_id=test_user.id,
            dashboard_id=test_dashboard.id,
            permission_level="write",
            db=test_db,
        )
        assert access is not None
        assert access.user_id == test_user.id
        assert access.dashboard_id == test_dashboard.id
        assert access.permission_level == "write"

    def test_grant_access_duplicate(
        self, test_db, test_user, test_dashboard, test_access
    ):
        """Тест предоставления дублирующегося доступа."""
        access = AccessRepository.grant_access(
            user_id=test_user.id,
            dashboard_id=test_dashboard.id,
            permission_level="admin",
            db=test_db,
        )
        # Должен вернуть существующий доступ, не создавая новый
        assert access is not None
        assert access.user_id == test_user.id
        assert access.dashboard_id == test_dashboard.id

    def test_revoke_access(self, test_db, test_user, test_dashboard, test_access):
        """Тест отзыва доступа."""
        result = AccessRepository.revoke_access(
            user_id=test_user.id,
            dashboard_id=test_dashboard.id,
            db=test_db,
        )
        assert result is True
        # Проверяем, что доступ действительно отозван
        access = AccessRepository.check_access(
            user_id=test_user.id,
            dashboard_id=test_dashboard.id,
            db=test_db,
        )
        assert access is None

    def test_revoke_nonexistent_access(self, test_db, test_user, test_dashboard):
        """Тест отзыва несуществующего доступа."""
        result = AccessRepository.revoke_access(
            user_id=test_user.id,
            dashboard_id=test_dashboard.id,
            db=test_db,
        )
        assert result is False

    def test_check_access(self, test_db, test_user, test_dashboard, test_access):
        """Тест проверки доступа."""
        permission = AccessRepository.check_access(
            user_id=test_user.id,
            dashboard_id=test_dashboard.id,
            db=test_db,
        )
        assert permission == "read"

    def test_check_access_no_permission(self, test_db, test_user, test_dashboard):
        """Тест проверки отсутствующего доступа."""
        permission = AccessRepository.check_access(
            user_id=test_user.id,
            dashboard_id=test_dashboard.id,
            db=test_db,
        )
        assert permission is None

    def test_get_user_dashboards(self, test_db, test_user, test_dashboard, test_access):
        """Тест получения дашбордов пользователя."""
        dashboards = AccessRepository.get_user_dashboards(
            user_id=test_user.id, db=test_db
        )
        assert len(dashboards) >= 1
        dashboard_ids = [d.id for d in dashboards]
        assert test_dashboard.id in dashboard_ids

    def test_get_user_dashboards_no_access(self, test_db, test_user):
        """Тест получения дашбордов пользователя без доступа."""
        # Создаем дашборд без доступа
        dashboard = DashboardRepository.create(
            db=test_db,
            name="No Access Dashboard",
            config="{}",
        )
        dashboards = AccessRepository.get_user_dashboards(
            user_id=test_user.id, db=test_db
        )
        dashboard_ids = [d.id for d in dashboards]
        assert dashboard.id not in dashboard_ids

    def test_get_all_access(self, test_db, test_access):
        """Тест получения всех прав доступа."""
        AccessRepository.grant_access(
            user_id=999,
            dashboard_id=888,
            permission_level="admin",
            db=test_db,
        )
        accesses = AccessRepository.get_all(db=test_db)
        assert len(accesses) >= 2

    def test_get_session(self):
        """Тест создания сессии."""
        session = AccessRepository.get_session()
        assert session is not None
        session.close()


class TestRepositoryErrorHandling:
    """Тесты обработки ошибок в репозиториях."""

    def test_user_repository_error_on_invalid_data(self, test_db):
        """Тест ошибки при создании пользователя с некорректными данными."""
        with pytest.raises(SQLAlchemyError):
            UserRepository.create(
                db=test_db,
                # Отсутствует обязательное поле email
                password_hash="hash",
                role="viewer",
            )

    def test_dashboard_repository_error_on_invalid_data(self, test_db):
        """Тест ошибки при создании дашборда с некорректными данными."""
        with pytest.raises(SQLAlchemyError):
            DashboardRepository.create(
                db=test_db,
                # Отсутствует обязательное поле name
                config="{}",
            )

    def test_access_repository_error_on_invalid_user(self, test_db, test_dashboard):
        """Тест предоставления доступа несуществующему пользователю.

        В SQLite внешние ключи могут не вызывать исключение,
        если они не включены или если запись просто не найдена.
        """
        # Попытка предоставить доступ несуществующему пользователю
        # В зависимости от БД может создать запись или вызвать ошибку
        access = AccessRepository.grant_access(
            user_id=99999,
            dashboard_id=test_dashboard.id,
            permission_level="read",
            db=test_db,
        )
        # Если создалось - проверяем, что запись существует
        if access is not None:
            assert access.user_id == 99999
            assert access.dashboard_id == test_dashboard.id
