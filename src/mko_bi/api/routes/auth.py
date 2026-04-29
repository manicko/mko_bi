"""Маршруты аутентификации и регистрации.

Этот модуль предоставляет эндпоинты для:
- Регистрации новых пользователей
- Входа пользователей (аутентификация)
- Обновления JWT токенов

Все эндпоинты возвращают стандартизированные JSON ответы.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from mko_bi.api.deps import get_current_user_dependency, get_auth_service
from mko_bi.interfaces.service_interfaces import IAuthService
from mko_bi.models.auth import LoginRequest, RegisterRequest, Token, RefreshRequest
from mko_bi.models.user import UserRead

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Вход пользователя",
    description="Аутентифицирует пользователя по email и паролю, возвращает JWT токен.",
)
async def login(
    login_data: LoginRequest,
    auth_service: IAuthService = Depends(get_auth_service),
) -> Token:
    """Эндпоинт входа пользователя.

    Принимает email и пароль, проверяет их корректность и возвращает
    JWT токен доступа при успешной аутентификации.

    Args:
        login_data: Модель с email и паролем.
        auth_service: Сервис аутентификации.

    Returns:
        Token: Модель с access_token и token_type.

    Raises:
        HTTPException 401: Неверный email или пароль.
        HTTPException 422: Ошибка валидации данных.
    """
    logger.info("Попытка входа пользователя: %s", login_data.email)

    try:
        token_data = auth_service.login_user(
            login_data.email, login_data.password
        )
    except ValueError as e:
        logger.warning("Неудачная попытка входа: %s", login_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        logger.error("Ошибка создания токена для %s: %s", login_data.email, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания токена",
        ) from e

    logger.info("Пользователь успешно вошел: %s", login_data.email)
    return Token(access_token=token_data["access_token"], token_type="bearer")


@router.post(
    "/login/form",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Вход пользователя (форма)",
    description="Аутентификация через форму OAuth2.",
)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: IAuthService = Depends(get_auth_service),
) -> Token:
    """Эндпоинт входа через OAuth2 форму.

    Принимает данные из формы OAuth2 и возвращает JWT токен.

    Args:
        form_data: Данные формы OAuth2.
        auth_service: Сервис аутентификации.

    Returns:
        Token: Модель с access_token и token_type.
    """
    logger.info("Попытка входа через форму: %s", form_data.username)

    try:
        token_data = auth_service.login_user(
            form_data.username, form_data.password
        )
    except ValueError as e:
        logger.warning("Неудачная попытка входа через форму: %s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        logger.error("Ошибка создания токена для %s: %s", form_data.username, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания токена",
        ) from e

    logger.info("Пользователь успешно вошел через форму: %s", form_data.username)
    return Token(access_token=token_data["access_token"], token_type="bearer")


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
    description="Создает нового пользователя и возвращает JWT токен.",
)
async def register(
    register_data: RegisterRequest,
    auth_service: IAuthService = Depends(get_auth_service),
) -> Token:
    """Эндпоинт регистрации нового пользователя.

    Принимает email, пароль и роль, создает пользователя и возвращает
    JWT токен доступа.

    Args:
        register_data: Модель с данными для регистрации.
        auth_service: Сервис аутентификации.

    Returns:
        Token: Модель с access_token и token_type.

    Raises:
        HTTPException 400: Пользователь с таким email уже существует.
        HTTPException 422: Ошибка валидации данных.
    """
    logger.info("Попытка регистрации пользователя: %s", register_data.email)

    try:
        user = auth_service.register_user(
            email=register_data.email,
            password=register_data.password,
            role=register_data.role,
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

    try:
        access_token = auth_service.create_access_token(user.id, user.role)
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
    auth_service: IAuthService = Depends(get_auth_service),
) -> Token:
    """Эндпоинт обновления токена.

    Принимает refresh токен (в текущей реализации - тот же JWT),
    декодирует его и выдает новый токен доступа.

    Args:
        refresh_data: Модель с refresh токеном.
        auth_service: Сервис аутентификации.

    Returns:
        Token: Модель с новым access_token и token_type.

    Raises:
        HTTPException 401: Неверный или истекший токен.
        HTTPException 422: Ошибка валидации данных.
    """
    logger.info("Попытка обновления токена")

    payload = auth_service.verify_token(refresh_data.refresh_token)
    if payload is None:
        logger.warning("Неверный refresh токен")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    email = payload.get("email")
    role = payload.get("role")

    if user_id is None or email is None or role is None:
        logger.warning("В токене отсутствуют необходимые данные")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_data = auth_service.refresh_token(user_id, email, role)
    except ValueError as e:
        logger.warning("Пользователь не найден при обновлении токена: %s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        logger.error("Ошибка создания нового токена для user_id=%s: %s", user_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания токена",
        ) from e

    logger.info("Токен успешно обновлен для user_id=%s", user_id)
    return Token(access_token=token_data["access_token"], token_type="bearer")


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Получение данных текущего пользователя",
    description="Возвращает данные о текущем аутентифицированном пользователе.",
)
async def get_current_user_info(
    current_user: UserRead = Depends(get_current_user_dependency),
) -> UserRead:
    """Эндпоинт получения информации о текущем пользователе.

    Требует валидный JWT токен в заголовке Authorization.

    Args:
        current_user: Текущий аутентифицированный пользователь.

    Returns:
        UserRead: Модель пользователя без пароля.

    Raises:
        HTTPException 401: Неверный или отсутствующий токен.
    """
    logger.info("Запрос данных пользователя: %s", current_user.email)
    return current_user
