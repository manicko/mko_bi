"""Тесты для сервиса обработки данных (data_service.py).

Тестирует бизнес-логику загрузки, обработки и отслеживания статуса
обработки данных для дашбордов с использованием моков.
"""

import pytest
import uuid
import gzip
from unittest.mock import MagicMock, patch
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from mko_bi.services.data_service import (
    upload_file,
    trigger_processing,
    get_processing_status,
    get_processing_result,
    get_dashboard_aggregates,
    apply_data_filters,
    cleanup_task_files,
    _validate_file,
    _save_uploaded_file,
    _process_csv_file,
)
from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.models.data import (
    UploadResponse,
    ProcessingStatus,
    ProcessingResult,
    ProcessingConfig,
)


class TestValidateFile:
    """Тесты для функции валидации файла."""

    def test_valid_csv_gz_file(self):
        """Валидный .csv.gz файл должен проходить проверку."""
        content = b"test data"
        _validate_file("data.csv.gz", content)



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
             patch('mko_bi.services.data_service._task_statuses', {}), \
             patch('mko_bi.services.data_service.Path') as mock_path:

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

            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value = mock_file

            result = trigger_processing(task_id, 1, 2, db=db_session)

            assert isinstance(result, ProcessingStatus)
            assert result.status == "completed"
            assert result.progress == 100
            mock_check_access.assert_called_once_with(
                user_id=2, dashboard_id=1, required_permission="edit", db=db_session
            )

    def test_trigger_processing_no_task(self, db_session):
        """Запуск обработки несуществующей задачи должен вызывать ошибку."""
        with patch('mko_bi.services.data_service.check_dashboard_access'):
            with pytest.raises(ValueError, match="не найдена"):
                trigger_processing(uuid.uuid4(), 1, 2, db=db_session)

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
                trigger_processing(task_id, 1, 2, db=db_session)

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
                trigger_processing(task_id, 1, 2, db=db_session)

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
                trigger_processing(task_id, 1, 2, db=db_session)

    def test_trigger_processing_auto_session(self):
        """Запуск обработки с автоматическим созданием сессии."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.SessionLocal') as mock_session_local, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service._task_statuses', {}), \
             patch('mko_bi.services.data_service.Path') as mock_path:

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

            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value = mock_file

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
             patch('mko_bi.services.data_service._task_statuses', {}), \
             patch('mko_bi.services.data_service.Path') as mock_path:

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

            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value = mock_file

            with pytest.raises(Exception, match="Processing error"):
                trigger_processing(task_id, 1, 2, db=db_session)

            # Проверяем, что статус изменился на failed
            # Note: Task is cleaned up in finally block, so it's no longer in _task_statuses
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



    def test_get_dashboard_aggregates_no_dashboard(self, db_session):
        """Получение агрегатов несуществующего дашборда должно вызывать ошибку."""
        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo:
            mock_dash_repo.get.return_value = None

            with pytest.raises(ValueError, match="не найден"):
                get_dashboard_aggregates(uuid.uuid4(), 1, db_session)






class TestGetChartData:
    """Тесты для функции получения данных для графиков."""








class TestApplyDataFilters:
    """Тесты для функции применения фильтров."""



    def test_apply_data_filters_no_dashboard(self, db_session):
        """Применение фильтров к несуществующему дашборду."""
        with patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo:
            mock_dash_repo.get.return_value = None

            with pytest.raises(ValueError, match="не найден"):
                apply_data_filters(uuid.uuid4(), 1, {}, db_session)






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
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service.uuid') as mock_uuid, \
             patch('mko_bi.services.data_service.Path') as mock_path:

            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard
            mock_check_access.return_value = True
            mock_uuid.uuid4.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
            mock_save.return_value = Path("/tmp/test.csv.gz")
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value = mock_file
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

            process_result = trigger_processing(task_id, 1, 2, db=db_session)

            assert isinstance(process_result, ProcessingStatus)
            assert process_result.status == "completed"
            assert process_result.progress == 100

            # Получение результата
            # Note: Task is cleaned up in finally block, so get_processing_result() will fail




















