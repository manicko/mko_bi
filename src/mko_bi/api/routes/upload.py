"""Маршруты для загрузки и обработки данных.

Этот модуль предоставляет эндпоинты для:
- Загрузки CSV файлов
- Запуска обработки данных
- Проверки статуса обработки

Все операции требуют аутентификации и соответствующих прав доступа.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from mko_bi.api.deps import (
    get_db,
    require_editor_role,
    CurrentUser,
)
from mko_bi.models.data import (
    DataUpload,
    UploadResponse,
    ProcessingStatus,
    ProcessingResult,
    ProcessingConfig,
)
from mko_bi.services.data_service import (
    upload_file,
    trigger_processing,
    get_processing_status,
    get_processing_result,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post(
    "/{dashboard_id}",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузка файла",
    description="Загружает CSV файл для последующей обработки. Доступно только редакторам и администраторам.",
)
async def upload_file_endpoint(
    dashboard_id: int,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """Загружает файл для дашборда.

    Принимает файл в формате .csv.gz и сохраняет его во временную директорию
    для последующей обработки. Проверяет формат файла и размер (максимум 100MB).

    Args:
        file: Загружаемый файл (должен быть в формате .csv.gz).
        dashboard_id: ID дашборда, для которого загружается файл.
        background_tasks: Фоновые задачи FastAPI.
        current_user: Текущий аутентифицированный пользователь.
        db: Сессия базы данных.

    Returns:
        UploadResponse: Модель с информацией о загрузке.

    Raises:
        HTTPException 403: Если у пользователя нет прав на загрузку.
        HTTPException 413: Если файл превышает максимальный размер.
        HTTPException 415: Если формат файла недопустим.
        HTTPException 422: Если данные не прошли валидацию.
        HTTPException 500: При ошибке сервера.
    """
    logger.info(
        "Загрузка файла: filename=%s, dashboard_id=%d, user_id=%s",
        file.filename,
        dashboard_id,
        current_user.id,
    )

    try:
        # Чтение содержимого файла
        # UploadFile.read() может быть как sync, так и async в зависимости от версии
        try:
            file_content = file.read()
        except TypeError:
            # Если read() ожидает await, вызываем его как async
            file_content = await file.read()

        # Вызов сервиса загрузки
        result = upload_file(
            filename=file.filename,
            file_content=file_content,
            dashboard_id=dashboard_id,
            user_id=current_user.id,
            db=db,
        )

        logger.info(
            "Файл успешно загружен: task_id=%s, filename=%s",
            result.task_id,
            file.filename,
        )

        return result

    except ValueError as e:
        logger.warning("Ошибка валидации при загрузке: %s", e)
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
    response_model=ProcessingStatus,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Запуск обработки",
    description="Запускает обработку загруженного файла. Доступно только редакторам и администраторам.",
)
async def process_file_endpoint(
    task_id: UUID,
    dashboard_id: int,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    config: ProcessingConfig | None = None,
) -> ProcessingStatus:
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
        "Запуск обработки: task_id=%s, dashboard_id=%d, user_id=%s",
        task_id,
        dashboard_id,
        current_user.id,
    )

    try:
        # Вызов сервиса обработки
        result = trigger_processing(
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
    response_model=ProcessingStatus,
    status_code=status.HTTP_200_OK,
    summary="Статус обработки",
    description="Возвращает текущий статус обработки файла.",
)
async def get_status_endpoint(
    task_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> ProcessingStatus:
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
        result = get_processing_status(
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
    db: Session = Depends(get_db),
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
        result = get_processing_result(
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