"""Сервис аутентификации и регистрации пользователей.

Предоставляет бизнес-логику для регистрации, аутентификации и авторизации
пользователей в системе BI Dashboard.

Реализует интерфейс IAuthService для внедрения зависимостей.
"""

import logging
import re
import time

from mko_bi.db.repositories.user_repo import UserRepository
from mko_bi.interfaces.service_interfaces import IAuthService
from mko_bi.models.user import UserRead, UserDB
from mko_bi.models.user_roles import UserRoleEnum

logger = logging.getLogger(__name__)


# Допустимые роли берем из UserRoleEnum

# Регулярное выражение для валидации email
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Rate limiting storage (in-memory, для простоты)
# В production использовать Redis или аналог
_login_attempts: dict[str, list[float]] = {}


class AuthService(IAuthService):
    """Сервис аутентификации и регистрации пользователей.
    
    Реализует интерфейс IAuthService.
    """

    def authenticate_user(self, email: str, password: str) -> dict[str, any] | None:
        """Аутентифицирует пользователя по email и паролю.

        Ищет пользователя по email и проверяет соответствие пароля.

        Args:
            email: Email пользователя.
            password: Пароль в открытом виде.

        Returns:
            Dict с данными пользователя или None, если аутентификация не удалась.
        """
        logger.info("Attempting user authentication: %s", email)

        db = get_session().__enter__()
        local_session = True

        try:
            # Поиск пользователя по email
            user_obj = UserRepository.get_by_email(email, db)

            if user_obj is None:
                logger.warning("User not found during authentication: %s", email)
                return None

            # Проверка пароля
            if not verify_password(password, user_obj.password_hash):
                logger.warning("Invalid password for user: %s", email)
                return None

            logger.info("User successfully authenticated: %s", email)

            # Преобразование в Pydantic модель
            user = UserDB.model_validate(user_obj)
            return user.model_dump()

        except Exception as e:
            logger.error("Error during user authentication %s: %s", email, e)
            raise
        finally:
            if local_session:
                db.close()

    def create_access_token(self, user_id: int, role: UserRoleEnum) -> str:
        """Создает JWT токен доступа для пользователя.

        Args:
            user_id: ID пользователя.
            role: Роль пользователя.

        Returns:
            JWT токен доступа.
        """
        # Создание JWT токена
        access_token = create_access_token(
            data={
                "user_id": user_id,
                "role": role,
            }
        )

        logger.info("Token created for user_id: %s", user_id)
        return access_token

    def verify_token(self, token: str) -> dict[str, any] | None:
        """Проверяет JWT токен и возвращает данные пользователя.

        Args:
            token: JWT токен для проверки.

        Returns:
            Dict с данными из токена или None, если токен недействителен.
        """
        from mko_bi.core.security import decode_token
        
        payload = decode_token(token)
        if payload is None:
            logger.warning("Invalid token during verification")
            return None
        
        logger.info("Token verified for user_id: %s", payload.get("user_id"))
        return payload


# --- Старые функции для обратной совместимости ---

# Допустимые роли берем из UserRoleEnum

# Регулярное выражение для валидации email
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Rate limiting storage (in-memory, для простоты)
# В production использовать Redis или аналог
_login_attempts: dict[str, list[float]] = {}


def _check_rate_limit(email: str) -> bool:
    """Проверяет лимит попыток входа (rate limiting).

    Разрешает максимум 5 попыток входа в течение 60 секунд.

    Args:
        email: Email пользователя, пытающегося войти.

    Returns:
        bool: True, если попытка разрешена, False - если лимит превышен.
    """
    now = time.time()
    window = 60  # 60 секунд
    max_attempts = 5

    if email not in _login_attempts:
        _login_attempts[email] = []

    # Очищаем старые попытки
    _login_attempts[email] = [
        attempt_time
        for attempt_time in _login_attempts[email]
        if now - attempt_time < window
    ]

    if len(_login_attempts[email]) >= max_attempts:
        logger.warning("Превышен лимит попыток входа для email: %s", email)
        return False

    _login_attempts[email].append(now)
    return True


def _validate_role(role: str) -> None:
    """Проверяет, что роль является допустимой.

    Args:
        role: Роль пользователя для проверки.

    Raises:
        ValueError: Если роль не входит в список допустимых.
    """
    try:
        UserRoleEnum(role)
    except ValueError:
        logger.error(
            "Недопустимая роль: %s. Допустимые роли: %s",
            role,
            [e.value for e in UserRoleEnum],
        )
        raise ValueError(
            f"Недопустимая роль: '{role}'. "
            f"Допустимые значения: {', '.join([e.value for e in UserRoleEnum])}"
        )


def _validate_email_format(email: str) -> str:
    """Проверяет формат email с использованием регулярного выражения.

    Args:
        email: Email для проверки.

    Returns:
        str: Валидный email.

    Raises:
        ValueError: Если email имеет некорректный формат.
    """
    if not EMAIL_REGEX.match(email):
        logger.error("Некорректный формат email: %s", email)
        raise ValueError(f"Некорректный формат email: '{email}'")
    return email


def _check_email_uniqueness(email: str, db: Session) -> None:
    """Проверяет, что email не используется другим пользователем.

    Args:
        email: Email для проверки уникальности.
        db: Сессия базы данных.

    Raises:
        ValueError: Если пользователь с таким email уже существует.
    """
    existing_user = UserRepository.get_by_email(email, db)
    if existing_user is not None:
        logger.warning("Попытка регистрации с существующим email: %s", email)
        raise ValueError(f"Пользователь с email '{email}' уже существует")


def register_user(
    email: str, password: str, role: str, db: Session | None = None
) -> UserRead:
    """Регистрирует нового пользователя в системе.

    Выполняет валидацию email и роли, проверяет уникальность email,
    хеширует пароль и сохраняет пользователя в базе данных.
    Операция выполняется в транзакции: если любая операция завершается
    ошибкой, транзакция откатывается.

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
        >>> user = register_user("user@example.com", "secure_password", "viewer")
        >>> user.email
        'user@example.com'
        >>> user.role
        'viewer'
        >>> hasattr(user, 'password_hash')
        False
    """
    logger.info("Starting user registration: email=%s, role=%s", email, role)

    # Валидация роли
    _validate_role(role)

    # Валидация формата email
    _validate_email_format(email)

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        # Регистрация пользователя в транзакции
        with db.begin():
            # Проверка уникальности email
            _check_email_uniqueness(email, db)

            # Хеширование пароля
            password_hash = hash_password(password)
            logger.info("Password successfully hashed for user: %s", email)

            # Создание пользователя
            user_obj = UserRepository.create(
                db=db,
                email=email,
                password_hash=password_hash,
                role=role,
            )

            logger.info(
                "User successfully registered: id=%s, email=%s, role=%s",
                user_obj.id,
                email,
                role,
            )

        # Преобразование в Pydantic модель (без password_hash)
        return UserRead.model_validate(user_obj)

    except Exception as e:
        logger.error("Error during user registration %s: %s", email, e)
        raise
    finally:
        if local_session:
            db.close()


def authenticate_user(
    email: str, password: str, db: Session | None = None
) -> UserDB | None:
    """Аутентифицирует пользователя по email и паролю.

    Ищет пользователя по email и проверяет соответствие пароля.

    Args:
        email: Email пользователя.
        password: Пароль в открытом виде.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        UserDB | None: Модель пользователя с хешем пароля, если аутентификация
        успешна, иначе None.

    Example:
        >>> user = authenticate_user("user@example.com", "correct_password")
        >>> user is not None
        True
        >>> user = authenticate_user("user@example.com", "wrong_password")
        >>> user is None
        True
    """
    logger.info("Attempting user authentication: %s", email)

    # Если сессия не передана, создаем новую
    local_session = False
    if db is None:
        db = get_session().__enter__()
        local_session = True

    try:
        # Поиск пользователя по email
        user_obj = UserRepository.get_by_email(email, db)

        if user_obj is None:
            logger.warning("User not found during authentication: %s", email)
            return None

        # Проверка пароля
        if not verify_password(password, user_obj.password_hash):
            logger.warning("Invalid password for user: %s", email)
            return None

        logger.info("User successfully authenticated: %s", email)

        # Преобразование в Pydantic модель
        return UserDB.model_validate(user_obj)

    except Exception as e:
        logger.error("Error during user authentication %s: %s", email, e)
        raise
    finally:
        if local_session:
            db.close()


def login_user(email: str, password: str, db: Session | None = None) -> dict:
    """Выполняет вход пользователя и возвращает JWT токен.

    Аутентифицирует пользователя и при успехе создает JWT токен доступа.

    Args:
        email: Email пользователя.
        password: Пароль в открытом виде.
        db: Опциональная сессия базы данных. Если не передана, создается новая.

    Returns:
        dict: Словарь с ключами:
            - access_token: JWT токен доступа
            - token_type: Тип токена (обычно "bearer")
            - user_id: ID пользователя
            - email: Email пользователя
            - role: Роль пользователя

    Raises:
        ValueError: Если аутентификация не удалась.

    Example:
        >>> result = login_user("user@example.com", "correct_password")
        >>> "access_token" in result
        True
        >>> result["token_type"]
        'bearer'
    """
    logger.info("Attempting user login: %s", email)

    # Аутентификация
    user = authenticate_user(email, password, db)

    if user is None:
        logger.warning("Failed login attempt (неверный email или пароль): %s", email)
        raise ValueError("Неверный email или пароль")

    # Создание JWT токена
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
        }
    )

    logger.info("User successfully logged in: %s", email)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
    }


def refresh_token(user_id: int, email: str, role: str, db: Session | None = None) -> dict:
    """Обновляет JWT токен доступа.
    
    Создает новый JWT токен доступа на основе данных пользователя.
    В текущей реализации используется тот же механизм JWT,
    что и для создания токена.
    
    Args:
        user_id: ID пользователя.
        email: Email пользователя.
        role: Роль пользователя.
        db: Опциональная сессия базы данных (не используется, но сохранен для совместимости).
    
    Returns:
        dict: Словарь с ключами:
            - access_token: JWT токен доступа
            - token_type: Тип токена (обычно "bearer")
            - user_id: ID пользователя
            - email: Email пользователя
            - role: Роль пользователя
    
    Example:
        >>> token_data = refresh_token(1, "user@example.com", "viewer")
        >>> "access_token" in token_data
        True
    """
    logger.info("Refreshing token for user_id: %s", user_id)
    
    access_token = create_access_token(
        data={
            "user_id": user_id,
            "email": email,
            "role": role,
        }
    )
    
    logger.info("Token refreshed for user_id: %s", user_id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id,
        "email": email,
        "role": role,
    }
