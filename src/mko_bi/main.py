"""Главный файл приложения FastAPI.

Создает и конфигурирует приложение FastAPI, подключает маршруты,
настройки CORS, документацию и обработчики ошибок.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mko_bi.api import routes
from mko_bi.config import config
from mko_bi.logging_config import setup_logging

# Настройка логирования
setup_logging()


def create_application() -> FastAPI:
    """Создает и конфигурирует приложение FastAPI.

    Returns:
        FastAPI: Сконфигурированное приложение.
    """
    application = FastAPI(
        title=config.APP_NAME,
        description="BI Dashboard System API",
        version="1.0.8",
        debug=config.DEBUG,
    )

    # Настройка CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключение маршрутов
    application.include_router(routes.auth.router)
    application.include_router(routes.users.router)
    application.include_router(routes.dashboards.router)

    @application.get("/", tags=["health"])
    async def root():
        """Корневой эндпоинт для проверки работы API."""
        return {
            "message": "BI Dashboard API",
            "status": "active",
            "version": "1.0.8",
        }

    @application.get("/health", tags=["health"])
    async def health_check():
        """Эндпоинт проверки здоровья приложения."""
        return {"status": "healthy"}

    return application


# Создаем экземпляр приложения
app = create_application()
