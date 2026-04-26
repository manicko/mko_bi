"""Тесты для API дашбордов.

Тестирует эндпоинты CRUD операций с дашбордами,
включая аутентификацию и проверку прав доступа.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from mko_bi.api.routes.dashboards import (
    create_dashboard_endpoint,
    get_dashboards_endpoint,
    get_dashboard_endpoint,
    update_dashboard_endpoint,
    delete_dashboard_endpoint,
    grant_dashboard_access_endpoint,
)
from mko_bi.models.dashboard import DashboardCreate, DashboardUpdate, DashboardRead
from mko_bi.models.access import AccessGrant
from mko_bi.models.user import UserDB


class TestCreateDashboardEndpoint:
    """Тесты эндпоинта создания дашборда."""

    @pytest.mark.asyncio
    async def test_create_dashboard_success(self, db_session):
        """Успешное создание дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        with patch("mko_bi.api.routes.dashboards.create_dashboard") as mock_create:
            mock_dashboard = MagicMock(spec=DashboardRead)
            mock_create.return_value = mock_dashboard

            result = await create_dashboard_endpoint(
                dashboard=DashboardCreate(
                    name="Test Dashboard",
                    config={"graph_types": ["bar"]},
                ),
                current_user=mock_user,
                db=db_session,
            )

            assert result == mock_dashboard
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["name"] == "Test Dashboard"
            assert call_kwargs["owner_id"] == 1
            assert call_kwargs["db"] == db_session

    @pytest.mark.asyncio
    async def test_create_dashboard_validation_error(self, db_session):
        """Ошибка валидации при создании дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        with patch("mko_bi.api.routes.dashboards.create_dashboard") as mock_create:
            mock_create.side_effect = ValueError("Invalid config")

            with pytest.raises(HTTPException) as exc_info:
                await create_dashboard_endpoint(
                    dashboard=DashboardCreate(
                        name="Test Dashboard",
                        config={"graph_types": []},
                    ),
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 422
            assert "Invalid config" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_dashboard_internal_error(self, db_session):
        """Внутренняя ошибка при создании дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        with patch("mko_bi.api.routes.dashboards.create_dashboard") as mock_create:
            mock_create.side_effect = Exception("DB error")

            with pytest.raises(HTTPException) as exc_info:
                await create_dashboard_endpoint(
                    dashboard=DashboardCreate(
                        name="Test Dashboard",
                        config={"graph_types": ["bar"]},
                    ),
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 500
            assert "Ошибка при создании дашборда" in str(exc_info.value.detail)


class TestGetDashboardsEndpoint:
    """Тесты эндпоинта получения списка дашбордов."""

    @pytest.mark.asyncio
    async def test_get_dashboards_success(self, db_session):
        """Успешное получение списка дашбордов."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        mock_dashboard = MagicMock(spec=DashboardRead)

        with patch("mko_bi.api.routes.dashboards.get_user_dashboards") as mock_get:
            mock_get.return_value = [mock_dashboard]

            result = await get_dashboards_endpoint(
                current_user=mock_user,
                db=db_session,
            )

            assert result == [mock_dashboard]
            mock_get.assert_called_once_with(user_id=1, db=db_session)

    @pytest.mark.asyncio
    async def test_get_dashboards_empty(self, db_session):
        """Получение пустого списка дашбордов."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        with patch("mko_bi.api.routes.dashboards.get_user_dashboards") as mock_get:
            mock_get.return_value = []

            result = await get_dashboards_endpoint(
                current_user=mock_user,
                db=db_session,
            )

            assert result == []

    @pytest.mark.asyncio
    async def test_get_dashboards_internal_error(self, db_session):
        """Внутренняя ошибка при получении списка дашбордов."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        with patch("mko_bi.api.routes.dashboards.get_user_dashboards") as mock_get:
            mock_get.side_effect = Exception("DB error")

            with pytest.raises(HTTPException) as exc_info:
                await get_dashboards_endpoint(
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 500
            assert "Ошибка при получении списка дашбордов" in str(exc_info.value.detail)


class TestGetDashboardEndpoint:
    """Тесты эндпоинта получения дашборда по ID."""

    @pytest.mark.asyncio
    async def test_get_dashboard_success(self, db_session):
        """Успешное получение дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        mock_dashboard = MagicMock(spec=DashboardRead)

        with patch("mko_bi.api.routes.dashboards.get_dashboard") as mock_get:
            mock_get.return_value = mock_dashboard

            result = await get_dashboard_endpoint(
                dashboard_id=dashboard_id,
                current_user=mock_user,
                db=db_session,
            )

            assert result == mock_dashboard
            mock_get.assert_called_once_with(
                dashboard_id=dashboard_id,
                user_id=1,
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_get_dashboard_not_found(self, db_session):
        """Дашборд не найден."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.api.routes.dashboards.get_dashboard") as mock_get:
            mock_get.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_endpoint(
                    dashboard_id=dashboard_id,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 404
            assert "Дашборд не найден" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_dashboard_internal_error(self, db_session):
        """Внутренняя ошибка при получении дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.api.routes.dashboards.get_dashboard") as mock_get:
            mock_get.side_effect = Exception("DB error")

            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_endpoint(
                    dashboard_id=dashboard_id,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 500
            assert "Ошибка при получении дашборда" in str(exc_info.value.detail)


class TestUpdateDashboardEndpoint:
    """Тесты эндпоинта обновления дашборда."""

    @pytest.mark.asyncio
    async def test_update_dashboard_success(self, db_session):
        """Успешное обновление дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        mock_dashboard = MagicMock(spec=DashboardRead)

        with patch("mko_bi.core.permissions.check_dashboard_access") as mock_check:
            mock_check.return_value = True
            with patch("mko_bi.api.routes.dashboards.update_dashboard") as mock_update:
                mock_update.return_value = mock_dashboard

                result = await update_dashboard_endpoint(
                    dashboard_id=dashboard_id,
                    dashboard_update=DashboardUpdate(
                        config={"graph_types": ["line"]},
                    ),
                    current_user=mock_user,
                    db=db_session,
                )

                assert result == mock_dashboard
                mock_check.assert_called_once_with(
                    user_id=1,
                    dashboard_id=dashboard_id,
                    required_permission="edit",
                    db=db_session,
                )
                mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_dashboard_access_denied(self, db_session):
        """Отказ в доступе при обновлении дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.core.permissions.check_dashboard_access") as mock_check:
            mock_check.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                await update_dashboard_endpoint(
                    dashboard_id=dashboard_id,
                    dashboard_update=DashboardUpdate(
                        config={"graph_types": ["line"]},
                    ),
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 403
            assert "нет прав" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_update_dashboard_not_found(self, db_session):
        """Дашборд не найден при обновлении."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.core.permissions.check_dashboard_access") as mock_check:
            mock_check.return_value = True
            with patch("mko_bi.api.routes.dashboards.update_dashboard") as mock_update:
                mock_update.return_value = None

                with pytest.raises(HTTPException) as exc_info:
                    await update_dashboard_endpoint(
                        dashboard_id=dashboard_id,
                        dashboard_update=DashboardUpdate(
                            config={"graph_types": ["line"]},
                        ),
                        current_user=mock_user,
                        db=db_session,
                    )

                assert exc_info.value.status_code == 404
                assert "Дашборд не найден" in str(exc_info.value.detail)



    @pytest.mark.asyncio
    async def test_update_dashboard_internal_error(self, db_session):
        """Внутренняя ошибка при обновлении дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.core.permissions.check_dashboard_access") as mock_check:
            mock_check.return_value = True
            with patch("mko_bi.api.routes.dashboards.update_dashboard") as mock_update:
                mock_update.side_effect = Exception("DB error")

                with pytest.raises(HTTPException) as exc_info:
                    await update_dashboard_endpoint(
                        dashboard_id=dashboard_id,
                        dashboard_update=DashboardUpdate(
                            config={"graph_types": ["line"]},
                        ),
                        current_user=mock_user,
                        db=db_session,
                    )

                assert exc_info.value.status_code == 500


class TestDeleteDashboardEndpoint:
    """Тесты эндпоинта удаления дашборда."""

    @pytest.mark.asyncio
    async def test_delete_dashboard_success(self, db_session):
        """Успешное удаление дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.core.permissions.check_dashboard_access") as mock_check:
            mock_check.return_value = True
            with patch("mko_bi.api.routes.dashboards.delete_dashboard") as mock_delete:
                mock_delete.return_value = True

                result = await delete_dashboard_endpoint(
                    dashboard_id=dashboard_id,
                    current_user=mock_user,
                    db=db_session,
                )

                assert result is None
                mock_check.assert_called_once_with(
                    user_id=1,
                    dashboard_id=dashboard_id,
                    required_permission="edit",
                    db=db_session,
                )
                mock_delete.assert_called_once_with(
                    dashboard_id=dashboard_id,
                    db=db_session,
                )

    @pytest.mark.asyncio
    async def test_delete_dashboard_access_denied(self, db_session):
        """Отказ в доступе при удалении дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.core.permissions.check_dashboard_access") as mock_check:
            mock_check.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                await delete_dashboard_endpoint(
                    dashboard_id=dashboard_id,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_dashboard_not_found(self, db_session):
        """Дашборд не найден при удалении."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.core.permissions.check_dashboard_access") as mock_check:
            mock_check.return_value = True
            with patch("mko_bi.api.routes.dashboards.delete_dashboard") as mock_delete:
                mock_delete.return_value = False

                with pytest.raises(HTTPException) as exc_info:
                    await delete_dashboard_endpoint(
                        dashboard_id=dashboard_id,
                        current_user=mock_user,
                        db=db_session,
                    )

                assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_dashboard_internal_error(self, db_session):
        """Внутренняя ошибка при удалении дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.core.permissions.check_dashboard_access") as mock_check:
            mock_check.return_value = True
            with patch("mko_bi.api.routes.dashboards.delete_dashboard") as mock_delete:
                mock_delete.side_effect = Exception("DB error")

                with pytest.raises(HTTPException) as exc_info:
                    await delete_dashboard_endpoint(
                        dashboard_id=dashboard_id,
                        current_user=mock_user,
                        db=db_session,
                    )

                assert exc_info.value.status_code == 500


class TestGrantDashboardAccessEndpoint:
    """Тесты эндпоинта предоставления доступа к дашборду."""

    @pytest.mark.asyncio
    async def test_grant_access_success(self, db_session):
        """Успешное предоставление доступа."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")
        user_id = UUID("87654321-4321-8765-4321-876543210987")

        with patch("mko_bi.core.permissions.check_dashboard_access") as mock_check:
            mock_check.return_value = True
            with patch("mko_bi.api.routes.dashboards.grant_access") as mock_grant:
                mock_grant.return_value = True

                result = await grant_dashboard_access_endpoint(
                    dashboard_id=dashboard_id,
                    access_grant=AccessGrant(
                        user_id=user_id,
                        dashboard_id=dashboard_id,
                        permission_level="edit",
                    ),
                    current_user=mock_user,
                    db=db_session,
                )

                assert result["message"] == "Доступ успешно предоставлен"
                assert result["permission"] == "edit"
                mock_check.assert_called_once_with(
                    user_id=1,
                    dashboard_id=dashboard_id,
                    required_permission="admin",
                    db=db_session,
                )
                mock_grant.assert_called_once_with(
                    dashboard_id=dashboard_id,
                    user_id=user_id,
                    permission="edit",
                    db=db_session,
                )

    @pytest.mark.asyncio
    async def test_grant_access_no_admin_rights(self, db_session):
        """Отказ при предоставлении доступа без прав админа."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")
        user_id = UUID("87654321-4321-8765-4321-876543210987")

        with patch("mko_bi.core.permissions.check_dashboard_access") as mock_check:
            mock_check.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                await grant_dashboard_access_endpoint(
                    dashboard_id=dashboard_id,
                    access_grant=AccessGrant(
                        user_id=user_id,
                        dashboard_id=dashboard_id,
                        permission_level="edit",
                    ),
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_grant_access_mismatched_ids(self, db_session):
        """Ошибка при несовпадении dashboard_id в URL и теле запроса."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")
        user_id = UUID("87654321-4321-8765-4321-876543210987")
        other_id = UUID("11111111-2222-3333-4444-555555555555")

        with patch("mko_bi.core.permissions.check_dashboard_access") as mock_check:
            mock_check.return_value = True

            with pytest.raises(HTTPException) as exc_info:
                await grant_dashboard_access_endpoint(
                    dashboard_id=dashboard_id,
                    access_grant=AccessGrant(
                        user_id=user_id,
                        dashboard_id=other_id,
                        permission_level="edit",
                    ),
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 422
            assert "не совпадает" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_grant_access_dashboard_not_found(self, db_session):
        """Ошибка при предоставлении доступа к несуществующему дашборду."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")
        user_id = UUID("87654321-4321-8765-4321-876543210987")

        with patch("mko_bi.core.permissions.check_dashboard_access") as mock_check:
            mock_check.return_value = True
            with patch("mko_bi.api.routes.dashboards.grant_access") as mock_grant:
                mock_grant.return_value = False

                with pytest.raises(HTTPException) as exc_info:
                    await grant_dashboard_access_endpoint(
                        dashboard_id=dashboard_id,
                        access_grant=AccessGrant(
                            user_id=user_id,
                            dashboard_id=dashboard_id,
                            permission_level="edit",
                        ),
                        current_user=mock_user,
                        db=db_session,
                    )

                assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_grant_access_validation_error(self, db_session):
        """Ошибка валидации при предоставлении доступа."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")
        user_id = UUID("87654321-4321-8765-4321-876543210987")

        with patch("mko_bi.core.permissions.check_dashboard_access") as mock_check:
            mock_check.return_value = True
            with patch("mko_bi.api.routes.dashboards.grant_access") as mock_grant:
                mock_grant.side_effect = ValueError("Invalid permission")

                with pytest.raises(HTTPException) as exc_info:
                    await grant_dashboard_access_endpoint(
                        dashboard_id=dashboard_id,
                        access_grant=AccessGrant(
                            user_id=user_id,
                            dashboard_id=dashboard_id,
                            permission_level="invalid",
                        ),
                        current_user=mock_user,
                        db=db_session,
                    )

                assert exc_info.value.status_code == 422