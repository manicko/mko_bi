"""Фабрика приложения FastAPI.

Этот модуль предоставляет функцию create_app() для создания
экземпляра FastAPI с использованием factory pattern.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from asgiref.wsgi import WsgiToAsgi
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from mkobi.api import routes
from mkobi.config import get_config
from mkobi.core.logging_config import setup_logging
from mkobi.db.starter import DatabaseStarter
from mkobi.dash_app import create_dash_app

# Настройка логирования
setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения."""
    starter = DatabaseStarter()
    try:
        await starter.startup()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    yield
    await starter.shutdown()


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
        title=config.app_name,
        description="BI Dashboard System API",
        version="1.0.0",
        debug=config.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Настройка CORS middleware
    logger.info(f"Configuring CORS with allowed origins: {config.cors_origins}")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
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
    application.include_router(routes.admin.router)

    # Создание и монтирование Dash приложения
    logger.info("Mounting Dash application at /dashboards")
    dash_app = create_dash_app(prefix="/dashboards/")
    asgi_dash = WsgiToAsgi(dash_app.server)
    application.mount("/dashboards", asgi_dash)

    # Настройка раздачи статических файлов React SPA (после всех API роутов)
    _setup_static_files(application)

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


def _setup_static_files(application: FastAPI) -> None:
    """Настраивает раздачу статических файлов React SPA.

    Монтирует статические файлы из frontend/dist и настраивает
    SPA fallback для всех не-API роутов.
    """
    import os

    static_dir = "frontend/dist"

    # Проверяем существование директории со сборкой React
    if os.path.isdir(static_dir):
        logger.info(f"Mounting static files from {static_dir}")
        application.mount(
            "/",
            StaticFiles(directory=static_dir, html=True),
            name="static",
        )
    else:
        logger.warning(
            f"Static directory '{static_dir}' not found. "
            "React SPA will not be served. Run 'cd frontend && npm run build' first."
        )

        # Fallback: SPA routing для разработки или если сборка не найдена
        @application.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str) -> Response:
            """SPA fallback - возвращает index.html для всех не-API роутов."""
            index_path = os.path.join(static_dir, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            return JSONResponse(
                status_code=404,
                content={"detail": "React SPA not built. Run 'cd frontend && npm run build'"},
            )
