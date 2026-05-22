"""Routes for client-side error reporting.

This module provides an endpoint for frontend error logging.
No database persistence - errors are logged for monitoring.
"""

import logging
from typing import Any

from fastapi import APIRouter, status

from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/client-errors", tags=["client-errors"], redirect_slashes=False)


class ClientErrorPayload(BaseModel):
    """Payload model for client-side error reports."""

    error: dict[str, Any]
    componentStack: str | None = None
    url: str
    userAgent: str
    timestamp: str


@router.post(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Report client-side error",
    description="Accepts client error details for logging. No authentication required.",
)
async def report_client_error(payload: ClientErrorPayload) -> None:
    """Report client-side error.

    Logs error details from frontend without persisting to database.

    Args:
        payload: Client error information including error, url, and context.
    """
    error_message = payload.error.get("message", "Unknown error")
    logger.error(
        "Client error: %s | url=%s | componentStack=%s",
        error_message,
        payload.url,
        payload.componentStack,
    )