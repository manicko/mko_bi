"""Routes for client-side error reporting.

This module provides an endpoint for frontend error logging.
No database persistence - errors are logged for monitoring.
"""

import logging

from fastapi import APIRouter, Request, status

from mkobi.config import get_config
from mkobi.core import redis_client
from mkobi.core.security import AsyncRateLimiter
from mkobi.models.data import ClientErrorPayload
from mkobi.models.enums import ErrorCode
from mkobi.utils.exceptions import AppException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/client-errors", tags=["client-errors"], redirect_slashes=False)


@router.post(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Report client-side error",
    description="Accepts client error details for logging. No authentication required.",
)
async def report_client_error(payload: ClientErrorPayload, request: Request) -> None:
    """Report client-side error.

    Logs error details from frontend without persisting to database.
    Rate limiting is applied per IP address to prevent DoS flooding attacks.

    Args:
        payload: Client error information including error, url, and context.
        request: FastAPI request object for extracting client IP.
    """
    config = get_config()
    client_ip = request.client.host if request.client else "unknown"

    # Rate limiting check
    rate_limiter = AsyncRateLimiter(
        redis_client.get_async_redis_client(),
        fail_closed=config.rate_limiter_fail_closed,
    )
    rate_limit_key = f"client-errors:{client_ip}"
    if not await rate_limiter.check_rate_limit(rate_limit_key, max_attempts=100, ttl=3600):
        logger.warning(
            "Rate limit exceeded for client-errors endpoint",
            extra={"ip": client_ip},
        )
        raise AppException(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            detail="Rate limit exceeded for client error reports",
        )

    error_message = payload.error.get("message", "Unknown error")
    logger.error(
        "Client error: %s | url=%s | componentStack=%s",
        error_message,
        payload.url,
        payload.componentStack,
    )