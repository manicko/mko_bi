"""Тесты для сервиса логов обработки."""

from unittest.mock import MagicMock, patch
from uuid import UUID
from datetime import datetime

from mko_bi.services.processing_log_service import (
    create_log,
    update_log_status,
    get_log,
    get_logs,
)
from mko_bi.models.processing_logs import (
    ProcessingLogCreate,
    ProcessingLogUpdate,
    ProcessingLogRead,
)
from mko_bi.db.models.processing_logs import ProcessingLog as ProcessingLogModel


class TestCreateLog:
    """Тесты для функции create_log."""

    def test_create_log_success(self, db_session):
        """Успешное создание лога обработки."""
        log_create = ProcessingLogCreate(
            dashboard_id=UUID("12345678-1234-5678-1234-567812345678"),
            status="started",
            message="Processing started",
            started_at=datetime.now(),
        )

        with patch('mko_bi.services.processing_log_service.ProcessingLogRepository') as mock_repo:
            mock_log = MagicMock(spec=ProcessingLogModel)
            mock_log.id = UUID("87654321-4321-8765-4321-876543210987")
            mock_log.dashboard_id = log_create.dashboard_id
            mock_log.status = log_create.status
            mock_log.message = log_create.message
            mock_log.started_at = log_create.started_at
            mock_log.finished_at = None
            mock_repo.create.return_value = mock_log

            result = create_log(db_session, log_create)

            assert isinstance(result, ProcessingLogRead)
            assert result.id == mock_log.id
            assert result.dashboard_id == log_create.dashboard_id
            assert result.status == log_create.status
            assert result.message == log_create.message
            mock_repo.create.assert_called_once()

    def test_create_log_without_dashboard(self, db_session):
        """Создание лога обработки без привязки к дашборду."""
        log_create = ProcessingLogCreate(
            status="started",
            message="Processing started",
        )

        with patch('mko_bi.services.processing_log_service.ProcessingLogRepository') as mock_repo:
            mock_log = MagicMock(spec=ProcessingLogModel)
            mock_log.id = UUID("87654321-4321-8765-4321-876543210987")
            mock_log.dashboard_id = None
            mock_log.status = log_create.status
            mock_log.message = log_create.message
            mock_log.started_at = None
            mock_log.finished_at = None
            mock_repo.create.return_value = mock_log

            result = create_log(db_session, log_create)

            assert isinstance(result, ProcessingLogRead)
            assert result.dashboard_id is None
            mock_repo.create.assert_called_once()


class TestUpdateLogStatus:
    """Тесты для функции update_log_status."""

    def test_update_log_status_success(self, db_session):
        """Успешное обновление статуса лога."""
        log_id = UUID("12345678-1234-5678-1234-567812345678")
        status_update = ProcessingLogUpdate(
            status="success",
            message="Processing completed",
            finished_at=datetime.now(),
        )

        with patch('mko_bi.services.processing_log_service.ProcessingLogRepository') as mock_repo:
            mock_log = MagicMock(spec=ProcessingLogModel)
            mock_log.id = log_id
            mock_log.dashboard_id = None
            mock_log.status = "success"
            mock_log.message = "Processing completed"
            mock_log.started_at = datetime.now()
            mock_log.finished_at = status_update.finished_at
            mock_repo.update.return_value = mock_log

            result = update_log_status(db_session, log_id, status_update)

            assert isinstance(result, ProcessingLogRead)
            assert result.id == log_id
            assert result.status == "success"
            mock_repo.update.assert_called_once()

    def test_update_log_status_not_found(self, db_session):
        """Обновление несуществующего лога."""
        log_id = UUID("12345678-1234-5678-1234-567812345678")
        status_update = ProcessingLogUpdate(status="success")

        with patch('mko_bi.services.processing_log_service.ProcessingLogRepository') as mock_repo:
            mock_repo.update.return_value = None

            result = update_log_status(db_session, log_id, status_update)

            assert result is None
            mock_repo.update.assert_called_once()

    def test_update_log_status_auto_finished_at(self, db_session):
        """Автоматическое заполнение finished_at при успехе/ошибке."""
        log_id = UUID("12345678-1234-5678-1234-567812345678")
        status_update = ProcessingLogUpdate(status="success")

        with patch('mko_bi.services.processing_log_service.ProcessingLogRepository') as mock_repo, \
             patch('mko_bi.services.processing_log_service.datetime') as mock_datetime:
            mock_now = datetime(2026, 4, 28, 17, 30, 0)
            mock_datetime.now.return_value = mock_now
            
            mock_log = MagicMock(spec=ProcessingLogModel)
            mock_log.id = log_id
            mock_log.dashboard_id = None
            mock_log.status = "success"
            mock_log.message = None
            mock_log.started_at = datetime.now()
            mock_log.finished_at = mock_now
            mock_repo.update.return_value = mock_log

            result = update_log_status(db_session, log_id, status_update)

            assert result.finished_at == mock_now
            # Проверяем, что finished_at был передан в update
            call_kwargs = mock_repo.update.call_args[1]
            assert "finished_at" in call_kwargs
            assert call_kwargs["finished_at"] == mock_now


class TestGetLog:
    """Тесты для функции get_log."""

    def test_get_log_success(self, db_session):
        """Успешное получение лога."""
        log_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch('mko_bi.services.processing_log_service.ProcessingLogRepository') as mock_repo:
            mock_log = MagicMock(spec=ProcessingLogModel)
            mock_log.id = log_id
            mock_log.dashboard_id = None
            mock_log.status = "success"
            mock_log.message = "Test message"
            mock_log.started_at = datetime.now()
            mock_log.finished_at = None
            mock_repo.get.return_value = mock_log

            result = get_log(db_session, log_id)

            assert isinstance(result, ProcessingLogRead)
            assert result.id == log_id
            mock_repo.get.assert_called_once_with(db_session, log_id)

    def test_get_log_not_found(self, db_session):
        """Получение несуществующего лога."""
        log_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch('mko_bi.services.processing_log_service.ProcessingLogRepository') as mock_repo:
            mock_repo.get.return_value = None

            result = get_log(db_session, log_id)

            assert result is None
            mock_repo.get.assert_called_once_with(db_session, log_id)


class TestGetLogs:
    """Тесты для функции get_logs."""

    def test_get_logs_with_filters(self, db_session):
        """Получение логов с фильтрацией."""
        dashboard_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch('mko_bi.services.processing_log_service.ProcessingLogRepository') as mock_repo:
            mock_logs = [
                MagicMock(spec=ProcessingLogModel),
                MagicMock(spec=ProcessingLogModel),
            ]
            mock_logs[0].id = UUID("11111111-1111-1111-1111-111111111111")
            mock_logs[0].dashboard_id = dashboard_id
            mock_logs[0].status = "success"
            mock_logs[0].message = "Success message"
            mock_logs[0].started_at = datetime(2026, 4, 28, 10, 0, 0)
            mock_logs[0].finished_at = datetime(2026, 4, 28, 10, 5, 0)
            
            mock_logs[1].id = UUID("22222222-2222-2222-2222-222222222222")
            mock_logs[1].dashboard_id = dashboard_id
            mock_logs[1].status = "failed"
            mock_logs[1].message = "Failed message"
            mock_logs[1].started_at = datetime(2026, 4, 28, 11, 0, 0)
            mock_logs[1].finished_at = datetime(2026, 4, 28, 11, 1, 0)
            
            mock_repo.get_all.return_value = mock_logs

            result = get_logs(
                db_session,
                dashboard_id=dashboard_id,
                status="success",
                skip=0,
                limit=10,
            )

            assert len(result) == 1
            assert result[0].dashboard_id == dashboard_id
            assert result[0].status == "success"
            mock_repo.get_all.assert_called_once_with(db_session)

    def test_get_logs_without_filters(self, db_session):
        """Получение всех логов без фильтрации."""
        with patch('mko_bi.services.processing_log_service.ProcessingLogRepository') as mock_repo:
            mock_logs = [
                MagicMock(spec=ProcessingLogModel),
                MagicMock(spec=ProcessingLogModel),
                MagicMock(spec=ProcessingLogModel),
            ]
            for i, log in enumerate(mock_logs):
                log.id = UUID(f"{i+1:08d}-1111-1111-1111-111111111111")
                log.dashboard_id = None
                log.status = ["started", "success", "failed"][i]
                log.message = f"Message {i}"
                log.started_at = datetime(2026, 4, 28, 10+i, 0, 0)
                log.finished_at = datetime(2026, 4, 28, 10+i, 5, 0)
            
            mock_repo.get_all.return_value = mock_logs

            result = get_logs(db_session, skip=0, limit=10)

            assert len(result) == 3
            mock_repo.get_all.assert_called_once_with(db_session)
