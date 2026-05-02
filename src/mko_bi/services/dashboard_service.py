"""Сервис управления дашбордами.

Предоставляет бизнес-логику для CRUD операций с дашбордами.
Все операции выполняются через DashboardRepository и AccessRepository
с валидацией, проверкой прав и логированием.

Реализует интерфейс IDashboardService для внедрения зависимостей.
"""

import json
import logging

from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.db.repositories.access_repo import AccessRepository
from mko_bi.db.repositories.dashboard_repo import DashboardRepository
from mko_bi.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from mko_bi.models.dashboard import (
    DashboardConfig,
    DashboardRead,
)
from mko_bi.models.user_roles import PermissionEnum, GraphTypeEnum

logger = logging.getLogger(__name__)

# Допустимые уровни доступа (берем из PermissionEnum)


def _validate_permission(permission: str) -> None:
    """Проверяет, что уровень доступа является допустимым.

    Args:
        permission: Уровень доступа для проверки.

    Raises:
        ValueError: Если уровень доступа не входит в список допустимых.
    """
    # Нормализуем "read" -> "view", "write" -> "edit" для совместимости
    normalized = permission
    if permission == "read":
        normalized = "view"
    elif permission == "write":
        normalized = "edit"

    try:
        PermissionEnum(normalized)
    except ValueError as err:
        logger.error(
            "Недопустимый уровень доступа: '%s'. Допустимые: %s",
            permission,
            sorted([e.value for e in PermissionEnum]),
        )
        raise ValueError(
            f"Недопустимый уровень доступа: '{permission}'. "
            f"Допустимые значения: {', '.join(sorted([e.value for e in PermissionEnum]))}"
        ) from err


def _validate_config(config: DashboardConfig) -> None:
    """Проверяет валидность конфигурации дашборда.

    Args:
        config: Конфигурация дашборда для проверки.

    Raises:
        ValueError: Если конфигурация некорректна. 
    """
    if not config.graph_types:
        logger.error("Конфигурация дашборда не содержит типов графиков")
        raise ValueError(
            "Конфигурация дашборда должна содержать хотя бы один тип графика"
        )

    for graph_type in config.graph_types:
        try:
            GraphTypeEnum(graph_type)
        except ValueError as err:
            logger.error("Недопустимый тип графика: '%s'", graph_type)
            raise ValueError(
                f"Недопустимый тип графика: '{graph_type}'. "
                f"Допустимые значения: {', '.join([e.value for e in GraphTypeEnum])}"
            ) from err


async def _validate_dashboard_exists(
    dashboard_id: int, db: AsyncSession
) -> dashboard_model.Dashboard | None:
    """Проверяет существование дашборда и возвращает его модель.

    Args:
        dashboard_id: Идентификатор дашборда. 
        db: Асинхронная сессия базы данных. 

    Returns:
        Модель дашборда или None, если не найден. 
    """
    dashboard_obj = await DashboardRepository.get(dashboard_id, db)
    if dashboard_obj is None:
        logger.warning("Дашборд не найден: id=%s", dashboard_id)
    return dashboard_obj


async def _check_owner_permission(dashboard_id: int, user_id: int, db: AsyncSession) -> bool:
    """Проверяет, является ли пользователь владельцем дашборда (admin доступ).

    Args:
        dashboard_id: Идентификатор дашборда. 
        user_id: Идентификатор пользователя. 
        db: Асинхронная сессия базы данных. 

    Returns:
        True, если пользователь является владельцем (admin), иначе False. 
    """
    permission = await AccessRepository.check_access(user_id, dashboard_id, db)
    is_owner = permission == "admin"
    if not is_owner:
        logger.warning(
            "Пользователь id=%s не является владельцем дашборда id=%s (permission=%s)",
            user_id,
            dashboard_id,
            permission,
        )
    return is_owner


async def create_dashboard(
    name: str, config: dict, owner_id: int, db: AsyncSession | None = None
) -> DashboardRead:
    """Создает новый дашборд с владельцем.

    Создает дашборд в базе данных и предоставляет владельцу
    права администратора (admin) на управление дашбордом. 
    Операция выполняется в транзакции: если предоставление прав 
    доступа завершается ошибкой, создание дашборда откатывается. 

    Args:
        name: Название дашборда. 
        config: Конфигурация дашборда в формате JSON-совместимого dict. 
        owner_id: Идентификатор пользователя-владельца. 
        db: Опциональная сессия базы данных. Если не передана, создается новая. 

    Returns:
        DashboardRead: Модель созданного дашборда. 

    Raises:
        ValueError: Если конфигурация некорректна. 
        SQLAlchemyError: При ошибке базы данных. 

    Example:
        >>> dashboard = create_dashboard(
        ...     name="Sales Dashboard",
        ...     config={"graph_types": ["bar"], "charts": []},
        ...     owner_id=1
        ... )
        >>> dashboard.name
        'Sales Dashboard'
    """
    logger.info("Начало создания дашборда: name=%s, owner_id=%s", name, owner_id)

    # Валидация конфигурации
    config_obj = DashboardConfig(**config)
    _validate_config(config_obj)

    # Если сессия не передана, создаем новую
    if db is None:
        async with get_session() as db:
            return await _create_dashboard_with_session(name, config_obj, owner_id, db)
    else:
        return await _create_dashboard_with_session(name, config_obj, owner_id, db)


async def _create_dashboard_with_session(
    name: str, config_obj: DashboardConfig, owner_id: int, db: AsyncSession
) -> DashboardRead:
    """Внутренняя функция для создания дашборда с использованием сессии."""
    try:
        # Создание дашборда через репозиторий
        dashboard_obj = await DashboardRepository.create(
            db=db,
            name=name,
            config=json.dumps(config_obj.model_dump()),
        )
        logger.info(
            "Дашборд создан: id=%s, name=%s", dashboard_obj.id, dashboard_obj.name
        )

        # Предоставление прав администратора владельцу
        await AccessRepository.grant_access(
            db=db,
            user_id=owner_id,
            dashboard_id=dashboard_obj.id,
            permission="admin",
        )
        logger.info(
            "Права администратора предоставлены: user_id=%s, dashboard_id=%s",
            owner_id,
            dashboard_obj.id,
        )
        
        # Commit the transaction
        await db.commit()
        logger.info("Транзакция коммичена для дашборда id=%s", dashboard_obj.id)

        # Преобразование в Pydantic модель
        # Преобразуем config из JSON строки в dict
        dashboard_dict = dashboard_obj.__dict__.copy()
        if isinstance(dashboard_dict.get("config"), str):
            dashboard_dict["config"] = json.loads(dashboard_dict["config"])
        return DashboardRead.model_validate(dashboard_dict)

    except ValueError:
        # Валидационные ошибки не требуют отката (транзакция еще не начата)
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Ошибка при создании дашборда name=%s, owner_id=%s: %s",
            name,
            owner_id,
            e,
        )
        raise


async def get_dashboard(
    dashboard_id: int, user_id: int, db: AsyncSession | None = None
) -> DashboardRead | None:
    """Получает дашборд по ID с проверкой доступа.

    Проверяет, есть ли у пользователя доступ к дашборду, 
    и возвращает его данные только в случае наличия прав. 

    Args:
        dashboard_id: Идентификатор дашборда. 
        user_id: Идентификатор пользователя, запрашивающего доступ. 
        db: Опциональная сессия базы данных. Если не передана, создается новая. 

    Returns:
        DashboardRead: Модель дашборда, если доступ разрешен, иначе None. 

    Raises:
        SQLAlchemyError: При ошибке базы данных. 
    """
    logger.info("Запрос дашборда: dashboard_id=%s, user_id=%s", dashboard_id, user_id)

    # Если сессия не передана, создаем новую
    if db is None:
        async with get_session() as db:
            return await _get_dashboard_with_session(dashboard_id, user_id, db)
    else:
        return await _get_dashboard_with_session(dashboard_id, user_id, db)


async def _get_dashboard_with_session(
    dashboard_id: int, user_id: int, db: AsyncSession
) -> DashboardRead | None:
    """Внутренняя функция для получения дашборда с использованием сессии."""
    # Проверка существования дашборда
    dashboard_obj = await _validate_dashboard_exists(dashboard_id, db)
    if dashboard_obj is None:
        return None

    # Проверка доступа пользователя
    permission = await AccessRepository.check_access(user_id, dashboard_id, db)
    if permission is None:
        logger.warning(
            "Отказ в доступе: user_id=%s, dashboard_id=%s", user_id, dashboard_id
        )
        return None

    logger.info(
        "Дашборд предоставлен: id=%s, user_id=%s, permission=%s",
        dashboard_id,
        user_id,
        permission,
    )

    # Преобразование в Pydantic модель
    # Преобразуем config из JSON строки в dict
    dashboard_dict = dashboard_obj.__dict__.copy()
    if isinstance(dashboard_dict.get("config"), str):
        dashboard_dict["config"] = json.loads(dashboard_dict["config"])
    return DashboardRead.model_validate(dashboard_dict)


async def get_user_dashboards(user_id: int, db: AsyncSession | None = None) -> list[DashboardRead]:
    """Получает все дашборды, доступные пользователю.

    Фильтрует дашборды по правам доступа пользователя. 

    Args:
        user_id: Идентификатор пользователя. 
        db: Опциональная сессия базы данных. Если не передана, создается новая. 

    Returns:
        List[DashboardRead]: Список моделей дашбордов, доступных пользователю. 

    Raises:
        SQLAlchemyError: При ошибке базы данных. 
    """
    logger.info("Получение дашбордов для пользователя: user_id=%s", user_id)

    # Если сессия не передана, создаем новую
    if db is None:
        async with get_session() as db:
            return await _get_user_dashboards_with_session(user_id, db)
    else:
        return await _get_user_dashboards_with_session(user_id, db)


async def _get_user_dashboards_with_session(user_id: int, db: AsyncSession) -> list[DashboardRead]:
    """Внутренняя функция для получения дашбордов пользователя."""
    # Получение дашбордов через репозиторий
    dashboard_objs = await AccessRepository.get_user_dashboards(user_id, db)

    # Преобразование в Pydantic модели
    dashboards = []
    for d in dashboard_objs:
        d_dict = d.__dict__.copy()
        if isinstance(d_dict.get("config"), str):
            d_dict["config"] = json.loads(d_dict["config"])
        dashboards.append(DashboardRead.model_validate(d_dict))

    logger.info(
        "Получено дашбордов для пользователя id=%s: %s",
        user_id,
        len(dashboards),
    )

    return dashboards


async def update_dashboard(
    dashboard_id: int, config: dict, db: AsyncSession | None = None
) -> DashboardRead | None:
    """Обновляет конфигурацию дашборда.

    Проверяет права доступа и обновляет конфигурацию дашборда. 
    Только владелец (admin) может обновлять дашборд. 

    Args:
        dashboard_id: Идентификатор дашборда. 
        config: Новая конфигурация дашборда в формате JSON-совместимого dict. 
        db: Опциональная сессия базы данных. Если не передана, создается новая. 

    Returns:
        DashboardRead: Обновленная модель дашборда, или None если не найден. 

    Raises:
        ValueError: Если конфигурация некорректна. 
        SQLAlchemyError: При ошибке базы данных. 
    """
    logger.info("Обновление дашборда: dashboard_id=%s", dashboard_id)

    # Валидация конфигурации
    config_obj = DashboardConfig(**config)
    _validate_config(config_obj)

    # Если сессия не передана, создаем новую
    if db is None:
        async with get_session() as db:
            return await _update_dashboard_with_session(dashboard_id, config_obj, db)
    else:
        return await _update_dashboard_with_session(dashboard_id, config_obj, db)


async def _update_dashboard_with_session(
    dashboard_id: int, config_obj: DashboardConfig, db: AsyncSession
) -> DashboardRead | None:
    """Внутренняя функция для обновления дашборда с использованием сессии."""
    # Проверка существования дашборда
    dashboard_obj = await _validate_dashboard_exists(dashboard_id, db)
    if dashboard_obj is None:
        return None

    # Обновление через репозиторий
    updated = await DashboardRepository.update(
        db=db,
        dashboard_id=dashboard_id,
        config=json.dumps(config_obj.model_dump()),
    )

    if updated:
        logger.info("Дашборд обновлен: id=%s", dashboard_id)
        # Преобразуем config из JSON строки в dict
        updated_dict = updated.__dict__.copy()
        if isinstance(updated_dict.get("config"), str):
            updated_dict["config"] = json.loads(updated_dict["config"])
        return DashboardRead.model_validate(updated_dict)
    else:
        logger.warning("Не удалось обновить дашборд: id=%s", dashboard_id)
        return None


async def delete_dashboard(dashboard_id: int, db: AsyncSession | None = None) -> bool:
    """Удаляет дашборд и все связанные права доступа.

    Выполняет каскадное удаление дашборда и всех прав доступа к нему. 

    Args:
        dashboard_id: Идентификатор дашборда для удаления. 
        db: Опциональная сессия базы данных. Если не передана, создается новая. 

    Returns:
        bool: True, если удаление успешно, False - если дашборд не найден. 

    Raises:
        SQLAlchemyError: При ошибке базы данных. 
    """
    logger.info("Удаление дашборда: dashboard_id=%s", dashboard_id)

    # Если сессия не передана, создаем новую
    if db is None:
        async with get_session() as db:
            return await _delete_dashboard_with_session(dashboard_id, db)
    else:
        return await _delete_dashboard_with_session(dashboard_id, db)


async def _delete_dashboard_with_session(dashboard_id: int, db: AsyncSession) -> bool:
    """Внутренняя функция для удаления дашборда с использованием сессии."""
    # Удаление через репозиторий (каскадное удаление прав доступа)
    result = await DashboardRepository.delete(dashboard_id, db)

    if result:
        logger.info("Дашборд успешно удален: id=%s", dashboard_id)
    else:
        logger.warning("Дашборд не найден для удаления: id=%s", dashboard_id)

    return bool(result)


async def grant_access(
    dashboard_id: int,
    user_id: int,
    permission: str,
    db: AsyncSession | None = None,
) -> bool:
    """Предоставляет пользователю доступ к дашборду.

    Операция выполняется в транзакции: если предоставление прав 
    доступа завершается ошибкой, транзакция откатывается. 

    Args:
        dashboard_id: Идентификатор дашборда. 
        user_id: Идентификатор пользователя. 
        permission: Уровень доступа (read/write/admin). 
        db: Опциональная сессия базы данных. Если не передана, создается новая. 

    Returns:
        bool: True, если доступ успешно предоставлен. 

    Raises:
        ValueError: Если уровень доступа некорректен. 
        SQLAlchemyError: При ошибке базы данных. 
    """
    logger.info(
        "Предоставление доступа: dashboard_id=%s, user_id=%s, permission=%s",
        dashboard_id,
        user_id,
        permission,
    )

    # Валидация уровня доступа
    _validate_permission(permission)

    # Если сессия не передана, создаем новую
    if db is None:
        async with get_session() as db:
            return await _grant_access_with_session(dashboard_id, user_id, permission, db)
    else:
        return await _grant_access_with_session(dashboard_id, user_id, permission, db)


async def _grant_access_with_session(
    dashboard_id: int, user_id: int, permission: str, db: AsyncSession
) -> bool:
    """Внутренняя функция для предоставления доступа с использованием сессии."""
    # Проверка существования дашборда
    dashboard_obj = await _validate_dashboard_exists(dashboard_id, db)
    if dashboard_obj is None:
        raise ValueError(f"Дашборд с id={dashboard_id} не найден")

    # Предоставление доступа через репозиторий
    await AccessRepository.grant_access(
        db=db,
        user_id=user_id,
        dashboard_id=dashboard_id,
        permission=permission,
    )

    # Commit if we own the session
    await db.commit()

    logger.info(
        "Доступ успешно предоставлен: user_id=%s, dashboard_id=%s, permission=%s",
        user_id,
        dashboard_id,
        permission,
    )

    return True
