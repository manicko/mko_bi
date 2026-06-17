"""RFC 7807 Problem Details error response model.

This module defines the standardized error response format for all API errors.
All error codes are defined in the ErrorCode enum.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict

from mkobi.models.enums import ErrorCode


class ErrorResponse(BaseModel):
    """Standardized error response model following RFC 7807 Problem Details format.

    Fields:
        type: URI-style error type for documentation/reference.
        title: Short human-readable summary.
        status: HTTP status code.
        detail: Developer-facing message (English, for logging/debug).
        code: Machine-readable ErrorCode enum value.
        details: Optional structured context (column names, field names, etc.).
    """

    type: str
    title: str
    status: int
    detail: str
    code: ErrorCode
    details: dict[str, Any] | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "type": "https://api.mkobi.com/errors/not_found",
                "title": "Resource not found",
                "status": 404,
                "detail": "Dashboard not found",
                "code": "DASHBOARD_NOT_FOUND",
                "details": {"dashboard_id": "550e8400-e29b-41d4-a716-446655440000"},
            }
        },
    )