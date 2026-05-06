"""Маршруты для управления графиками дашбордов.

Этот модуль предоставляет эндпоинты для CRUD операций с графиками.
Доступ к операциям создания, обновления и удаления ограничен ролью admin.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mko_b_i.api.deps import (
    get_db_dependency,
    require_admin_role,
    CurrentUser,
)
from mko_b_i.models.enums import GraphType
from mko_b_i.models.graph import (
    GraphCreate,
    GraphRead,
    GraphUpdate,
)
from mko_b_i.services.graph_service import (
    create_graph,
    get_graph_by_id,
    get_graphs_by_dashboard,
    update_graph,
    delete_graph,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graphs", tags=["graphs"])


@router.post(
    "/dashboards/{dashboard_id}/graphs",
    response_model=GraphRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создание графика для дашборда",
    description="Создает новый график для указанного дашборда. Доступно только администраторам.",
    dependencies=[Depends(require_admin_role)],
)
async def create_graph_endpoint(
    dashboard_id: UUID,
    graph: GraphCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> GraphRead:
    """Создает новый график для дашборда.

    Args:
        dashboard_id: ID дашборда.
        graph: Модель с данными для создания графика.
        current_user: Текущий аутентифицированный пользователь.
        db: Асинхронная сессия базы данных.

    Returns:
        GraphRead: Модель созданного графика.

    Raises:
        HTTPException 404: Если дашборд не найден.
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Создание графика: name=%s, dashboard_id=%s, user_id=%s",
        graph.name,
        dashboard_id,
        current_user.id,
    )

    # Проверка, что dashboard_id в пути совпадает с dashboard_id в теле запроса
    if graph.dashboard_id != dashboard_id:
        logger.warning(
            "Несовпадение dashboard_id: path=%s, body=%s",
            dashboard_id,
            graph.dashboard_id,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="dashboard_id в теле запроса не совпадает с dashboard_id в URL",
        )

    try:
        result = await create_graph(
            dashboard_id=dashboard_id,
            name=graph.name,
            type_=graph.type,
            config=graph.config,
            dimensions=graph.dimensions,
            metrics=graph.metrics,
            db=db,
        )
        return result
    except ValueError as e:
        logger.warning("Ошибка валидации при создании графика: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Ошибка при создании графика name=%s, dashboard_id=%s: %s",
            graph.name,
            dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании графика",
        ) from e


@router.get(
    "/dashboards/{dashboard_id}/graphs",
    response_model=list[GraphRead],
    status_code=status.HTTP_200_OK,
    summary="Список графиков дашборда",
    description="Возвращает список всех графиков указанного дашборда.",
)
async def get_dashboard_graphs_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> list[GraphRead]:
    """Получает список графиков дашборда.

    Args:
        dashboard_id: ID дашборда.
        current_user: Текущий аутентифицированный пользователь.
        db: Асинхронная сессия базы данных.

    Returns:
        list[GraphRead]: Список моделей графиков.

    Raises:
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Получение графиков для дашборда: dashboard_id=%s, user_id=%s",
        dashboard_id,
        current_user.id,
    )

    try:
        graphs: list[GraphRead] = await get_graphs_by_dashboard(
            dashboard_id=dashboard_id,
            db=db,
        )
        logger.info(
            "Получено графиков для дашборда id=%s: %s",
            dashboard_id,
            len(graphs),
        )
        return graphs
    except Exception as e:
        logger.error(
            "Ошибка при получении графиков для дашборда id=%s: %s",
            dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении графиков дашборда",
        ) from e


@router.put(
    "/{graph_id}",
    response_model=GraphRead,
    status_code=status.HTTP_200_OK,
    summary="Обновление графика",
    description="Обновляет данные графика. Доступно только администраторам.",
    dependencies=[Depends(require_admin_role)],
)
async def update_graph_endpoint(
    graph_id: UUID,
    graph_update: GraphUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> GraphRead:
    """Обновляет график.

    Доступно только пользователям с ролью admin.

    Args:
        graph_id: ID графика для обновления.
        graph_update: Модель с новыми данными.
        current_user: Текущий аутентифицированный пользователь.
        db: Асинхронная сессия базы данных.

    Returns:
        GraphRead: Модель обновленного графика.

    Raises:
        HTTPException 404: Если график не найден.
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Обновление графика: graph_id=%s, user_id=%s",
        graph_id,
        current_user.id,
    )

    try:
        updated = await update_graph(
            graph_id=graph_id,
            name=graph_update.name,
            type_=graph_update.type,
            config=graph_update.config,
            dimensions=graph_update.dimensions,
            metrics=graph_update.metrics,
            db=db,
        )
        if updated is None:
            logger.warning("График не найден для обновления: id=%s", graph_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="График не найден",
            )
        return updated
    except ValueError as e:
        logger.warning("Ошибка валидации при обновлении графика: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка при обновлении графика id=%s: %s", graph_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении графика",
        ) from e


@router.delete(
    "/{graph_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление графика",
    description="Удаляет график. Доступно только администраторам.",
    dependencies=[Depends(require_admin_role)],
)
async def delete_graph_endpoint(
    graph_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> None:
    """Удаляет график.

    Доступно только пользователям с ролью admin.

    Args:
        graph_id: ID графика для удаления.
        current_user: Текущий аутентифицированный пользователь.
        db: Асинхронная сессия базы данных.

    Raises:
        HTTPException 404: Если график не найден.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Удаление графика: graph_id=%s, user_id=%s",
        graph_id,
        current_user.id,
    )

    try:
        result = await delete_graph(graph_id=graph_id, db=db)
        if not result:
            logger.warning("График не найден для удаления: id=%s", graph_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="График не найден",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка при удалении графика id=%s: %s", graph_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении графика",
        ) from e
