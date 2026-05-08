"""Factory for FastAPI application.

This module provides the create_app() function to create
a FastAPI instance using the factory pattern.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from mkobi.api import routes
from mkobi.config import get_config
from mkobi.core.logging_config import setup_logging
from mkobi.db.session import get_session
from mkobi.db.starter import DatabaseStarter, DatabaseStarterConfig, DatabaseNotFoundError, SchemaNotFoundError
from mkobi.models.enums import EnvironmentEnum

# Get configuration and setup logging
config = get_config()
setup_logging(
    log_level=config.log_level,
    log_file=config.log_file,
    json_logging=config.logging.json_logging,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager.
    
    Handles startup and shutdown events with proper error handling.
    Logs all errors with context and ensures clean shutdown on startup failure.
    """
    config = get_config()
    starter_config = DatabaseStarterConfig(
        env=config.environment,
        main_database_url=config.DATABASE_URL,
        test_database_url=config.TEST_DATABASE_URL,
        auto_migrate=config.auto_migrate,
        migration_script_path=config.migration_script_path,
        alembic_ini_path=config.alembic_ini_path,
        recreate_test_db=config.recreate_test_db,
    )
    starter = DatabaseStarter(starter_config)
    try:
        logger.info("Initializing application...")
        await starter.startup()
        logger.info("Application initialized successfully")
        yield
    except DatabaseNotFoundError as e:
        logger.error("Database not found: %s", e)
        raise
    except SchemaNotFoundError as e:
        logger.error("Database schema not initialized: %s", e)
        raise
    except Exception as e:
        logger.error("Failed to initialize application: %s", e, exc_info=True)
        raise
    finally:
        logger.info("Shutting down application...")
        await starter.shutdown()


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application.

    Creates a FastAPI instance using the factory pattern,
    configures middleware, error handlers, and registers routes.

    Returns:
        FastAPI: Configured FastAPI application.
    """
    # Create application
    config = get_config()

    # Validate JWT secret key is configured
    if not config.jwt.secret_key:
        logger.error("JWT secret key is not configured. Set JWT__SECRET_KEY environment variable.")
        raise ValueError("JWT_SECRET_KEY must be set")

    # Validate CORS configuration for production
    if config.environment == EnvironmentEnum.PRODUCTION:
        if not config.cors_origins:
            logger.error("CORS origins must be set in production environment")
            raise ValueError("CORS origins must be configured for production")
        if "*" in config.cors_origins:
            logger.warning("CORS is configured to allow all origins (*) in production")

    application = FastAPI(
        title=config.app_name,
        description="BI Dashboard System API",
        version="1.0.0",
        debug=config.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    logger.info("Configuring CORS with allowed origins: %s", config.cors_origins)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Configure GZip middleware
    application.add_middleware(
        GZipMiddleware,
        minimum_size=1000,
    )

    # Register routers with /api/v1 prefix
    application.include_router(routes.auth.router, prefix="/api/v1")
    application.include_router(routes.users.router, prefix="/api/v1")
    application.include_router(routes.dashboards.router, prefix="/api/v1")
    application.include_router(routes.layouts.router, prefix="/api/v1")
    application.include_router(routes.upload.router, prefix="/api/v1")
    application.include_router(routes.data.router, prefix="/api/v1")
    application.include_router(routes.filters.router, prefix="/api/v1/filters")
    application.include_router(routes.processing_configs.router, prefix="/api/v1")
    application.include_router(routes.processing_logs.router, prefix="/api/v1")
    application.include_router(routes.admin.router, prefix="/api/v1")

    # Setup static files for React SPA (after all API routes)
    _setup_static_files(application)

    # Root endpoint
    @application.get("/", tags=["health"])
    async def root() -> dict[str, str | int]:
        """Root endpoint for API health check."""
        return {
            "message": "BI Dashboard API",
            "status": "active",
            "version": "1.0.0",
        }

    @application.get("/health", tags=["health"])
    async def health_check() -> Response:
        """Application health check endpoint.
        
        Verifies database connectivity by executing a simple query.
        Returns 503 if database is not accessible.
        """
        try:
            # Quick DB connectivity check
            async with get_session() as db:
                await db.execute(text("SELECT 1"))
            return JSONResponse(
                content={"status": "healthy", "database": "connected"}
            )
        except Exception as e:
            logger.error("Health check failed: %s", e)
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "database": "disconnected"},
            )

    @application.get("/health/detailed", tags=["health"])
    async def detailed_health_check() -> dict[str, Any]:
        """Detailed health check with component status.
        
        Checks database connectivity and returns detailed status information.
        This endpoint is intended for admin use and monitoring systems.
        """
        health_status: dict[str, Any] = {
            "status": "healthy",
            "components": {},
        }
        
        components: dict[str, Any] = {}
        
        # Check database connectivity
        try:
            async with get_session() as db:
                await db.execute(text("SELECT 1"))
            components["database"] = {
                "status": "connected",
                "type": "postgresql",
            }
        except Exception as e:
            logger.error("Database health check failed: %s", e)
            health_status["status"] = "unhealthy"
            components["database"] = {
                "status": "disconnected",
                "error": str(e),
            }
        
        # Check if static files are mounted
        import os
        components["static_files"] = {
            "status": "available" if os.path.isdir("frontend/dist") else "unavailable",
            "path": "frontend/dist",
        }
        
        health_status["components"] = components
        return health_status

    # Exception handlers
    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handler for HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "status_code": exc.status_code,
            },
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handler for request validation errors."""
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
                "status_code": 422,
            },
        )

    @application.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Handler for Pydantic validation errors."""
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
    """Sets up static file serving for React SPA.

    Mounts static files from frontend/dist and configures
    SPA fallback for all non-API routes.
    """
    import os

    static_dir = "frontend/dist"

    # Check if React build directory exists
    if os.path.isdir(static_dir):
        logger.info("Mounting static files from %s", static_dir)
        application.mount(
            "/",
            StaticFiles(directory=static_dir, html=True),
            name="static",
        )
    else:
        logger.warning(
            "Static directory '%s' not found. "
            "React SPA will not be served. Run 'cd frontend && npm run build' first.",
            static_dir,
        )

        # Fallback: SPA routing for development or if build not found
        @application.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str) -> Response:
            """SPA fallback - returns index.html for all non-API routes."""
            index_path = os.path.join(static_dir, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "React SPA not built. Run 'cd frontend && npm run build'"
                },
            )
