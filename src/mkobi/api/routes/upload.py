"""Upload and processing routes.

This module provides endpoints for:
- Uploading CSV files
- Checking processing status

All operations require authentication and appropriate permissions.
"""

from pathlib import Path
from typing import NoReturn
from uuid import UUID, uuid4

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.api.deps import (
    EditorUser,
    get_db_dependency,
    get_data_service,
)
from mkobi.config import get_config
from mkobi.core.logging_config import get_logger
from mkobi.core import redis_client
from mkobi.core.permissions import DashboardPermissionError
from mkobi.core.security import AsyncRateLimiter
from mkobi.models.data import (
    ProcessingResult,
    ProcessingStatusResponse,
    UploadResponse,
)
from mkobi.models.enums import UploadMode
from mkobi.services.data_service import DataService
from mkobi.utils.exceptions import AppException

router = APIRouter(prefix="/upload", tags=["upload"], redirect_slashes=False)

logger = get_logger(__name__)

# Chunk size for streaming file uploads (8KB)
CHUNK_SIZE = 8192


@router.post(
    "/{dashboard_id}",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file",
    description="Uploads a CSV file for processing. Available to editors and admins only.",
)
async def upload_file_endpoint(
    dashboard_id: UUID,
    current_user: EditorUser,
    file: UploadFile = File(...),
    mode: UploadMode = UploadMode.OVERWRITE,
    db: AsyncSession = Depends(get_db_dependency),
    data_service: DataService = Depends(get_data_service),
) -> UploadResponse:
    """Upload file for dashboard."""
    logger.info(
        "File upload started",
        extra={
            "file_name": file.filename,
            "dashboard_id": str(dashboard_id),
            "user_id": str(current_user.id),
        },
    )

    def _handle_value_error(e: ValueError) -> NoReturn:
        """Handle ValueError by mapping to appropriate HTTPException with generic messages."""
        logger.warning("Validation error during upload", exc_info=True)
        error_msg = str(e).lower()
        if "mime" in error_msg or "invalid mime" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Invalid file type",
            ) from e
        elif (
            "format" in error_msg
            or "invalid format" in error_msg
            or "extension" in error_msg
        ):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Invalid file format",
            ) from e
        elif "size" in error_msg or "exceeds" in error_msg or "max" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="File size exceeds limit",
            ) from e
        elif "limit" in error_msg or "rate limit" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Validation error",
            ) from e

    try:
        config = get_config()

        # Enforce file size limit before reading into memory
        if file.size is not None and file.size > config.max_file_size:
            logger.warning(
                "File size exceeds limit",
                extra={
                    "file_name": file.filename,
                    "size_bytes": file.size,
                    "max_bytes": config.max_file_size,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,  # Use new constant
                detail=f"File size exceeds maximum limit of {config.upload.max_file_size_mb}MB",
            )

        # Apply rate limiting for upload endpoint
        rate_limiter = AsyncRateLimiter(
            redis_client.get_async_redis_client(),
            fail_closed=config.rate_limiter_fail_closed,
        )
        if not await rate_limiter.check_rate_limit(
            f"upload:{current_user.id}",
            max_attempts=100,
            ttl=3600,
        ):
            logger.warning(
                "Upload rate limit exceeded",
                extra={"user_id": str(current_user.id)},
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded for uploads",
            )

        # Read and stream file content to temporary location
        filename = file.filename or "unknown"
        sanitized_filename = Path(filename).name

        # Create temporary file path with unique name
        upload_dir = Path(get_config().upload_temp_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_file_path = upload_dir / f"upload_{uuid4()}_{sanitized_filename}"

        try:
            # Stream file in chunks to reduce memory pressure
            total_bytes = 0
            async with aiofiles.open(temp_file_path, "wb") as f:
                while chunk := await file.read(CHUNK_SIZE):
                    total_bytes += len(chunk)
                    # Enforce size limit during streaming even when file.size is None
                    # This prevents disk exhaustion attacks when Content-Length is missing
                    if total_bytes > config.max_file_size:
                        await file.close()
                        temp_file_path.unlink(missing_ok=True)
                        logger.warning(
                            "Upload rejected: cumulative size exceeds limit",
                            extra={
                                "file_name": sanitized_filename,
                                "size_bytes": total_bytes,
                                "max_bytes": config.max_file_size,
                            },
                        )
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File size exceeds maximum limit of {config.upload.max_file_size_mb}MB",
                        )
                    await f.write(chunk)

            await file.close()

            logger.info(
                "File streamed to disk",
                extra={"file_name": sanitized_filename, "size_bytes": total_bytes},
            )

            # Call service (validation is in service layer)
            result = await data_service.process_upload(
                file_path=str(temp_file_path),
                dashboard_id=dashboard_id,
                user_id=current_user.id,
                filename=filename,
                content_type=file.content_type,
                mode=mode,
                db=db,
            )

            logger.info(
                "File uploaded successfully",
                extra={
                    "task_id": str(result.task_id),
                    "file_name": file.filename,
                    "mode": mode,
                },
            )

            return result
        finally:
            # Clean up temp file if processing failed (file was not moved to final location)
            # temp_file_path no longer exists if process_upload succeeded (file was moved)
            if temp_file_path.exists():
                logger.info("Cleaning up temp file after failed upload", extra={"path": str(temp_file_path)})
                temp_file_path.unlink(missing_ok=True)

    except HTTPException:
        raise
    except AppException as e:
        # Re-raise AppException to let global handler format it with error_code
        raise e
    except ValueError as e:
        _handle_value_error(e)
    except DashboardPermissionError as e:
        logger.warning("Permission denied for upload: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Error during file upload", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during file upload",
        ) from e


@router.get(
    "/status/{task_id}",
    response_model=ProcessingStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get processing status",
    description="Returns current processing status of file.",
)
async def get_status_endpoint(
    task_id: UUID,
    current_user: EditorUser,
    db: AsyncSession = Depends(get_db_dependency),
    data_service: DataService = Depends(get_data_service),
) -> ProcessingStatusResponse:
    """Get current processing status of file."""
    logger.info(
        "Status check requested",
        extra={
            "task_id": str(task_id),
            "user_id": str(current_user.id),
        },
    )

    try:
        result = await data_service.get_processing_status(
            task_id=task_id,
            user_id=current_user.id,
            db=db,
        )

        logger.info(
            "Status retrieved",
            extra={"task_id": str(task_id), "status": result.status},
        )

        return result

    except ValueError as e:
        logger.warning("Task not found", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from e
    except DashboardPermissionError as e:
        logger.warning("Permission denied for status check", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from e
    except Exception as e:
        logger.error("Error getting status", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting status",
        ) from e


@router.get(
    "/result/{task_id}",
    response_model=ProcessingResult,
    status_code=status.HTTP_200_OK,
    summary="Get processing result",
    description="Returns processing result of file.",
)
async def get_result_endpoint(
    task_id: UUID,
    current_user: EditorUser,
    db: AsyncSession = Depends(get_db_dependency),
    data_service: DataService = Depends(get_data_service),
) -> ProcessingResult:
    """Get processing result of file."""
    logger.info(
        "Result requested",
        extra={
            "task_id": str(task_id),
            "user_id": str(current_user.id),
        },
    )

    try:
        result = await data_service.get_processing_result(
            task_id=task_id,
            user_id=current_user.id,
            db=db,
        )

        logger.info(
            "Result retrieved",
            extra={"task_id": str(task_id), "rows_processed": result.rows_processed},
        )

        return result

    except ValueError as e:
        logger.warning("Error getting result", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found",
        ) from e
    except DashboardPermissionError as e:
        logger.warning("Permission denied for result", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        ) from e
    except Exception as e:
        logger.error("Error getting result", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting result",
        ) from e