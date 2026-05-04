"""Сервис управления дашбордами.

Предоставляет бизнес-логику для CRUD операций с дашбордами.
Все операции выполняются через DashboardRepository и AccessRepository
с валидацией, проверкой прав и логированием.

Реализует интерфейс IDashboardService для внедрения зависимостей.
"""

from typing import Any

import json
import logging

from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.db.repositories.access_repo import AccessRepository
from mko_bi.db.repositories.dashboard_repo import DashboardRepository
from mko_bi.db.repositories.layout_repo import LayoutRepository
from mko_bi.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from mko_bi.models.dashboard import (
    DashboardConfig,
    DashboardRead,
    DashboardUpdate,
)
from mko_bi.models.user_roles import PermissionEnum, GraphTypeEnum
from mko_bi.models.layout import LayoutRead

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


async def _dashboard_to_read(dashboard_obj: dashboard_model.Dashboard) -> DashboardRead:
    """Преобразует модель дашборда в Pydantic модель DashboardRead с layout данными.

    Args:
        dashboard_obj: Модель дашборда SQLAlchemy.

    Returns:
        DashboardRead с заполненными layout данными.
    """
    dashboard_dict = {
        "id": dashboard_obj.id,
        "name": dashboard_obj.name,
        "description": dashboard_obj.description,
        "config": DashboardConfig(**dashboard_obj.config) if isinstance(dashboard_obj.config, dict) else DashboardConfig(**json.loads(dashboard_obj.config)),
        "layout_id": dashboard_obj.layout_id,
        "created_at": dashboard_obj.created_at,
        "updated_at": dashboard_obj.updated_at,
    }
    # Добавляем layout если есть
    if dashboard_obj.layout:
        dashboard_dict["layout"] = LayoutRead.model_validate(dashboard_obj.layout)
    return DashboardRead.model_validate(dashboard_dict)


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
    is_owner: bool = permission == "admin"
    if not is_owner:
        logger.warning(
            "Пользователь id=%s не является владельцем дашборда id=%s (permission=%s)",
            user_id,
            dashboard_id,
            permission,
        )
    return is_owner


async def create_dashboard(
    name: str, config: dict[str, Any], owner_id: int, db: AsyncSession | None = None
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

        # Преобразование в Pydantic модель с layout данными
        return await _dashboard_to_read(dashboard_obj)

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

    # Преобразование в Pydantic модель с layout данными
    return await _dashboard_to_read(dashboard_obj)


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

    # Преобразование в Pydantic модели с layout данными
    dashboards = []
    for d in dashboard_objs:
        dashboards.append(await _dashboard_to_read(d))

    logger.info(
        "Получено дашбордов для пользователя id=%s: %s",
        user_id,
        len(dashboards),
    )

    return dashboards


async def update_dashboard(
    dashboard_id: int,
    update_data: dict | DashboardUpdate | None = None,
    config: dict | None = None,
    db: AsyncSession | None = None
) -> DashboardRead | None:
    """Обновляет конфигурацию дашборда.

    Проверяет права доступа и обновляет конфигурацию дашборда. 
    Только владелец (admin) может обновлять дашборд. 

    Args:
        dashboard_id: Идентификатор дашборда. 
        update_data: Данные для обновления (config, layout_id и т.д.).
        db: Опциональная сессия базы данных. Если не передана, создается новая. 

    Returns:
        DashboardRead: Обновленная модель дашборда, или None если не найден. 

    Raises:
        ValueError: Если конфигурация некорректна. 
        SQLAlchemyError: При ошибке базы данных. 
    """
    logger.info("Обновление дашборда: dashboard_id=%s", dashboard_id)

    # Handle config parameter if provided
    if config is not None:
        if update_data is None:
            update_data = {'config': config}
        elif isinstance(update_data, dict):
            update_data['config'] = config
        else:
            update_data = update_data.model_dump(exclude_unset=True)
            update_data['config'] = config

    if not update_data:
        logger.warning("Нет данных для обновления дашборда: dashboard_id=%s", dashboard_id)
        return None

    # Валидация конфигурации если она предоставлена
    config_to_validate = None
    if update_data:
        if isinstance(update_data, dict):
            config_to_validate = update_data.get('config')
        else:
            config_to_validate = update_data.config
    if config_to_validate:
        if isinstance(config_to_validate, dict):
            config_to_validate = DashboardConfig(**config_to_validate)
        _validate_config(config_to_validate)

    # Если сессия не передана, создаем новую
    if db is None:
        async with get_session() as db:
            return await _update_dashboard_with_session(dashboard_id, update_data, db)
    else:
        return await _update_dashboard_with_session(dashboard_id, update_data, db)


async def _update_dashboard_with_session(
    dashboard_id: int, update_data: dict | DashboardUpdate, db: AsyncSession
) -> DashboardRead | None:
    """Внутренняя функция для обновления дашборда с использованием сессии."""
    # Проверка существования дашборда
    dashboard_obj = await _validate_dashboard_exists(dashboard_id, db)
    if dashboard_obj is None:
        return None

    # Подготовка данных для обновления
    update_kwargs = {}
    # Extract fields from update_data (dict or DashboardUpdate)
    if isinstance(update_data, dict):
        config = update_data.get('config')
        name = update_data.get('name')
        description = update_data.get('description')
        layout_id = update_data.get('layout_id')
    else:
        config = update_data.config
        name = update_data.name
        description = update_data.description
        layout_id = update_data.layout_id

    if config is not None:
        if isinstance(config, dict):
            config = DashboardConfig(**config)
        update_kwargs["config"] = json.dumps(config.model_dump())
    if name is not None:
        update_kwargs["name"] = name
    if description is not None:
        update_kwargs["description"] = description
    if layout_id is not None:
        # Проверка существования layout если указан
        layout = await LayoutRepository.get(layout_id, db)
        if not layout:
            logger.error("Layout не найден: id=%s", layout_id)
            raise ValueError(f"Layout с id={layout_id} не найден")
        update_kwargs["layout_id"] = layout_id

    # Обновление через репозиторий
    updated = await DashboardRepository.update(
        db=db,
        dashboard_id=dashboard_id,
        **update_kwargs,
    )

    if updated:
        logger.info("Дашборд обновлен: id=%s", dashboard_id)
        await db.commit()
        # Преобразование в Pydantic модель с layout данными
        return await _dashboard_to_read(updated)
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
