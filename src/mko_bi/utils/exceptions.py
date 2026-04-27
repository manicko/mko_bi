"""HTTP exceptions for the application.

Provides custom HTTPException class for raising HTTP errors with status codes and details.
"""

from typing import Any

from fastapi import HTTPException as FastAPIHTTPException


class HTTPException(FastAPIHTTPException):
    """Custom HTTP exception with status code and detail.

    Extends FastAPI's HTTPException to provide a consistent interface for
    raising HTTP errors throughout the application.

    Attributes:
        status_code: HTTP status code (e.g., 404, 500).
        detail: Error message describing what went wrong.
        headers: Optional HTTP headers to include in the response.
    """

    def __init__(
        self,
        status_code: int,
        detail: str | None = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        """Initialize HTTPException.

        Args:
            status_code: HTTP status code (e.g., 404, 500).
            detail: Error message describing what went wrong. Defaults to None.
            headers: Optional HTTP headers to include in the response. Defaults to None.

        Example:
            >>> raise HTTPException(status_code=404, detail="Item not found")
        """
        super().__init__(status_code=status_code, detail=detail, headers=headers)
