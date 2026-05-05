"""Зависимости FastAPI для API маршрутов.

Этот модуль предоставляет готовые зависимости FastAPI для использования
в API маршрутах, включая аутентификацию, авторизацию и проверку прав доступа.

Типичные сценарии использования:
    - Защита эндпоинтов аутентификацией
    - Проверка ролей пользователей
    - Проверка доступа к дашбордам
    - Получение текущего пользователя
"""

import logging
from typing import Annotated, Any
from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession

from mko_bi.core.permissions import (
    get_current_user,
    check_dashboard_access,
    check_role,
    AuthenticationError,
)
from mko_bi.db.session import get_db, get_session  # noqa: F401 - re-exported for backwards compatibility
from mko_bi.models.user import UserDB
from mko_bi.interfaces import (
    IUserRepository,
    IDashboardRepository,
    IAccessRepository,
    IAggregatedDataRepository,
    IFilterRepository,
    IProcessingConfigRepository,
    IProcessingLogRepository,
    IAuthService,
    IUserService,
    IDashboardService,
    IFilterService,
    IDataService,
    IProcessingConfigService,
    IProcessingLogService,
)

from mko_bi.models.user_roles import UserRoleEnum

logger = logging.getLogger(__name__)


# --- Базовые зависимости ---

security = HTTPBearer()


async def get_db_dependency() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения асинхронной сессии базы данных.

    Создает новую сессию для каждого запроса и закрывает её после завершения.

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy.

    Example:
        @app.get("/users/")
        async def get_users(db: AsyncSession = Depends(get_db_dependency)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with get_session() as db:
        yield db


# --- Dependency Injection для репозиториев ---


def get_user_repository(db: AsyncSession = Depends(get_db_dependency)) -> IUserRepository:
    """DI фабрика для получения репозитория пользователей.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IUserRepository: Реализация репозитория пользователей.
    """
    from mko_bi.db.repositories.user_repo import UserRepository
    return UserRepository()


def get_dashboard_repository(db: AsyncSession = Depends(get_db_dependency)) -> IDashboardRepository:
    """DI фабрика для получения репозитория дашбордов.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IDashboardRepository: Реализация репозитория дашбордов.
    """
    from mko_bi.db.repositories.dashboard_repo import DashboardRepository
    return DashboardRepository()


def get_access_repository(db: AsyncSession = Depends(get_db_dependency)) -> IAccessRepository:
    """DI фабрика для получения репозитория прав доступа.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IAccessRepository: Реализация репозитория прав доступа.
    """
    from mko_bi.db.repositories.access_repo import AccessRepository
    return AccessRepository()


def get_aggregated_data_repository(db: AsyncSession = Depends(get_db_dependency)) -> IAggregatedDataRepository:
    """DI фабрика для получения репозитория агрегированных данных.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IAggregatedDataRepository: Реализация репозитория агрегированных данных.
    """
    from mko_bi.db.repositories.aggregated_data_repo import AggregatedDataRepository
    return AggregatedDataRepository()


def get_filter_repository(db: AsyncSession = Depends(get_db_dependency)) -> IFilterRepository:
    """DI фабрика для получения репозитория фильтров.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IFilterRepository: Реализация репозитория фильтров.
    """
    from mko_bi.db.repositories.filter_repo import FilterRepository
    return FilterRepository()


def get_processing_config_repository(db: AsyncSession = Depends(get_db_dependency)) -> IProcessingConfigRepository:
    """DI фабрика для получения репозитория настроек обработки.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IProcessingConfigRepository: Реализация репозитория настроек обработки.
    """
    from mko_bi.db.repositories.processing_config_repo import ProcessingConfigRepository
    return ProcessingConfigRepository()


def get_processing_log_repository(db: AsyncSession = Depends(get_db_dependency)) -> IProcessingLogRepository:
    """DI фабрика для получения репозитория логов обработки.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IProcessingLogRepository: Реализация репозитория логов обработки.
    """
    from mko_bi.db.repositories.processing_log_repo import ProcessingLogRepository
    return ProcessingLogRepository()


# --- Dependency Injection для сервисов ---


def get_auth_service(db: AsyncSession = Depends(get_db_dependency)) -> IAuthService:
    """DI фабрика для получения сервиса аутентификации.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IAuthService: Реализация сервиса аутентификации.
    """
    from mko_bi.services.auth_service import AuthService
    return AuthService()


def get_user_service(db: AsyncSession = Depends(get_db_dependency)) -> IUserService:
    """DI фабрика для получения сервиса пользователей.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IUserService: Реализация сервиса пользователей.
    """
    from mko_bi.services.user_service import UserService
    return UserService()


def get_dashboard_service(db: AsyncSession = Depends(get_db_dependency)) -> IDashboardService:
    """DI фабрика для получения сервиса дашбордов.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IDashboardService: Реализация сервиса дашбордов.
    """
    from mko_bi.services.dashboard_service import DashboardService
    return DashboardService()


def get_filter_service(db: AsyncSession = Depends(get_db_dependency)) -> IFilterService:
    """DI фабрика для получения сервиса фильтров.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IFilterService: Реализация сервиса фильтров.
    """
    from mko_bi.services.filter_service import FilterService
    return FilterService()


def get_data_service(db: AsyncSession = Depends(get_db_dependency)) -> IDataService:
    """DI фабрика для получения сервиса данных.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IDataService: Реализация сервиса данных.
    """
    from mko_bi.services.data_service import DataService
    return DataService()


def get_processing_config_service(db: AsyncSession = Depends(get_db_dependency)) -> IProcessingConfigService:
    """DI фабрика для получения сервиса настроек обработки.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IProcessingConfigService: Реализация сервиса настроек обработки.
    """
    from mko_bi.services.processing_config_service import ProcessingConfigService
    return ProcessingConfigService()


def get_processing_log_service(db: AsyncSession = Depends(get_db_dependency)) -> IProcessingLogService:
    """DI фабрика для получения сервиса логов обработки.
    
    Args:
        db: Асинхронная сессия базы данных.
        
    Returns:
        IProcessingLogService: Реализация сервиса логов обработки.
    """
    from mko_bi.services.processing_log_service import ProcessingLogService
    return ProcessingLogService()


# --- Аутентификация ---


def get_token_from_header(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Извлекает токен из заголовка Authorization.

    Args:
        credentials: Учетные данные из заголовка.

    Returns:
        str: JWT токен.

    Raises:
        HTTPException: Если заголовок отсутствует или некорректен.
    """
    if credentials.scheme.lower() != "bearer":
        logger.warning("Некорректная схема аутентификации: %s", credentials.scheme)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректная схема аутентификации",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


async def get_current_user_dependency(
    token: str = Depends(get_token_from_header),
    db: AsyncSession = Depends(get_db_dependency),
) -> UserDB:
    """Получает текущего аутентифицированного пользователя.

    Декодирует JWT токен, извлекает user_id и получает данные
    пользователя из базы данных.

    Args:
        token: JWT токен доступа.
        db: Асинхронная сессия базы данных.

    Returns:
        UserDB: Модель аутентифицированного пользователя.

    Raises:
        HTTPException: Если токен недействителен, истек или пользователь не найден.

    Example:
        @app.get("/users/me")
        async def read_users_me(user: UserDB = Depends(get_current_user_dependency)):
            return user
    """
    try:
        user = await get_current_user(token, db)
        logger.debug("Пользователь аутентифицирован: user_id=%s", user.id)
        return user
    except ExpiredSignatureError:
        logger.warning("Истёкший токен")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истёк",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except AuthenticationError:
        # AuthenticationError уже залогирована в get_current_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось аутентифицировать пользователя",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except Exception as e:
        logger.error("Неожиданная ошибка аутентификации: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера",
        ) from e


# --- Авторизация (проверка ролей) ---


def require_admin_role(
    user: UserDB = Depends(get_current_user_dependency),
) -> UserDB:
    """Требует роль администратора.

    Args:
        user: Пользователь (получается через get_current_user_dependency).

    Returns:
        UserDB: Пользователь, если у него роль admin.

    Raises:
        HTTPException: Если у пользователя нет роли admin.

    Example:
        @app.post("/users/")
        async def create_user(
            user_data: UserCreate,
            _: UserDB = Depends(require_admin_role),
        ):
            return create_user(user_data)
    """
    if not check_role(user.role, UserRoleEnum.admin):
        logger.warning(
            "Требуется роль admin, у пользователя: user_id=%s, role=%s",
            user.id,
            user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль: admin",
        )
    return user


def require_editor_role(
    user: UserDB = Depends(get_current_user_dependency),
) -> UserDB:
    """Требует роль редактора или выше (editor, admin).

    Args:
        user: Пользователь (получается через get_current_user_dependency).

    Returns:
        UserDB: Пользователь, если у него роль editor или admin.

    Raises:
        HTTPException: Если у пользователя недостаточно прав.

    Example:
        @app.post("/upload/")
        async def upload_file(
            _: UserDB = Depends(require_editor_role),
        ):
            return {"message": "Upload allowed"}
    """
    if not check_role(user.role, UserRoleEnum.editor):
        logger.warning(
            "Требуется роль editor или выше, у пользователя: user_id=%s, role=%s",
            user.id,
            user.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль: editor или admin",
        )
    return user


def require_viewer_role(
    user: UserDB = Depends(get_current_user_dependency),
) -> UserDB:
    """Требует роль зрителя или выше (viewer, editor, admin).

    По сути, просто проверяет, что пользователь аутентифицирован,
    так как viewer - минимальная роль.

    Args:
        user: Пользователь (получается через get_current_user_dependency).

    Returns:
        UserDB: Пользователь.

    Example:
        @app.get("/dashboards/")
        async def list_dashboards(
            user: UserDB = Depends(require_viewer_role),
        ):
            return {"message": "Access granted"}
    """
    # Все аутентифицированные пользователи имеют хотя бы роль viewer
    return user


def require_role_dependency(required_role: str):
    """Создает зависимость для проверки конкретной роли.

    Универсальная зависимость для проверки любой роли.

    Args:
        required_role: Требуемая роль (viewer, editor, admin).

    Returns:
        Callable: Функция-зависимость FastAPI.

    Raises:
        HTTPException: Если у пользователя недостаточно прав.

    Example:
        @app.get("/admin-only")
        async def admin_only(
            user: UserDB = Depends(require_role_dependency(UserRoleEnum.admin)),
        ):
            return {"message": "Admin area"}
    """

    def role_checker(
        user: UserDB = Depends(get_current_user_dependency),
    ) -> UserDB:
        if not check_role(user.role, required_role):
            logger.warning(
                "Недостаточно прав: user_id=%s, user_role=%s, required_role=%s",
                user.id,
                user.role,
                required_role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Требуется роль: {required_role} или выше",
            )
        return user

    return role_checker


# --- Проверка доступа к дашбордам ---


async def require_dashboard_read_access(
    dashboard_id: UUID,
    user: UserDB = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db_dependency),
) -> UserDB:
    """Требует права на чтение дашборда.

    Args:
        dashboard_id: ID дашборда (извлекается из пути).
        user: Пользователь (получается через get_current_user_dependency).
        db: Асинхронная сессия базы данных.

    Returns:
        UserDB: Пользователь, если у него есть доступ.

    Raises:
        HTTPException: Если у пользователя нет прав на чтение.

    Example:
        @app.get("/dashboards/{dashboard_id}")
        async def get_dashboard(
            dashboard_id: UUID,
            user: UserDB = Depends(require_dashboard_read_access),
        ):
            return {"message": "Dashboard data"}
    """
    if not await check_dashboard_access(
        user_id=user.id,
        dashboard_id=dashboard_id,
        required_permission="view",
        db=db,
    ):
        logger.warning(
            "Отказано в чтении дашборда: user_id=%s, dashboard_id=%s",
            user.id,
            dashboard_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на чтение этого дашборда",
        )
    return user


async def require_dashboard_write_access(
    dashboard_id: UUID,
    user: UserDB = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db_dependency),
) -> UserDB:
    """Требует права на запись (редактирование) дашборда.

    Args:
        dashboard_id: ID дашборда (извлекается из пути).
        user: Пользователь (получается через get_current_user_dependency).
        db: Асинхронная сессия базы данных.

    Returns:
        UserDB: Пользователь, если у него есть права на запись.

    Raises:
        HTTPException: Если у пользователя нет прав на запись.

    Example:
        @app.put("/dashboards/{dashboard_id}")
        async def update_dashboard(
            dashboard_id: UUID,
            user: UserDB = Depends(require_dashboard_write_access),
        ):
            return {"message": "Update allowed"}
    """
    if not await check_dashboard_access(
        user_id=user.id,
        dashboard_id=dashboard_id,
        required_permission="edit",
        db=db,
    ):
        logger.warning(
            "Отказано в записи дашборда: user_id=%s, dashboard_id=%s",
            user.id,
            dashboard_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на редактирование этого дашборда",
        )
    return user


async def require_dashboard_admin_access(
    dashboard_id: UUID,
    user: UserDB = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db_dependency),
) -> UserDB:
    """Требует права на администрирование дашборда.

    Args:
        dashboard_id: ID дашборда (извлекается из пути).
        user: Пользователь (получается через get_current_user_dependency).
        db: Асинхронная сессия базы данных.

    Returns:
        UserDB: Пользователь, если у него есть права на администрирование.

    Raises:
        HTTPException: Если у пользователя нет прав на администрирование.

    Example:
        @app.delete("/dashboards/{dashboard_id}")
        async def delete_dashboard(
            dashboard_id: UUID,
            user: UserDB = Depends(require_dashboard_admin_access),
        ):
            return {"message": "Delete allowed"}
    """
    if not await check_dashboard_access(
        user_id=user.id,
        dashboard_id=dashboard_id,
        required_permission="admin",
        db=db,
    ):
        logger.warning(
            "Отказано в администрировании дашборда: user_id=%s, dashboard_id=%s",
            user.id,
            dashboard_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на администрирование этого дашборда",
        )
    return user


# --- Комбинированные зависимости ---

# Типизированные алиасы для удобства использования
CurrentUser = Annotated[UserDB, Depends(get_current_user_dependency)]
AdminUser = Annotated[UserDB, Depends(require_admin_role)]
EditorUser = Annotated[UserDB, Depends(require_editor_role)]
ViewerUser = Annotated[UserDB, Depends(require_viewer_role)]


async def get_dashboard_permissions(
    dashboard_id: UUID,
    user: UserDB = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db_dependency),
    access_repo: IAccessRepository = Depends(get_access_repository),
) -> dict[str, Any]:
    """Получает права доступа пользователя к дашборду.

    Args:
        dashboard_id: ID дашборда.
        user: Пользователь.
        db: Асинхронная сессия базы данных.
        access_repo: Репозиторий доступа.

    Returns:
        dict: Словарь с информацией о правах доступа.
    """
    permission = access_repo.check_access(
        user_id=user.id,
        dashboard_id=dashboard_id,
        db=db,
    )

    return {
        "user_id": user.id,
        "dashboard_id": dashboard_id,
        "permission": permission,
        "can_read": check_dashboard_access(
            user_id=user.id,
            dashboard_id=dashboard_id,
            required_permission="view",
            db=db,
        ),
        "can_write": check_dashboard_access(
            user_id=user.id,
            dashboard_id=dashboard_id,
            required_permission="edit",
            db=db,
        ),
        "can_admin": check_dashboard_access(
            user_id=user.id,
            dashboard_id=dashboard_id,
            required_permission="admin",
            db=db,
        ),
    }
