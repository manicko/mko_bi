"""Сервис управления пользователями.

Предоставляет бизнес-логику для CRUD операций с пользователями.
Все операции выполняются через UserRepository с валидацией,
проверкой прав и логированием.

Реализует интерфейс IUserService для внедрения зависимостей.
"""

# mypy: ignore-errors

import logging
from typing import Any
from uuid import UUID

from mko_bi.core.security import hash_password
from mko_bi.db.models import user as user_model
from mko_bi.db.repositories.user_repo import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from mko_bi.db.session import get_session
from mko_bi.interfaces import IUserService
from mko_bi.models.user import UserRead
from mko_bi.models.user_roles import UserRoleEnum

logger = logging.getLogger(__name__)


# Допустимые роли в системе (берем из UserRoleEnum)
def _validate_role(role: str) -> None:
    """Проверяет, что роль является допустимой.

    Args:
        role: Роль пользователя для проверки.

    Raises:
        ValueError: Если роль не входит в список допустиых.
    """
    try:
        UserRoleEnum(role)
    except ValueError as err:
        logger.error(
            "Недопустимая роль: '%s'. Допустимые роли: %s",
            role,
            sorted([e.value for e in UserRoleEnum]),
        )
        raise ValueError(
            f"Недопустимая роль: '{role}'. "
            f"Допустимые значения: {', '.join(sorted([e.value for e in UserRoleEnum]))}"
        ) from err


async def _validate_user_exists(user_id: UUID, db: AsyncSession) -> user_model.User | None:
    """Проверяет существование пользователя и возвращает его модель.

    Args:
        user_id: Идентификатор пользователя. 
        db: Асинхронная сессия базы данных. 

    Returns:
        Модель пользователя или None, если не найден. 
    """
    user_obj = await UserRepository.get(user_id, db)
    if user_obj is None:
        logger.warning("Пользователь не найден: id=%s", user_id)
    return user_obj


async def _check_admin_deletion_allowed(db: AsyncSession) -> None:
    """Проверяет, разрешено ли удаление администратора.

    Запрещает удалять администраторов, если в системе есть другие пользователи. 
    Это защищает от ситуации, когда все администраторы удалены и доступ 
    к управлению пользователями будет потерян. 

    Args:
        db: Асинхронная сессия базы данных. 

    Raises:
        ValueError: Если в системе есть другие пользователи помимо удаляемого. 
    """
    all_users = await UserRepository.get_all(db)
    admin_users = [u for u in all_users if u.role == "admin"]
    if len(all_users) > 1 and len(admin_users) <= 1:
        logger.error(
            "Запрещено удаление последнего администратора. "
            "Всего пользователей: %s, администраторов: %s",
            len(all_users),
            len(admin_users),
        )
        raise ValueError(
            "Нельзя удалить администратора, если в системе есть другие пользователи. "
            "Сначала назначьте другого администратора."
        )


class UserService(IUserService):
    """Сервис управления пользователями. 
    
    Реализует интерфейс IUserService для работы с пользователями. 
    """

    async def get_user_by_id(self, user_id: UUID) -> dict[str, Any] | None:
        """Получить пользователя по ID. 

        Args:
            user_id: Идентификатор пользователя. 

        Returns:
            Данные пользователя или None, если не найден. 
        """
        async with get_session() as db:
            user_obj = await UserRepository.get(user_id, db)
            if user_obj:
                logger.info("Пользователь получен: id=%s", user_id)
                return UserRead.model_validate(user_obj).model_dump()
            else:
                logger.warning("Пользователь не найден: id=%s", user_id)
                return None

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Получить пользователя по email. 

        Args:
            email: Email пользователя для поиска. 

        Returns:
            Данные пользователя или None, если не найден. 
        """
        async with get_session() as db:
            user_obj = await UserRepository.get_by_email(email, db)
            if user_obj:
                logger.info("Пользователь найден по email: %s", email)
                return UserRead.model_validate(user_obj).model_dump()
            else:
                logger.warning("Пользователь не найден по email: %s", email)
                return None

    async def create_user(self, email: str, password: str, role: UserRoleEnum) -> dict[str, Any]:
        """Создать нового пользователя. 

        Выполняет валидацию email и роли, проверяет уникальность email, 
        хеширует пароль и сохраняет пользователя в базе данных. 

        Args:
            email: Email пользователя. Должен быть валидным и уникальным. 
            password: Пароль пользователя. Будет захеширован перед сохранением. 
            role: Роль пользователя. 

        Returns:
            Данные созданного пользователя. 

        Raises:
            ValueError: Если email или роль некорректны, либо email уже занят. 
            SQLAlchemyError: При ошибке базы данных. 
        """
        logger.info("Начало создания пользователя: email=%s, role=%s", email, role)

        # Валидация роли
        _validate_role(role)

        async with get_session() as db:
            # Проверка уникальности email
            existing_user = await UserRepository.get_by_email(email, db)
            if existing_user is not None:
                logger.warning(
                    "Попытка создания пользователя с существующим email: %s", email
                )
                raise ValueError(f"Пользователь с email '{email}' уже существует")

            # Хеширование пароля
            password_hash = hash_password(password)
            logger.info("Пароль успешно захеширован для пользователя: %s", email)

            # Создание пользователя через репозиторий
            user_obj = await UserRepository.create(
                db=db,
                email=email,
                password_hash=password_hash,
                role=role,
            )

            logger.info(
                "Пользователь успешно создан: id=%s, email=%s, role=%s",
                user_obj.id,
                email,
                role,
            )

            # Преобразование в Pydantic модель (без password_hash)
            return UserRead.model_validate(user_obj).model_dump()

    async def update_user_role(self, user_id: UUID, role: UserRoleEnum) -> UserRead | None:
        """Обновить роль пользователя. 

        Проверяет валидность новой роли и существование пользователя, 
        затем обновляет роль в базе данных. 

        Args:
            user_id: Идентификатор пользователя. 
            role: Новая роль пользователя. 

        Returns:
            True, если обновление успешно, False - если пользователь не найден. 

        Raises:
            ValueError: Если роль недопустима. 
            SQLAlchemyError: При ошибке базы данных. 
        """
        logger.info("Обновление роли пользователя: id=%s, new_role=%s", user_id, role)

        # Валидация роли
        _validate_role(role)

        async with get_session() as db:
            # Проверка существования пользователя
            user_obj = await _validate_user_exists(user_id, db)
            if user_obj is None:
                return False

            # Обновление роли через репозиторий
            updated = await UserRepository.update(db=db, user_id=user_id, role=role)

            if updated:
                logger.info(
                    "Роль пользователя обновлена: id=%s, old_role=%s, new_role=%s",
                    user_id,
                    user_obj.role,
                    role,
                )
            else:
                logger.warning("Не удалось обновить роль пользователя: id=%s", user_id)

            return updated is not None

    async def delete_user(self, user_id: UUID) -> bool:
        """Удалить пользователя из системы. 

        Проверяет существование пользователя и запрещает удаление 
        администраторов, если в системе есть другие пользователи. 
        При удалении также очищаются все права доступа пользователя. 

        Args:
            user_id: Идентификатор пользователя для удаления. 

        Returns:
            True, если удаление успешно, False - если пользователь не найден. 

        Raises:
            ValueError: Если попытка удалить администратора при наличии других пользователей. 
            SQLAlchemyError: При ошибке базы данных. 
        """
        logger.info("Удаление пользователя: id=%s", user_id)

        async with get_session() as db:
            # Проверка существования пользователя
            user_obj = await _validate_user_exists(user_id, db)
            if user_obj is None:
                return False

            # Проверка запрета удаления администраторов
            if user_obj.role == "admin":
                await _check_admin_deletion_allowed(db)

            # Удаление через репозиторий
            result = await UserRepository.delete(user_id, db)

            if result:
                logger.info(
                    "Пользователь успешно удален: id=%s, email=%s", user_id, user_obj.email
                )
            else:
                logger.warning("Не удалось удалить пользователя: id=%s", user_id)

            return result

    async def get_all_users(self) -> list[UserRead]:
        """Получить список всех пользователей в системе. 

        Returns:
            Список всех пользователей. 

        Raises:
            SQLAlchemyError: При ошибке базы данных. 
        """
        logger.info("Получение списка всех пользователей")

        async with get_session() as db:
            users = await UserRepository.get_all(db)
            logger.info("Получено пользователей: %s", len(users))
        return [UserRead.model_validate(user).model_dump() for user in users]
