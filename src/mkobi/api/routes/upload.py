"""Маршруты для загрузки и обработки данных.

Этот модуль предоставляет эндпоинты для:
- Загрузки CSV файлов
- Запуска обработки данных
- Проверки статуса обработки

Все операции требуют аутентификации и соответствующих прав доступа.
"""

import asyncio
import logging
import shutil
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.config import get_config
from mkobi.utils import file_utils
from mkobi.data.loaders.validator import validate_file_extension, validate_mime_type
from mkobi.models.enums import FileExtensionEnum, MimeTypeEnum
from mkobi.api.deps import (
    get_db,
    CurrentUser,
)
from mkobi.models.data import (
    ProcessingConfig,
    ProcessingResult,
    ProcessingStatusResponse,
)
from mkobi.models.enums import UploadMode
from mkobi.services.data_service import (
    upload_file,
    trigger_processing,
    get_processing_status,
    get_processing_result,
)
from werkzeug.utils import secure_filename

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post(
    "/{dashboard_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Загрузка файла",
    description="Загружает CSV файл для последующей обработки. Доступно только редакторам и администраторам.",
)
async def upload_file_endpoint(
    dashboard_id: UUID,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    mode: UploadMode = UploadMode.OVERWRITE,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | UUID]:
    """Загружает файл для дашборда.

    Принимает файл, проверяет его параметры, сохраняет во временную директорию
    пользователя (platformdirs) и создает задачу на обработку.

    Args:
        dashboard_id: ID дашборда, для которого загружается файл.
        current_user: Текущий аутентифицированный пользователь.
        file: Загружаемый файл (поддерживаются .csv и .csv.gz).
        mode: Режим загрузки (overwrite/append).
        db: Сессия базы данных.

    Returns:
        dict: Словарь с сообщением и ID лога обработки.

    Raises:
        HTTPException 403: Если у пользователя нет прав на загрузку.
        HTTPException 413: Если файл превышает максимальный размер.
        HTTPException 415: Если формат файла недопустим.
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 429: Если превышен лимит запросов.
        HTTPException 500: При ошибке сервера.
    """
    logger.info(
        "Загрузка файла: filename=%s, dashboard_id=%s, user_id=%s",
        file.filename,
        dashboard_id,
        current_user.id,
    )

    try:
        # 1. Валидация расширения файла
        if not validate_file_extension(file.filename):
            logger.warning("Недопустимое расширение файла: %s", file.filename)
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Недопустимое расширение файла. Разрешены: {[e.value for e in FileExtensionEnum]}",
            )

        # 2. Валидация MIME-типа
        if file.content_type and not validate_mime_type(file.content_type):
            logger.warning("Недопустимый MIME-тип: %s", file.content_type)
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Недопустимый MIME-тип. Разрешены: {MimeTypeEnum.allowed_values()}",
            )

        # 3. Валидация размера файла по заголовку Content-Length
        config = get_config()
        max_size_bytes = config.max_file_size
        if file.size and file.size > max_size_bytes:
            logger.warning("Файл превышает максимальный размер: %s", file.filename)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Файл превышает максимальный размер ({max_size_bytes // (1024*1024)} MB)",
            )

        # 4. Сохранение файла во временную директорию пользователя (platformdirs)
        temp_dir = file_utils.get_user_temp_dir(current_user.id)
        secured_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{dashboard_id}_{secured_filename}"
        file_path = temp_dir / unique_filename

        # Проверка безопасности пути (защита от directory traversal)
        resolved_temp_dir = temp_dir.resolve()
        resolved_file_path = file_path.resolve()
        if not str(resolved_file_path).startswith(str(resolved_temp_dir)):
            logger.error("Попытка directory traversal: %s", file.filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Недопустимый путь к файлу",
            )

        # Потоковая запись файла на диск (без загрузки в память)
        try:
            await asyncio.to_thread(
                shutil.copyfileobj,
                file.file,
                open(file_path, "wb"),
            )
        finally:
            await file.close()

        # Проверка размера файла на диске (если не был проверен по заголовку)
        if not file.size and file_path.stat().st_size > max_size_bytes:
            file_path.unlink(missing_ok=True)
            logger.warning("Файл превышает максимальный размер после сохранения: %s", file.filename)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Файл превышает максимальный размер ({max_size_bytes // (1024*1024)} MB)",
            )

        logger.info("Файл успешно сохранен: %s", file_path)

        # 5. Вызов сервиса загрузки для обработки логики (права, режим, создание лога, очередь)
        result = await upload_file(
            filename=file.filename,
            file_path=file_path,
            content_type=file.content_type,
            dashboard_id=dashboard_id,
            user_id=current_user.id,
            mode=mode,
            db=db,
        )

        logger.info(
            "Файл успешно загружен: processing_log_id=%s, filename=%s, mode=%s",
            result.task_id,
            file.filename,
            mode,
        )

        # Возврат согласно спецификации: {"message": str, "processing_log_id": UUID}
        return {
            "message": result.message,
            "processing_log_id": result.task_id,
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Ошибка валидации при загрузке: %s", e)
        if "лимит" in str(e).lower() or "rate limit" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning("Отказано в загрузке: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Ошибка при загрузке файла: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при загрузке файла",
        ) from e


@router.post(
    "/{dashboard_id}/process",
    response_model=ProcessingStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Запуск обработки",
    description="Запускает обработку загруженного файла. Доступно только редакторам и администраторам.",
)
async def process_file_endpoint(
    task_id: UUID,
    dashboard_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    config: ProcessingConfig | None = None,
) -> ProcessingStatusResponse:
    """Запускает обработку загруженного файла.

    Асинхронно обрабатывает загруженный файл с использованием заданной
    конфигурации обработки. Статус обработки можно отслеживать через
    эндпоинт GET /upload/status/{task_id}.

    Args:
        task_id: ID задачи загрузки.
        dashboard_id: ID дашборда.
        config: Конфигурация обработки (опционально).
        background_tasks: Фоновые задачи FastAPI.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        ProcessingStatus: Статус обработки.

    Raises:
        HTTPException 403: Если у пользователя нет прав на обработку.
        HTTPException 404: Если задача не найдена.
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 500: При ошибке сервера.
    """
    logger.info(
        "Запуск обработки: task_id=%s, dashboard_id=%s, user_id=%s",
        task_id,
        dashboard_id,
        current_user.id,
    )

    try:
        # Вызов сервиса обработки
        result = await trigger_processing(
            task_id=task_id,
            dashboard_id=dashboard_id,
            user_id=current_user.id,
            processing_config=config,
            db=db,
        )

        logger.info(
            "Обработка запущена: task_id=%s, status=%s",
            task_id,
            result.status,
        )

        return result

    except ValueError as e:
        logger.warning("Ошибка при запуске обработки: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning("Отказано в обработке: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Ошибка при запуске обработки: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при запуске обработки",
        ) from e


@router.get(
    "/status/{task_id}",
    response_model=ProcessingStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Статус обработки",
    description="Возвращает текущий статус обработки файла.",
)
async def get_status_endpoint(
    task_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ProcessingStatusResponse:
    """Получает текущий статус обработки файла.

    Args:
        task_id: ID задачи.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        ProcessingStatus: Статус обработки.

    Raises:
        HTTPException 403: Если у пользователя нет прав на просмотр.
        HTTPException 404: Если задача не найдена.
        HTTPException 500: При ошибке сервера.
    """
    logger.info(
        "Запрос статуса: task_id=%s, user_id=%s",
        task_id,
        current_user.id,
    )

    try:
        # Вызов сервиса получения статуса
        result = await get_processing_status(
            task_id=task_id,
            user_id=current_user.id,
            db=db,
        )

        logger.info(
            "Статус получен: task_id=%s, status=%s",
            task_id,
            result.status,
        )

        return result

    except ValueError as e:
        logger.warning("Задача не найдена: %s", e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning("Отказано в доступе: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Ошибка при получении статуса: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении статуса",
        ) from e


@router.get(
    "/result/{task_id}",
    response_model=ProcessingResult,
    status_code=status.HTTP_200_OK,
    summary="Результат обработки",
    description="Возвращает результат обработки файла.",
)
async def get_result_endpoint(
    task_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ProcessingResult:
    """Получает результат обработки файла.

    Args:
        task_id: ID задачи.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        ProcessingResult: Результат обработки.

    Raises:
        HTTPException 403: Если у пользователя нет прав на просмотр.
        HTTPException 404: Если задача не найдена или не завершена.
        HTTPException 500: При ошибке сервера.
    """
    logger.info(
        "Запрос результата: task_id=%s, user_id=%s",
        task_id,
        current_user.id,
    )

    try:
        # Вызов сервиса получения результата
        result = await get_processing_result(
            task_id=task_id,
            user_id=current_user.id,
            db=db,
        )

        logger.info(
            "Результат получен: task_id=%s, rows=%d",
            task_id,
            result.rows_processed,
        )

        return result

    except ValueError as e:
        logger.warning("Ошибка при получении результата: %s", e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except PermissionError as e:
        logger.warning("Отказано в доступе: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Ошибка при получении результата: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении результата",
        ) from e