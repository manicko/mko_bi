"""Тесты для сервиса обработки данных (data_service.py).

Тестирует бизнес-логику загрузки, обработки и отслеживания статуса
обработки данных для дашбордов с использованием моков.
"""

import pytest
import uuid
import gzip
from unittest.mock import MagicMock, patch
from pathlib import Path
from sqlalchemy.orm import Session

from mko_bi.services.data_service import (
    upload_file,
    trigger_processing,
    _validate_file,
    _save_uploaded_file,
    _process_csv_file,
)
from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.models.data import (
    UploadResponse,
    ProcessingStatus,
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

        with patch('mko_bi.config.get_config') as mock_get_config, \
             patch('mko_bi.services.data_service.uuid') as mock_uuid:
            mock_config = MagicMock()
            mock_config.upload_temp_dir = str(tmp_path)
            mock_get_config.return_value = mock_config
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

        with patch('mko_bi.config.get_config') as mock_get_config, \
             patch('mko_bi.services.data_service.uuid') as mock_uuid:
            mock_config = MagicMock()
            mock_config.upload_temp_dir = str(upload_dir)
            mock_get_config.return_value = mock_config
            mock_uuid.uuid4.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')

            result = _save_uploaded_file(filename, content)

            assert upload_dir.exists()
            assert result.exists()


class TestProcessCSVFile:
    """Тесты для функции обработки CSV файла."""

    def test_process_csv_file_basic(self, tmp_path):
        """Базовая обработка CSV файла."""
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
             patch('mko_bi.services.data_service._save_uploaded_file') as mock_save, \
             patch('mko_bi.services.data_service.ProcessingLogRepository') as mock_repo:

            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard
            mock_check_access.return_value = True
            mock_save.return_value = Path("/tmp/test.csv.gz")
            mock_repo.create.return_value = MagicMock()

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

        with patch('mko_bi.services.data_service.get_session') as mock_get_session, \
             patch('mko_bi.services.data_service.DashboardRepository') as mock_dash_repo, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._validate_file'), \
             patch('mko_bi.services.data_service._save_uploaded_file') as mock_save, \
             patch('mko_bi.services.data_service.ProcessingLogRepository') as mock_repo:

            mock_session = MagicMock(spec=Session)
            mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_get_session.return_value.__exit__ = MagicMock(return_value=False)
            mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
            mock_dash_repo.get.return_value = mock_dashboard
            mock_check_access.return_value = True
            mock_save.return_value = Path("/tmp/test.csv.gz")
            mock_repo.create.return_value = MagicMock()

            result = upload_file("test.csv.gz", content, 1, 2)

            assert isinstance(result, UploadResponse)
            mock_get_session.assert_called_once()


class TestTriggerProcessing:
    """Тесты для функции запуска обработки."""

    def test_trigger_processing_success(self, db_session):
        """Успешный запуск обработки."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service.ProcessingLogRepository') as mock_repo, \
             patch('mko_bi.config.get_config') as mock_get_config:

            mock_check_access.return_value = True
            mock_process.return_value = {
                "columns": ["category", "value"],
                "rows": 10,
                "preview": [],
                "processed_rows": 10,
                "processed_columns": ["category", "value"],
            }

            mock_config = MagicMock()
            mock_config.upload_temp_dir = "/tmp"
            mock_get_config.return_value = mock_config

            # Мокаем лог обработки
            mock_log = MagicMock()
            mock_log.id = uuid.uuid4()
            mock_log.status = "uploaded"
            mock_log.dashboard_id = 1
            mock_log.message = "Файл test.csv.gz успешно загружен"
            mock_repo.get_by_dashboard_and_status.return_value = [mock_log]
            mock_repo.update.return_value = mock_log

            # Правильно мокаем Path для поиска файлов
            with patch('mko_bi.services.data_service.Path') as mock_path:
                mock_file = MagicMock()
                mock_file.exists.return_value = True
                mock_path.return_value = mock_file
                mock_path.return_value.__truediv__ = MagicMock(return_value=mock_file)
                mock_file.glob.return_value = [mock_file]

                result = trigger_processing(task_id, 1, 2, db=db_session)

            assert isinstance(result, ProcessingStatus)
            assert result.status == "completed"
            assert result.progress == 100
            mock_check_access.assert_called_once_with(
                user_id=2, dashboard_id=1, required_permission="edit", db=db_session
            )

    def test_trigger_processing_no_task(self, db_session):
        """Запуск обработки несуществующей задачи должен вызывать ошибку."""
        with patch('mko_bi.services.data_service.check_dashboard_access'), \
             patch('mko_bi.services.data_service.ProcessingLogRepository') as mock_repo:
            mock_repo.get_by_dashboard_and_status.return_value = []
            with pytest.raises(ValueError, match="не найдена"):
                trigger_processing(uuid.uuid4(), 1, 2, db=db_session)

    def test_trigger_processing_already_processed(self, db_session):
        """Запуск обработки уже обработанной задачи должен вызывать ошибку."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access'), \
             patch('mko_bi.services.data_service.ProcessingLogRepository') as mock_repo:

            mock_log = MagicMock()
            mock_log.status = "success"
            mock_log.dashboard_id = 1
            mock_repo.get_by_dashboard_and_status.return_value = [mock_log]

            with pytest.raises(ValueError, match="уже находится в статусе"):
                trigger_processing(task_id, 1, 2, db=db_session)

    def test_trigger_processing_no_permission(self, db_session):
        """Запуск обработки без прав должен вызывать ошибку."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service.ProcessingLogRepository') as mock_repo:

            mock_check_access.return_value = False

            mock_log = MagicMock()
            mock_log.status = "uploaded"
            mock_log.dashboard_id = 1
            mock_repo.get_by_dashboard_and_status.return_value = [mock_log]

            with pytest.raises(PermissionError, match="Недостаточно прав"):
                trigger_processing(task_id, 1, 2, db=db_session)

    def test_trigger_processing_file_not_found(self, db_session):
        """Запуск обработки с отсутствующим файлом должен вызывать ошибку."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service.ProcessingLogRepository') as mock_repo, \
             patch('mko_bi.config.get_config') as mock_get_config:

            mock_check_access.return_value = True

            mock_log = MagicMock()
            mock_log.status = "uploaded"
            mock_log.dashboard_id = 1
            mock_log.message = "Файл test.csv.gz успешно загружен"
            mock_repo.get_by_dashboard_and_status.return_value = [mock_log]

            mock_config = MagicMock()
            mock_config.upload_temp_dir = "/tmp"
            mock_get_config.return_value = mock_config

            # Мокаем Path - файл не существует
            with patch('mko_bi.services.data_service.Path') as mock_path:
                mock_file = MagicMock()
                mock_file.exists.return_value = False
                mock_path.return_value = mock_file
                mock_path.return_value.__truediv__ = MagicMock(return_value=mock_file)
                mock_file.glob.return_value = []  # Файлы не найдены

                with pytest.raises(FileNotFoundError):
                    trigger_processing(task_id, 1, 2, db=db_session)

    def test_trigger_processing_auto_session(self):
        """Запуск обработки с автоматическим созданием сессии."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.get_session') as mock_get_session, \
             patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service.ProcessingLogRepository') as mock_repo, \
             patch('mko_bi.config.get_config') as mock_get_config:

            mock_session = MagicMock(spec=Session)
            mock_get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_get_session.return_value.__exit__ = MagicMock(return_value=False)

            mock_check_access.return_value = True
            mock_process.return_value = {
                "columns": ["category", "value"],
                "rows": 10,
                "preview": [],
                "processed_rows": 10,
                "processed_columns": ["category", "value"],
            }

            mock_config = MagicMock()
            mock_config.upload_temp_dir = "/tmp"
            mock_get_config.return_value = mock_config

            mock_log = MagicMock()
            mock_log.id = uuid.uuid4()
            mock_log.status = "uploaded"
            mock_log.dashboard_id = 1
            mock_log.message = "Файл test.csv.gz успешно загружен"
            mock_repo.get_by_dashboard_and_status.return_value = [mock_log]
            mock_repo.update.return_value = mock_log

            # Правильно мокаем Path
            with patch('mko_bi.services.data_service.Path') as mock_path:
                mock_file = MagicMock()
                mock_file.exists.return_value = True
                mock_path.return_value = mock_file
                mock_path.return_value.__truediv__ = MagicMock(return_value=mock_file)
                mock_file.glob.return_value = [mock_file]

                result = trigger_processing(task_id, 1, 2)

            assert isinstance(result, ProcessingStatus)
            assert result.status == "completed"
            mock_get_session.assert_called_once()

    def test_trigger_processing_failure(self, db_session):
        """Обработка ошибки при обработке файла."""
        task_id = uuid.uuid4()

        with patch('mko_bi.services.data_service.check_dashboard_access') as mock_check_access, \
             patch('mko_bi.services.data_service._process_csv_file') as mock_process, \
             patch('mko_bi.services.data_service.ProcessingLogRepository') as mock_repo, \
             patch('mko_bi.config.get_config') as mock_get_config:

            mock_check_access.return_value = True
            mock_process.side_effect = Exception("Processing error")

            mock_log = MagicMock()
            mock_log.id = uuid.uuid4()
            mock_log.status = "uploaded"
            mock_log.dashboard_id = 1
            mock_log.message = "Файл test.csv.gz успешно загружен"
            mock_repo.get_by_dashboard_and_status.return_value = [mock_log]
            mock_repo.update.return_value = mock_log

            mock_config = MagicMock()
            mock_config.upload_temp_dir = "/tmp"
            mock_get_config.return_value = mock_config

            # Мокаем Path
            with patch('mko_bi.services.data_service.Path') as mock_path:
                mock_file = MagicMock()
                mock_file.exists.return_value = True
                mock_path.return_value = mock_file
                mock_path.return_value.__truediv__ = MagicMock(return_value=mock_file)
                mock_file.glob.return_value = [mock_file]

                with pytest.raises(Exception, match="Processing error"):
                    trigger_processing(task_id, 1, 2, db=db_session)
