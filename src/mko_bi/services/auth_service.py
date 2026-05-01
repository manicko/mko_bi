"""Сервис аутентификации и регистрации пользователей.

Предоставляет бизнес-логику для регистрации, аутентификации и авторизации
пользователей в системе BI Dashboard. Использует классовый подход.
"""

import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from mko_bi.config import get_redis_client
from mko_bi.core.security import RateLimiter, create_access_token, hash_password, verify_password, decode_token
from mko_bi.db.repositories.user_repo import UserRepository
from mko_bi.db.session import get_session
from mko_bi.interfaces.service_interfaces import IAuthService
from mko_bi.models.user import UserRead, UserDB
from mko_bi.models.user_roles import UserRoleEnum

logger = logging.getLogger(__name__)

# Регулярное выражение для валидации email
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class AuthService(IAuthService):
    """Сервис аутентификации и регистрации пользователей.

    Реализует интерфейс IAuthService. Использует классовый подход
    для всех операций аутентификации и регистрации.
    """

    def __init__(self) -> None:
        self._rate_limiter = RateLimiter(get_redis_client())

    def _validate_role(self, role: str) -> None:
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
                "Недопустимая роль: %s. Допустимые роли: %s",
                role,
                [e.value for e in UserRoleEnum],
            )
            raise ValueError(
                f"Недопустимая роль: '{role}'. "
                f"Допустимые значения: {', '.join([e.value for e in UserRoleEnum])}"
            ) from err

    def _validate_email_format(self, email: str) -> str:
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

    def _check_email_uniqueness(self, email: str, db: Session) -> None:
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
        self, email: str, password: str, role: str, db: Session | None = None
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
        """
        logger.info("Starting user registration: email=%s, role=%s", email, role)

        self._validate_role(role)
        self._validate_email_format(email)

        if db is None:
            with get_session() as db:
                return self.register_user(email, password, role, db)

        try:
            with db.begin():
                self._check_email_uniqueness(email, db)
                password_hash = hash_password(password)
                logger.info("Password successfully hashed for user: %s", email)

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

            return UserRead.model_validate(user_obj)

        except Exception as e:
            logger.error("Error during user registration %s: %s", email, e)
            raise

    def authenticate_user(
        self, email: str, password: str, db: Session | None = None
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
        """
        logger.info("Attempting user authentication: %s", email)

        if db is None:
            with get_session() as db:
                return self.authenticate_user(email, password, db)

        user_obj = UserRepository.get_by_email(email, db)

        if user_obj is None:
            logger.warning("User not found during authentication: %s", email)
            return None

        if not verify_password(password, user_obj.password_hash):
            logger.warning("Invalid password for user: %s", email)
            return None

        logger.info("User successfully authenticated: %s", email)
        return UserDB.model_validate(user_obj)

    def login_user(
        self, email: str, password: str, db: Session | None = None
    ) -> dict[str, Any]:
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
        """
        logger.info("Attempting user login: %s", email)

        if not self._rate_limiter.check_rate_limit(f"rate_limit:{email}", 5, 60):
            raise ValueError("Превышен лимит попыток входа")

        user = self.authenticate_user(email, password, db)

        if user is None:
            logger.warning("Failed login attempt (неверный email или пароль): %s", email)
            raise ValueError("Неверный email или пароль")

        access_token = self.create_access_token(user.id, user.role)

        logger.info("User successfully logged in: %s", email)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
        }

    def refresh_token(
        self, user_id: Any, email: str, role: str, db: Session | None = None
    ) -> dict[str, Any]:
        """Обновляет JWT токен доступа.

        Создает новый JWT токен доступа на основе данных пользователя.

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
        """
        logger.info("Refreshing token for user_id: %s", user_id)

        access_token = self.create_access_token(user_id, role)

        logger.info("Token refreshed for user_id: %s", user_id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user_id,
            "email": email,
            "role": role,
        }

    def create_access_token(self, user_id: Any, role: Any) -> str:
        """Создает JWT токен доступа для пользователя.

        Args:
            user_id: ID пользователя.
            role: Роль пользователя.

        Returns:
            JWT токен доступа.
        """
        access_token = create_access_token(
            data={
                "user_id": user_id,
                "role": role,
            }
        )

        logger.info("Token created for user_id: %s", user_id)
        return access_token  # type: ignore[no-any-return]

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Проверяет JWT токен и возвращает данные пользователя.

        Args:
            token: JWT токен для проверки.

        Returns:
            Dict с данными из токена или None, если токен недействителен.
        """
        payload = decode_token(token)
        if payload is None:
            logger.warning("Invalid token during verification")
            return None

        logger.info("Token verified for user_id: %s", payload.get("user_id"))
        return payload  # type: ignore[no-any-return]
