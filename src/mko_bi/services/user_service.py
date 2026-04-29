"""Сервис управления пользователями.

Предоставляет бизнес-логику для CRUD операций с пользователями.
Все операции выполняются через UserRepository с валидацией,
проверкой прав и логированием.

Реализует интерфейс IUserService для внедрения зависимостей.
"""

import logging
from typing import Any
from uuid import UUID

from mko_bi.core.security import hash_password
from mko_bi.db.models import user as user_model
from mko_bi.db.repositories.user_repo import UserRepository
from sqlalchemy.orm import Session
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
        ValueError: Если роль не входит в список допустимых.
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


def _validate_user_exists(user_id: int, db: Session) -> user_model.User | None:
    """Проверяет существование пользователя и возвращает его модель.

    Args:
        user_id: Идентификатор пользователя.
        db: Сессия базы данных.

    Returns:
        Модель пользователя или None, если не найден.
    """
    user_obj = UserRepository.get(user_id, db)
    if user_obj is None:
        logger.warning("Пользователь не найден: id=%s", user_id)
    return user_obj


def _check_admin_deletion_allowed(db: Session) -> None:
    """Проверяет, разрешено ли удаление администратора.

    Запрещает удалять администраторов, если в системе есть другие пользователи.
    Это защищает от ситуации, когда все администраторы удалены и доступ
    к управлению пользователями будет потерян.

    Args:
        db: Сессия базы данных.

    Raises:
        ValueError: Если в системе есть другие пользователи помимо удаляемого.
    """
    all_users = UserRepository.get_all(db)
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

    def get_user_by_id(self, user_id: UUID) -> dict[str, Any] | None:
        """Получить пользователя по ID.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Данные пользователя или None, если не найден.
        """
        db = get_session().__enter__()
        try:
            user_obj = UserRepository.get(user_id, db)
            if user_obj:
                logger.info("Пользователь получен: id=%s", user_id)
                return UserRead.model_validate(user_obj).model_dump()
            else:
                logger.warning("Пользователь не найден: id=%s", user_id)
                return None
        except Exception as e:
            logger.error("Ошибка при получении пользователя id=%s: %s", user_id, e)
            raise
        finally:
            db.close()

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Получить пользователя по email.

        Args:
            email: Email пользователя для поиска.

        Returns:
            Данные пользователя или None, если не найден.
        """
        db = get_session().__enter__()
        try:
            user_obj = UserRepository.get_by_email(email, db)
            if user_obj:
                logger.info("Пользователь найден по email: %s", email)
                return UserRead.model_validate(user_obj).model_dump()
            else:
                logger.warning("Пользователь не найден по email: %s", email)
                return None
        except Exception as e:
            logger.error("Ошибка при получении пользователя email=%s: %s", email, e)
            raise
        finally:
            db.close()

    def create_user(self, email: str, password: str, role: UserRoleEnum) -> dict[str, Any]:
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

        db = get_session().__enter__()
        local_session = True
        try:
            # Проверка уникальности email
            existing_user = UserRepository.get_by_email(email, db)
            if existing_user is not None:
                logger.warning(
                    "Попытка создания пользователя с существующим email: %s", email
                )
                raise ValueError(f"Пользователь с email '{email}' уже существует")

            # Хеширование пароля
            password_hash = hash_password(password)
            logger.info("Пароль успешно захеширован для пользователя: %s", email)

            # Создание пользователя через репозиторий
            user_obj = UserRepository.create(
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

        except ValueError:
            # Валидационные ошибки не требуют отката (транзакция еще не начата)
            raise
        except Exception as e:
            if local_session:
                db.rollback()
            logger.error("Ошибка при создании пользователя %s: %s", email, e)
            raise
        finally:
            if local_session:
                db.close()

    def update_user_role(self, user_id: UUID, role: UserRoleEnum) -> bool:
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

        db = get_session().__enter__()
        local_session = True
        try:
            # Проверка существования пользователя
            user_obj = UserRepository.get(user_id, db)
            if user_obj is None:
                logger.warning("Пользователь не найден: id=%s", user_id)
                return False

            # Обновление роли через репозиторий
            updated = UserRepository.update(db=db, user_id=user_id, role=role)

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

        except ValueError:
            raise
        except Exception as e:
            if local_session:
                db.rollback()
            logger.error("Ошибка при обновлении роли пользователя id=%s: %s", user_id, e)
            raise
        finally:
            if local_session:
                db.close()

    def delete_user(self, user_id: UUID) -> bool:
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

        db = get_session().__enter__()
        local_session = True
        try:
            # Проверка существования пользователя
            user_obj = UserRepository.get(user_id, db)
            if user_obj is None:
                logger.warning("Пользователь не найден: id=%s", user_id)
                return False

            # Проверка запрета удаления администраторов
            if user_obj.role == "admin":
                _check_admin_deletion_allowed(db)

            # Удаление через репозиторий
            result = UserRepository.delete(user_id, db)

            if result:
                logger.info(
                    "Пользователь успешно удален: id=%s, email=%s", user_id, user_obj.email
                )
            else:
                logger.warning("Не удалось удалить пользователя: id=%s", user_id)

            return result

        except ValueError:
            raise
        except Exception as e:
            if local_session:
                db.rollback()
            logger.error("Ошибка при удалении пользователя id=%s: %s", user_id, e)
            raise
        finally:
            if local_session:
                db.close()

    def list_users(self) -> list[dict[str, Any]]:
        """Получить список всех пользователей в системе.

        Returns:
            Список всех пользователей.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        logger.info("Получение списка всех пользователей")

        db = get_session().__enter__()
        local_session = True
        try:
            users = UserRepository.get_all(db)
            logger.info("Получено пользователей: %s", len(users))
            return [UserRead.model_validate(user).model_dump() for user in users]
        except Exception as e:
            logger.error("Ошибка при получении списка пользователей: %s", e)
            raise
        finally:
            if local_session:
                db.close()


# Сохраняем старые функции для обратной совместимости
def create_user(
    email: str, password: str, role: str, db: Session | None = None
) -> UserRead:
    """Создает нового пользователя в системе (старая функция для обратной совместимости).

    Выполняет валидацию email и роли, проверяет уникальность email,
    хеширует пароль и сохраняет пользователя в базе данных.

    Args:
        email: Email пользователя. Должен быть валидным и уникальным.
        password: Пароль пользователя. Будет захеширован перед сохранением.
        role: Роль пользователя. Допустимые значения: 'admin', 'editor', 'viewer'.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        UserRead: Модель пользователя без пароля (с id и created_at).

    Raises:
        ValueError: Если email или роль некорректны, либо email уже занят.
        SQLAlchemyError: При ошибке базы данных.

    Example:
        >>> user = create_user("user@example.com", "secure_password", "viewer")
        >>> user.email
        'user@example.com'
        >>> user.role
        'viewer'
    """
    logger.info("Начало создания пользователя: email=%s, role=%s", email, role)

    # Валидация роли
    _validate_role(role)

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        # Проверка уникальности email
        existing_user = UserRepository.get_by_email(email, db)
        if existing_user is not None:
            logger.warning(
                "Попытка создания пользователя с существующим email: %s", email
            )
            raise ValueError(f"Пользователь с email '{email}' уже существует")

        # Хеширование пароля
        password_hash = hash_password(password)
        logger.info("Пароль успешно захеширован для пользователя: %s", email)

        # Создание пользователя через репозиторий
        user_obj = UserRepository.create(
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
        return UserRead.model_validate(user_obj)

    except ValueError:
        # Валидационные ошибки не требуют отката (транзакция еще не начата)
        raise
    except Exception as e:
        if local_session:
            db.rollback()
        logger.error("Ошибка при создании пользователя %s: %s", email, e)
        raise
    finally:
        if local_session:
            db.close()


def get_user_by_email(email: str, db: Session | None = None) -> user_model.User | None:
    """Получает пользователя по email (старая функция для обратной совместимости).

    Args:
        email: Email пользователя для поиска.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        Модель пользователя из базы данных или None, если не найден.

    Raises:
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info("Поиск пользователя по email: %s", email)

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        user_obj = UserRepository.get_by_email(email, db)
        if user_obj:
            logger.info("Пользователь найден по email: %s", email)
        else:
            logger.warning("Пользователь не найден по email: %s", email)
        return user_obj
    except Exception as e:
        logger.error("Ошибка при получении пользователя email=%s: %s", email, e)
        raise
    finally:
        if local_session:
            db.close()


def get_user_by_id(user_id: int, db: Session | None = None) -> user_model.User | None:
    """Получает пользователя по ID (старая функция для обратной совместимости).

    Args:
        user_id: Идентификатор пользователя.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        Модель пользователя из базы данных или None, если не найден.

    Raises:
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info("Получение пользователя по id: %s", user_id)

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        user_obj = UserRepository.get(user_id, db)
        if user_obj:
            logger.info("Пользователь получен: id=%s", user_id)
        else:
            logger.warning("Пользователь не найден: id=%s", user_id)
        return user_obj
    except Exception as e:
        logger.error("Ошибка при получении пользователя id=%s: %s", user_id, e)
        raise
    finally:
        if local_session:
            db.close()


def update_user_role(
    user_id: int, new_role: str, db: Session | None = None
) -> user_model.User | None:
    """Обновляет роль пользователя (старая функция для обратной совместимости).

    Проверяет валидность новой роли и существование пользователя,
    затем обновляет роль в базе данных.

    Args:
        user_id: Идентификатор пользователя.
        new_role: Новая роль пользователя.
            Допустимые значения: 'admin', 'editor', 'viewer'.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        Обновленная модель пользователя или None, если пользователь не найден.

    Raises:
        ValueError: Если роль недопустима.
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info("Обновление роли пользователя: id=%s, new_role=%s", user_id, new_role)

    # Валидация роли
    _validate_role(new_role)

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        # Проверка существования пользователя
        user_obj = _validate_user_exists(user_id, db)
        if user_obj is None:
            return None

        # Обновление роли через репозиторий
        updated = UserRepository.update(db=db, user_id=user_id, role=new_role)

        if updated:
            logger.info(
                "Роль пользователя обновлена: id=%s, old_role=%s, new_role=%s",
                user_id,
                user_obj.role,
                new_role,
            )
        else:
            logger.warning("Не удалось обновить роль пользователя: id=%s", user_id)

        return updated

    except ValueError:
        raise
    except Exception as e:
        if local_session:
            db.rollback()
        logger.error("Ошибка при обновлении роли пользователя id=%s: %s", user_id, e)
        raise
    finally:
        if local_session:
            db.close()


def delete_user(user_id: int, db: Session | None = None) -> bool:
    """Удаляет пользователя из системы (старая функция для обратной совместимости).

    Проверяет существование пользователя и запрещает удаление
    администраторов, если в системе есть другие пользователи.
    При удалении также очищаются все права доступа пользователя.

    Args:
        user_id: Идентификатор пользователя для удаления.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        True, если удаление успешно, False - если пользователь не найден.

    Raises:
        ValueError: Если попытка удалить администратора при наличии других пользователей.
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info("Удаление пользователя: id=%s", user_id)

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        # Проверка существования пользователя
        user_obj = _validate_user_exists(user_id, db)
        if user_obj is None:
            return False

        # Проверка запрета удаления администраторов
        if user_obj.role == "admin":
            _check_admin_deletion_allowed(db)

        # Удаление через репозиторий
        result = UserRepository.delete(user_id, db)

        if result:
            logger.info(
                "Пользователь успешно удален: id=%s, email=%s", user_id, user_obj.email
            )
        else:
            logger.warning("Не удалось удалить пользователя: id=%s", user_id)

        return result

    except ValueError:
        raise
    except Exception as e:
        if local_session:
            db.rollback()
        logger.error("Ошибка при удалении пользователя id=%s: %s", user_id, e)
        raise
    finally:
        if local_session:
            db.close()


def get_all_users(db: Session | None = None) -> list[user_model.User]:
    """Получает список всех пользователей в системе (старая функция для обратной совместимости).

    Args:
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        Список всех моделей пользователей.

    Raises:
        SQLAlchemyError: При ошибке базы данных.
    """
    logger.info("Получение списка всех пользователей")

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        users = UserRepository.get_all(db)
        logger.info("Получено пользователей: %s", len(users))
        return users
    except Exception as e:
        logger.error("Ошибка при получении списка пользователей: %s", e)
        raise
    finally:
        if local_session:
            db.close()


def register_user(
    email: str, password: str, role: str, db: Session | None = None
) -> UserRead:
    """Регистрирует нового пользователя (алиас для create_user).

    Args:
        email: Email пользователя.
        password: Пароль пользователя.
        role: Роль пользователя.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        UserRead: Модель созданного пользователя.

    Raises:
        ValueError: Если email или роль некорректны, либо email уже занят.
        SQLAlchemyError: При ошибке базы данных.
    """
    return create_user(email, password, role, db)
