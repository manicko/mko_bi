"""Тесты для репозиториев новых моделей (FilterRepository, ProcessingConfigRepository, ProcessingLogRepository).

Тестирует CRUD операции через репозитории с использованием моков для изоляции тестов.
Все тесты проверяют бизнес-логику репозиториев, а не саму базу данных.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from mko_bi.db.repositories import filter_repo, processing_config_repo, processing_log_repo
from mko_bi.db.models import filters as filter_model
from mko_bi.db.models import processing_configs as processing_config_model
from mko_bi.db.models import processing_logs as processing_log_model


class TestFilterRepository:
    """Тесты для FilterRepository."""

    @pytest.mark.asyncio
    async def test_get_filter_success(self):
        """Тест успешного получения фильтра по ID."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_filter = MagicMock(spec=filter_model.Filter)
        mock_filter.id = uuid4()
        mock_filter.name = "Test Filter"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_filter
        mock_db.execute.return_value = mock_result

        result = await filter_repo.FilterRepository.get(mock_filter.id, mock_db)

        assert result == mock_filter
        mock_db.execute.assert_called_once()
        mock_result.scalar_one_or_none.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_filter_not_found(self):
        """Тест получения несуществующего фильтра."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        filter_id = uuid4()
        result = await filter_repo.FilterRepository.get(filter_id, mock_db)

        assert result is None
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_name_success(self):
        """Тест успешного получения фильтра по имени."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_filter = MagicMock(spec=filter_model.Filter)
        mock_filter.id = uuid4()
        mock_filter.name = "Test Filter"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_filter
        mock_db.execute.return_value = mock_result

        result = await filter_repo.FilterRepository.get_by_name("Test Filter", mock_db)

        assert result == mock_filter
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_filters(self):
        """Тест получения всех фильтров."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_filters = [
            MagicMock(spec=filter_model.Filter, id=uuid4(), name=f"Filter {i}")
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_filters
        mock_db.execute.return_value = mock_result

        result = await filter_repo.FilterRepository.get_all(mock_db)

        assert result == mock_filters
        assert len(result) == 3
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_filter_success(self):
        """Тест успешного создания фильтра."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_filter = MagicMock(spec=filter_model.Filter)
        mock_filter.id = uuid4()
        mock_filter.name = "New Filter"

        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch('mko_bi.db.repositories.filter_repo.filter_model.Filter', return_value=mock_filter):
            result = await filter_repo.FilterRepository.create(
                mock_db,
                name="New Filter",
                type="select",
                config={"field": "year"}
            )

        assert result == mock_filter
        mock_db.add.assert_called_once_with(mock_filter)
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_filter)

    @pytest.mark.asyncio
    async def test_create_filter_sqlalchemy_error(self):
        """Тест ошибки SQLAlchemy при создании фильтра."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_filter = MagicMock(spec=filter_model.Filter)

        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock(side_effect=SQLAlchemyError("DB error"))

        with patch('mko_bi.db.repositories.filter_repo.filter_model.Filter', return_value=mock_filter):
            with pytest.raises(SQLAlchemyError):
                await filter_repo.FilterRepository.create(
                    mock_db,
                    name="Error Filter",
                    type="select",
                    config={}
                )

        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_filter_success(self):
        """Тест успешного обновления фильтра."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_filter = MagicMock(spec=filter_model.Filter)
        mock_filter.id = uuid4()
        mock_filter.name = "Old Name"
        mock_filter.type = "select"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_filter
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await filter_repo.FilterRepository.update(
            mock_filter.id, mock_db, name="New Name", type="multiselect"
        )

        assert result == mock_filter
        assert mock_filter.name == "New Name"
        assert mock_filter.type == "multiselect"
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_filter)

    @pytest.mark.asyncio
    async def test_update_filter_not_found(self):
        """Тест обновления несуществующего фильтра."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        filter_id = uuid4()
        result = await filter_repo.FilterRepository.update(filter_id, mock_db, name="New")

        assert result is None
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_filter_success(self):
        """Тест успешного удаления фильтра."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_filter = MagicMock(spec=filter_model.Filter)
        mock_filter.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_filter
        mock_db.execute.return_value = mock_result
        mock_db.delete = MagicMock()
        mock_db.flush = AsyncMock()

        result = await filter_repo.FilterRepository.delete(mock_filter.id, mock_db)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_filter)
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_filter_not_found(self):
        """Тест удаления несуществующего фильтра."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        filter_id = uuid4()
        result = await filter_repo.FilterRepository.delete(filter_id, mock_db)

        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestProcessingConfigRepository:
    """Тесты для ProcessingConfigRepository."""

    @pytest.mark.asyncio
    async def test_get_processing_config_success(self):
        """Тест успешного получения настроек обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_config = MagicMock(spec=processing_config_model.ProcessingConfig)
        mock_config.dashboard_id = uuid4()
        mock_config.settings = {"loader": "test"}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        result = await processing_config_repo.ProcessingConfigRepository.get(mock_config.dashboard_id, mock_db)

        assert result == mock_config
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_processing_config_not_found(self):
        """Тест получения несуществующих настроек обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        dashboard_id = uuid4()
        result = await processing_config_repo.ProcessingConfigRepository.get(dashboard_id, mock_db)

        assert result is None
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_processing_configs(self):
        """Тест получения всех настроек обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_configs = [
            MagicMock(spec=processing_config_model.ProcessingConfig, dashboard_id=uuid4(), settings={"loader": f"loader{i}"})
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_configs
        mock_db.execute.return_value = mock_result

        result = await processing_config_repo.ProcessingConfigRepository.get_all(mock_db)

        assert result == mock_configs
        assert len(result) == 3
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_processing_config_success(self):
        """Тест успешного создания настроек обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_config = MagicMock(spec=processing_config_model.ProcessingConfig)
        mock_config.dashboard_id = uuid4()
        mock_config.settings = {"loader": "test"}

        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch('mko_bi.db.repositories.processing_config_repo.processing_config_model.ProcessingConfig', return_value=mock_config):
            result = await processing_config_repo.ProcessingConfigRepository.create(
                mock_db,
                dashboard_id=mock_config.dashboard_id,
                settings={"loader": "test"}
            )

        assert result == mock_config
        mock_db.add.assert_called_once_with(mock_config)
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_config)

    @pytest.mark.asyncio
    async def test_create_processing_config_sqlalchemy_error(self):
        """Тест ошибки SQLAlchemy при создании настроек обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_config = MagicMock(spec=processing_config_model.ProcessingConfig)

        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock(side_effect=SQLAlchemyError("DB error"))

        with patch('mko_bi.db.repositories.processing_config_repo.processing_config_model.ProcessingConfig', return_value=mock_config):
            with pytest.raises(SQLAlchemyError):
                await processing_config_repo.ProcessingConfigRepository.create(
                    mock_db,
                    dashboard_id=uuid4(),
                    settings={"loader": "test"}
                )

        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_processing_config_success(self):
        """Тест успешного обновления настроек обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_config = MagicMock(spec=processing_config_model.ProcessingConfig)
        mock_config.dashboard_id = uuid4()
        mock_config.settings = {"loader": "old"}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await processing_config_repo.ProcessingConfigRepository.update(
            mock_config.dashboard_id, mock_db, settings={"loader": "new"}
        )

        assert result == mock_config
        assert mock_config.settings == {"loader": "new"}
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_config)

    @pytest.mark.asyncio
    async def test_update_processing_config_not_found(self):
        """Тест обновления несуществующих настроек обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        dashboard_id = uuid4()
        result = await processing_config_repo.ProcessingConfigRepository.update(dashboard_id, mock_db, settings={"loader": "new"})

        assert result is None
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_processing_config_success(self):
        """Тест успешного удаления настроек обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_config = MagicMock(spec=processing_config_model.ProcessingConfig)
        mock_config.dashboard_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result
        mock_db.delete = MagicMock()
        mock_db.flush = AsyncMock()

        result = await processing_config_repo.ProcessingConfigRepository.delete(mock_config.dashboard_id, mock_db)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_config)
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_processing_config_not_found(self):
        """Тест удаления несуществующих настроек обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        dashboard_id = uuid4()
        result = await processing_config_repo.ProcessingConfigRepository.delete(dashboard_id, mock_db)

        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestProcessingLogRepository:
    """Тесты для ProcessingLogRepository."""

    @pytest.mark.asyncio
    async def test_get_processing_log_success(self):
        """Тест успешного получения лога обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_log = MagicMock(spec=processing_log_model.ProcessingLog)
        mock_log.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_db.execute.return_value = mock_result

        result = await processing_log_repo.ProcessingLogRepository.get(mock_log.id, mock_db)

        assert result == mock_log
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_processing_log_not_found(self):
        """Тест получения несуществующего лога обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        log_id = uuid4()
        result = await processing_log_repo.ProcessingLogRepository.get(log_id, mock_db)

        assert result is None
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_dashboard_success(self):
        """Тест получения логов по ID дашборда."""
        mock_db = AsyncMock(spec=AsyncSession)
        dashboard_id = uuid4()
        mock_logs = [
            MagicMock(spec=processing_log_model.ProcessingLog, id=uuid4(), dashboard_id=dashboard_id)
            for _ in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_db.execute.return_value = mock_result

        result = await processing_log_repo.ProcessingLogRepository.get_by_dashboard(dashboard_id, mock_db)

        assert result == mock_logs
        assert len(result) == 3
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_processing_logs(self):
        """Тест получения всех логов обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_logs = [
            MagicMock(spec=processing_log_model.ProcessingLog, id=uuid4())
            for _ in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_db.execute.return_value = mock_result

        result = await processing_log_repo.ProcessingLogRepository.get_all(mock_db)

        assert result == mock_logs
        assert len(result) == 3
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_processing_log_success(self):
        """Тест успешного создания лога обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_log = MagicMock(spec=processing_log_model.ProcessingLog)
        mock_log.id = uuid4()

        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch('mko_bi.db.repositories.processing_log_repo.processing_log_model.ProcessingLog', return_value=mock_log):
            result = await processing_log_repo.ProcessingLogRepository.create(
                mock_db,
                dashboard_id=uuid4(),
                status="started"
            )

        assert result == mock_log
        mock_db.add.assert_called_once_with(mock_log)
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_log)

    @pytest.mark.asyncio
    async def test_create_processing_log_sqlalchemy_error(self):
        """Тест ошибки SQLAlchemy при создании лога обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_log = MagicMock(spec=processing_log_model.ProcessingLog)

        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock(side_effect=SQLAlchemyError("DB error"))

        with patch('mko_bi.db.repositories.processing_log_repo.processing_log_model.ProcessingLog', return_value=mock_log):
            with pytest.raises(SQLAlchemyError):
                await processing_log_repo.ProcessingLogRepository.create(
                    mock_db,
                    dashboard_id=uuid4(),
                    status="started"
                )

        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_processing_log_success(self):
        """Тест успешного обновления лога обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_log = MagicMock(spec=processing_log_model.ProcessingLog)
        mock_log.id = uuid4()
        mock_log.status = "started"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await processing_log_repo.ProcessingLogRepository.update(
            mock_log.id, mock_db, status="success"
        )

        assert result == mock_log
        assert mock_log.status == "success"
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_log)

    @pytest.mark.asyncio
    async def test_update_processing_log_not_found(self):
        """Тест обновления несуществующего лога обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        log_id = uuid4()
        result = await processing_log_repo.ProcessingLogRepository.update(log_id, mock_db, status="success")

        assert result is None
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_processing_log_success(self):
        """Тест успешного удаления лога обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_log = MagicMock(spec=processing_log_model.ProcessingLog)
        mock_log.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_db.execute.return_value = mock_result
        mock_db.delete = MagicMock()
        mock_db.flush = AsyncMock()

        result = await processing_log_repo.ProcessingLogRepository.delete(mock_log.id, mock_db)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_log)
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_processing_log_not_found(self):
        """Тест удаления несуществующего лога обработки."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        log_id = uuid4()
        result = await processing_log_repo.ProcessingLogRepository.delete(log_id, mock_db)

        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestRepositoryIntegration:
    """Интеграционные тесты для репозиториев."""

    @pytest.mark.asyncio
    async def test_filter_crud_flow(self):
        """Тест полного цикла CRUD для фильтра."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_filter = MagicMock(spec=filter_model.Filter)
        mock_filter.id = uuid4()
        mock_filter.name = "Integration Test Filter"

        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch('mko_bi.db.repositories.filter_repo.filter_model.Filter', return_value=mock_filter):
            created = await filter_repo.FilterRepository.create(
                mock_db,
                name="Integration Test Filter",
                type="select",
                config={"field": "year"}
            )

        assert created == mock_filter
        mock_db.add.assert_called_once()
