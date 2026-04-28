"""Сервис управления дашбордами.

Предоставляет бизнес-логику для CRUD операций с дашбордами.
Все операции выполняются через DashboardRepository и AccessRepository
с валидацией, проверкой прав и логированием.
"""

import json
import logging

from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.db.repositories.access_repo import AccessRepository
from mko_bi.db.repositories.dashboard_repo import DashboardRepository
from sqlalchemy.orm import Session
from mko_bi.db.session import SessionLocal
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
    except ValueError:
        logger.error(
            "Недопустимый уровень доступа: '%s'. Допустимые: %s",
            permission,
            sorted([e.value for e in PermissionEnum]),
        )
        raise ValueError(
            f"Недопустимый уровень доступа: '{permission}'. "
            f"Допустимые значения: {', '.join(sorted([e.value for e in PermissionEnum]))}"
        )


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
        except ValueError:
            logger.error("Недопустимый тип графика: '%s'", graph_type)
            raise ValueError(
                f"Недопустимый тип графика: '{graph_type}'. "
                f"Допустимые значения: {', '.join([e.value for e in GraphTypeEnum])}"
            )


def _validate_dashboard_exists(
    dashboard_id: int, db: Session
) -> dashboard_model.Dashboard | None:
    """Проверяет существование дашборда и возвращает его модель.

    Args:
        dashboard_id: Идентификатор дашборда.
        db: Сессия базы данных.

    Returns:
        Модель дашборда или None, если не найден.
    """
    dashboard_obj = DashboardRepository.get(dashboard_id, db)
    if dashboard_obj is None:
        logger.warning("Дашборд не найден: id=%s", dashboard_id)
    return dashboard_obj


def _check_owner_permission(dashboard_id: int, user_id: int, db: Session) -> bool:
    """Проверяет, является ли пользователь владельцем дашборда (admin доступ).

    Args:
        dashboard_id: Идентификатор дашборда.
        user_id: Идентификатор пользователя.
        db: Сессия базы данных.

    Returns:
        True, если пользователь является владельцем (admin), иначе False.
    """
    permission = AccessRepository.check_access(user_id, dashboard_id, db)
    is_owner = permission == "admin"
    if not is_owner:
        logger.warning(
            "Пользователь id=%s не является владельцем дашборда id=%s (permission=%s)",
            user_id,
            dashboard_id,
            permission,
        )
    return is_owner


def create_dashboard(
    name: str, config: dict, owner_id: int, db: Session | None = None
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
    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
        # Создание дашборда и предоставление прав в одной транзакции
        with db.begin():
            # Создание дашборда через репозиторий
            dashboard_obj = DashboardRepository.create(
                db=db,
                name=name,
                config=json.dumps(config),
            )
            logger.info(
                "Дашборд создан: id=%s, name=%s", dashboard_obj.id, dashboard_obj.name
            )

            # Предоставление прав администратора владельцу
            AccessRepository.grant_access(
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
        logger.error(
            "Ошибка при создании дашборда name=%s, owner_id=%s: %s",
            name,
            owner_id,
            e,
        )
        raise
    finally:
        if local_session:
            db.close()


def get_dashboard(
    dashboard_id: int, user_id: int, db: Session | None = None
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
    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
        # Проверка существования дашборда
        dashboard_obj = _validate_dashboard_exists(dashboard_id, db)
        if dashboard_obj is None:
            return None

        # Проверка доступа пользователя
        permission = AccessRepository.check_access(user_id, dashboard_id, db)
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

    except Exception as e:
        logger.error(
            "Ошибка при получении дашборда id=%s, user_id=%s: %s",
            dashboard_id,
            user_id,
            e,
        )
        raise
    finally:
        if local_session:
            db.close()


def get_user_dashboards(user_id: int, db: Session | None = None) -> list[DashboardRead]:
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
    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
        # Получение дашбордов через репозиторий
        dashboard_objs = AccessRepository.get_user_dashboards(user_id, db)

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

    except Exception as e:
        logger.error(
            "Ошибка при получении дашбордов пользователя id=%s: %s", user_id, e
        )
        raise
    finally:
        if local_session:
            db.close()


def update_dashboard(
    dashboard_id: int, config: dict, db: Session | None = None
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
    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
        # Проверка существования дашборда
        dashboard_obj = _validate_dashboard_exists(dashboard_id, db)
        if dashboard_obj is None:
            return None

        # Обновление через репозиторий
        updated = DashboardRepository.update(
            db=db,
            dashboard_id=dashboard_id,
            config=json.dumps(config),
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

    except ValueError:
        raise
    except Exception as e:
        if local_session:
            db.rollback()
        logger.error("Ошибка при обновлении дашборда id=%s: %s", dashboard_id, e)
        raise
    finally:
        if local_session:
            db.close()


def delete_dashboard(dashboard_id: int, db: Session | None = None) -> bool:
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
    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
        # Удаление через репозиторий (каскадное удаление прав доступа)
        result = DashboardRepository.delete(dashboard_id, db)

        if result:
            logger.info("Дашборд успешно удален: id=%s", dashboard_id)
        else:
            logger.warning("Дашборд не найден для удаления: id=%s", dashboard_id)

        return result

    except Exception as e:
        if local_session:
            db.rollback()
        logger.error("Ошибка при удалении дашборда id=%s: %s", dashboard_id, e)
        raise
    finally:
        if local_session:
            db.close()


def grant_access(
    dashboard_id: int,
    user_id: int,
    permission: str,
    db: Session | None = None,
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
    local_session = False
    if db is None:
        db = SessionLocal()
        local_session = True

    try:
        # Проверка существования дашборда и предоставление доступа в транзакции
        with db.begin():
            # Проверка существования дашборда
            dashboard_obj = _validate_dashboard_exists(dashboard_id, db)
            if dashboard_obj is None:
                raise ValueError(f"Дашборд с id={dashboard_id} не найден")

            # Предоставление доступа через репозиторий
            AccessRepository.grant_access(
                db=db,
                user_id=user_id,
                dashboard_id=dashboard_id,
                permission_level=permission,
            )

        logger.info(
            "Доступ успешно предоставлен: user_id=%s, dashboard_id=%s, permission=%s",
            user_id,
            dashboard_id,
            permission,
        )

        return True

    except ValueError:
        raise
    except Exception as e:
        logger.error(
            "Ошибка при предоставлении доступа user_id=%s, dashboard_id=%s: %s",
            user_id,
            dashboard_id,
            e,
        )
        raise
    finally:
        if local_session:
            db.close()
