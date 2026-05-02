"""Тесты для сервиса управления дашбордами (dashboard_service.py).

Тестирует бизнес-логику CRUD операций с дашбордами
с использованием моков для изоляции тестов.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.services.dashboard_service import (
    create_dashboard,
    get_dashboard,
    get_user_dashboards,
    update_dashboard,
    delete_dashboard,
    grant_access,
    _validate_permission,
    _validate_config,
    _validate_dashboard_exists,
    _check_owner_permission,
)
from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.models.dashboard import DashboardConfig
from mko_bi.models.user_roles import GraphTypeEnum


class TestValidatePermission:
    """Тесты для функции валидации уровня доступа."""

    def test_valid_permission_view(self):
        """Валидный уровень доступа 'view' должен проходить проверку."""
        _validate_permission("view")

    def test_valid_permission_edit(self):
        """Валидный уровень доступа 'edit' должен проходить проверку."""
        _validate_permission("edit")

    def test_valid_permission_admin(self):
        """Валидный уровень доступа 'admin' должен проходить проверку."""
        _validate_permission("admin")

    def test_valid_permission_read_alias(self):
        """Уровень доступа 'read' должен нормализоваться в 'view'."""
        _validate_permission("read")

    def test_valid_permission_write_alias(self):
        """Уровень доступа 'write' должен нормализоваться в 'edit'."""
        _validate_permission("write")

    def test_invalid_permission_raises_value_error(self):
        """Недопустимый уровень доступа должен вызывать ValueError."""
        with pytest.raises(ValueError, match="Недопустимый уровень доступа"):
            _validate_permission("invalid")

    def test_empty_permission_raises_value_error(self):
        """Пустой уровень доступа должен вызывать ValueError."""
        with pytest.raises(ValueError):
            _validate_permission("")


class TestValidateConfig:
    """Тесты для функции валидации конфигурации дашборда."""

    def test_valid_config(self):
        """Валидная конфигурация должна проходить проверку."""
        config = DashboardConfig(graph_types=[GraphTypeEnum.bar])
        _validate_config(config)

    def test_valid_config_with_multiple_graph_types(self):
        """Конфигурация с несколькими типами графиков должна проходить проверку."""
        config = DashboardConfig(graph_types=[GraphTypeEnum.bar, GraphTypeEnum.line])
        _validate_config(config)


class TestValidateDashboardExists:
    """Тесты для функции проверки существования дашборда."""

    async def test_dashboard_exists(self):
        """Существующий дашборд должен возвращаться."""
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        test_uuid = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service.DashboardRepository') as mock_repo:
            mock_repo.get = AsyncMock(return_value=mock_dashboard)
            result = await _validate_dashboard_exists(test_uuid, mock_session)
            assert result == mock_dashboard

    async def test_dashboard_not_exists(self):
        """Несуществующий дашборд должен возвращать None."""
        test_uuid = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service.DashboardRepository') as mock_repo:
            mock_repo.get = AsyncMock(return_value=None)
            result = await _validate_dashboard_exists(test_uuid, mock_session)
            assert result is None


class TestCheckOwnerPermission:
    """Тесты для функции проверки прав владельца."""

    async def test_is_owner(self):
        """Пользователь с правами admin должен быть владельцем."""
        test_dashboard_id = uuid4()
        test_user_id = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service.AccessRepository') as mock_repo:
            mock_repo.check_access = AsyncMock(return_value="admin")
            result = await _check_owner_permission(test_dashboard_id, test_user_id, mock_session)
            assert result is True

    async def test_is_not_owner(self):
        """Пользователь без прав admin не должен быть владельцем."""
        test_dashboard_id = uuid4()
        test_user_id = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service.AccessRepository') as mock_repo:
            mock_repo.check_access = AsyncMock(return_value="view")
            result = await _check_owner_permission(test_dashboard_id, test_user_id, mock_session)
            assert result is False

    async def test_no_access_not_owner(self):
        """Пользователь без доступа не должен быть владельцем."""
        test_dashboard_id = uuid4()
        test_user_id = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service.AccessRepository') as mock_repo:
            mock_repo.check_access = AsyncMock(return_value=None)
            result = await _check_owner_permission(test_dashboard_id, test_user_id, mock_session)
            assert result is False


class TestCreateDashboard:
    """Тесты для функции создания дашборда."""

    async def test_create_dashboard_invalid_config_raises_error(self):
        """Некорректная конфигурация должна вызывать ошибку."""
        test_user_id = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service._validate_config',
                   side_effect=ValueError("Некорректная конфигурация")):

            with pytest.raises(ValueError, match="Некорректная конфигурация"):
                await create_dashboard(
                    "Test",
                    {"graph_types": []},
                    test_user_id,
                    mock_session,
                )

    async def test_create_dashboard_database_error_rolls_back(self):
        """Ошибка базы данных должна вызывать откат транзакции."""
        test_user_id = uuid4()
        mock_session = MagicMock()
        mock_session.rollback = AsyncMock()

        with patch('mko_bi.services.dashboard_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.dashboard_service._validate_config'), \
             patch('mko_bi.services.dashboard_service.AccessRepository'):

            mock_dash_repo.create = AsyncMock(side_effect=SQLAlchemyError("DB error"))

            with pytest.raises(SQLAlchemyError):
                await create_dashboard(
                    "Test",
                    {"graph_types": ["bar"]},
                    test_user_id,
                    mock_session,
                )


class TestGetDashboard:
    """Тесты для функции получения дашборда."""

    async def test_get_dashboard_not_found(self):
        """Несуществующий дашборд должен возвращать None."""
        test_dashboard_id = uuid4()
        test_user_id = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service._validate_dashboard_exists') as mock_validate:
            mock_validate.return_value = None
            result = await get_dashboard(test_dashboard_id, test_user_id, mock_session)
            assert result is None

    async def test_get_dashboard_no_access(self):
        """Дашборд без доступа должен возвращать None."""
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        test_dashboard_id = uuid4()
        test_user_id = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service._validate_dashboard_exists') as mock_validate, \
             patch('mko_bi.services.dashboard_service.AccessRepository') as mock_access_repo:

            mock_validate.return_value = mock_dashboard
            mock_access_repo.check_access = AsyncMock(return_value=None)

            result = await get_dashboard(test_dashboard_id, test_user_id, mock_session)
            assert result is None


class TestGetUserDashboards:
    """Тесты для функции получения дашбордов пользователя."""

    async def test_get_user_dashboards_empty(self):
        """При отсутствии дашбордов должен возвращаться пустой список."""
        test_user_id = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service.AccessRepository') as mock_access_repo:
            mock_access_repo.get_user_dashboards = AsyncMock(return_value=[])
            result = await get_user_dashboards(test_user_id, mock_session)
            assert result == []


class TestUpdateDashboard:
    """Тесты для функции обновления дашборда."""

    async def test_update_dashboard_not_found(self):
        """Обновление несуществующего дашборда должно вернуть None."""
        test_dashboard_id = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service._validate_config'), \
             patch('mko_bi.services.dashboard_service._validate_dashboard_exists', return_value=None):

            result = await update_dashboard(test_dashboard_id, {"graph_types": ["bar"]}, mock_session)
            assert result is None

    async def test_update_dashboard_invalid_config_raises_error(self):
        """Некорректная конфигурация должна вызывать ошибку."""
        test_dashboard_id = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service._validate_config',
                   side_effect=ValueError("Некорректная конфигурация")):

            with pytest.raises(ValueError, match="Некорректная конфигурация"):
                await update_dashboard(test_dashboard_id, {"graph_types": []}, mock_session)


class TestDeleteDashboard:
    """Тесты для функции удаления дашборда."""

    async def test_delete_dashboard_not_found(self):
        """Удаление несуществующего дашборда должно вернуть False."""
        test_dashboard_id = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service.DashboardRepository') as mock_dash_repo:
            mock_dash_repo.delete = AsyncMock(return_value=False)
            result = await delete_dashboard(test_dashboard_id, mock_session)
            assert result is False


class TestGrantAccess:
    """Тесты для функции предоставления доступа."""

    async def test_grant_access_dashboard_not_found(self):
        """Предоставление доступа к несуществующему дашборду должно вызывать ошибку."""
        test_dashboard_id = uuid4()
        test_user_id = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service._validate_permission'), \
             patch('mko_bi.services.dashboard_service._validate_dashboard_exists', return_value=None):

            with pytest.raises(ValueError, match="не найден"):
                await grant_access(test_dashboard_id, test_user_id, "view", mock_session)

    async def test_grant_access_invalid_permission_raises_error(self):
        """Недопустимый уровень доступа должен вызывать ошибку."""
        test_dashboard_id = uuid4()
        test_user_id = uuid4()
        mock_session = MagicMock()

        with patch('mko_bi.services.dashboard_service._validate_permission',
                   side_effect=ValueError("Недопустимый уровень доступа")):

            with pytest.raises(ValueError, match="Недопустимый уровень доступа"):
                await grant_access(test_dashboard_id, test_user_id, "invalid", mock_session)
