"""Тесты для API данных дашбордов.

Тестирует эндпоинты получения агрегированных данных,
данных для графиков и применения фильтров.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from uuid import UUID

from mko_bi.api.routes.data import (
    get_dashboard_aggregates_endpoint,
    get_dashboard_charts_endpoint,
    apply_filters_endpoint,
)
from mko_bi.models.data import AggregatedData, DataFilter
from mko_bi.models.user import UserDB


class TestGetDashboardAggregatesEndpoint:
    """Тесты эндпоинта получения агрегатов дашборда."""

    @pytest.mark.asyncio
    async def test_get_aggregates_success(self, db_session):
        """Успешное получение агрегатов дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        mock_aggregate = MagicMock(spec=AggregatedData)
        mock_aggregate.dashboard_id = int(dashboard_id)
        mock_aggregate.chart_type = "bar"
        mock_aggregate.data = [{"dims": {"category": "A"}, "metrics": {"revenue": 1000}}]
        mock_aggregate.metadata = {"graph_id": "graph-1", "graph_name": "Sales", "count": 1}

        with patch("mko_bi.api.routes.data.get_dashboard_aggregates") as mock_get:
            mock_get.return_value = [mock_aggregate]

            result = await get_dashboard_aggregates_endpoint(
                dashboard_id=dashboard_id,
                current_user=mock_user,
                db=db_session,
            )

            assert result == [mock_aggregate]
            mock_get.assert_called_once_with(
                dashboard_id=dashboard_id,
                user_id=1,
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_get_aggregates_dashboard_not_found(self, db_session):
        """Дашборд не найден."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.api.routes.data.get_dashboard_aggregates") as mock_get:
            mock_get.side_effect = ValueError("Дашборд с id=12345678-1234-5678-1234-567812345678 не найден")

            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_aggregates_endpoint(
                    dashboard_id=dashboard_id,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 404
            assert "Дашборд" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_aggregates_access_denied(self, db_session):
        """Отказано в доступе к дашборду."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.api.routes.data.get_dashboard_aggregates") as mock_get:
            mock_get.side_effect = PermissionError("У вас нет доступа к этому дашборду")

            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_aggregates_endpoint(
                    dashboard_id=dashboard_id,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 403
            assert "доступа" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_get_aggregates_empty(self, db_session):
        """Получение пустого списка агрегатов."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.api.routes.data.get_dashboard_aggregates") as mock_get:
            mock_get.return_value = []

            result = await get_dashboard_aggregates_endpoint(
                dashboard_id=dashboard_id,
                current_user=mock_user,
                db=db_session,
            )

            assert result == []

    @pytest.mark.asyncio
    async def test_get_aggregates_internal_error(self, db_session):
        """Внутренняя ошибка при получении агрегатов."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.api.routes.data.get_dashboard_aggregates") as mock_get:
            mock_get.side_effect = Exception("DB error")

            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_aggregates_endpoint(
                    dashboard_id=dashboard_id,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 500
            assert "Ошибка" in str(exc_info.value.detail)


class TestGetDashboardChartsEndpoint:
    """Тесты эндпоинта получения данных для графиков."""

    @pytest.mark.asyncio
    async def test_get_charts_success(self, db_session):
        """Успешное получение данных для графиков."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")
        chart_id = UUID("87654321-4321-8765-4321-876543210987")

        mock_chart_data = MagicMock(spec=AggregatedData)
        mock_chart_data.dashboard_id = int(dashboard_id)
        mock_chart_data.chart_type = "line"
        mock_chart_data.data = [{"dims": {"month": "Jan"}, "metrics": {"sales": 100}}]
        mock_chart_data.metadata = {"graph_id": str(chart_id), "graph_name": "Monthly Sales", "count": 1}

        with patch("mko_bi.api.routes.data.get_chart_data") as mock_get:
            mock_get.return_value = [mock_chart_data]

            result = await get_dashboard_charts_endpoint(
                dashboard_id=dashboard_id,
                chart_ids=[chart_id],
                current_user=mock_user,
                db=db_session,
            )

            assert result == [mock_chart_data]
            mock_get.assert_called_once_with(
                dashboard_id=dashboard_id,
                user_id=1,
                chart_ids=[chart_id],
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_get_charts_all(self, db_session):
        """Получение данных для всех графиков (без фильтрации)."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        mock_chart_data = MagicMock(spec=AggregatedData)
        mock_chart_data.dashboard_id = int(dashboard_id)
        mock_chart_data.chart_type = "bar"
        mock_chart_data.data = [{"dims": {"category": "A"}, "metrics": {"value": 100}}]
        mock_chart_data.metadata = {"graph_id": "graph-1", "graph_name": "Chart 1", "count": 1}

        with patch("mko_bi.api.routes.data.get_chart_data") as mock_get:
            mock_get.return_value = [mock_chart_data]

            result = await get_dashboard_charts_endpoint(
                dashboard_id=dashboard_id,
                chart_ids=None,
                current_user=mock_user,
                db=db_session,
            )

            assert result == [mock_chart_data]
            mock_get.assert_called_once_with(
                dashboard_id=dashboard_id,
                user_id=1,
                chart_ids=None,
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_get_charts_not_found(self, db_session):
        """Графики не найдены."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")
        chart_id = UUID("87654321-4321-8765-4321-876543210987")

        with patch("mko_bi.api.routes.data.get_chart_data") as mock_get:
            mock_get.side_effect = ValueError("Графики не найдены: 87654321-4321-8765-4321-876543210987")

            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_charts_endpoint(
                    dashboard_id=dashboard_id,
                    chart_ids=[chart_id],
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 404
            assert "Графики" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_charts_access_denied(self, db_session):
        """Отказано в доступе к дашборду."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.api.routes.data.get_chart_data") as mock_get:
            mock_get.side_effect = PermissionError("У вас нет доступа к этому дашборду")

            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_charts_endpoint(
                    dashboard_id=dashboard_id,
                    chart_ids=None,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_charts_internal_error(self, db_session):
        """Внутренняя ошибка при получении данных для графиков."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.api.routes.data.get_chart_data") as mock_get:
            mock_get.side_effect = Exception("DB error")

            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_charts_endpoint(
                    dashboard_id=dashboard_id,
                    chart_ids=None,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 500


class TestApplyFiltersEndpoint:
    """Тесты эндпоинта применения фильтров."""

    @pytest.mark.asyncio
    async def test_apply_filters_success(self, db_session):
        """Успешное применение фильтров."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        mock_filtered_data = MagicMock(spec=AggregatedData)
        mock_filtered_data.dashboard_id = int(dashboard_id)
        mock_filtered_data.chart_type = "bar"
        mock_filtered_data.data = [{"dims": {"category": "A", "year": 2023}, "metrics": {"revenue": 1000}}]
        mock_filtered_data.metadata = {"graph_id": "graph-1", "graph_name": "Sales", "count": 1, "filters_applied": {"year": 2023}}

        with patch("mko_bi.api.routes.data.apply_data_filters") as mock_apply:
            mock_apply.return_value = [mock_filtered_data]

            filter_request = DataFilter(
                dashboard_id=dashboard_id,
                year=2023,
                category="Electronics",
                filters={"region": "North"},
            )

            result = await apply_filters_endpoint(
                filter_request=filter_request,
                current_user=mock_user,
                db=db_session,
            )

            assert result == [mock_filtered_data]
            mock_apply.assert_called_once_with(
                dashboard_id=dashboard_id,
                user_id=1,
                filters={"year": 2023, "category": "Electronics", "region": "North"},
                db=db_session,
            )

    @pytest.mark.asyncio
    async def test_apply_filters_dashboard_not_found(self, db_session):
        """Дашборд не найден при применении фильтров."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.api.routes.data.apply_data_filters") as mock_apply:
            mock_apply.side_effect = ValueError("Дашборд с id=12345678-1234-5678-1234-567812345678 не найден")

            filter_request = DataFilter(dashboard_id=dashboard_id)

            with pytest.raises(HTTPException) as exc_info:
                await apply_filters_endpoint(
                    filter_request=filter_request,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_apply_filters_access_denied(self, db_session):
        """Отказано в доступе при применении фильтров."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.api.routes.data.apply_data_filters") as mock_apply:
            mock_apply.side_effect = PermissionError("У вас нет доступа к этому дашборду")

            filter_request = DataFilter(dashboard_id=dashboard_id)

            with pytest.raises(HTTPException) as exc_info:
                await apply_filters_endpoint(
                    filter_request=filter_request,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_apply_filters_invalid_filters(self, db_session):
        """Некорректные параметры фильтрации."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.api.routes.data.apply_data_filters") as mock_apply:
            mock_apply.side_effect = ValueError("Некорректные параметры фильтрации")

            filter_request = DataFilter(dashboard_id=dashboard_id)

            with pytest.raises(HTTPException) as exc_info:
                await apply_filters_endpoint(
                    filter_request=filter_request,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_apply_filters_internal_error(self, db_session):
        """Внутренняя ошибка при применении фильтров."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("mko_bi.api.routes.data.apply_data_filters") as mock_apply:
            mock_apply.side_effect = Exception("DB error")

            filter_request = DataFilter(dashboard_id=dashboard_id)

            with pytest.raises(HTTPException) as exc_info:
                await apply_filters_endpoint(
                    filter_request=filter_request,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == 500
