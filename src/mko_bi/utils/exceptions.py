"""Custom exceptions for the application.

Provides base application exception and specialized subclasses, plus FastAPI exception handlers.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mko_bi.core.logging_config import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base application exception.

    Attributes:
        status_code: HTTP status code for the error.
        detail: Human-readable error message.
        error_code: Machine-readable error code.
    """

    def __init__(
        self,
        status_code: int = 500,
        detail: str = "Internal server error",
        error_code: str = "INTERNAL_ERROR",
    ) -> None:
        """Initialize AppException.

        Args:
            status_code: HTTP status code. Defaults to 500.
            detail: Error message. Defaults to "Internal server error".
            error_code: Error code. Defaults to "INTERNAL_ERROR".
        """
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(detail)


class NotFoundException(AppException):
    """Exception raised when a resource is not found."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(
            status_code=404,
            detail=detail,
            error_code="NOT_FOUND",
        )


class PermissionDeniedException(AppException):
    """Exception raised when user lacks permission."""

    def __init__(self, detail: str = "Permission denied") -> None:
        super().__init__(
            status_code=403,
            detail=detail,
            error_code="PERMISSION_DENIED",
        )


class ValidationException(AppException):
    """Exception raised for validation errors."""

    def __init__(self, detail: str = "Validation error") -> None:
        super().__init__(
            status_code=400,
            detail=detail,
            error_code="VALIDATION_ERROR",
        )


class FileUploadException(AppException):
    """Exception raised for file upload errors."""

    def __init__(self, detail: str = "File upload failed") -> None:
        super().__init__(
            status_code=400,
            detail=detail,
            error_code="FILE_UPLOAD_ERROR",
        )


def add_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for custom exceptions in FastAPI app.

    Args:
        app: FastAPI application instance.
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.error(
            "AppException raised: error_code=%s, detail=%s",
            exc.error_code,
            exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status_code": exc.status_code,
                "detail": exc.detail,
                "error_code": exc.error_code,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "detail": "Internal server error",
                "error_code": "INTERNAL_ERROR",
            },
        )
