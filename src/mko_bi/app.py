# Application entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mko_bi.api.routes import (
    auth_router,
    users_router,
    dashboards_router,
    upload_router,
)
from mko_bi.db.base import get_db


def create_app():
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="mko_bi",
        version="1.0.0",
        description="BI Dashboard System API",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth_router, prefix="/api")
    app.include_router(users_router, prefix="/api")
    app.include_router(dashboards_router, prefix="/api")
    app.include_router(upload_router, prefix="/api")

    # Dependency override for testing
    app.dependency_overrides[get_db] = lambda: None

    return app


app = create_app()


@app.get("/")
async def root():
    """Root endpoint.

    Returns:
        API information
    """
    return {
        "name": "mko_bi",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
    }
