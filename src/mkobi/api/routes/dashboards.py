"""Маршруты для управления дашбордами.

Этот модуль предоставляет эндпоинты для CRUD операций с дашбордами.
Доступ к большинству операций ограничен и требует аутентификации.
Операции создания, обновления и удаления доступны только владельцам.
"""

import logging
from uuid import UUID

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    get_db_dependency,
    require_admin_role,
    require_viewer_role,
    CurrentUser,
)
from mkobi.core.permissions import check_dashboard_access
from mkobi.models.dashboard import (
    DashboardCreate,
    DashboardRead,
    DashboardUpdate,
)
from mkobi.models.access import AccessGrant
from mkobi.models.graph import GraphCreate, GraphRead
from mkobi.services.dashboard_service import (
    create_dashboard,
    get_dashboard,
    get_user_dashboards,
    update_dashboard,
    delete_dashboard,
    grant_access,
    revoke_access,
    get_dashboard_access_list,
)
from mkobi.db.repositories.dashboard_filter_repo import DashboardFilterRepository
from mkobi.db.repositories.filter_repo import FilterRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.post(
    "/",
    response_model=DashboardRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создание дашборда",
    description="Создает новый дашборд. Доступно только администраторам.",
    dependencies=[Depends(require_admin_role)],
)
async def create_dashboard_endpoint(
    dashboard_data: DashboardCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> DashboardRead:
    """Создает новый дашборд.

    Текущий аутентифицированный пользователь автоматически становится
    владельцем (admin) созданного дашборда.

    Args:
        dashboard: Модель с данными для создания дашборда.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        DashboardRead: Модель созданного дашборда.

    Raises:
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 500: При ошибке базы данных.
    """
    dashboard = DashboardCreate(
        name=dashboard_data.name,
        description=dashboard_data.description,
        config=dashboard_data.config,
    )

    logger.info(
        "Создание дашборда: name=%s, owner_id=%s",
        dashboard.name,
        current_user.id,
    )

    try:
        result = await create_dashboard(
            name=dashboard.name,
            config=dashboard.config.model_dump(),
            owner_id=current_user.id,
            db=db,
        )

        logger.info(
            "Дашборд успешно создан: id=%s, name=%s",
            result.id,
            result.name,
        )
        return result

    except ValueError as e:
        logger.warning("Ошибка валидации при создании дашборда: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Ошибка при создании дашборда name=%s: %s",
            dashboard.name,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании дашборда",
        ) from e


@router.get(
    "/my",
    response_model=list[DashboardRead],
    status_code=status.HTTP_200_OK,
    summary="Список дашбордов пользователя",
    description="Возвращает список дашбордов, доступных текущему пользователю.",
)
async def get_my_dashboards_endpoint(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> list[DashboardRead]:
    """Получает список всех дашбордов, доступных пользователю.

    Args:
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        list[DashboardRead]: Список моделей дашбордов.

    Raises:
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Получение списка дашбордов для пользователя: user_id=%s",
        current_user.id,
    )

    try:
        dashboards = await get_user_dashboards(user_id=current_user.id, db=db)
        logger.info(
            "Получено дашбордов для пользователя id=%s: %s",
            current_user.id,
            len(dashboards),
        )
        return dashboards  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(
            "Ошибка при получении списка дашбордов для пользователя id=%s: %s",
            current_user.id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении списка дашбордов",
        ) from e


@router.get(
    "/{dashboard_id}",
    response_model=DashboardRead,
    status_code=status.HTTP_200_OK,
    summary="Получение дашборда по ID",
    description="Возвращает данные дашборда по его ID с проверкой доступа.",
    dependencies=[Depends(require_viewer_role)],
)
async def get_dashboard_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> DashboardRead:
    """Получает дашборд по ID с проверкой доступа.

    Args:
        dashboard_id: ID дашборда.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        DashboardRead: Модель дашборда.

    Raises:
        HTTPException 403: Если у пользователя нет доступа.
        HTTPException 404: Если дашборд не найден.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Запрос дашборда: dashboard_id=%s, user_id=%s",
        dashboard_id,
        current_user.id,
    )

    try:
        dashboard = await get_dashboard(dashboard_id, db)
        if dashboard is None:
            logger.warning(
                "Дашборд не найден: dashboard_id=%s",
                dashboard_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Дашборд не найден",
            )

        # Проверяем доступ на чтение
        has_access = await check_dashboard_access(
            user_id=current_user.id,
            dashboard_id=dashboard_id,
            required_permission="view",
            db=db,
        )
        if not has_access:
            logger.warning(
                "Нет прав на чтение дашборда: dashboard_id=%s, user_id=%s",
                dashboard_id,
                current_user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на чтение этого дашборда",
            )

        logger.info(
            "Дашборд успешно получен: id=%s, name=%s",
            dashboard.id,
            dashboard.name,
        )
        return dashboard

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Ошибка при получении дашборда dashboard_id=%s: %s",
            dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении дашборда",
        ) from e


@router.put(
    "/{dashboard_id}",
    response_model=DashboardRead,
    status_code=status.HTTP_200_OK,
    summary="Обновление дашборда",
    description="Обновляет конфигурацию дашборда. Доступно только администраторам.",
    dependencies=[Depends(require_admin_role)],
)
async def update_dashboard_endpoint(
    dashboard_id: UUID,
    dashboard_update: DashboardUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> DashboardRead:
    """Обновляет конфигурацию дашборда.

    Доступно только владельцу дашборда (пользователю с правами admin).

    Args:
        dashboard_id: ID дашборда для обновления.
        dashboard_update: Модель с новыми данными.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        DashboardRead: Модель обновленного дашборда.

    Raises:
        HTTPException 403: Если у пользователя нет прав на обновление.
        HTTPException 404: Если дашборд не найден.
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Обновление дашборда: dashboard_id=%s, user_id=%s",
        dashboard_id,
        current_user.id,
    )

    try:
        # Проверяем доступ на запись (требуется роль admin для этого дашборда)
        from mkobi.core.permissions import check_dashboard_access
        
        if not await check_dashboard_access(
            user_id=current_user.id,
            dashboard_id=dashboard_id,
            required_permission="edit",
            db=db,
        ):
            logger.warning(
                "Нет прав на обновление дашборда: dashboard_id=%s, user_id=%s",
                dashboard_id,
                current_user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на обновление этого дашборда",
            )
        
        updated = await update_dashboard(
            dashboard_id=dashboard_id,
            config=dashboard_update.config.model_dump() if dashboard_update.config else None,
            db=db,
        )
        if updated is None:
            logger.warning("Дашборд не найден для обновления: id=%s", dashboard_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Дашборд не найден",
            )
        return updated
    except ValueError as e:
        logger.warning("Ошибка валидации при обновлении дашборда: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка при обновлении дашборда id=%s: %s", dashboard_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обновлении дашборда",
        ) from e


@router.delete(
    "/{dashboard_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление дашборда",
    description="Удаляет дашборд. Доступно только администраторам.",
    dependencies=[Depends(require_admin_role)],
)
async def delete_dashboard_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> None:
    """Удаляет дашборд.

    Доступно только владельцу дашборда (пользователю с правами admin).

    Args:
        dashboard_id: ID дашборда для удаления.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Raises:
        HTTPException 403: Если у пользователя нет прав на удаление.
        HTTPException 404: Если дашборд не найден.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Удаление дашборда: dashboard_id=%s, user_id=%s",
        dashboard_id,
        current_user.id,
    )

    try:
        # Проверяем доступ на запись (требуется роль admin для этого дашборда)
        from mkobi.core.permissions import check_dashboard_access

        if not await check_dashboard_access(
            user_id=current_user.id,
            dashboard_id=dashboard_id,
            required_permission="edit",
            db=db,
        ):
            logger.warning(
                "Нет прав на удаление дашборда: dashboard_id=%s, user_id=%s",
                dashboard_id,
                current_user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на удаление этого дашборда",
            )
        
        result = await delete_dashboard(dashboard_id=dashboard_id, db=db)
        if not result:
            logger.warning("Дашборд не найден для удаления: id=%s", dashboard_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Дашборд не найден",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка при удалении дашборда id=%s: %s", dashboard_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении дашборда",
        ) from e


@router.post(
    "/{dashboard_id}/access",
    status_code=status.HTTP_200_OK,
    summary="Предоставление доступа к дашборду",
    description="Предоставляет пользователю доступ к дашборду. Доступно только владельцу.",
    dependencies=[Depends(require_viewer_role)],
)
async def grant_dashboard_access_endpoint(
    dashboard_id: UUID,
    access_grant: AccessGrant,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> dict[str, Any]:
    """Предоставляет пользователю доступ к дашборду.

    Доступно только владельцу дашборда (пользователю с правами admin).

    Args:
        dashboard_id: ID дашборда.
        access_grant: Модель с данными для предоставления доступа.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        dict: Сообщение об успешном предоставлении доступа.

    Raises:
        HTTPException 403: Если у пользователя нет прав на предоставление доступа.
        HTTPException 404: Если дашборд не найден.
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 500: При ошибке базы данных.
    """
    logger.info(
        "Предоставление доступа: dashboard_id=%s, user_id=%s, permission=%s",
        dashboard_id,
        access_grant.user_id,
        access_grant.permission_level,
    )

    try:
        # Проверяем, что текущий пользователь имеет права на управление доступом
        from mkobi.core.permissions import check_dashboard_access

        if not await check_dashboard_access(
            user_id=current_user.id,
            dashboard_id=dashboard_id,
            required_permission="admin",
            db=db,
        ):
            logger.warning(
                "Нет прав на управление доступом: dashboard_id=%s, user_id=%s",
                dashboard_id,
                current_user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на управление доступом к этому дашборду",
            )
        
        # Проверяем, что dashboard_id из пути совпадает с dashboard_id в теле запроса
        if str(access_grant.dashboard_id) != str(dashboard_id):
            logger.warning(
                "Несовпадение dashboard_id: path=%s, body=%s",
                dashboard_id,
                access_grant.dashboard_id,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="dashboard_id в теле запроса не совпадает с dashboard_id в URL",
            )
        
        result = await grant_access(
            dashboard_id=dashboard_id,
            user_id=access_grant.user_id,
            permission=access_grant.permission_level,
            db=db,
        )

        if result:
            logger.info(
                "Доступ успешно предоставлен: dashboard_id=%s, user_id=%s, permission=%s",
                dashboard_id,
                access_grant.user_id,
                access_grant.permission_level,
            )
            return {
                "message": "Доступ успешно предоставлен",
                "dashboard_id": str(dashboard_id),
                "user_id": str(access_grant.user_id),
                "permission": access_grant.permission_level,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Дашборд не найден",
            )
    except ValueError as e:
        logger.warning("Ошибка валидации при предоставлении доступа: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Ошибка при предоставлении доступа к дашборду id=%s: %s",
            dashboard_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при предоставлении доступа",
        ) from e


# --- Dashboard-Filter binding endpoints ---


@router.post(
    "/{dashboard_id}/filters",
    status_code=status.HTTP_200_OK,
    summary="Bind filter to dashboard",
    description="Binds a filter to a dashboard. Requires admin role.",
    dependencies=[Depends(require_admin_role)],
)
async def bind_filter_endpoint(
    dashboard_id: UUID,
    filter_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> dict[str, Any]:
    """Bind a filter to a dashboard."""
    logger.info("Binding filter to dashboard: dashboard_id=%s, filter_id=%s", dashboard_id, filter_id)
    try:
        filter_obj = FilterRepository.get(filter_id, db)
        if not filter_obj:
            raise HTTPException(status_code=404, detail="Filter not found")
        
        result = await DashboardFilterRepository.bind_filter(
            dashboard_id=dashboard_id, filter_id=filter_id, db=db
        )
        await db.commit()
        return {"message": "Filter bound to dashboard", "bound": result}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete(
    "/{dashboard_id}/filters/{filter_id}",
    status_code=status.HTTP_200_OK,
    summary="Unbind filter from dashboard",
    description="Unbinds a filter from a dashboard. Requires admin role.",
    dependencies=[Depends(require_admin_role)],
)
async def unbind_filter_endpoint(
    dashboard_id: UUID,
    filter_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> dict[str, Any]:
    """Unbind a filter from a dashboard."""
    logger.info("Unbinding filter from dashboard: dashboard_id=%s, filter_id=%s", dashboard_id, filter_id)
    try:
        result = await DashboardFilterRepository.unbind_filter(
            dashboard_id=dashboard_id, filter_id=filter_id, db=db
        )
        await db.commit()
        if result:
            return {"message": "Filter unbound from dashboard"}
        else:
            raise HTTPException(status_code=404, detail="Filter not bound to this dashboard")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/{dashboard_id}/filters",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List dashboard filters",
    description="Returns all filters bound to a dashboard.",
)
async def get_dashboard_filters_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> list[dict[str, Any]]:
    """Get all filters bound to a dashboard."""
    logger.info("Getting filters for dashboard: dashboard_id=%s", dashboard_id)
    try:
        filter_ids = await DashboardFilterRepository.get_dashboard_filters(
            dashboard_id=dashboard_id, db=db
        )
        return [{"filter_id": str(fid)} for fid in filter_ids]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Dashboard Access management endpoints ---


@router.get(
    "/{dashboard_id}/access",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List dashboard access",
    description="Returns all access records for a dashboard. Requires admin role.",
    dependencies=[Depends(require_admin_role)],
)
async def get_dashboard_access_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> list[dict[str, Any]]:
    """Get all access records for a dashboard."""
    logger.info("Getting access list for dashboard: dashboard_id=%s", dashboard_id)
    try:
        access_list = await get_dashboard_access_list(
            dashboard_id=dashboard_id, db=db
        )
        return access_list  # type: ignore[no-any-return]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete(
    "/{dashboard_id}/access/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Revoke dashboard access",
    description="Revokes user's access to a dashboard. Requires admin role.",
    dependencies=[Depends(require_admin_role)],
)
async def revoke_dashboard_access_endpoint(
    dashboard_id: UUID,
    user_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> dict[str, Any]:
    """Revoke a user's access to a dashboard."""
    logger.info("Revoking access: dashboard_id=%s, user_id=%s", dashboard_id, user_id)
    try:
        result = await revoke_access(
            dashboard_id=dashboard_id, user_id=user_id, db=db
        )
        await db.commit()
        if result:
            return {"message": "Access revoked successfully"}
        else:
            raise HTTPException(status_code=404, detail="Access record not found")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Dashboard graph endpoints ---


@router.post(
    "/{dashboard_id}/graphs",
    response_model=GraphRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new graph for a dashboard",
    description="Creates a new graph for a specific dashboard. Requires admin role.",
    dependencies=[Depends(require_admin_role)],
)
async def create_dashboard_graph_endpoint(
    dashboard_id: UUID,
    graph: GraphCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> GraphRead:
    """Create a new graph for a dashboard.

    Args:
        dashboard_id: Dashboard ID.
        graph: Model with data for creating the graph.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        GraphRead: Model of the created graph.

    Raises:
        HTTPException 404: If dashboard not found.
        HTTPException 422: If data validation failed.
        HTTPException 500: On database error.
    """
    from mkobi.db.repositories.graph_repo import GraphRepository

    logger.info(
        "Creating graph for dashboard: name=%s, dashboard_id=%s, user_id=%s",
        graph.name,
        dashboard_id,
        current_user.id,
    )

    try:
        result = await GraphRepository.create(
            db=db,
            name=graph.name,
            type=graph.type,
            dashboard_id=dashboard_id,
            config=graph.config,
            dimensions=graph.dimensions,
            metrics=graph.metrics,
        )
        await db.commit()
        return GraphRead.model_validate(result)
    except ValueError as e:
        logger.warning("Validation error creating graph: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        await db.rollback()
        logger.error("Error creating graph name=%s: %s", graph.name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating graph",
        ) from e


@router.get(
    "/{dashboard_id}/graphs",
    response_model=list[GraphRead],
    status_code=status.HTTP_200_OK,
    summary="List graphs for a dashboard",
    description="Returns a list of all graphs for a specific dashboard.",
)
async def get_dashboard_graphs_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db_dependency),
) -> list[GraphRead]:
    """Get all graphs for a dashboard.

    Args:
        dashboard_id: Dashboard ID.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        list[GraphRead]: List of graph models.

    Raises:
        HTTPException 500: On database error.
    """
    from mkobi.db.repositories.graph_repo import GraphRepository

    logger.info("Getting graphs for dashboard: dashboard_id=%s", dashboard_id)

    try:
        graphs = await GraphRepository.get_by_dashboard(
            dashboard_id=dashboard_id, db=db
        )
        return [GraphRead.model_validate(g) for g in graphs]
    except Exception as e:
        logger.error("Error getting graphs for dashboard %s: %s", dashboard_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting graphs",
        ) from e