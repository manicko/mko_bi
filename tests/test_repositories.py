"""Тесты для репозиториев (UserRepository, DashboardRepository, AccessRepository).

Тестирует CRUD операции через репозитории с использованием моков для изоляции тестов.
Все тесты проверяют бизнес-логику репозиториев, а не саму базу данных.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from mko_bi.db.repositories import user_repo, dashboard_repo, access_repo
from mko_bi.db.models import user as user_model
from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.db.models import access as access_model


class TestUserRepository:
    """Тесты для UserRepository."""

    def test_get_user_success(self):
        """Тест успешного получения пользователя по ID."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = user_repo.UserRepository.get(mock_user.id, mock_db)

        assert result == mock_user
        mock_db.execute.assert_called_once()
        mock_result.scalar_one_or_none.assert_called_once()

    def test_get_user_not_found(self):
        """Тест получения несуществующего пользователя."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        user_id = uuid4()
        result = user_repo.UserRepository.get(user_id, mock_db)

        assert result is None
        mock_db.execute.assert_called_once()

    def test_get_user_by_email_success(self):
        """Тест успешного получения пользователя по email."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = user_repo.UserRepository.get_by_email("test@example.com", mock_db)

        assert result == mock_user
        mock_db.execute.assert_called_once()

    def test_get_user_by_email_not_found(self):
        """Тест получения пользователя по несуществующему email."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = user_repo.UserRepository.get_by_email("nonexistent@example.com", mock_db)

        assert result is None
        mock_db.execute.assert_called_once()

    def test_create_user_success(self):
        """Тест успешного создания пользователя."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_user.email = "newuser@example.com"

        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        with patch('mko_bi.db.repositories.user_repo.user_model.User', return_value=mock_user):
            result = user_repo.UserRepository.create(
                mock_db,
                email="newuser@example.com",
                password_hash="$2b$12$hash",
                role="viewer"
            )

        assert result == mock_user
        mock_db.add.assert_called_once_with(mock_user)
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)

    def test_create_user_sqlalchemy_error(self):
        """Тест ошибки SQLAlchemy при создании пользователя."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)

        mock_db.add = MagicMock()
        mock_db.flush = MagicMock(side_effect=SQLAlchemyError("DB error"))

        with patch('mko_bi.db.repositories.user_repo.user_model.User', return_value=mock_user):
            with pytest.raises(SQLAlchemyError):
                user_repo.UserRepository.create(
                    mock_db,
                    email="error@example.com",
                    password_hash="$2b$12$hash"
                )

        mock_db.flush.assert_called_once()

    def test_update_user_success(self):
        """Тест успешного обновления пользователя."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_user.email = "old@example.com"
        mock_user.role = "viewer"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        result = user_repo.UserRepository.update(
            mock_user.id, mock_db, role="admin", email="new@example.com"
        )

        assert result == mock_user
        assert mock_user.role == "admin"
        assert mock_user.email == "new@example.com"
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)

    def test_update_user_not_found(self):
        """Тест обновления несуществующего пользователя."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        user_id = uuid4()
        result = user_repo.UserRepository.update(user_id, mock_db, role="admin")

        assert result is None
        mock_db.flush.assert_not_called()

    def test_update_user_sqlalchemy_error(self):
        """Тест ошибки SQLAlchemy при обновлении пользователя."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        mock_db.flush = MagicMock(side_effect=SQLAlchemyError("DB error"))

        with pytest.raises(SQLAlchemyError):
            user_repo.UserRepository.update(mock_user.id, mock_db, role="admin")

        mock_db.flush.assert_called_once()

    def test_delete_user_success(self):
        """Тест успешного удаления пользователя."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        mock_db.delete = MagicMock()
        mock_db.flush = MagicMock()

        result = user_repo.UserRepository.delete(mock_user.id, mock_db)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_user)
        mock_db.flush.assert_called_once()

    def test_delete_user_not_found(self):
        """Тест удаления несуществующего пользователя."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        user_id = uuid4()
        result = user_repo.UserRepository.delete(user_id, mock_db)

        assert result is False
        mock_db.flush.assert_not_called()

    def test_delete_user_sqlalchemy_error(self):
        """Тест ошибки SQLAlchemy при удалении пользователя."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        mock_db.delete = MagicMock()
        mock_db.flush = MagicMock(side_effect=SQLAlchemyError("DB error"))

        with pytest.raises(SQLAlchemyError):
            user_repo.UserRepository.delete(mock_user.id, mock_db)

        mock_db.flush.assert_called_once()

    def test_get_all_users(self):
        """Тест получения всех пользователей."""
        mock_db = MagicMock(spec=Session)
        mock_users = [
            MagicMock(spec=user_model.User, id=uuid4(), email=f"user{i}@example.com")
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_db.execute.return_value = mock_result

        result = user_repo.UserRepository.get_all(mock_db)

        assert result == mock_users
        assert len(result) == 3
        mock_db.execute.assert_called_once()

    def test_get_session(self):
        """Тест создания сессии."""
        # Патчим get_session в session.py, который используется репозиториями
        with patch('mko_bi.db.session.get_session') as mock_get_session:
            session_instance = MagicMock(spec=Session)
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=session_instance)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_get_session.return_value = mock_context

            result = user_repo.UserRepository.get_session()

            assert result == mock_context
            mock_get_session.assert_called_once()


class TestDashboardRepository:
    """Тесты для DashboardRepository."""

    def test_get_dashboard_success(self):
        """Тест успешного получения дашборда по ID."""
        mock_db = MagicMock(spec=Session)
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_dashboard.id = uuid4()
        mock_dashboard.name = "Test Dashboard"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_dashboard
        mock_db.execute.return_value = mock_result

        result = dashboard_repo.DashboardRepository.get(mock_dashboard.id, mock_db)

        assert result == mock_dashboard
        mock_db.execute.assert_called_once()

    def test_get_dashboard_not_found(self):
        """Тест получения несуществующего дашборда."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        dashboard_id = uuid4()
        result = dashboard_repo.DashboardRepository.get(dashboard_id, mock_db)

        assert result is None

    def test_get_dashboard_by_user(self):
        """Тест получения дашбордов пользователя."""
        mock_db = MagicMock(spec=Session)
        mock_dashboards = [
            MagicMock(spec=dashboard_model.Dashboard, id=uuid4(), name=f"Dash {i}")
            for i in range(2)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_dashboards
        mock_db.execute.return_value = mock_result

        user_id = uuid4()
        result = dashboard_repo.DashboardRepository.get_by_user(user_id, mock_db)

        assert result == mock_dashboards
        assert len(result) == 2

    def test_create_dashboard_success(self):
        """Тест успешного создания дашборда."""
        mock_db = MagicMock(spec=Session)
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_dashboard.id = uuid4()
        mock_dashboard.name = "New Dashboard"

        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        with patch('mko_bi.db.repositories.dashboard_repo.dashboard_model.Dashboard',
                   return_value=mock_dashboard):
            result = dashboard_repo.DashboardRepository.create(
                mock_db,
                name="New Dashboard",
                config={"type": "default"}
            )

        assert result == mock_dashboard
        mock_db.add.assert_called_once_with(mock_dashboard)
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_dashboard)

    def test_create_dashboard_sqlalchemy_error(self):
        """Тест ошибки SQLAlchemy при создании дашборда."""
        mock_db = MagicMock(spec=Session)
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)

        mock_db.add = MagicMock()
        mock_db.flush = MagicMock(side_effect=SQLAlchemyError("DB error"))

        with patch('mko_bi.db.repositories.dashboard_repo.dashboard_model.Dashboard',
                   return_value=mock_dashboard):
            with pytest.raises(SQLAlchemyError):
                dashboard_repo.DashboardRepository.create(
                    mock_db, name="Error Dashboard", config={}
                )

        mock_db.flush.assert_called_once()

    def test_update_dashboard_success(self):
        """Тест успешного обновления дашборда."""
        mock_db = MagicMock(spec=Session)
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_dashboard.id = uuid4()
        mock_dashboard.name = "Old Name"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_dashboard
        mock_db.execute.return_value = mock_result
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        result = dashboard_repo.DashboardRepository.update(
            mock_dashboard.id, mock_db, name="New Name", description="Updated"
        )

        assert result == mock_dashboard
        assert mock_dashboard.name == "New Name"
        assert mock_dashboard.description == "Updated"
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_dashboard)

    def test_update_dashboard_not_found(self):
        """Тест обновления несуществующего дашборда."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        dashboard_id = uuid4()
        result = dashboard_repo.DashboardRepository.update(dashboard_id, mock_db, name="New")

        assert result is None
        mock_db.flush.assert_not_called()

    def test_update_dashboard_sqlalchemy_error(self):
        """Тест ошибки SQLAlchemy при обновлении дашборда."""
        mock_db = MagicMock(spec=Session)
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_dashboard.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_dashboard
        mock_db.execute.return_value = mock_result
        mock_db.flush = MagicMock(side_effect=SQLAlchemyError("DB error"))

        with pytest.raises(SQLAlchemyError):
            dashboard_repo.DashboardRepository.update(mock_dashboard.id, mock_db, name="New")

        mock_db.flush.assert_called_once()

    def test_revoke_access_success(self):
        """Тест успешного отзыва доступа."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_dashboard.id = uuid4()

        mock_access = MagicMock(spec=access_model.DashboardAccess)
        mock_access.user_id = mock_user.id
        mock_access.dashboard_id = mock_dashboard.id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_access
        mock_db.execute.return_value = mock_result
        mock_db.delete = MagicMock()
        mock_db.flush = MagicMock()

        result = access_repo.AccessRepository.revoke_access(
            mock_user.id, mock_dashboard.id, mock_db
        )

        assert result is True
        mock_db.delete.assert_called_once_with(mock_access)
        mock_db.flush.assert_called_once()

    def test_revoke_access_not_found(self):
        """Тест отзыва несуществующего доступа."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_dashboard.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = access_repo.AccessRepository.revoke_access(
            mock_user.id, mock_dashboard.id, mock_db
        )

        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.flush.assert_not_called()

    def test_revoke_access_sqlalchemy_error(self):
        """Тест ошибки SQLAlchemy при отзыве доступа."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_dashboard.id = uuid4()

        mock_access = MagicMock(spec=access_model.DashboardAccess)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_access
        mock_db.execute.return_value = mock_result
        mock_db.delete = MagicMock()
        mock_db.flush = MagicMock(side_effect=SQLAlchemyError("DB error"))

        with pytest.raises(SQLAlchemyError):
            access_repo.AccessRepository.revoke_access(
                mock_user.id, mock_dashboard.id, mock_db
            )

        mock_db.flush.assert_called_once()

    def test_check_access_exists(self):
        """Тест проверки существующего доступа."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_dashboard.id = uuid4()

        mock_access = MagicMock(spec=access_model.DashboardAccess)
        mock_access.permission = "edit"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_access
        mock_db.execute.return_value = mock_result

        result = access_repo.AccessRepository.check_access(
            mock_user.id, mock_dashboard.id, mock_db
        )

        assert result == "edit"

    def test_check_access_not_found(self):
        """Тест проверки несуществующего доступа."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_dashboard.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = access_repo.AccessRepository.check_access(
            mock_user.id, mock_dashboard.id, mock_db
        )

        assert result is None

    def test_check_access_sqlalchemy_error(self):
        """Тест ошибки SQLAlchemy при проверке доступа."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_dashboard.id = uuid4()

        mock_db.execute = MagicMock(side_effect=SQLAlchemyError("DB error"))

        with pytest.raises(SQLAlchemyError):
            access_repo.AccessRepository.check_access(
                mock_user.id, mock_dashboard.id, mock_db
            )

    def test_get_user_dashboards(self):
        """Тест получения дашбордов пользователя."""
        mock_db = MagicMock(spec=Session)
        mock_dashboards = [
            MagicMock(spec=dashboard_model.Dashboard, id=uuid4(), name=f"Dash {i}")
            for i in range(2)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_dashboards
        mock_db.execute.return_value = mock_result

        user_id = uuid4()
        result = access_repo.AccessRepository.get_user_dashboards(user_id, mock_db)

        assert result == mock_dashboards
        assert len(result) == 2

    def test_get_all_access(self):
        """Тест получения всех прав доступа."""
        mock_db = MagicMock(spec=Session)
        mock_accesses = [
            MagicMock(spec=access_model.DashboardAccess, id=i, permission="view")
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_accesses
        mock_db.execute.return_value = mock_result

        result = access_repo.AccessRepository.get_all(mock_db)

        assert result == mock_accesses
        assert len(result) == 3

    def test_get_session(self):
        """Тест создания сессии."""
        # Патчим get_session в session.py, который используется репозиториями
        with patch('mko_bi.db.session.get_session') as mock_get_session:
            session_instance = MagicMock(spec=Session)
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=session_instance)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_get_session.return_value = mock_context

            result = access_repo.AccessRepository.get_session()

            assert result == mock_context
            mock_get_session.assert_called_once()


class TestRepositoryIntegration:
    """Интеграционные тесты."""

    def test_user_crud_flow(self):
        """Тест полного цикла CRUD для пользователя."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_user.email = "integration@test.com"
        mock_user.password_hash = "$2b$12$hash"

        with patch('mko_bi.db.repositories.user_repo.user_model.User', return_value=mock_user):
            created = user_repo.UserRepository.create(
                mock_db, email="integration@test.com", password_hash="$2b$12$hash"
            )
        assert created == mock_user

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        retrieved = user_repo.UserRepository.get(mock_user.id, mock_db)
        assert retrieved == mock_user

        mock_db.execute.return_value = mock_result
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        updated = user_repo.UserRepository.update(
            mock_user.id, mock_db, role="admin"
        )
        assert updated == mock_user
        assert mock_user.role == "admin"

        mock_db.delete = MagicMock()
        mock_db.commit = MagicMock()

        result = user_repo.UserRepository.delete(mock_user.id, mock_db)
        assert result is True

    def test_dashboard_crud_flow(self):
        """Тест полного цикла CRUD для дашборда."""
        mock_db = MagicMock(spec=Session)
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_dashboard.id = uuid4()
        mock_dashboard.name = "Integration Dashboard"

        with patch('mko_bi.db.repositories.dashboard_repo.dashboard_model.Dashboard',
                   return_value=mock_dashboard):
            created = dashboard_repo.DashboardRepository.create(
                mock_db, name="Integration Dashboard", config={}
            )
        assert created == mock_dashboard

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_dashboard
        mock_db.execute.return_value = mock_result

        retrieved = dashboard_repo.DashboardRepository.get(mock_dashboard.id, mock_db)
        assert retrieved == mock_dashboard

        mock_db.execute.return_value = mock_result
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        updated = dashboard_repo.DashboardRepository.update(
            mock_dashboard.id, mock_db, name="Updated Dashboard"
        )
        assert updated == mock_dashboard
        assert mock_dashboard.name == "Updated Dashboard"

        mock_db.delete = MagicMock()
        mock_db.commit = MagicMock()

        result = dashboard_repo.DashboardRepository.delete(mock_dashboard.id, mock_db)
        assert result is True

    def test_access_flow(self):
        """Тест полного цикла управления доступом."""
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_dashboard.id = uuid4()

        mock_access = MagicMock(spec=access_model.DashboardAccess)
        mock_access.user_id = mock_user.id
        mock_access.dashboard_id = mock_dashboard.id
        mock_access.permission = "view"

        # Мокаем цепочку select().where().scalar_one_or_none()
        mock_select = MagicMock()
        mock_where = MagicMock()
        mock_scalar = MagicMock()
        mock_scalar.scalar_one_or_none.return_value = None
        mock_where.return_value = mock_scalar
        mock_select.return_value = mock_where

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_scalar
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        with patch('mko_bi.db.repositories.access_repo.select', mock_select):
            with patch('mko_bi.db.repositories.access_repo.access_model.DashboardAccess',
                       return_value=mock_access):
                granted = access_repo.AccessRepository.grant_access(
                    mock_db, mock_user.id, mock_dashboard.id, "view"
                )
        assert granted == mock_access

        mock_result.scalar_one_or_none.return_value = mock_access
        mock_db.execute.return_value = mock_result

        permission = access_repo.AccessRepository.check_access(
            mock_user.id, mock_dashboard.id, mock_db
        )
        assert permission == "view"

        mock_db.delete = MagicMock()
        mock_db.flush = MagicMock()

        revoked = access_repo.AccessRepository.revoke_access(
            mock_user.id, mock_dashboard.id, mock_db
        )
        assert revoked is True

        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        permission = access_repo.AccessRepository.check_access(
            mock_user.id, mock_dashboard.id, mock_db
        )
        assert permission is None

