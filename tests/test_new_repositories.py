"""Тесты для репозиториев новых моделей (FilterRepository, ProcessingConfigRepository, ProcessingLogRepository).

Тестирует CRUD операции через репозитории с использованием моков для изоляции тестов.
Все тесты проверяют бизнес-логику репозиториев, а не саму базу данных.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from mko_bi.db.repositories import filter_repo, processing_config_repo, processing_log_repo
from mko_bi.db.models import filters as filter_model
from mko_bi.db.models import processing_configs as processing_config_model
from mko_bi.db.models import processing_logs as processing_log_model
from mko_bi.db.models import dashboard as dashboard_model


class TestFilterRepository:
    """Тесты для FilterRepository."""

    def test_get_filter_success(self):
        """Тест успешного получения фильтра по ID."""
        mock_db = MagicMock(spec=Session)
        mock_filter = MagicMock(spec=filter_model.Filter)
        mock_filter.id = uuid4()
        mock_filter.name = "Test Filter"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_filter
        mock_db.execute.return_value = mock_result

        result = filter_repo.FilterRepository.get(mock_filter.id, mock_db)

        assert result == mock_filter
        mock_db.execute.assert_called_once()
        mock_result.scalar_one_or_none.assert_called_once()

    def test_get_filter_not_found(self):
        """Тест получения несуществующего фильтра."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        filter_id = uuid4()
        result = filter_repo.FilterRepository.get(filter_id, mock_db)

        assert result is None
        mock_db.execute.assert_called_once()

    def test_get_by_name_success(self):
        """Тест успешного получения фильтра по имени."""
        mock_db = MagicMock(spec=Session)
        mock_filter = MagicMock(spec=filter_model.Filter)
        mock_filter.id = uuid4()
        mock_filter.name = "Test Filter"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_filter
        mock_db.execute.return_value = mock_result

        result = filter_repo.FilterRepository.get_by_name("Test Filter", mock_db)

        assert result == mock_filter
        mock_db.execute.assert_called_once()

    def test_get_all_filters(self):
        """Тест получения всех фильтров."""
        mock_db = MagicMock(spec=Session)
        mock_filters = [
            MagicMock(spec=filter_model.Filter, id=uuid4(), name=f"Filter {i}")
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_filters
        mock_db.execute.return_value = mock_result

        result = filter_repo.FilterRepository.get_all(mock_db)

        assert result == mock_filters
        assert len(result) == 3
        mock_db.execute.assert_called_once()

    def test_create_filter_success(self):
        """Тест успешного создания фильтра."""
        mock_db = MagicMock(spec=Session)
        mock_filter = MagicMock(spec=filter_model.Filter)
        mock_filter.id = uuid4()
        mock_filter.name = "New Filter"

        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        with patch('mko_bi.db.repositories.filter_repo.filter_model.Filter', return_value=mock_filter):
            result = filter_repo.FilterRepository.create(
                mock_db,
                name="New Filter",
                type="select",
                config={"field": "year"}
            )

        assert result == mock_filter
        mock_db.add.assert_called_once_with(mock_filter)
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_filter)

    def test_create_filter_sqlalchemy_error(self):
        """Тест ошибки SQLAlchemy при создании фильтра."""
        mock_db = MagicMock(spec=Session)
        mock_filter = MagicMock(spec=filter_model.Filter)

        mock_db.add = MagicMock()
        mock_db.flush = MagicMock(side_effect=SQLAlchemyError("DB error"))

        with patch('mko_bi.db.repositories.filter_repo.filter_model.Filter', return_value=mock_filter):
            with pytest.raises(SQLAlchemyError):
                filter_repo.FilterRepository.create(
                    mock_db,
                    name="Error Filter",
                    type="select",
                    config={}
                )

        mock_db.flush.assert_called_once()

    def test_update_filter_success(self):
        """Тест успешного обновления фильтра."""
        mock_db = MagicMock(spec=Session)
        mock_filter = MagicMock(spec=filter_model.Filter)
        mock_filter.id = uuid4()
        mock_filter.name = "Old Name"
        mock_filter.type = "select"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_filter
        mock_db.execute.return_value = mock_result
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        result = filter_repo.FilterRepository.update(
            mock_filter.id, mock_db, name="New Name", type="multiselect"
        )

        assert result == mock_filter
        assert mock_filter.name == "New Name"
        assert mock_filter.type == "multiselect"
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_filter)

    def test_update_filter_not_found(self):
        """Тест обновления несуществующего фильтра."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        filter_id = uuid4()
        result = filter_repo.FilterRepository.update(filter_id, mock_db, name="New")

        assert result is None
        mock_db.commit.assert_not_called()

    def test_delete_filter_success(self):
        """Тест успешного удаления фильтра."""
        mock_db = MagicMock(spec=Session)
        mock_filter = MagicMock(spec=filter_model.Filter)
        mock_filter.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_filter
        mock_db.execute.return_value = mock_result
        mock_db.delete = MagicMock()
        mock_db.flush = MagicMock()

        result = filter_repo.FilterRepository.delete(mock_filter.id, mock_db)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_filter)
        mock_db.flush.assert_called_once()

    def test_delete_filter_not_found(self):
        """Тест удаления несуществующего фильтра."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        filter_id = uuid4()
        result = filter_repo.FilterRepository.delete(filter_id, mock_db)

        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_get_session(self):
        """Тест создания сессии."""
        with patch('mko_bi.db.repositories.filter_repo.SessionLocal') as mock_session:
            session_instance = MagicMock()
            mock_session.return_value = session_instance

            result = filter_repo.FilterRepository.get_session()

            assert result == session_instance
            mock_session.assert_called_once()


class TestProcessingConfigRepository:
    """Тесты для ProcessingConfigRepository."""

    def test_get_processing_config_success(self):
        """Тест успешного получения настроек обработки."""
        mock_db = MagicMock(spec=Session)
        mock_config = MagicMock(spec=processing_config_model.ProcessingConfig)
        mock_config.dashboard_id = uuid4()
        mock_config.settings = {"loader": "test"}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        result = processing_config_repo.ProcessingConfigRepository.get(mock_config.dashboard_id, mock_db)

        assert result == mock_config
        mock_db.execute.assert_called_once()

    def test_get_processing_config_not_found(self):
        """Тест получения несуществующих настроек обработки."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        dashboard_id = uuid4()
        result = processing_config_repo.ProcessingConfigRepository.get(dashboard_id, mock_db)

        assert result is None
        mock_db.execute.assert_called_once()

    def test_get_all_processing_configs(self):
        """Тест получения всех настроек обработки."""
        mock_db = MagicMock(spec=Session)
        mock_configs = [
            MagicMock(spec=processing_config_model.ProcessingConfig, dashboard_id=uuid4(), settings={"loader": f"loader{i}"})
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_configs
        mock_db.execute.return_value = mock_result

        result = processing_config_repo.ProcessingConfigRepository.get_all(mock_db)

        assert result == mock_configs
        assert len(result) == 3
        mock_db.execute.assert_called_once()

    def test_create_processing_config_success(self):
        """Тест успешного создания настроек обработки."""
        mock_db = MagicMock(spec=Session)
        mock_config = MagicMock(spec=processing_config_model.ProcessingConfig)
        mock_config.dashboard_id = uuid4()
        mock_config.settings = {"loader": "test"}

        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        with patch('mko_bi.db.repositories.processing_config_repo.processing_config_model.ProcessingConfig', return_value=mock_config):
            result = processing_config_repo.ProcessingConfigRepository.create(
                mock_db,
                dashboard_id=mock_config.dashboard_id,
                settings={"loader": "test"}
            )

        assert result == mock_config
        mock_db.add.assert_called_once_with(mock_config)
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_config)

    def test_create_processing_config_sqlalchemy_error(self):
        """Тест ошибки SQLAlchemy при создании настроек обработки."""
        mock_db = MagicMock(spec=Session)
        mock_config = MagicMock(spec=processing_config_model.ProcessingConfig)

        mock_db.add = MagicMock()
        mock_db.flush = MagicMock(side_effect=SQLAlchemyError("DB error"))

        with patch('mko_bi.db.repositories.processing_config_repo.processing_config_model.ProcessingConfig', return_value=mock_config):
            with pytest.raises(SQLAlchemyError):
                processing_config_repo.ProcessingConfigRepository.create(
                    mock_db,
                    dashboard_id=uuid4(),
                    settings={}
                )

        mock_db.flush.assert_called_once()

    def test_update_processing_config_success(self):
        """Тест успешного обновления настроек обработки."""
        mock_db = MagicMock(spec=Session)
        mock_config = MagicMock(spec=processing_config_model.ProcessingConfig)
        mock_config.dashboard_id = uuid4()
        mock_config.settings = {"loader": "old"}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        result = processing_config_repo.ProcessingConfigRepository.update(
            mock_config.dashboard_id, mock_db, settings={"loader": "new"}
        )

        assert result == mock_config
        assert mock_config.settings == {"loader": "new"}
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_config)

    def test_update_processing_config_not_found(self):
        """Тест обновления несуществующих настроек обработки."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        dashboard_id = uuid4()
        result = processing_config_repo.ProcessingConfigRepository.update(dashboard_id, mock_db, settings={})

        assert result is None
        mock_db.commit.assert_not_called()

    def test_delete_processing_config_success(self):
        """Тест успешного удаления настроек обработки."""
        mock_db = MagicMock(spec=Session)
        mock_config = MagicMock(spec=processing_config_model.ProcessingConfig)
        mock_config.dashboard_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result
        mock_db.delete = MagicMock()
        mock_db.flush = MagicMock()

        result = processing_config_repo.ProcessingConfigRepository.delete(mock_config.dashboard_id, mock_db)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_config)
        mock_db.flush.assert_called_once()

    def test_delete_processing_config_not_found(self):
        """Тест удаления несуществующих настроек обработки."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        dashboard_id = uuid4()
        result = processing_config_repo.ProcessingConfigRepository.delete(dashboard_id, mock_db)

        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_get_session(self):
        """Тест создания сессии."""
        with patch('mko_bi.db.repositories.processing_config_repo.SessionLocal') as mock_session:
            session_instance = MagicMock()
            mock_session.return_value = session_instance

            result = processing_config_repo.ProcessingConfigRepository.get_session()

            assert result == session_instance
            mock_session.assert_called_once()


class TestProcessingLogRepository:
    """Тесты для ProcessingLogRepository."""

    def test_get_processing_log_success(self):
        """Тест успешного получения лога обработки."""
        mock_db = MagicMock(spec=Session)
        mock_log = MagicMock(spec=processing_log_model.ProcessingLog)
        mock_log.id = uuid4()
        mock_log.status = "success"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_db.execute.return_value = mock_result

        result = processing_log_repo.ProcessingLogRepository.get(mock_log.id, mock_db)

        assert result == mock_log
        mock_db.execute.assert_called_once()

    def test_get_processing_log_not_found(self):
        """Тест получения несуществующего лога обработки."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        log_id = uuid4()
        result = processing_log_repo.ProcessingLogRepository.get(log_id, mock_db)

        assert result is None
        mock_db.execute.assert_called_once()

    def test_get_by_dashboard_success(self):
        """Тест успешного получения логов по дашборду."""
        mock_db = MagicMock(spec=Session)
        dashboard_id = uuid4()
        mock_logs = [
            MagicMock(spec=processing_log_model.ProcessingLog, id=uuid4(), status="success"),
            MagicMock(spec=processing_log_model.ProcessingLog, id=uuid4(), status="failed"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_db.execute.return_value = mock_result

        result = processing_log_repo.ProcessingLogRepository.get_by_dashboard(dashboard_id, mock_db)

        assert result == mock_logs
        assert len(result) == 2
        mock_db.execute.assert_called_once()

    def test_get_all_processing_logs(self):
        """Тест получения всех логов обработки."""
        mock_db = MagicMock(spec=Session)
        mock_logs = [
            MagicMock(spec=processing_log_model.ProcessingLog, id=uuid4(), status="success"),
            MagicMock(spec=processing_log_model.ProcessingLog, id=uuid4(), status="failed"),
            MagicMock(spec=processing_log_model.ProcessingLog, id=uuid4(), status="started"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_db.execute.return_value = mock_result

        result = processing_log_repo.ProcessingLogRepository.get_all(mock_db)

        assert result == mock_logs
        assert len(result) == 3
        mock_db.execute.assert_called_once()

    def test_create_processing_log_success(self):
        """Тест успешного создания лога обработки."""
        mock_db = MagicMock(spec=Session)
        mock_log = MagicMock(spec=processing_log_model.ProcessingLog)
        mock_log.id = uuid4()
        mock_log.status = "started"

        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        with patch('mko_bi.db.repositories.processing_log_repo.processing_log_model.ProcessingLog', return_value=mock_log):
            result = processing_log_repo.ProcessingLogRepository.create(
                mock_db,
                status="started",
                message="Processing started"
            )

        assert result == mock_log
        mock_db.add.assert_called_once_with(mock_log)
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_log)

    def test_create_processing_log_sqlalchemy_error(self):
        """Тест ошибки SQLAlchemy при создании лога обработки."""
        mock_db = MagicMock(spec=Session)
        mock_log = MagicMock(spec=processing_log_model.ProcessingLog)

        mock_db.add = MagicMock()
        mock_db.flush = MagicMock(side_effect=SQLAlchemyError("DB error"))

        with patch('mko_bi.db.repositories.processing_log_repo.processing_log_model.ProcessingLog', return_value=mock_log):
            with pytest.raises(SQLAlchemyError):
                processing_log_repo.ProcessingLogRepository.create(
                    mock_db,
                    status="error",
                    message="Test error"
                )

        mock_db.flush.assert_called_once()

    def test_update_processing_log_success(self):
        """Тест успешного обновления лога обработки."""
        mock_db = MagicMock(spec=Session)
        mock_log = MagicMock(spec=processing_log_model.ProcessingLog)
        mock_log.id = uuid4()
        mock_log.status = "started"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_db.execute.return_value = mock_result
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        result = processing_log_repo.ProcessingLogRepository.update(
            mock_log.id, mock_db, status="success", message="Completed"
        )

        assert result == mock_log
        assert mock_log.status == "success"
        assert mock_log.message == "Completed"
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_log)

    def test_update_processing_log_not_found(self):
        """Тест обновления несуществующего лога обработки."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        log_id = uuid4()
        result = processing_log_repo.ProcessingLogRepository.update(log_id, mock_db, status="success")

        assert result is None
        mock_db.flush.assert_not_called()

    def test_delete_processing_log_success(self):
        """Тест успешного удаления лога обработки."""
        mock_db = MagicMock(spec=Session)
        mock_log = MagicMock(spec=processing_log_model.ProcessingLog)
        mock_log.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_db.execute.return_value = mock_result
        mock_db.delete = MagicMock()
        mock_db.flush = MagicMock()

        result = processing_log_repo.ProcessingLogRepository.delete(mock_log.id, mock_db)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_log)
        mock_db.flush.assert_called_once()

    def test_delete_processing_log_not_found(self):
        """Тест удаления несуществующего лога обработки."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        log_id = uuid4()
        result = processing_log_repo.ProcessingLogRepository.delete(log_id, mock_db)

        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_get_session(self):
        """Тест создания сессии."""
        with patch('mko_bi.db.repositories.processing_log_repo.SessionLocal') as mock_session:
            session_instance = MagicMock()
            mock_session.return_value = session_instance

            result = processing_log_repo.ProcessingLogRepository.get_session()

            assert result == session_instance
            mock_session.assert_called_once()


class TestRepositoryIntegration:
    """Интеграционные тесты для новых репозиториев."""

    def test_filter_crud_flow(self, db_session):
        """Тест полного цикла CRUD для фильтра."""
        # Создание
        filter_obj = filter_repo.FilterRepository.create(
            db_session,
            name="Integration Filter",
            type="select",
            config={"field": "test"}
        )
        assert filter_obj.id is not None
        assert filter_obj.name == "Integration Filter"

        # Чтение
        retrieved = filter_repo.FilterRepository.get(filter_obj.id, db_session)
        assert retrieved == filter_obj

        # Обновление
        updated = filter_repo.FilterRepository.update(
            filter_obj.id, db_session, name="Updated Filter"
        )
        assert updated == filter_obj
        assert filter_obj.name == "Updated Filter"

        # Удаление
        result = filter_repo.FilterRepository.delete(filter_obj.id, db_session)
        assert result is True

    def test_processing_config_crud_flow(self, db_session):
        """Тест полного цикла CRUD для настроек обработки."""
        from mko_bi.db.models import dashboard as dashboard_model

        # Создаем дашборд
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={},
        )
        db_session.add(dashboard)
        db_session.commit()

        # Создание
        config = processing_config_repo.ProcessingConfigRepository.create(
            db_session,
            dashboard_id=dashboard.id,
            settings={"loader": "test_loader"}
        )
        assert config.dashboard_id == dashboard.id
        assert config.settings == {"loader": "test_loader"}

        # Чтение
        retrieved = processing_config_repo.ProcessingConfigRepository.get(dashboard.id, db_session)
        assert retrieved == config

        # Обновление
        updated = processing_config_repo.ProcessingConfigRepository.update(
            dashboard.id, db_session, settings={"loader": "updated_loader"}
        )
        assert updated == config
        assert config.settings == {"loader": "updated_loader"}

        # Удаление
        result = processing_config_repo.ProcessingConfigRepository.delete(dashboard.id, db_session)
        assert result is True

    def test_processing_log_crud_flow(self, db_session):
        """Тест полного цикла CRUD для лога обработки."""
        # Создание
        log = processing_log_repo.ProcessingLogRepository.create(
            db_session,
            status="started",
            message="Test log"
        )
        assert log.id is not None
        assert log.status == "started"

        # Чтение
        retrieved = processing_log_repo.ProcessingLogRepository.get(log.id, db_session)
        assert retrieved == log

        # Обновление
        updated = processing_log_repo.ProcessingLogRepository.update(
            log.id, db_session, status="success", message="Updated"
        )
        assert updated == log
        assert log.status == "success"

        # Удаление
        result = processing_log_repo.ProcessingLogRepository.delete(log.id, db_session)
        assert result is True
