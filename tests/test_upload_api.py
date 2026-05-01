"""Тесты для API загрузки и обработки данных.

Тестирует эндпоинты загрузки файлов, запуска обработки и проверки статуса.
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
from fastapi import HTTPException, status

from mko_bi.api.routes.upload import (
    upload_file_endpoint,
    process_file_endpoint,
    get_status_endpoint,
    get_result_endpoint,
)
from mko_bi.models.data import (
    UploadResponse,
    ProcessingStatus,
    ProcessingResult,
    ProcessingConfig,
)
from mko_bi.models.user import UserDB


class TestUploadFileEndpoint:
    """Тесты эндпоинта загрузки файла."""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, db_session):
        """Успешная загрузка файла."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        mock_file = MagicMock()
        mock_file.filename = "test_data.csv.gz"
        mock_file.read = AsyncMock(return_value=b"col1,col2\n1,2\n3,4")

        mock_response = UploadResponse(
            task_id=uuid.uuid4(),
            filename="test_data.csv.gz",
            dashboard_id=1,
            status="uploaded",
            message="File uploaded successfully",
            uploaded_at=datetime.now(),
        )

        with patch("mko_bi.api.routes.upload.upload_file") as mock_upload:
            mock_upload.return_value = mock_response

            result = await upload_file_endpoint(
                dashboard_id=1,
                background_tasks=MagicMock(),
                current_user=mock_user,
                file=mock_file,
                db=db_session,
            )

            assert result == mock_response
            assert result.filename == "test_data.csv.gz"
            assert result.dashboard_id == 1
            mock_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_invalid_format(self, db_session):
        """Ошибка при загрузке файла с недопустимым форматом."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        mock_file = MagicMock()
        mock_file.filename = "test_data.txt"
        mock_file.read = AsyncMock(return_value=b"invalid content")

        with patch("mko_bi.api.routes.upload.upload_file") as mock_upload:
            mock_upload.side_effect = ValueError("Недопустимый формат файла")

            with pytest.raises(HTTPException) as exc_info:
                await upload_file_endpoint(
                    dashboard_id=1,
                    background_tasks=MagicMock(),
                    current_user=mock_user,
                    file=mock_file,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert "Недопустимый формат" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, db_session):
        """Ошибка при загрузке слишком большого файла."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        mock_file = MagicMock()
        mock_file.filename = "large_data.csv.gz"
        mock_file.read = AsyncMock(return_value=b"x" * (100 * 1024 * 1024 + 1))

        with patch("mko_bi.api.routes.upload.upload_file") as mock_upload:
            mock_upload.side_effect = ValueError("Превышен максимальный размер")

            with pytest.raises(HTTPException) as exc_info:
                await upload_file_endpoint(
                    dashboard_id=1,
                    background_tasks=MagicMock(),
                    current_user=mock_user,
                    file=mock_file,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_upload_file_no_permission(self, db_session):
        """Ошибка при загрузке файла без прав доступа."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        mock_file = MagicMock()
        mock_file.filename = "test_data.csv.gz"
        mock_file.read = AsyncMock(return_value=b"col1,col2\n1,2")

        with patch("mko_bi.api.routes.upload.upload_file") as mock_upload:
            mock_upload.side_effect = PermissionError("Недостаточно прав")

            with pytest.raises(HTTPException) as exc_info:
                await upload_file_endpoint(
                    dashboard_id=1,
                    background_tasks=MagicMock(),
                    current_user=mock_user,
                    file=mock_file,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_upload_file_dashboard_not_found(self, db_session):
        """Ошибка при загрузке файла для несуществующего дашборда."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        mock_file = MagicMock()
        mock_file.filename = "test_data.csv.gz"
        mock_file.read = AsyncMock(return_value=b"col1,col2\n1,2")

        with patch("mko_bi.api.routes.upload.upload_file") as mock_upload:
            mock_upload.side_effect = ValueError("Дашборд не найден")

            with pytest.raises(HTTPException) as exc_info:
                await upload_file_endpoint(
                    dashboard_id=999,
                    background_tasks=MagicMock(),
                    current_user=mock_user,
                    file=mock_file,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_upload_file_internal_error(self, db_session):
        """Внутренняя ошибка при загрузке файла."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        mock_file = MagicMock()
        mock_file.filename = "test_data.csv.gz"
        mock_file.read = AsyncMock(return_value=b"col1,col2\n1,2")

        with patch("mko_bi.api.routes.upload.upload_file") as mock_upload:
            mock_upload.side_effect = Exception("Unexpected error")

            with pytest.raises(HTTPException) as exc_info:
                await upload_file_endpoint(
                    dashboard_id=1,
                    background_tasks=MagicMock(),
                    current_user=mock_user,
                    file=mock_file,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestProcessFileEndpoint:
    """Тесты эндпоинта запуска обработки."""

    @pytest.mark.asyncio
    async def test_process_file_success(self, db_session):
        """Успешный запуск обработки."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()
        mock_status = ProcessingStatus(
            task_id=task_id,
            filename="test_data.csv.gz",
            dashboard_id=1,
            status="processing",
            progress=10,
            message="Processing started",
        )

        with patch("mko_bi.api.routes.upload.trigger_processing") as mock_process:
            mock_process.return_value = mock_status

            result = await process_file_endpoint(
                task_id=task_id,
                dashboard_id=1,
                config=None,
                background_tasks=MagicMock(),
                current_user=mock_user,
                db=db_session,
            )

            assert result == mock_status
            assert result.status == "processing"
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_file_with_config(self, db_session):
        """Запуск обработки с конфигурацией."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()
        config = ProcessingConfig(
            groupby=["category"],
            aggregations=[{"type": "sum", "field": "revenue"}],
        )
        mock_status = ProcessingStatus(
            task_id=task_id,
            filename="test_data.csv.gz",
            dashboard_id=1,
            status="processing",
            progress=10,
            message="Processing started",
        )

        with patch("mko_bi.api.routes.upload.trigger_processing") as mock_process:
            mock_process.return_value = mock_status

            result = await process_file_endpoint(
                task_id=task_id,
                dashboard_id=1,
                config=config,
                background_tasks=MagicMock(),
                current_user=mock_user,
                db=db_session,
            )

            assert result == mock_status
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_file_no_permission(self, db_session):
        """Ошибка при запуске обработки без прав доступа."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()

        with patch("mko_bi.api.routes.upload.trigger_processing") as mock_process:
            mock_process.side_effect = PermissionError("Недостаточно прав")

            with pytest.raises(HTTPException) as exc_info:
                await process_file_endpoint(
                    task_id=task_id,
                    dashboard_id=1,
                    config=None,
                    background_tasks=MagicMock(),
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_process_file_task_not_found(self, db_session):
        """Ошибка при запуске обработки несуществующей задачи."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()

        with patch("mko_bi.api.routes.upload.trigger_processing") as mock_process:
            mock_process.side_effect = ValueError("Задача не найдена")

            with pytest.raises(HTTPException) as exc_info:
                await process_file_endpoint(
                    task_id=task_id,
                    dashboard_id=1,
                    config=None,
                    background_tasks=MagicMock(),
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_process_file_already_processed(self, db_session):
        """Ошибка при повторной обработке."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()

        with patch("mko_bi.api.routes.upload.trigger_processing") as mock_process:
            mock_process.side_effect = ValueError("Задача уже completed")

            with pytest.raises(HTTPException) as exc_info:
                await process_file_endpoint(
                    task_id=task_id,
                    dashboard_id=1,
                    config=None,
                    background_tasks=MagicMock(),
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_process_file_internal_error(self, db_session):
        """Внутренняя ошибка при запуске обработки."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()

        with patch("mko_bi.api.routes.upload.trigger_processing") as mock_process:
            mock_process.side_effect = Exception("DB error")

            with pytest.raises(HTTPException) as exc_info:
                await process_file_endpoint(
                    task_id=task_id,
                    dashboard_id=1,
                    config=None,
                    background_tasks=MagicMock(),
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestGetStatusEndpoint:
    """Тесты эндпоинта получения статуса."""

    @pytest.mark.asyncio
    async def test_get_status_success(self, db_session):
        """Успешное получение статуса."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()
        mock_status = ProcessingStatus(
            task_id=task_id,
            filename="test_data.csv.gz",
            dashboard_id=1,
            status="completed",
            progress=100,
            message="Processing completed successfully",
        )

        with patch("mko_bi.api.routes.upload.get_processing_status") as mock_get:
            mock_get.return_value = mock_status

            result = await get_status_endpoint(
                task_id=task_id,
                current_user=mock_user,
                db=db_session,
            )

            assert result == mock_status
            assert result.status == "completed"
            assert result.progress == 100
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, db_session):
        """Ошибка при получении статуса несуществующей задачи."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()

        with patch("mko_bi.api.routes.upload.get_processing_status") as mock_get:
            mock_get.side_effect = ValueError("Задача не найдена")

            with pytest.raises(HTTPException) as exc_info:
                await get_status_endpoint(
                    task_id=task_id,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_status_no_permission(self, db_session):
        """Ошибка при получении статуса без прав доступа."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()

        with patch("mko_bi.api.routes.upload.get_processing_status") as mock_get:
            mock_get.side_effect = PermissionError("Недостаточно прав")

            with pytest.raises(HTTPException) as exc_info:
                await get_status_endpoint(
                    task_id=task_id,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_status_internal_error(self, db_session):
        """Внутренняя ошибка при получении статуса."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()

        with patch("mko_bi.api.routes.upload.get_processing_status") as mock_get:
            mock_get.side_effect = Exception("DB error")

            with pytest.raises(HTTPException) as exc_info:
                await get_status_endpoint(
                    task_id=task_id,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestGetResultEndpoint:
    """Тесты эндпоинта получения результата."""

    @pytest.mark.asyncio
    async def test_get_result_success(self, db_session):
        """Успешное получение результата."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()
        mock_result = ProcessingResult(
            success=True,
            task_id=task_id,
            dashboard_id=1,
            rows_processed=1000,
            message="Processing completed successfully",
            data={"columns": ["category", "revenue"], "rows": 50},
        )

        with patch("mko_bi.api.routes.upload.get_processing_result") as mock_get:
            mock_get.return_value = mock_result

            result = await get_result_endpoint(
                task_id=task_id,
                current_user=mock_user,
                db=db_session,
            )

            assert result == mock_result
            assert result.success is True
            assert result.rows_processed == 1000
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_result_not_found(self, db_session):
        """Ошибка при получении результата несуществующей задачи."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()

        with patch("mko_bi.api.routes.upload.get_processing_result") as mock_get:
            mock_get.side_effect = ValueError("Задача не найдена")

            with pytest.raises(HTTPException) as exc_info:
                await get_result_endpoint(
                    task_id=task_id,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_result_not_completed(self, db_session):
        """Ошибка при получении результата незавершенной задачи."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()

        with patch("mko_bi.api.routes.upload.get_processing_result") as mock_get:
            mock_get.side_effect = ValueError("Задача не завершена")

            with pytest.raises(HTTPException) as exc_info:
                await get_result_endpoint(
                    task_id=task_id,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_result_no_permission(self, db_session):
        """Ошибка при получении результата без прав доступа."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()

        with patch("mko_bi.api.routes.upload.get_processing_result") as mock_get:
            mock_get.side_effect = PermissionError("Недостаточно прав")

            with pytest.raises(HTTPException) as exc_info:
                await get_result_endpoint(
                    task_id=task_id,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_result_internal_error(self, db_session):
        """Внутренняя ошибка при получении результата."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()

        with patch("mko_bi.api.routes.upload.get_processing_result") as mock_get:
            mock_get.side_effect = Exception("DB error")

            with pytest.raises(HTTPException) as exc_info:
                await get_result_endpoint(
                    task_id=task_id,
                    current_user=mock_user,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestIntegration:
    """Интеграционные тесты."""

    @pytest.mark.asyncio
    async def test_full_upload_and_process_flow(self, db_session):
        """Полный цикл: загрузка, обработка, проверка статуса и результата."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 1

        task_id = uuid.uuid4()

        # 1. Загрузка файла
        mock_file = MagicMock()
        mock_file.filename = "test_data.csv.gz"
        mock_file.read = AsyncMock(return_value=b"category,revenue\nA,100\nB,200")

        upload_response = UploadResponse(
            task_id=task_id,
            filename="test_data.csv.gz",
            dashboard_id=1,
            status="uploaded",
            message="File uploaded successfully",
            uploaded_at=datetime.now(),
        )

        with patch("mko_bi.api.routes.upload.upload_file") as mock_upload:
            mock_upload.return_value = upload_response

            result = await upload_file_endpoint(
                dashboard_id=1,
                background_tasks=MagicMock(),
                current_user=mock_user,
                file=mock_file,
                db=db_session,
            )

            assert result.task_id == task_id
            assert result.status == "uploaded"

        # 2. Запуск обработки
        processing_status = ProcessingStatus(
            task_id=task_id,
            filename="test_data.csv.gz",
            dashboard_id=1,
            status="processing",
            progress=10,
            message="Processing started",
        )

        with patch("mko_bi.api.routes.upload.trigger_processing") as mock_process:
            mock_process.return_value = processing_status

            result = await process_file_endpoint(
                task_id=task_id,
                dashboard_id=1,
                config=None,
                background_tasks=MagicMock(),
                current_user=mock_user,
                db=db_session,
            )

            assert result.status == "processing"

        # 3. Проверка статуса
        completed_status = ProcessingStatus(
            task_id=task_id,
            filename="test_data.csv.gz",
            dashboard_id=1,
            status="completed",
            progress=100,
            message="Processing completed successfully",
        )

        with patch("mko_bi.api.routes.upload.get_processing_status") as mock_get_status:
            mock_get_status.return_value = completed_status

            result = await get_status_endpoint(
                task_id=task_id,
                current_user=mock_user,
                db=db_session,
            )

            assert result.status == "completed"
            assert result.progress == 100

        # 4. Получение результата
        processing_result = ProcessingResult(
            success=True,
            task_id=task_id,
            dashboard_id=1,
            rows_processed=2,
            message="Processing completed successfully",
            data={"columns": ["category", "revenue"], "rows": 2},
        )

        with patch("mko_bi.api.routes.upload.get_processing_result") as mock_get_result:
            mock_get_result.return_value = processing_result

            result = await get_result_endpoint(
                task_id=task_id,
                current_user=mock_user,
                db=db_session,
            )

            assert result.success is True
            assert result.rows_processed == 2

    @pytest.mark.asyncio
    async def test_editor_cannot_access_admin_upload(self, db_session):
        """Editor не может загружать файлы для дашбордов без прав."""
        mock_user = MagicMock(spec=UserDB)
        mock_user.id = 2
        mock_user.role = "editor"

        mock_file = MagicMock()
        mock_file.filename = "test_data.csv.gz"
        mock_file.read = AsyncMock(return_value=b"col1,col2\n1,2")

        with patch("mko_bi.api.routes.upload.upload_file") as mock_upload:
            mock_upload.side_effect = PermissionError("Недостаточно прав")

            with pytest.raises(HTTPException) as exc_info:
                await upload_file_endpoint(
                    dashboard_id=1,
                    background_tasks=MagicMock(),
                    current_user=mock_user,
                    file=mock_file,
                    db=db_session,
                )

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN