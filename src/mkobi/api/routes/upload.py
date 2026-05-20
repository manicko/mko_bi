"""Upload and processing routes.

This module provides endpoints for:
- Uploading CSV files
- Triggering data processing
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
    get_db,
    get_data_service,
)
from mkobi.config import get_config
from mkobi.core.logging_config import get_logger
from mkobi.core import redis_client
from mkobi.core.permissions import PermissionError as PermissionError
from mkobi.core.security import AsyncRateLimiter
from mkobi.models.data import (
    ProcessingConfig,
    ProcessingResult,
    ProcessingStatusResponse,
)
from mkobi.models.enums import UploadMode
from mkobi.services.data_service import DataService

router = APIRouter(prefix="/upload", tags=["upload"])

logger = get_logger(__name__)

# Chunk size for streaming file uploads (8KB)
CHUNK_SIZE = 8192


@router.post(
    "/{dashboard_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Upload file",
    description="Uploads a CSV file for processing. Available to editors and admins only.",
)
async def upload_file_endpoint(
    dashboard_id: UUID,
    current_user: EditorUser,
    file: UploadFile = File(...),
    mode: UploadMode = UploadMode.OVERWRITE,
    db: AsyncSession = Depends(get_db),
    data_service: DataService = Depends(get_data_service),
) -> dict[str, str | UUID]:
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
        """Handle ValueError by mapping to appropriate HTTPException with logging."""
        logger.warning("Validation error during upload: %s", e)
        error_msg = str(e).lower()
        if "mime" in error_msg or "invalid mime" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=str(e),
            ) from e
        elif (
            "format" in error_msg
            or "invalid format" in error_msg
            or "extension" in error_msg
        ):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=str(e),
            ) from e
        elif "size" in error_msg or "exceeds" in error_msg or "max" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=str(e),
            ) from e
        elif "limit" in error_msg or "rate limit" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e),
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(e),
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
            max_attempts=10,
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

        # Stream file in chunks to reduce memory pressure
        total_bytes = 0
        async with aiofiles.open(temp_file_path, "wb") as f:
            while chunk := await file.read(CHUNK_SIZE):
                await f.write(chunk)
                total_bytes += len(chunk)

        await file.close()

        logger.info(
            "File streamed to disk",
            extra={"file_name": sanitized_filename, "size_bytes": total_bytes},
        )

        # Call service (validation is in service layer)
        try:
            result = await data_service.process_upload(
                file_path=str(temp_file_path),
                dashboard_id=dashboard_id,
                user_id=current_user.id,
                filename=filename,
                content_type=file.content_type,
                mode=mode,
                db=db,
            )
        except PermissionError as e:
            logger.warning("Permission denied for upload: %s", e)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            ) from e
        except ValueError as e:
            _handle_value_error(e)
        except Exception as e:
            logger.error("Error during file processing: %s", e, exc_info=True)
            raise

        logger.info(
            "File uploaded successfully",
            extra={
                "processing_log_id": str(result.task_id),
                "file_name": file.filename,
                "mode": mode,
            },
        )

        return {
            "message": result.message,
            "processing_log_id": result.task_id,
        }

    except HTTPException:
        raise
    except ValueError as e:
        _handle_value_error(e)
    except PermissionError as e:
        logger.warning("Permission denied for upload: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Error during file upload: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during file upload: {e}",
        ) from e


@router.post(
    "/{dashboard_id}/process",
    response_model=ProcessingStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start processing",
    description="Starts processing of uploaded file.",
)
async def process_file_endpoint(
    task_id: UUID,
    dashboard_id: UUID,
    current_user: EditorUser,
    db: AsyncSession = Depends(get_db),
    data_service: DataService = Depends(get_data_service),
    config: ProcessingConfig | None = None,
) -> ProcessingStatusResponse:
    """Start processing of uploaded file."""
    logger.info(
        "Processing start requested",
        extra={
            "task_id": str(task_id),
            "dashboard_id": str(dashboard_id),
            "user_id": str(current_user.id),
        },
    )

    try:
        result = await data_service.trigger_processing(
            task_id=task_id,
            dashboard_id=dashboard_id,
            user_id=current_user.id,
            processing_config=config,
            db=db,
        )

        logger.info(
            "Processing started",
            extra={"task_id": str(task_id), "status": result.status},
        )

        return result

    except ValueError as e:
        logger.warning("Error starting processing: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning("Permission denied for processing: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Error starting processing: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error starting processing",
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
    db: AsyncSession = Depends(get_db),
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
        logger.warning("Task not found: %s", e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning("Permission denied for status check: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Error getting status: %s", e)
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
    db: AsyncSession = Depends(get_db),
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
        logger.warning("Error getting result: %s", e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning("Permission denied for result: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Error getting result: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting result",
        ) from e