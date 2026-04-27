"""Тесты для сервиса обработки данных (data_service.py).

Тестирует бизнес-логику загрузки, обработки и отслеживания статуса
обработки данных для дашбордов с использованием моков.
"""

import pytest
import uuid
import gzip
import json
import tempfile
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from mko_bi.services.data_service import (
    upload_file,
    trigger_processing,
    get_processing_status,
    get_processing_result,
    get_dashboard_aggregates,
    get_chart_data,
    apply_data_filters,
    cleanup_task_files,
    _validate_file,
    _save_uploaded_file,
    _process_csv_file,
)
from mko_bi.db.repositories.dashboard_repo import DashboardRepository
from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.models.data import (
    UploadResponse,
    ProcessingStatus,
    ProcessingResult,
    AggregatedData,
    ProcessingConfig,
)
from mko_bi.core.permissions import check_dashboard_access


class TestValidateFile:
    """Тесты для функции валидации файла."""

    def test_valid_csv_gz_file(self):
        """Валидный .csv.gz файл должен проходить проверку."""
        content = b"test data"
        _validate_file("data.csv.gz", content)

    def test_valid_csv_file(self):
        """Валидный .csv файл должен проходить проверку."""
        content = b"test data"
        _validate_file("data.csv", content)

    def test_invalid_file_type_raises_error(self):
        """Недопустимый тип файла должен вызывать ошибку."""
        content = b"test data"
        with pytest.raises(ValueError, match="Недопустимый формат файла"):
            _validate_file("data.txt", content)

    def test_file_too_large_raises_error(self):
        """Файл, превышающий максимальный размер, должен вызывать ошибку."""
        content = b"x" * (100 * 1024 * 1024 + 1)  # 100MB + 1 byte
        with pytest.raises(ValueError, match="превышает максимальный размер"):
            _validate_file("data.csv.gz", content)

    def test_empty_filename_raises_error(self):
        """Пустое имя файла должно вызывать ошибку."""
        content = b"test"
        with pytest.raises(ValueError, match="Недопустимый формат файла"):
            _validate_file("", content)


class TestSaveUploadedFile:
    """Тесты для функции сохранения загруженного файла."""

    def test_save_file_success(self, tmp_path):
        """Успешное сохранение файла."""
        content = b"test data"
        filename = "test.csv.gz"

        with patch('mko_bi.services.data_service.config') as mock_config, \
             patch('mko_bi.services.data_service.uuid') as mock_uuid:
            mock_config.upload_temp_dir = str(tmp_path)
            mock_uuid.uuid4.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')

            result = _save_uploaded_file(filename, content)

            assert isinstance(result, Path)
            assert result.name == "12345678-1234-5678-1234-567812345678_test.csv.gz"
            assert result.exists()

    def test_save_file_creates_directory(self, tmp_path):
        """Функция должна создавать директорию, если её нет."""
        content = b"test data"
        filename = "test.csv.gz"
        upload_dir = tmp_path / "subdir" / "nested"

        with patch('mko_bi.services.data_service.config') as mock_config, \
             patch('mko_bi.services.data_service.uuid') as mock_uuid:
            mock_config.upload_temp_dir = str(upload_dir)
            mock_uuid.uuid4.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')

            result = _save_uploaded_file(filename, content)

            assert upload_dir.exists()
            assert result.exists()


class TestProcessCSVFile:
    """Тесты для функции обработки CSV файла."""

    def test_process_csv_file_basic(self, tmp_path):
        """Базовая обработка CSV файла."""
        # Создаем тестовый CSV файл
        csv_content = """category,value,year
A,100,2023
B,200,2023
A,150,2024
"""
        file_path = tmp_path / "test.csv.gz"
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            f.write(csv_content)

        result = _process_csv_file(file_path)

        assert "columns" in result
        assert "rows" in result
        assert "preview" in result
        assert result["rows"] == 3
        assert "category" in result["columns"]
        assert "value" in result["columns"]

    def test_process_csv_file_with_filters(self, tmp_path):
        """Обработка CSV файла с фильтрами."""
        csv_content = """category,value,year
A,100,2023
B,200,2023
A,150,2024
"""
        file_path = tmp_path / "test.csv.gz"
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            f.write(csv_content)

        config = ProcessingConfig(
            filters=[{"field": "year", "operator": ">=", "value": 2024}]
        )

        result = _process_csv_file(file_path, config)

        assert result["processed_rows"] == 1

    def test_process_csv_file_with_groupby(self, tmp_path):
        """Обработка CSV файла с группировкой."""
        csv_content = """category,value,year
A,100,2023
B,200,2023
A,150,2024
"""
        file_path = tmp_path / "test.csv.gz"
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            f.write(csv_content)

        config = ProcessingConfig(
            groupby=["category"],
            aggregations=[{"type": "sum", "field": "value"}]
        )

        result = _process_csv_file(file_path, config)

        assert result["processed_rows"] > 0

    def test_process_csv_file_empty_config(self, tmp_path):
        """Обработка CSV файла без конфигурации."""
        csv_content = """category,value
A,100
B,200
"""
        file_path = tmp_path / "test.csv.gz"
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            f.write(csv_content)

        result = _process_csv_file(file_path)

        assert result["rows"] == 2
        assert result["processed_rows"] == 2


class TestUploadFile:
    """Тесты для функции загрузки файла."""

    def test_upload_file_success(self, db_session):
        """Успешная загрузка файла."""
        content = b"test data"

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._validate_file'), \
             patch('mko_bi.services.data_service._save_uploaded_file') as mock_save:

            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard
            mock_check_access.return_value = True
            mock_save.return_value = Path("/tmp/test.csv.gz")

            result = upload_file(
                "test.csv.gz",
                content,
                1,
                2,
                db_session
            )

            assert isinstance(result, UploadResponse)
            assert result.filename == "test.csv.gz"
            assert result.dashboard_id == 1
            assert result.status == "uploaded"
            mock_dash_repo.get.assert_called_once_with(1, db_session)
            mock_check_access.assert_called_once_with(
                user_id=2,
                dashboard_id=1,
                required_permission="edit",
                db=db_session,
            )

    def test_upload_file_dashboard_not_found(self, db_session):
        """Загрузка файла для несуществующего дашборда должна вызывать ошибку."""
        content = b"test data"

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service._validate_file'):

            mock_dash_repo.get.return_value = None

            with pytest.raises(ValueError, match="не найден"):
                upload_file("test.csv.gz", content, 999, 1, db_session)

    def test_upload_file_no_permission(self, db_session):
        """Загрузка файла без прав должна вызывать ошибку."""
        content = b"test data"

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._validate_file'):

            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard
            mock_check_access.return_value = False

            with pytest.raises(PermissionError, match="Недостаточно прав"):
                upload_file("test.csv.gz", content, 1, 2, db_session)

    def test_upload_file_invalid_file(self, db_session):
        """Загрузка некорректного файла должна вызывать ошибку."""
        content = b"x" * (100 * 1024 * 1024 + 1)

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service._validate_file',
                   side_effect=ValueError("Превышает максимальный размер")):

            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard

            with pytest.raises(ValueError, match="превышает максимальный размер"):
                upload_file("test.csv.gz", content, 1, 2, db_session)

    def test_upload_file_auto_session(self):
        """Загрузка файла с автоматическим созданием сессии."""
        content = b"test data"

        with patch('mko_bi.services.data_service.SessionLocal') as mock_session_local, \
             patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._validate_file'), \
             patch('mko_bi.services.data_service._save_uploaded_file') as mock_save:

            mock_session = MagicMock(spec=Session)
            mock_session_local.return_value = mock_session
            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard
            mock_check_access.return_value = True
            mock_save.return_value = Path("/tmp/test.csv.gz")

            result = upload_file("test.csv.gz", content, 1, 2)

            assert isinstance(result, UploadResponse)
            mock_session_local.assert_called_once()
            mock_session.close.assert_called_once()


class TestTriggerProcessing:
    """Тесты для функции запуска обработки."""

    def test_trigger_processing_success(self, db_session):
        """Успешный запуск обработки."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service._task_statuses', {}):

            # Создаем задачу
            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "filename": "test.csv.gz",
                "dashboard_id": 1,
                "status": "uploaded",
                "progress": 0,
                "message": "File uploaded",
                "uploaded_at": datetime.now(),
                "started_at": None,
                "completed_at": None,
                "file_path": "/tmp/test.csv.gz",
                "user_id": 2,
            }

            mock_check_access.return_value = True
            mock_process.return_value = {
                "columns": ["category", "value"],
                "rows": 10,
                "preview": [],
                "processed_rows": 10,
                "processed_columns": ["category", "value"],
            }

            result = trigger_processing(task_id, 1, 2, db_session=db_session)

            assert isinstance(result, ProcessingStatus)
            assert result.status == "completed"
            assert result.progress == 100
            mock_check_access.assert_called_once_with(2, 1, "edit", db_session)

    def test_trigger_processing_no_task(self, db_session):
        """Запуск обработки несуществующей задачи должен вызывать ошибку."""
        with patch('mko_bi.services.data_service.check_dashboard_access'):
            with pytest.raises(ValueError, match="не найдена"):
                trigger_processing(uuid.uuid4(), 1, 2, db_session)

    def test_trigger_processing_already_processed(self, db_session):
        """Запуск обработки уже обработанной задачи должен вызывать ошибку."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access'), \
             patch('mko_bi.services.data_service._task_statuses', {}):

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "status": "completed",
                "dashboard_id": 1,
            }

            with pytest.raises(ValueError, match="уже находится в статусе"):
                trigger_processing(task_id, 1, 2, db_session)

    def test_trigger_processing_no_permission(self, db_session):
        """Запуск обработки без прав должен вызывать ошибку."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._task_statuses', {}):

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "status": "uploaded",
                "dashboard_id": 1,
            }

            mock_check_access.return_value = False

            with pytest.raises(PermissionError, match="Недостаточно прав"):
                trigger_processing(task_id, 1, 2, db_session)

    def test_trigger_processing_file_not_found(self, db_session):
        """Запуск обработки с отсутствующим файлом должен вызывать ошибку."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._task_statuses', {}), \
             patch('mko_bi.services.data_service.Path') as mock_path:

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "status": "uploaded",
                "dashboard_id": 1,
                "file_path": "/tmp/nonexistent.csv.gz",
            }

            mock_check_access.return_value = True
            mock_path.return_value.exists.return_value = False

            with pytest.raises(FileNotFoundError):
                trigger_processing(task_id, 1, 2, db_session)

    def test_trigger_processing_auto_session(self):
        """Запуск обработки с автоматическим созданием сессии."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.SessionLocal') as mock_session_local, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service._task_statuses', {}):

            mock_session = MagicMock(spec=Session)
            mock_session_local.return_value = mock_session

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "filename": "test.csv.gz",
                "dashboard_id": 1,
                "status": "uploaded",
                "progress": 0,
                "message": "File uploaded",
                "uploaded_at": datetime.now(),
                "started_at": None,
                "completed_at": None,
                "file_path": "/tmp/test.csv.gz",
                "user_id": 2,
            }

            mock_check_access.return_value = True
            mock_process.return_value = {
                "columns": ["category", "value"],
                "rows": 10,
                "preview": [],
                "processed_rows": 10,
                "processed_columns": ["category", "value"],
            }

            result = trigger_processing(task_id, 1, 2)

            assert isinstance(result, ProcessingStatus)
            assert result.status == "completed"
            mock_session_local.assert_called_once()
            mock_session.close.assert_called_once()

    def test_trigger_processing_failure(self, db_session):
        """Обработка ошибки при обработке файла."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service._task_statuses', {}):

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "filename": "test.csv.gz",
                "dashboard_id": 1,
                "status": "uploaded",
                "progress": 0,
                "message": "File uploaded",
                "uploaded_at": datetime.now(),
                "started_at": None,
                "completed_at": None,
                "file_path": "/tmp/test.csv.gz",
                "user_id": 2,
            }

            mock_check_access.return_value = True
            mock_process.side_effect = Exception("Processing error")

            with pytest.raises(Exception, match="Processing error"):
                trigger_processing(task_id, 1, 2, db_session)

            # Проверяем, что статус изменился на failed
            assert _task_statuses[task_id]["status"] == "failed"


class TestGetProcessingStatus:
    """Тесты для функции получения статуса обработки."""

    def test_get_processing_status_success(self, db_session):
        """Успешное получение статуса."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._task_statuses', {}):

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "filename": "test.csv.gz",
                "dashboard_id": 1,
                "status": "processing",
                "progress": 50,
                "message": "Processing...",
                "uploaded_at": datetime.now(),
                "started_at": datetime.now(),
                "completed_at": None,
                "user_id": 2,
            }

            mock_check_access.return_value = True

            result = get_processing_status(task_id, 2, db_session)

            assert isinstance(result, ProcessingStatus)
            assert result.status == "processing"
            assert result.progress == 50
            mock_check_access.assert_called_once_with(
                user_id=2,
                dashboard_id=1,
                required_permission="view",
                db=db_session,
            )

    def test_get_processing_status_no_task(self, db_session):
        """Получение статуса несуществующей задачи должно вызывать ошибку."""
        with patch('mko_bi.services.data_service.check_dashboard_access'):
            with pytest.raises(ValueError, match="не найдена"):
                get_processing_status(uuid.uuid4(), 1, db_session)

    def test_get_processing_status_no_permission(self, db_session):
        """Получение статуса без прав должно вызывать ошибку."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._task_statuses', {}):

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "dashboard_id": 1,
            }

            mock_check_access.return_value = False

            with pytest.raises(PermissionError, match="Недостаточно прав"):
                get_processing_status(task_id, 2, db_session)

    def test_get_processing_status_auto_session(self):
        """Получение статуса с автоматическим созданием сессии."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.SessionLocal') as mock_session_local, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._task_statuses', {}):

            mock_session = MagicMock(spec=Session)
            mock_session_local.return_value = mock_session

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "filename": "test.csv.gz",
                "dashboard_id": 1,
                "status": "completed",
                "progress": 100,
                "message": "Done",
                "uploaded_at": datetime.now(),
                "started_at": datetime.now(),
                "completed_at": datetime.now(),
                "user_id": 2,
            }

            mock_check_access.return_value = True

            result = get_processing_status(task_id, 2)

            assert isinstance(result, ProcessingStatus)
            assert result.status == "completed"
            mock_session_local.assert_called_once()
            mock_session.close.assert_called_once()


class TestGetProcessingResult:
    """Тесты для функции получения результата обработки."""

    def test_get_processing_result_success(self, db_session):
        """Успешное получение результата."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._task_statuses', {}):

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "filename": "test.csv.gz",
                "dashboard_id": 1,
                "status": "completed",
                "progress": 100,
                "message": "Processing completed successfully",
                "uploaded_at": datetime.now(),
                "started_at": datetime.now(),
                "completed_at": datetime.now(),
                "user_id": 2,
                "result": {
                    "columns": ["category", "value"],
                    "rows": 100,
                    "preview": [],
                    "processed_rows": 100,
                    "processed_columns": ["category", "value"],
                },
            }

            mock_check_access.return_value = True

            result = get_processing_result(task_id, 2, db_session)

            assert isinstance(result, ProcessingResult)
            assert result.success is True
            assert result.rows_processed == 100
            mock_check_access.assert_called_once_with(
                user_id=2,
                dashboard_id=1,
                required_permission="view",
                db=db_session,
            )

    def test_get_processing_result_not_completed(self, db_session):
        """Получение результата для незавершенной задачи должно вызывать ошибку."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._task_statuses', {}):

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "dashboard_id": 1,
                "status": "processing",
                "user_id": 2,
            }

            mock_check_access.return_value = True

            with pytest.raises(ValueError, match="не завершена"):
                get_processing_result(task_id, 2, db_session)

    def test_get_processing_result_no_task(self, db_session):
        """Получение результата несуществующей задачи должно вызывать ошибку."""
        with patch('mko_bi.services.data_service.check_dashboard_access'):
            with pytest.raises(ValueError, match="не найдена"):
                get_processing_result(uuid.uuid4(), 1, db_session)

    def test_get_processing_result_no_permission(self, db_session):
        """Получение результата без прав должно вызывать ошибку."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._task_statuses', {}):

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "dashboard_id": 1,
                "status": "completed",
                "user_id": 2,
            }

            mock_check_access.return_value = False

            with pytest.raises(PermissionError, match="Недостаточно прав"):
                get_processing_result(task_id, 2, db_session)


class TestGetDashboardAggregates:
    """Тесты для функции получения агрегатов дашборда."""

    def test_get_dashboard_aggregates_success(self, db_session):
        """Успешное получение агрегатов."""
        dashboard_id = uuid.uuid4()
        graph_id = uuid.uuid4()



            result = get_dashboard_aggregates(dashboard_id, 1, db_session)

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], AggregatedData)
            assert result[0].dashboard_id == int(dashboard_id)

    def test_get_dashboard_aggregates_no_dashboard(self, db_session):
        """Получение агрегатов несуществующего дашборда должно вызывать ошибку."""
        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo:
            mock_dash_repo.get.return_value = None

            with pytest.raises(ValueError, match="не найден"):
                get_dashboard_aggregates(uuid.uuid4(), 1, db_session)

    def test_get_dashboard_aggregates_no_permission(self, db_session):
        """Получение агрегатов без прав должно вызывать ошибку."""
        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access:

            mock_dash_repo.get.return_value = MagicMock()
            mock_check_access.return_value = False

            with pytest.raises(PermissionError, match="нет доступа"):
                get_dashboard_aggregates(uuid.uuid4(), 1, db_session)

    def test_get_dashboard_aggregates_empty(self, db_session):
        """Получение агрегатов для дашборда без данных."""
        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service.db') as mock_db:

            mock_dash_repo.get.return_value = MagicMock()
            mock_check_access.return_value = True
            mock_db.query.return_value.filter.return_value.all.return_value = []

            result = get_dashboard_aggregates(uuid.uuid4(), 1, db_session)

            assert result == []


class TestGetChartData:
    """Тесты для функции получения данных для графиков."""

    def test_get_chart_data_success(self, db_session):
        """Успешное получение данных для графиков."""
        dashboard_id = uuid.uuid4()
        chart_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service.db') as mock_db:

            mock_dash_repo.get.return_value = MagicMock()
            mock_check_access.return_value = True

            mock_graph = MagicMock()
            mock_graph.id = chart_id
            mock_graph.type = "bar"
            mock_graph.name = "Test Chart"
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_graph]

            mock_agg = MagicMock()
            mock_agg.dims = {"x": "A"}
            mock_agg.metrics = {"y": 100}
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_agg]

            result = get_chart_data(dashboard_id, 1, [chart_id], db_session)

            assert isinstance(result, list)
            assert len(result) == 1

    def test_get_chart_data_no_chart_ids(self, db_session):
        """Получение данных для всех графиков дашборда."""
        dashboard_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service.db') as mock_db:

            mock_dash_repo.get.return_value = MagicMock()
            mock_check_access.return_value = True

            mock_graph = MagicMock()
            mock_graph.id = uuid.uuid4()
            mock_graph.type = "line"
            mock_graph.name = "Chart"
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_graph]

            mock_db.query.return_value.filter.return_value.all.return_value = []

            result = get_chart_data(dashboard_id, 1, None, db_session)

            assert isinstance(result, list)

    def test_get_chart_data_chart_not_found(self, db_session):
        """Запрос несуществующего графика должен вызывать ошибку."""
        dashboard_id = uuid.uuid4()
        chart_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access:

            mock_dash_repo.get.return_value = MagicMock()
            mock_check_access.return_value = True

            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.all.return_value = []

            with patch('mko_bi.services.data_service.db', mock_db):
                with pytest.raises(ValueError, match="не найдены"):
                    get_chart_data(dashboard_id, 1, [chart_id], db_session)


class TestApplyDataFilters:
    """Тесты для функции применения фильтров."""

    def test_apply_data_filters_success(self, db_session):
        """Успешное применение фильтров."""
        dashboard_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service.db') as mock_db:

            mock_dash_repo.get.return_value = MagicMock()
            mock_check_access.return_value = True

            mock_graph = MagicMock()
            mock_graph.id = uuid.uuid4()
            mock_graph.type = "bar"
            mock_graph.name = "Test"
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_graph]

            mock_agg = MagicMock()
            mock_agg.dims = {"year": 2023, "category": "A"}
            mock_agg.metrics = {"value": 100}
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_agg]

            filters = {"year": 2023}
            result = apply_data_filters(dashboard_id, 1, filters, db_session)

            assert isinstance(result, list)
            assert len(result) == 1

    def test_apply_data_filters_no_dashboard(self, db_session):
        """Применение фильтров к несуществующему дашборду."""
        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo:
            mock_dash_repo.get.return_value = None

            with pytest.raises(ValueError, match="не найден"):
                apply_data_filters(uuid.uuid4(), 1, {}, db_session)

    def test_apply_data_filters_no_permission(self, db_session):
        """Применение фильтров без прав доступа."""
        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access:

            mock_dash_repo.get.return_value = MagicMock()
            mock_check_access.return_value = False

            with pytest.raises(PermissionError, match="нет доступа"):
                apply_data_filters(uuid.uuid4(), 1, {}, db_session)

    def test_apply_data_filters_year_filter(self, db_session):
        """Применение фильтра по году."""
        dashboard_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service.db') as mock_db:

            mock_dash_repo.get.return_value = MagicMock()
            mock_check_access.return_value = True

            mock_graph = MagicMock()
            mock_graph.id = uuid.uuid4()
            mock_graph.type = "bar"
            mock_graph.name = "Test"
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_graph]

            mock_db.query.return_value.filter.return_value.all.return_value = []

            filters = {"year": 2023}
            result = apply_data_filters(dashboard_id, 1, filters, db_session)

            assert result == []


class TestCleanupTaskFiles:
    """Тесты для функции очистки файлов задачи."""

    def test_cleanup_task_files_success(self):
        """Успешная очистка файлов задачи."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service._task_statuses', {}), \
             patch('mko_bi.services.data_service.Path') as mock_path:

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "file_path": "/tmp/test.csv.gz",
            }

            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value = mock_file

            cleanup_task_files(task_id)

            assert task_id not in _task_statuses
            mock_file.unlink.assert_called_once()

    def test_cleanup_task_files_no_file(self):
        """Очистка задачи без файла."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service._task_statuses', {}), \
             patch('mko_bi.services.data_service.Path') as mock_path:

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
            }

            mock_file = MagicMock()
            mock_file.exists.return_value = False
            mock_path.return_value = mock_file

            cleanup_task_files(task_id)

            assert task_id not in _task_statuses
            mock_file.unlink.assert_not_called()

    def test_cleanup_task_files_error_on_delete(self):
        """Ошибка при удалении файла не должна прерывать очистку."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service._task_statuses', {}), \
             patch('mko_bi.services.data_service.Path') as mock_path, \
             patch('mko_bi.services.data_service.logger') as mock_logger:

            from mko_bi.services.data_service import _task_statuses
            _task_statuses[task_id] = {
                "task_id": task_id,
                "file_path": "/tmp/test.csv.gz",
            }

            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_file.unlink.side_effect = Exception("Delete error")
            mock_path.return_value = mock_file

            cleanup_task_files(task_id)

            assert task_id not in _task_statuses
            mock_logger.error.assert_called_once()


class TestDataServiceIntegration:
    """Интеграционные тесты для сервиса данных."""

    def test_full_data_processing_flow(self, db_session):
        """Полный цикл обработки данных."""
        content = b"category,value\nA,100\nB,200\n"

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._validate_file'), \
             patch('mko_bi.services.data_service._save_uploaded_file') as mock_save, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service.uuid') as mock_uuid:

            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard
            mock_check_access.return_value = True
            mock_uuid.uuid4.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
            mock_save.return_value = Path("/tmp/test.csv.gz")
            mock_process.return_value = {
                "columns": ["category", "value"],
                "rows": 2,
                "preview": [],
                "processed_rows": 2,
                "processed_columns": ["category", "value"],
            }

            # Загрузка файла
            upload_result = upload_file(
                "test.csv.gz",
                content,
                1,
                2,
                db_session
            )

            assert isinstance(upload_result, UploadResponse)
            assert upload_result.status == "uploaded"

            # Запуск обработки
            from mko_bi.services.data_service import _task_statuses
            task_id = list(_task_statuses.keys())[0]

            process_result = trigger_processing(task_id, 1, 2, db_session)

            assert isinstance(process_result, ProcessingStatus)
            assert process_result.status == "completed"
            assert process_result.progress == 100

            # Получение результата
            final_result = get_processing_result(task_id, 2, db_session)

            assert isinstance(final_result, ProcessingResult)
            assert final_result.success is True
            assert final_result.rows_processed == 2

    def test_data_processing_with_filters(self, db_session):
        """Обработка данных с фильтрами."""
        content = b"category,value,year\nA,100,2023\nB,200,2024\n"

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._validate_file'), \
             patch('mko_bi.services.data_service._save_uploaded_file') as mock_save, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service.uuid') as mock_uuid:

            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard
            mock_check_access.return_value = True
            mock_uuid.uuid4.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
            mock_save.return_value = Path("/tmp/test.csv.gz")
            mock_process.return_value = {
                "columns": ["category", "value", "year"],
                "rows": 1,
                "preview": [],
                "processed_rows": 1,
                "processed_columns": ["category", "value", "year"],
            }

            # Загрузка файла
            upload_file("test.csv.gz", content, 1, 2, db_session)

            # Запуск обработки с фильтром
            from mko_bi.services.data_service import _task_statuses
            task_id = list(_task_statuses.keys())[0]

            config = ProcessingConfig(
                filters=[{"field": "year", "operator": ">=", "value": 2024}]
            )

            process_result = trigger_processing(task_id, 1, 2, config, db_session)

            assert process_result.status == "completed"
            mock_process.assert_called_once()

    def test_multiple_tasks_concurrent(self, db_session):
        """Параллельная обработка нескольких задач."""
        content1 = b"category,value\nA,100\n"
        content2 = b"category,value\nB,200\n"

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._validate_file'), \
             patch('mko_bi.services.data_service._save_uploaded_file') as mock_save, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service.uuid') as mock_uuid:

            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard
            mock_check_access.return_value = True

            # Первая задача
            mock_uuid.uuid4.return_value = uuid.UUID('11111111-1111-1111-1111-111111111111')
            mock_save.return_value = Path("/tmp/test1.csv.gz")
            mock_process.return_value = {
                "columns": ["category", "value"],
                "rows": 1,
                "preview": [],
                "processed_rows": 1,
                "processed_columns": ["category", "value"],
            }

            upload_file("test1.csv.gz", content1, 1, 2, db_session)

            # Вторая задача
            mock_uuid.uuid4.return_value = uuid.UUID('22222222-2222-2222-2222-222222222222')
            mock_save.return_value = Path("/tmp/test2.csv.gz")

            upload_file("test2.csv.gz", content2, 1, 2, db_session)

            from mko_bi.services.data_service import _task_statuses

            assert len(_task_statuses) == 2

            # Обрабатываем обе задачи
            for task_id in list(_task_statuses.keys()):
                process_result = trigger_processing(task_id, 1, 2, db_session)
                assert process_result.status == "completed"

    def test_dashboard_aggregates_with_multiple_graphs(self, db_session):
        """Агрегаты для дашборда с несколькими графиками."""
        dashboard_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service.db') as mock_db:

            mock_dash_repo.get.return_value = MagicMock()
            mock_check_access.return_value = True

            # Мокаем несколько графиков
            mock_graph1 = MagicMock()
            mock_graph1.id = uuid.uuid4()
            mock_graph1.type = "bar"
            mock_graph1.name = "Graph 1"

            mock_graph2 = MagicMock()
            mock_graph2.id = uuid.uuid4()
            mock_graph2.type = "line"
            mock_graph2.name = "Graph 2"

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_graph1, mock_graph2]

            # Мокаем агрегаты
            mock_agg1 = MagicMock()
            mock_agg1.dims = {"category": "A"}
            mock_agg1.metrics = {"value": 100}

            mock_agg2 = MagicMock()
            mock_agg2.dims = {"category": "B"}
            mock_agg2.metrics = {"value": 200}

            mock_db.query.return_value.filter.return_value.all.side_effect = [
                [mock_agg1],
                [mock_agg2]
            ]

            result = get_dashboard_aggregates(dashboard_id, 1, db_session)

            assert len(result) == 2
            assert result[0].chart_type == "bar"
            assert result[1].chart_type == "line"

    def test_data_filtering_by_category(self, db_session):
        """Фильтрация данных по категории."""
        dashboard_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service.db') as mock_db:

            mock_dash_repo.get.return_value = MagicMock()
            mock_check_access.return_value = True

            mock_graph = MagicMock()
            mock_graph.id = uuid.uuid4()
            mock_graph.type = "bar"
            mock_graph.name = "Test"
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_graph]

            mock_agg = MagicMock()
            mock_agg.dims = {"category": "Electronics", "year": 2023}
            mock_agg.metrics = {"revenue": 5000}
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_agg]

            filters = {"category": "Electronics"}
            result = apply_data_filters(dashboard_id, 1, filters, db_session)

            assert len(result) == 1
            assert result[0].data[0]["dims"]["category"] == "Electronics"

    def test_chart_data_for_specific_charts(self, db_session):
        """Получение данных для конкретных графиков."""
        dashboard_id = uuid.uuid4()
        chart_ids = [uuid.uuid4(), uuid.uuid4()]

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service.db') as mock_db:

            mock_dash_repo.get.return_value = MagicMock()
            mock_check_access.return_value = True

            # Мокаем запрошенные графики
            mock_graph1 = MagicMock()
            mock_graph1.id = chart_ids[0]
            mock_graph1.type = "bar"
            mock_graph1.name = "Chart 1"

            mock_graph2 = MagicMock()
            mock_graph2.id = chart_ids[1]
            mock_graph2.type = "line"
            mock_graph2.name = "Chart 2"

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_graph1, mock_graph2]

            # Мокаем агрегаты
            mock_agg1 = MagicMock()
            mock_agg1.dims = {"x": "A"}
            mock_agg1.metrics = {"y": 100}

            mock_agg2 = MagicMock()
            mock_agg2.dims = {"x": "B"}
            mock_agg2.metrics = {"y": 200}

            mock_db.query.return_value.filter.return_value.all.side_effect = [
                [mock_agg1],
                [mock_agg2]
            ]

            result = get_chart_data(dashboard_id, 1, chart_ids, db_session)

            assert len(result) == 2
            assert result[0].chart_type == "bar"
            assert result[1].chart_type == "line"

    def test_error_handling_in_data_processing(self, db_session):
        """Обработка ошибок при обработке данных."""
        content = b"category,value\nA,100\nB,200\n"

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._validate_file'), \
             patch('mko_bi.services.data_service._save_uploaded_file') as mock_save, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service.uuid') as mock_uuid:

            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard
            mock_check_access.return_value = True
            mock_uuid.uuid4.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
            mock_save.return_value = Path("/tmp/test.csv.gz")
            mock_process.side_effect = Exception("Processing failed")

            # Загрузка файла
            upload_file("test.csv.gz", content, 1, 2, db_session)

            # Запуск обработки
            from mko_bi.services.data_service import _task_statuses
            task_id = list(_task_statuses.keys())[0]

            with pytest.raises(Exception, match="Processing failed"):
                trigger_processing(task_id, 1, 2, db_session)

            # Проверяем, что статус изменился на failed
            assert _task_statuses[task_id]["status"] == "failed"
            assert "failed" in _task_statuses[task_id]["message"].lower()

    def test_data_service_with_real_csv_content(self, db_session):
        """Тест с реальным CSV содержимым."""
        # Создаем реалистичный CSV контент
        csv_content = """date,category,brand,revenue,quantity
2023-01-01,Electronics,BrandA,1000.50,5
2023-01-02,Electronics,BrandB,1500.75,3
2023-01-03,Clothing,BrandA,500.25,10
2023-01-04,Clothing,BrandC,750.00,8
2023-01-05,Electronics,BrandA,2000.00,2
"""
        content = gzip.compress(csv_content.encode('utf-8'))

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._validate_file'), \
             patch('mko_bi.services.data_service._save_uploaded_file') as mock_save, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service.uuid') as mock_uuid:

            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard
            mock_check_access.return_value = True
            mock_uuid.uuid4.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
            mock_save.return_value = Path("/tmp/data.csv.gz")
            mock_process.return_value = {
                "columns": ["date", "category", "brand", "revenue", "quantity"],
                "rows": 5,
                "preview": [],
                "processed_rows": 5,
                "processed_columns": ["date", "category", "brand", "revenue", "quantity"],
            }

            # Загрузка файла
            upload_result = upload_file(
                "data.csv.gz",
                content,
                1,
                2,
                db_session
            )

            assert upload_result.status == "uploaded"
            assert upload_result.filename == "data.csv.gz"

            # Запуск обработки
            from mko_bi.services.data_service import _task_statuses
            task_id = list(_task_statuses.keys())[0]

            process_result = trigger_processing(task_id, 1, 2, db_session)

            assert process_result.status == "completed"
            assert process_result.progress == 100

            # Получение результата
            final_result = get_processing_result(task_id, 2, db_session)

            assert final_result.success is True
            assert final_result.rows_processed == 5
            assert final_result.data["rows"] == 5

    def test_concurrent_data_operations(self, db_session):
        """Проверка корректности при конкурентных операциях с данными."""
        contents = [
            b"category,value\nA,100\n",
            b"category,value\nB,200\n",
            b"category,value\nC,300\n",
        ]

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._validate_file'), \
             patch('mko_bi.services.data_service._save_uploaded_file') as mock_save, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service.uuid') as mock_uuid:

            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard
            mock_check_access.return_value = True
            mock_save.return_value = Path("/tmp/test.csv.gz")
            mock_process.return_value = {
                "columns": ["category", "value"],
                "rows": 1,
                "preview": [],
                "processed_rows": 1,
                "processed_columns": ["category", "value"],
            }

            # Создаем несколько задач
            task_ids = []
            for i, content in enumerate(contents):
                mock_uuid.uuid4.return_value = uuid.UUID(
                    f'{i+1:08d}-1234-5678-1234-567812345678'
                )
                upload_file(f"test{i}.csv.gz", content, 1, 2, db_session)

            from mko_bi.services.data_service import _task_statuses
            task_ids = list(_task_statuses.keys())

            assert len(task_ids) == 3

            # Обрабатываем все задачи
            for task_id in task_ids:
                process_result = trigger_processing(task_id, 1, 2, db_session)
                assert process_result.status == "completed"

            # Проверяем статусы всех задач
            for task_id in task_ids:
                status = get_processing_status(task_id, 2, db_session)
                assert status.status == "completed"
                assert status.progress == 100

    def test_data_service_cleanup(self, db_session):
        """Очистка данных после обработки."""
        content = b"category,value\nA,100\n"

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._validate_file'), \
             patch('mko_bi.services.data_service._save_uploaded_file') as mock_save, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service.uuid') as mock_uuid:

            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard
            mock_check_access.return_value = True
            mock_uuid.uuid4.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
            mock_save.return_value = Path("/tmp/test.csv.gz")
            mock_process.return_value = {
                "columns": ["category", "value"],
                "rows": 1,
                "preview": [],
                "processed_rows": 1,
                "processed_columns": ["category", "value"],
            }

            # Загрузка и обработка
            upload_file("test.csv.gz", content, 1, 2, db_session)

            from mko_bi.services.data_service import _task_statuses
            task_id = list(_task_statuses.keys())[0]

            trigger_processing(task_id, 1, 2, db_session)

            # Очистка
            cleanup_task_files(task_id)

            assert task_id not in _task_statuses

    def test_data_service_with_complex_filters(self, db_session):
        """Применение сложных фильтров к данным."""
        dashboard_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service.db') as mock_db:

            mock_dash_repo.get.return_value = MagicMock()
            mock_check_access.return_value = True

            mock_graph = MagicMock()
            mock_graph.id = uuid.uuid4()
            mock_graph.type = "bar"
            mock_graph.name = "Test"
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_graph]

            mock_agg = MagicMock()
            mock_agg.dims = {"year": 2023, "category": "A", "brand": "BrandA"}
            mock_agg.metrics = {"revenue": 1000, "quantity": 50}
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_agg]

            # Сложный фильтр
            filters = {
                "year": 2023,
                "category": "A",
                "filters": {
                    "brand": "BrandA",
                    "revenue": {"$gte": 500}
                }
            }

            result = apply_data_filters(dashboard_id, 1, filters, db_session)

            assert len(result) == 1
            assert result[0].data[0]["dims"]["year"] == 2023
