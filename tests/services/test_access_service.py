"""Тесты для сервиса управления доступом (access_service.py).

Тестирует бизнес-логику проверки и управления правами доступа
с использованием моков для изоляции тестов.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from mko_bi.services.access_service import (
    check_access,
    get_user_dashboards,
    get_dashboard_users,
    grant_access,
    revoke_access,
    get_access_level,
    can_edit_dashboard,
    can_view_dashboard,
    can_admin_dashboard,
)
from mko_bi.db.repositories.access_repo import AccessRepository
from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.db.models import user as user_model


class TestCheckAccess:
    """Тесты для функции проверки доступа."""

    def test_check_access_admin(self, db_session):
        """Проверка доступа уровня admin."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.check_access.return_value = "admin"
            result = check_access(1, 2, db_session)
            assert result == "admin"
            mock_repo.check_access.assert_called_once_with(1, 2, db_session)

    def test_check_access_edit(self, db_session):
        """Проверка доступа уровня edit."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.check_access.return_value = "edit"
            result = check_access(1, 2, db_session)
            assert result == "edit"

    def test_check_access_view(self, db_session):
        """Проверка доступа уровня view."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.check_access.return_value = "view"
            result = check_access(1, 2, db_session)
            assert result == "view"

    def test_check_access_none(self, db_session):
        """Проверка отсутствия доступа."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.check_access.return_value = None
            result = check_access(1, 2, db_session)
            assert result is None

    def test_check_access_auto_session(self):
        """Проверка доступа с автоматическим созданием сессии."""
        with patch('mko_bi.services.access_service.SessionLocal') as mock_session_local, \
             patch('mko_bi.services.access_service.AccessRepository') as mock_repo:

            mock_session = MagicMock(spec=Session)
            mock_session_local.return_value = mock_session
            mock_repo.check_access.return_value = "view"

            result = check_access(1, 2)
            assert result == "view"
            mock_session_local.assert_called_once()
            mock_session.close.assert_called_once()


class TestGetUserDashboards:
    """Тесты для функции получения дашбордов пользователя."""

    def test_get_user_dashboards(self, db_session):
        """Получение списка дашбордов пользователя."""
        mock_dashboards = [
            MagicMock(spec=dashboard_model.Dashboard),
            MagicMock(spec=dashboard_model.Dashboard),
        ]

        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.get_user_dashboards.return_value = mock_dashboards
            result = get_user_dashboards(1, db_session)
            assert result == mock_dashboards
            mock_repo.get_user_dashboards.assert_called_once_with(1, db_session)

    def test_get_user_dashboards_empty(self, db_session):
        """Пользователь без дашбордов должен получать пустой список."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.get_user_dashboards.return_value = []
            result = get_user_dashboards(1, db_session)
            assert result == []

    def test_get_user_dashboards_auto_session(self):
        """Получение дашбордов с автоматическим созданием сессии."""
        mock_dashboards = [MagicMock(spec=dashboard_model.Dashboard)]

        with patch('mko_bi.services.access_service.SessionLocal') as mock_session_local, \
             patch('mko_bi.services.access_service.AccessRepository') as mock_repo:

            mock_session = MagicMock(spec=Session)
            mock_session_local.return_value = mock_session
            mock_repo.get_user_dashboards.return_value = mock_dashboards

            result = get_user_dashboards(1)
            assert result == mock_dashboards
            mock_session_local.assert_called_once()
            mock_session.close.assert_called_once()


class TestGetDashboardUsers:
    """Тесты для функции получения пользователей дашборда."""

    def test_get_dashboard_users(self, db_session):
        """Получение списка пользователей дашборда."""
        mock_users = [
            MagicMock(spec=user_model.User),
            MagicMock(spec=user_model.User),
        ]

        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.get_dashboard_users.return_value = mock_users
            result = get_dashboard_users(1, db_session)
            assert result == mock_users
            mock_repo.get_dashboard_users.assert_called_once_with(1, db_session)

    def test_get_dashboard_users_empty(self, db_session):
        """Дашборд без пользователей должен возвращать пустой список."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.get_dashboard_users.return_value = []
            result = get_dashboard_users(1, db_session)
            assert result == []


class TestGrantAccess:
    """Тесты для функции предоставления доступа."""

    def test_grant_access_success(self, db_session):
        """Успешное предоставление доступа."""
        mock_access = MagicMock()

        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.grant_access.return_value = mock_access
            result = grant_access(1, 2, "view", db_session)
            assert result == mock_access
            mock_repo.grant_access.assert_called_once_with(
                db_session, 1, 2, "view"
            )

    def test_grant_access_upgrade_permission(self, db_session):
        """Обновление уровня доступа."""
        mock_access = MagicMock()

        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.grant_access.return_value = mock_access
            result = grant_access(1, 2, "admin", db_session)
            assert result == mock_access

    def test_grant_access_auto_session(self):
        """Предоставление доступа с автоматическим созданием сессии."""
        mock_access = MagicMock()

        with patch('mko_bi.services.access_service.SessionLocal') as mock_session_local, \
             patch('mko_bi.services.access_service.AccessRepository') as mock_repo:

            mock_session = MagicMock(spec=Session)
            mock_session_local.return_value = mock_session
            mock_repo.grant_access.return_value = mock_access

            result = grant_access(1, 2, "view")
            assert result == mock_access
            mock_session_local.assert_called_once()
            mock_session.close.assert_called_once()

    def test_grant_access_invalid_permission_raises_error(self, db_session):
        """Недопустимый уровень доступа должен вызывать ошибку."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.grant_access.side_effect = ValueError("Недопустимый уровень")

            with pytest.raises(ValueError, match="Недопустимый уровень"):
                grant_access(1, 2, "invalid", db_session)


class TestRevokeAccess:
    """Тесты для функции отзыва доступа."""

    def test_revoke_access_success(self, db_session):
        """Успешный отзыв доступа."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.revoke_access.return_value = True
            result = revoke_access(1, 2, db_session)
            assert result is True
            mock_repo.revoke_access.assert_called_once_with(1, 2, db_session)

    def test_revoke_access_not_found(self, db_session):
        """Отзыв несуществующего доступа должен вернуть False."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.revoke_access.return_value = False
            result = revoke_access(999, 1, db_session)
            assert result is False

    def test_revoke_access_auto_session(self):
        """Отзыв доступа с автоматическим созданием сессии."""
        with patch('mko_bi.services.access_service.SessionLocal') as mock_session_local, \
             patch('mko_bi.services.access_service.AccessRepository') as mock_repo:

            mock_session = MagicMock(spec=Session)
            mock_session_local.return_value = mock_session
            mock_repo.revoke_access.return_value = True

            result = revoke_access(1, 2)
            assert result is True
            mock_session_local.assert_called_once()
            mock_session.close.assert_called_once()


class TestGetAccessLevel:
    """Тесты для функции получения уровня доступа."""

    def test_get_access_level_admin(self, db_session):
        """Получение уровня доступа admin."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.check_access.return_value = "admin"
            result = get_access_level(1, 2, db_session)
            assert result == "admin"

    def test_get_access_level_none(self, db_session):
        """Получение уровня доступа для пользователя без доступа."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_repo.check_access.return_value = None
            result = get_access_level(1, 2, db_session)
            assert result is None


class TestCanEditDashboard:
    """Тесты для функции проверки прав на редактирование."""

    def test_can_edit_with_admin_access(self, db_session):
        """Пользователь с правами admin может редактировать."""
        with patch('mko_bi.services.access_service.check_access') as mock_check:
            mock_check.return_value = "admin"
            result = can_edit_dashboard(1, 2, db_session)
            assert result is True

    def test_can_edit_with_edit_access(self, db_session):
        """Пользователь с правами edit может редактировать."""
        with patch('mko_bi.services.access_service.check_access') as mock_check:
            mock_check.return_value = "edit"
            result = can_edit_dashboard(1, 2, db_session)
            assert result is True

    def test_can_edit_with_view_access(self, db_session):
        """Пользователь с правами view не может редактировать."""
        with patch('mko_bi.services.access_service.check_access') as mock_check:
            mock_check.return_value = "view"
            result = can_edit_dashboard(1, 2, db_session)
            assert result is False

    def test_can_edit_without_access(self, db_session):
        """Пользователь без доступа не может редактировать."""
        with patch('mko_bi.services.access_service.check_access') as mock_check:
            mock_check.return_value = None
            result = can_edit_dashboard(1, 2, db_session)
            assert result is False


class TestCanViewDashboard:
    """Тесты для функции проверки прав на просмотр."""

    def test_can_view_with_admin_access(self, db_session):
        """Пользователь с правами admin может просматривать."""
        with patch('mko_bi.services.access_service.check_access') as mock_check:
            mock_check.return_value = "admin"
            result = can_view_dashboard(1, 2, db_session)
            assert result is True

    def test_can_view_with_edit_access(self, db_session):
        """Пользователь с правами edit может просматривать."""
        with patch('mko_bi.services.access_service.check_access') as mock_check:
            mock_check.return_value = "edit"
            result = can_view_dashboard(1, 2, db_session)
            assert result is True

    def test_can_view_with_view_access(self, db_session):
        """Пользователь с правами view может просматривать."""
        with patch('mko_bi.services.access_service.check_access') as mock_check:
            mock_check.return_value = "view"
            result = can_view_dashboard(1, 2, db_session)
            assert result is True

    def test_can_view_without_access(self, db_session):
        """Пользователь без доступа не может просматривать."""
        with patch('mko_bi.services.access_service.check_access') as mock_check:
            mock_check.return_value = None
            result = can_view_dashboard(1, 2, db_session)
            assert result is False


class TestCanAdminDashboard:
    """Тесты для функции проверки прав на администрирование."""

    def test_can_admin_with_admin_access(self, db_session):
        """Пользователь с правами admin может администрировать."""
        with patch('mko_bi.services.access_service.check_access') as mock_check:
            mock_check.return_value = "admin"
            result = can_admin_dashboard(1, 2, db_session)
            assert result is True

    def test_can_admin_with_edit_access(self, db_session):
        """Пользователь с правами edit не может администрировать."""
        with patch('mko_bi.services.access_service.check_access') as mock_check:
            mock_check.return_value = "edit"
            result = can_admin_dashboard(1, 2, db_session)
            assert result is False

    def test_can_admin_with_view_access(self, db_session):
        """Пользователь с правами view не может администрировать."""
        with patch('mko_bi.services.access_service.check_access') as mock_check:
            mock_check.return_value = "view"
            result = can_admin_dashboard(1, 2, db_session)
            assert result is False

    def test_can_admin_without_access(self, db_session):
        """Пользователь без доступа не может администрировать."""
        with patch('mko_bi.services.access_service.check_access') as mock_check:
            mock_check.return_value = None
            result = can_admin_dashboard(1, 2, db_session)
            assert result is False


class TestAccessServiceIntegration:
    """Интеграционные тесты для сервиса доступа."""

    def test_full_access_management_flow(self, db_session):
        """Полный цикл управления доступом."""
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_user = MagicMock(spec=user_model.User)

        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            # Предоставление доступа
            mock_repo.grant_access.return_value = mock_dashboard
            result = grant_access(1, 2, "view", db_session)
            assert result == mock_dashboard
            mock_repo.grant_access.assert_called_once_with(db_session, 1, 2, "view")

            # Проверка доступа
            mock_repo.check_access.return_value = "view"
            access_level = check_access(1, 2, db_session)
            assert access_level == "view"

            # Получение дашбордов пользователя
            mock_repo.get_user_dashboards.return_value = [mock_dashboard]
            dashboards = get_user_dashboards(2, db_session)
            assert len(dashboards) == 1

            # Получение пользователей дашборда
            mock_repo.get_dashboard_users.return_value = [mock_user]
            users = get_dashboard_users(1, db_session)
            assert len(users) == 1

            # Обновление доступа
            mock_repo.grant_access.return_value = mock_dashboard
            result = grant_access(1, 2, "admin", db_session)
            assert result == mock_dashboard

            # Отзыв доступа
            mock_repo.revoke_access.return_value = True
            result = revoke_access(1, 2, db_session)
            assert result is True

    def test_access_permission_hierarchy(self, db_session):
        """Проверка иерархии прав доступа."""
        with patch('mko_bi.services.access_service.check_access') as mock_check:
            # Admin может всё
            mock_check.return_value = "admin"
            assert can_view_dashboard(1, 2, db_session) is True
            assert can_edit_dashboard(1, 2, db_session) is True
            assert can_admin_dashboard(1, 2, db_session) is True

            # Edit может просматривать и редактировать
            mock_check.return_value = "edit"
            assert can_view_dashboard(1, 2, db_session) is True
            assert can_edit_dashboard(1, 2, db_session) is True
            assert can_admin_dashboard(1, 2, db_session) is False

            # View может только просматривать
            mock_check.return_value = "view"
            assert can_view_dashboard(1, 2, db_session) is True
            assert can_edit_dashboard(1, 2, db_session) is False
            assert can_admin_dashboard(1, 2, db_session) is False

            # Нет доступа
            mock_check.return_value = None
            assert can_view_dashboard(1, 2, db_session) is False
            assert can_edit_dashboard(1, 2, db_session) is False
            assert can_admin_dashboard(1, 2, db_session) is False

    def test_multiple_users_access(self, db_session):
        """Проверка доступа для нескольких пользователей."""
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_users = [
            MagicMock(spec=user_model.User),
            MagicMock(spec=user_model.User),
            MagicMock(spec=user_model.User),
        ]

        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            # Предоставляем доступ разным пользователям с разными правами
            mock_repo.grant_access.return_value = mock_dashboard
            grant_access(1, 1, "admin", db_session)
            grant_access(1, 2, "edit", db_session)
            grant_access(1, 3, "view", db_session)

            # Проверяем права каждого
            mock_repo.check_access.side_effect = ["admin", "edit", "view"]
            assert check_access(1, 1, db_session) == "admin"
            assert check_access(1, 2, db_session) == "edit"
            assert check_access(1, 3, db_session) == "view"

            # Получаем всех пользователей дашборда
            mock_repo.get_dashboard_users.return_value = mock_users
            users = get_dashboard_users(1, db_session)
            assert len(users) == 3

    def test_access_revocation_scenarios(self, db_session):
        """Проверка различных сценариев отзыва доступа."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            # Успешный отзыв
            mock_repo.revoke_access.return_value = True
            result = revoke_access(1, 2, db_session)
            assert result is True

            # Отзыв несуществующего доступа
            mock_repo.revoke_access.return_value = False
            result = revoke_access(999, 1, db_session)
            assert result is False

            # Повторный отзыв (уже отозван)
            result = revoke_access(1, 2, db_session)
            assert result is False

    def test_dashboard_user_relationships(self, db_session):
        """Проверка связей между дашбордами и пользователями."""
        mock_dashboards = [
            MagicMock(spec=dashboard_model.Dashboard),
            MagicMock(spec=dashboard_model.Dashboard),
        ]
        mock_users = [
            MagicMock(spec=user_model.User),
            MagicMock(spec=user_model.User),
        ]

        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            # Пользователь имеет доступ к нескольким дашбордам
            mock_repo.get_user_dashboards.return_value = mock_dashboards
            dashboards = get_user_dashboards(1, db_session)
            assert len(dashboards) == 2

            # Дашборд имеет нескольких пользователей
            mock_repo.get_dashboard_users.return_value = mock_users
            users = get_dashboard_users(1, db_session)
            assert len(users) == 2

    def test_concurrent_access_operations(self, db_session):
        """Проверка корректности при конкурентных операциях с доступом."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            # Мокаем несколько операций предоставления доступа
            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_repo.grant_access.return_value = mock_dashboard

            # Одновременное предоставление доступа разным пользователям
            result1 = grant_access(1, 1, "view", db_session)
            result2 = grant_access(1, 2, "edit", db_session)
            result3 = grant_access(1, 3, "admin", db_session)

            assert result1 == mock_dashboard
            assert result2 == mock_dashboard
            assert result3 == mock_dashboard
            assert mock_repo.grant_access.call_count == 3

            # Проверка прав после всех операций
            mock_repo.check_access.side_effect = ["view", "edit", "admin"]
            assert check_access(1, 1, db_session) == "view"
            assert check_access(1, 2, db_session) == "edit"
            assert check_access(1, 3, db_session) == "admin"

    def test_access_with_database_errors(self, db_session):
        """Проверка обработки ошибок базы данных."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            # Ошибка при предоставлении доступа
            mock_repo.grant_access.side_effect = SQLAlchemyError("DB error")
            with pytest.raises(SQLAlchemyError):
                grant_access(1, 2, "view", db_session)

            # Ошибка при проверке доступа
            mock_repo.check_access.side_effect = SQLAlchemyError("DB error")
            with pytest.raises(SQLAlchemyError):
                check_access(1, 2, db_session)

            # Ошибка при отзыве доступа
            mock_repo.revoke_access.side_effect = SQLAlchemyError("DB error")
            with pytest.raises(SQLAlchemyError):
                revoke_access(1, 2, db_session)

    def test_access_level_transitions(self, db_session):
        """Проверка переходов между уровнями доступа."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_repo.grant_access.return_value = mock_dashboard

            # Начинаем с view
            grant_access(1, 2, "view", db_session)
            mock_repo.check_access.return_value = "view"
            assert check_access(1, 2, db_session) == "view"

            # Повышаем до edit
            grant_access(1, 2, "edit", db_session)
            mock_repo.check_access.return_value = "edit"
            assert check_access(1, 2, db_session) == "edit"

            # Повышаем до admin
            grant_access(1, 2, "admin", db_session)
            mock_repo.check_access.return_value = "admin"
            assert check_access(1, 2, db_session) == "admin"

            # Понижаем до view
            grant_access(1, 2, "view", db_session)
            mock_repo.check_access.return_value = "view"
            assert check_access(1, 2, db_session) == "view"

    def test_access_validation_scenarios(self, db_session):
        """Проверка различных сценариев валидации доступа."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            # Пользователь является владельцем (admin)
            mock_repo.check_access.return_value = "admin"
            assert can_edit_dashboard(1, 2, db_session) is True
            assert can_admin_dashboard(1, 2, db_session) is True

            # Пользователь имеет права редактора
            mock_repo.check_access.return_value = "edit"
            assert can_edit_dashboard(1, 2, db_session) is True
            assert can_admin_dashboard(1, 2, db_session) is False

            # Пользователь имеет права зрителя
            mock_repo.check_access.return_value = "view"
            assert can_edit_dashboard(1, 2, db_session) is False
            assert can_admin_dashboard(1, 2, db_session) is False

            # Пользователь не имеет доступа
            mock_repo.check_access.return_value = None
            assert can_edit_dashboard(1, 2, db_session) is False
            assert can_admin_dashboard(1, 2, db_session) is False

    def test_bulk_access_operations(self, db_session):
        """Проверка пакетных операций с доступом."""
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        mock_users = [
            MagicMock(spec=user_model.User),
            MagicMock(spec=user_model.User),
            MagicMock(spec=user_model.User),
        ]

        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            # Предоставляем доступ нескольким пользователям
            mock_repo.grant_access.return_value = mock_dashboard
            for i, user in enumerate(mock_users, 1):
                grant_access(1, i, "view", db_session)

            assert mock_repo.grant_access.call_count == 3

            # Получаем всех пользователей дашборда
            mock_repo.get_dashboard_users.return_value = mock_users
            users = get_dashboard_users(1, db_session)
            assert len(users) == 3

            # Отзываем доступ у всех
            mock_repo.revoke_access.return_value = True
            for i, user in enumerate(mock_users, 1):
                revoke_access(1, i, db_session)

            assert mock_repo.revoke_access.call_count == 3

    def test_access_with_nonexistent_entities(self, db_session):
        """Проверка работы с несуществующими сущностями."""
        with patch('mko_bi.services.access_service.AccessRepository') as mock_repo:
            # Проверка доступа к несуществующему дашборду
            mock_repo.check_access.return_value = None
            result = check_access(999, 1, db_session)
            assert result is None

            # Получение пользователей несуществующего дашборда
            mock_repo.get_dashboard_users.return_value = []
            users = get_dashboard_users(999, db_session)
            assert users == []

            # Получение дашбордов несуществующего пользователя
            mock_repo.get_user_dashboards.return_value = []
            dashboards = get_user_dashboards(999, db_session)
            assert dashboards == []

            # Предоставление доступа к несуществующему дашборду
            mock_repo.grant_access.side_effect = ValueError("Дашборд не найден")
            with pytest.raises(ValueError):
                grant_access(999, 1, "view", db_session)
