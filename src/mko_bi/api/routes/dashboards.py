"""Маршруты для управления дашбордами.

Этот модуль предоставляет эндпоинты для CRUD операций с дашбордами.
Доступ к большинству операций ограничен и требует аутентификации.
Операции создания, обновления и удаления доступны только владельцам.
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
from mko_bi.models.dashboard import (
    DashboardCreate,
    DashboardRead,
    DashboardUpdate,
)
from mko_bi.models.access import AccessGrant
from mko_bi.services.dashboard_service import (
    create_dashboard,
    get_dashboard,
    get_user_dashboards,
    update_dashboard,
    delete_dashboard,
    grant_access,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.post(
    "/",
    response_model=DashboardRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создание дашборда",
    description="Создает новый дашборд. Текущий пользователь становится владельцем.",
)
async def create_dashboard_endpoint(
    dashboard: DashboardCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
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
    logger.info(
        "Создание дашборда: name=%s, owner_id=%s",
        dashboard.name,
        current_user.id,
    )

    try:
        result = create_dashboard(
            name=dashboard.name,
            config=dashboard.config.model_dump(),
            owner_id=current_user.id,
            db=db,
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
    "/",
    response_model=list[DashboardRead],
    status_code=status.HTTP_200_OK,
    summary="Список доступных дашбордов",
    description="Возвращает список всех дашбордов, доступных текущему пользователю.",
)
async def get_dashboards_endpoint(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
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
        dashboards = get_user_dashboards(user_id=current_user.id, db=db)
        logger.info(
            "Получено дашбордов для пользователя id=%s: %s",
            current_user.id,
            len(dashboards),
        )
        return dashboards
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
    db: Session = Depends(get_db),
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
        dashboard = get_dashboard(
            dashboard_id=dashboard_id,
            user_id=current_user.id,
            db=db,
        )
        if dashboard is None:
            logger.warning(
                "Дашборд не найден или нет доступа: dashboard_id=%s, user_id=%s",
                dashboard_id,
                current_user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Дашборд не найден или у вас нет доступа",
            )
        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Ошибка при получении дашборда id=%s: %s",
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
    description="Обновляет конфигурацию дашборда. Доступно только владельцу.",
    dependencies=[Depends(require_viewer_role)],
)
async def update_dashboard_endpoint(
    dashboard_id: UUID,
    dashboard_update: DashboardUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
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
        from mko_bi.core.permissions import check_dashboard_access

        if not check_dashboard_access(
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

        updated = update_dashboard(
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
    description="Удаляет дашборд. Доступно только владельцу.",
    dependencies=[Depends(require_viewer_role)],
)
async def delete_dashboard_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
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
        from mko_bi.core.permissions import check_dashboard_access

        if not check_dashboard_access(
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

        result = delete_dashboard(dashboard_id=dashboard_id, db=db)
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
    db: Session = Depends(get_db),
) -> dict:
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
        from mko_bi.core.permissions import check_dashboard_access

        if not check_dashboard_access(
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

        result = grant_access(
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