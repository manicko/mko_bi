"""Маршруты аутентификации и регистрации.

Этот модуль предоставляет эндпоинты для:
- Регистрации новых пользователей
- Входа пользователей (аутентификация)
- Обновления JWT токенов

Все эндпоинты возвращают стандартизированные JSON ответы.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from mko_bi.api.deps import get_db
from mko_bi.core.security import create_access_token, decode_token
from mko_bi.models.auth import LoginRequest, RegisterRequest, Token, RefreshRequest
from mko_bi.models.user import UserRead
from mko_bi.services.auth_service import (
    authenticate_user,
    register_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


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
    import time

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


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Вход пользователя",
    description="Аутентифицирует пользователя по email и паролю, возвращает JWT токен.",
)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> Token:
    """Эндпоинт входа пользователя.

    Принимает email и пароль, проверяет их корректность и возвращает
    JWT токен доступа при успешной аутентификации.

    Args:
        login_data: Модель с email и паролем.
        db: Сессия базы данных.

    Returns:
        Token: Модель с access_token и token_type.

    Raises:
        HTTPException 401: Неверный email или пароль.
        HTTPException 429: Превышен лимит попыток входа.
        HTTPException 422: Ошибка валидации данных.
    """
    logger.info("Попытка входа пользователя: %s", login_data.email)

    # Проверка rate limiting
    if not _check_rate_limit(login_data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Превышен лимит попыток входа. Попробуйте позже.",
        )

    # Аутентификация
    user = authenticate_user(login_data.email, login_data.password, db)
    if user is None:
        logger.warning("Неудачная попытка входа: %s", login_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Создание токена
    try:
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
            }
        )
    except Exception as e:
        logger.error("Ошибка создания токена для %s: %s", login_data.email, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания токена",
        ) from e

    logger.info("Пользователь успешно вошел: %s", login_data.email)
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/login/form",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Вход пользователя (форма)",
    description="Аутентификация через форму OAuth2.",
)
async def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> Token:
    """Эндпоинт входа через OAuth2 форму.

    Принимает данные из формы OAuth2 и возвращает JWT токен.

    Args:
        form_data: Данные формы OAuth2.
        db: Сессия базы данных.

    Returns:
        Token: Модель с access_token и token_type.
    """
    logger.info("Попытка входа через форму: %s", form_data.username)

    # Проверка rate limiting
    if not _check_rate_limit(form_data.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Превышен лимит попыток входа. Попробуйте позже.",
        )

    # Аутентификация
    user = authenticate_user(form_data.username, form_data.password, db)
    if user is None:
        logger.warning("Неудачная попытка входа через форму: %s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Создание токена
    try:
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
            }
        )
    except Exception as e:
        logger.error("Ошибка создания токена для %s: %s", form_data.username, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания токена",
        ) from e

    logger.info("Пользователь успешно вошел через форму: %s", form_data.username)
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
    description="Создает нового пользователя и возвращает JWT токен.",
)
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db),
) -> Token:
    """Эндпоинт регистрации нового пользователя.

    Принимает email, пароль и роль, создает пользователя и возвращает
    JWT токен доступа.

    Args:
        register_data: Модель с данными для регистрации.
        db: Сессия базы данных.

    Returns:
        Token: Модель с access_token и token_type.

    Raises:
        HTTPException 400: Пользователь с таким email уже существует.
        HTTPException 422: Ошибка валидации данных.
    """
    logger.info("Попытка регистрации пользователя: %s", register_data.email)

    try:
        # Регистрация пользователя
        user = register_user(
            email=register_data.email,
            password=register_data.password,
            role=register_data.role,
            db=db,
        )
    except ValueError as e:
        logger.warning(
            "Ошибка валидации при регистрации %s: %s", register_data.email, e
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Ошибка регистрации пользователя %s: %s", register_data.email, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка регистрации пользователя",
        ) from e

    # Создание токена
    try:
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
            }
        )
    except Exception as e:
        logger.error(
            "Ошибка создания токена после регистрации %s: %s", register_data.email, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания токена",
        ) from e

    logger.info("Пользователь успешно зарегистрирован: %s", register_data.email)
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Обновление токена",
    description="Обновляет истекший JWT токен доступа.",
)
async def refresh(
    refresh_data: RefreshRequest,
    db: Session = Depends(get_db),
) -> Token:
    """Эндпоинт обновления токена.

    Принимает refresh токен (в текущей реализации - тот же JWT),
    декодирует его и выдает новый токен доступа.

    Args:
        refresh_data: Модель с refresh токеном.
        db: Сессия базы данных.

    Returns:
        Token: Модель с новым access_token и token_type.

    Raises:
        HTTPException 401: Неверный или истекший токен.
        HTTPException 422: Ошибка валидации данных.
    """
    logger.info("Попытка обновления токена")

    # Декодируем токен
    payload = decode_token(refresh_data.refresh_token)
    if payload is None:
        logger.warning("Неверный refresh токен")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем наличие user_id
    user_id = payload.get("user_id")
    email = payload.get("email")

    if user_id is None or email is None:
        logger.warning("В токене отсутствуют необходимые данные")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем, что пользователь существует
    from mko_bi.db.repositories.user_repo import UserRepository

    user = UserRepository.get(user_id, db)
    if user is None:
        logger.warning("Пользователь не найден при обновлении токена: %s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Создаем новый токен
    try:
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
            }
        )
    except Exception as e:
        logger.error("Ошибка создания нового токена для user_id=%s: %s", user_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания токена",
        ) from e

    logger.info("Токен успешно обновлен для user_id=%s", user_id)
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Получение данных текущего пользователя",
    description="Возвращает данные о текущем аутентифицированном пользователе.",
)
async def get_current_user_info(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(),  # Зависимость будет добавлена через require_role
) -> UserRead:
    """Эндпоинт получения информации о текущем пользователе.

    Требует валидный JWT токен в заголовке Authorization.

    Args:
        db: Сессия базы данных.
        current_user: Текущий аутентифицированный пользователь.

    Returns:
        UserRead: Модель пользователя без пароля.

    Raises:
        HTTPException 401: Неверный или отсутствующий токен.
    """
    logger.info("Запрос данных пользователя: %s", current_user.email)
    return current_user
