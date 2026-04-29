"""Фабрика приложения FastAPI.

Этот модуль предоставляет функцию create_app() для создания
экземпляра FastAPI с использованием factory pattern.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from mko_bi.api import routes
from mko_bi.config import get_config
from mko_bi.logging_config import setup_logging

# Настройка логирования
setup_logging()


def create_app() -> FastAPI:
    """Создает и конфигурирует приложение FastAPI.

    Создает экземпляр FastAPI с использованием factory pattern,
    настраивает middleware, обработчики ошибок и регистрирует маршруты.

    Returns:
        FastAPI: Сконфигурированное приложение FastAPI.
    """
    # Создаем приложение
    config = get_config()
    application = FastAPI(
        title=config.APP_NAME,
        description="BI Dashboard System API",
        version="1.0.0",
        debug=config.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Настройка CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Настройка GZip middleware
    application.add_middleware(
        GZipMiddleware,
        minimum_size=1000,
    )

    # Регистрация роутеров
    application.include_router(routes.auth.router)
    application.include_router(routes.users.router)
    application.include_router(routes.dashboards.router)
    application.include_router(routes.upload.router)
    application.include_router(routes.data.router)
    application.include_router(routes.filters.router)
    application.include_router(routes.processing_configs.router)
    application.include_router(routes.processing_logs.router)

    # Корневой эндпоинт
    @application.get("/", tags=["health"])
    async def root() -> dict[str, str | int]:
        """Корневой эндпоинт для проверки работы API."""
        return {
            "message": "BI Dashboard API",
            "status": "active",
            "version": "1.0.0",
        }

    @application.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Эндпоинт проверки здоровья приложения."""
        return {"status": "healthy"}

    # Обработчики исключений
    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Обработчик HTTP исключений."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "status_code": exc.status_code,
            },
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Обработчик ошибок валидации запросов."""
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
                "status_code": 422,
            },
        )

    @application.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Обработчик ошибок валидации Pydantic."""
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Pydantic validation error",
                "errors": str(exc),
                "status_code": 500,
            },
        )

    return application
