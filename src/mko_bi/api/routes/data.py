"""Маршруты для получения агрегированных данных дашбордов.

Этот модуль предоставляет эндпоинты для:
- Получения агрегированных данных для дашбордов
- Получения данных для конкретных графиков
- Применения фильтров к данным

Все операции требуют аутентификации и соответствующих прав доступа.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from mko_bi.api.deps import (
    get_db,
    require_viewer_role,
    CurrentUser,
)
from mko_bi.models.data import (
    AggregatedData,
    DataFilter,
)
from mko_bi.services.data_service import (
    get_dashboard_aggregates,
    get_chart_data,
    apply_data_filters,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["data"])


@router.get(
    "/{dashboard_id}",
    response_model=list[AggregatedData],
    status_code=status.HTTP_200_OK,
    summary="Получение агрегатов дашборда",
    description="Возвращает все агрегированные данные для указанного дашборда.",
    dependencies=[Depends(require_viewer_role)],
)
async def get_dashboard_aggregates_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> list[AggregatedData]:
    """Получает все агрегированные данные для дашборда.

    Возвращает все агрегаты (данные для всех графиков) указанного дашборда.
    Проверяет права доступа пользователя к дашборду.

    Args:
        dashboard_id: ID дашборда.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        list[AggregatedData]: Список агрегированных данных для всех графиков дашборда.

    Raises:
        HTTPException 403: Если у пользователя нет прав на чтение дашборда.
        HTTPException 404: Если дашборд не найден.
        HTTPException 500: При ошибке сервера.
    """
    logger.info(
        "Запрос агрегатов дашборда: dashboard_id=%s, user_id=%s",
        dashboard_id,
        current_user.id,
    )

    try:
        # Вызов сервиса получения агрегатов
        result: list[AggregatedData] = get_dashboard_aggregates(
            dashboard_id=dashboard_id,
            user_id=current_user.id,
            db=db,
        )

        logger.info(
            "Агрегаты получены: dashboard_id=%s, charts_count=%s",
            dashboard_id,
            len(result),
        )
        return result

    except ValueError as e:
        logger.warning("Ошибка при получении агрегатов: %s", e)
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
            "Ошибка при получении агрегатов дашборда id=%s: %s",
            dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении агрегатов дашборда",
        ) from e


@router.get(
    "/{dashboard_id}/charts",
    response_model=list[AggregatedData],
    status_code=status.HTTP_200_OK,
    summary="Получение данных для графиков",
    description="Возвращает данные для конкретных графиков дашборда.",
    dependencies=[Depends(require_viewer_role)],
)
async def get_dashboard_charts_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    chart_ids: list[UUID] | None = None,
    db: Session = Depends(get_db),
) -> list[AggregatedData]:
    """Получает данные для конкретных графиков дашборда.

    Если chart_ids не указан, возвращает данные для всех графиков дашборда.
    Проверяет права доступа пользователя к дашборду.

    Args:
        dashboard_id: ID дашборда.
        current_user: Текущий аутентифицированный пользователь.
        chart_ids: Опциональный список ID графиков для фильтрации.
        db: Сессия базы данных.

    Returns:
        list[AggregatedData]: Список агрегированных данных для запрошенных графиков.

    Raises:
        HTTPException 403: Если у пользователя нет прав на чтение дашборда.
        HTTPException 404: Если дашборд или графики не найдены.
        HTTPException 500: При ошибке сервера.
    """
    logger.info(
        "Запрос данных для графиков: dashboard_id=%s, chart_ids=%s, user_id=%s",
        dashboard_id,
        chart_ids,
        current_user.id,
    )

    try:
        # Вызов сервиса получения данных для графиков
        result: list[AggregatedData] = get_chart_data(
            dashboard_id=dashboard_id,
            user_id=current_user.id,
            chart_ids=chart_ids,
            db=db,
        )

        logger.info(
            "Данные для графиков получены: dashboard_id=%s, charts_count=%s",
            dashboard_id,
            len(result),
        )
        return result

    except ValueError as e:
        logger.warning("Ошибка при получении данных для графиков: %s", e)
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
            "Ошибка при получении данных для графиков дашборда id=%s: %s",
            dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении данных для графиков",
        ) from e


@router.post(
    "/filter",
    response_model=list[AggregatedData],
    status_code=status.HTTP_200_OK,
    summary="Применение фильтров",
    description="Применяет фильтры к агрегированным данным дашборда.",
    dependencies=[Depends(require_viewer_role)],
)
async def apply_filters_endpoint(
    filter_request: DataFilter,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> list[AggregatedData]:
    """Применяет фильтры к агрегированным данным дашборда.

    Фильтрует данные по году, категории, бренду и другим параметрам.
    Проверяет права доступа пользователя к дашборду.

    Args:
        filter_request: Модель с параметрами фильтрации.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        list[AggregatedData]: Отфильтрованные агрегированные данные.

    Raises:
        HTTPException 403: Если у пользователя нет прав на чтение дашборда.
        HTTPException 404: Если дашборд не найден.
        HTTPException 422: Если параметры фильтрации некорректны.
        HTTPException 500: При ошибке сервера.
    """
    logger.info(
        "Применение фильтров: dashboard_id=%s, user_id=%s",
        filter_request.dashboard_id,
        current_user.id,
    )

    try:
        # Собираем все фильтры в один словарь
        all_filters = {}
        if filter_request.year is not None:
            all_filters["year"] = filter_request.year
        if filter_request.category is not None:
            all_filters["category"] = filter_request.category
        if filter_request.brand is not None:
            all_filters["brand"] = filter_request.brand
        if filter_request.filters:
            all_filters.update(filter_request.filters)

        # Вызов сервиса применения фильтров
        result: list[AggregatedData] = apply_data_filters(
            dashboard_id=filter_request.dashboard_id,
            user_id=current_user.id,
            filters=all_filters,
            db=db,
        )

        logger.info(
            "Фильтры применены: dashboard_id=%s, filtered_charts=%s",
            filter_request.dashboard_id,
            len(result),
        )
        return result

    except ValueError as e:
        logger.warning("Ошибка при применении фильтров: %s", e)
        # Determine if this is a "not found" error vs validation error
        if "не найден" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
            "Ошибка при применении фильтров к дашборду id=%s: %s",
            filter_request.dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при применении фильтров",
        ) from e