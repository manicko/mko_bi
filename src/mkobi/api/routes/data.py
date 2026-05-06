"""Маршруты для получения агрегированных данных дашбордов.

Этот модуль предоставляет эндпоинты для:
- Получения агрегированных данных для дашбордов
- Получения данных для конкретных графиков
- Применения фильтров к данным

Все операции требуют аутентификации и соответствующих прав доступа.
"""

import json
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    CurrentUser,
    get_db_dependency,
    require_viewer_role,
)
from mkobi.services.data_service import (
    get_filtered_data,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["data"])


@router.get(
    "/aggregated",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Получение агрегированных данных дашборда",
    description="Возвращает данные для всех графиков дашборда с применением фильтров.",
    dependencies=[Depends(require_viewer_role)],
)
async def get_aggregated_data_endpoint(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
    dashboard_id: UUID = Query(..., description="ID дашборда"),
    filters: str | None = Query(default=None, description="JSON строка с фильтрами"),
) -> dict[str, Any]:
    """Получает агрегированные данные для дашборда.

    Применяет фильтры к JSONB полю dims и группирует данные по graph_id.
    Формат ответа: {"graphs": [{"graph_id": "...", "data": [...]}]}

    Args:
        dashboard_id: ID дашборда.
        filters: JSON строка с фильтрами (опционально).
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        dict: Данные для графиков в формате для React (Plotly.js).

    Raises:
        HTTPException 403: Если у пользователя нет прав на чтение дашборда.
        HTTPException 404: Если дашборд не найден.
        HTTPException 500: При ошибке сервера.
    """
    logger.info(
        "Запрос агрегированных данных: dashboard_id=%s, user_id=%s, filters=%s",
        dashboard_id,
        current_user.id,
        filters,
    )

    try:
        # Парсим фильтры из JSON строки
        filters_dict: dict[str, Any] = {}
        if filters:
            try:
                filters_dict = json.loads(filters)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Некорректный JSON в filters: {e}",
                ) from e

        # Получаем данные через сервис с применением фильтров
        result: dict[str, Any] = await get_filtered_data(
            dashboard_id=dashboard_id,
            filters=filters_dict,
            db=db,
        )

        logger.info(
            "Агрегированные данные получены: dashboard_id=%s, charts_count=%d",
            dashboard_id,
            len(result.get("charts", [])),
        )
        return result

    except ValueError as e:
        logger.warning("Ошибка при получении данных: %s", e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning("Отказано в доступе: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Ошибка при получении агрегированных данных для дашборда id=%s: %s",
            dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении данных",
        ) from e
