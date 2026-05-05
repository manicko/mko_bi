"""Тесты для новых моделей SQLAlchemy (Filter, ProcessingConfig, ProcessingLog).

Тестирует создание, чтение, обновление и удаление новых моделей,
а также проверки ограничений, связей и каскадного удаления.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from mko_bi.db.models import filters as filter_model
from mko_bi.db.models import processing_configs as processing_config_model
from mko_bi.db.models import processing_logs as processing_log_model
from mko_bi.db.models import dashboard as dashboard_model


class TestFilterModel:
    """Тесты для модели Filter."""

    async def test_create_filter(self, async_db_session):
        """Создание фильтра с валидными данными."""
        filter_obj = filter_model.Filter(
            name="Year Filter",
            type="select",
            config={"field": "year", "source": "dims", "multi": False},
        )
        async_db_session.add(filter_obj)
        await async_db_session.commit()
        await async_db_session.refresh(filter_obj)

        assert filter_obj.id is not None
        assert isinstance(filter_obj.id, UUID)
        assert filter_obj.name == "Year Filter"
        assert filter_obj.type == "select"
        assert filter_obj.config == {"field": "year", "source": "dims", "multi": False}

    async def test_create_filter_with_defaults(self, async_db_session):
        """Создание фильтра со значениями по умолчанию."""
        filter_obj = filter_model.Filter(
            name="Category Filter",
            type="multiselect",
            config={},
        )
        async_db_session.add(filter_obj)
        await async_db_session.commit()

        assert filter_obj.config == {}
        assert filter_obj.created_at is not None

    async def test_unique_name_constraint(self, async_db_session):
        """Проверка уникальности имени фильтра."""
        filter1 = filter_model.Filter(
            name="Same Name",
            type="select",
            config={},
        )
        async_db_session.add(filter1)
        await async_db_session.commit()

        filter2 = filter_model.Filter(
            name="Same Name",
            type="multiselect",
            config={},
        )
        async_db_session.add(filter2)

        with pytest.raises(IntegrityError):
            await async_db_session.commit()

        await async_db_session.rollback()

    async def test_filter_type_values(self, async_db_session):
        """Проверка допустимых значений типа фильтра."""
        for filter_type in ["select", "multiselect", "range", "date"]:
            filter_obj = filter_model.Filter(
                name=f"{filter_type} Filter",
                type=filter_type,
                config={},
            )
            async_db_session.add(filter_obj)
        await async_db_session.commit()

        result = await async_db_session.execute(select(filter_model.Filter))
        filters = result.scalars().all()
        assert len(filters) == 4

    # Note: Removed low-value string representation tests (__repr__, __str__)
    # These tests have low diagnostic value and are fragile to changes

    async def test_filter_dashboards_relationship(self, async_db_session):
        """Проверка связи фильтра с дашбордами."""
        filter_obj = filter_model.Filter(
            name="Dashboard Filter",
            type="select",
            config={},
        )
        async_db_session.add(filter_obj)

        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()
        await async_db_session.refresh(filter_obj)
        await async_db_session.refresh(dashboard)

        # Добавляем связь через промежуточную таблицу
        dashboard.filters.append(filter_obj)
        await async_db_session.commit()

        # Проверяем, что у фильтра есть дашборд
        result = await async_db_session.execute(
            select(filter_model.Filter).where(
                filter_model.Filter.id == filter_obj.id
            )
        )
        filters = result.scalar_one()
        assert len(filters.dashboards) == 1
        assert filters.dashboards[0].name == "Test Dashboard"


class TestProcessingConfigModel:
    """Тесты для модели ProcessingConfig."""

    async def test_create_processing_config(self, async_db_session):
        """Создание настроек обработки с валидными данными."""
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        config = processing_config_model.ProcessingConfig(
            dashboard_id=dashboard.id,
            settings={
                "loader": "sales_loader",
                "date_column": "event_date",
                "timezone": "UTC",
            },
        )
        async_db_session.add(config)
        await async_db_session.commit()
        await async_db_session.refresh(config)

        assert config.dashboard_id == dashboard.id
        assert config.settings == {
            "loader": "sales_loader",
            "date_column": "event_date",
            "timezone": "UTC",
        }
        assert config.updated_at is not None

    async def test_create_processing_config_with_defaults(self, async_db_session):
        """Создание настроек обработки со значениями по умолчанию."""
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        config = processing_config_model.ProcessingConfig(
            dashboard_id=dashboard.id,
            settings={},
        )
        async_db_session.add(config)
        await async_db_session.commit()

        assert config.settings == {}
        assert config.updated_at is not None

    async def test_unique_dashboard_id_constraint(self, async_db_session):
        """Проверка уникальности dashboard_id (один-к-одному)."""
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        config1 = processing_config_model.ProcessingConfig(
            dashboard_id=dashboard.id,
            settings={"loader": "loader1"},
        )
        async_db_session.add(config1)
        await async_db_session.commit()

        config2 = processing_config_model.ProcessingConfig(
            dashboard_id=dashboard.id,
            settings={"loader": "loader2"},
        )
        async_db_session.add(config2)

        with pytest.raises(IntegrityError):
            await async_db_session.commit()

        await async_db_session.rollback()

    async def test_processing_config_dashboard_relationship(self, async_db_session):
        """Проверка связи настроек обработки с дашбордом."""
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        config = processing_config_model.ProcessingConfig(
            dashboard_id=dashboard.id,
            settings={"loader": "sales_loader"},
        )
        async_db_session.add(config)
        await async_db_session.commit()
        await async_db_session.refresh(dashboard)

        assert dashboard.processing_config is not None
        assert dashboard.processing_config.settings == {"loader": "sales_loader"}

    # Note: Removed low-value string representation tests (__repr__, __str__)
    # These tests have low diagnostic value and are fragile to changes

    async def test_cascade_delete_dashboard(self, async_db_session):
        """Проверка каскадного удаления настроек при удалении дашборда."""
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        config = processing_config_model.ProcessingConfig(
            dashboard_id=dashboard.id,
            settings={"loader": "sales_loader"},
        )
        async_db_session.add(config)
        await async_db_session.commit()

        # Удаляем дашборд
        await async_db_session.delete(dashboard)
        await async_db_session.commit()
        
        # Проверяем, что настройки тоже удалены
        result = await async_db_session.execute(
            select(processing_config_model.ProcessingConfig)
        )
        result = result.fetchall()
        assert len(result) == 0


class TestProcessingLogModel:
    """Тесты для модели ProcessingLog."""

    async def test_create_processing_log(self, async_db_session):
        """Создание лога обработки с валидными данными."""
        log = processing_log_model.ProcessingLog(
            status="started",
            message="Processing started",
        )
        async_db_session.add(log)
        await async_db_session.commit()
        await async_db_session.refresh(log)

        assert log.id is not None
        assert isinstance(log.id, UUID)
        assert log.status == "started"
        assert log.message == "Processing started"
        assert log.dashboard_id is None
        assert log.started_at is None
        assert log.finished_at is None

    async def test_create_processing_log_with_dashboard(self, async_db_session):
        """Создание лога обработки с привязкой к дашборду."""
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        log = processing_log_model.ProcessingLog(
            dashboard_id=dashboard.id,
            status="success",
            message="Processing completed",
            started_at=datetime.now(),
            finished_at=datetime.now(),
        )
        async_db_session.add(log)
        await async_db_session.commit()
        await async_db_session.refresh(log)

        assert log.dashboard_id == dashboard.id
        assert log.status == "success"
        assert log.started_at is not None
        assert log.finished_at is not None

    async def test_create_processing_log_with_defaults(self, async_db_session):
        """Создание лога обработки со значениями по умолчанию."""
        log = processing_log_model.ProcessingLog(
            status="started",
        )
        async_db_session.add(log)
        await async_db_session.commit()

        assert log.message is None
        assert log.dashboard_id is None

    async def test_processing_log_status_values(self, async_db_session):
        """Проверка допустимых значений статуса."""
        for status in ["started", "success", "failed"]:
            log = processing_log_model.ProcessingLog(
                status=status,
            )
            async_db_session.add(log)
        await async_db_session.commit()

        result = await async_db_session.execute(
            select(processing_log_model.ProcessingLog)
        )
        logs = result.scalars().all()
        assert len(logs) == 3

    async def test_processing_log_dashboard_relationship(self, async_db_session):
        """Проверка связи лога обработки с дашбордом."""
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()

        log = processing_log_model.ProcessingLog(
            dashboard_id=dashboard.id,
            status="success",
            message="Processing completed",
        )
        async_db_session.add(log)
        await async_db_session.commit()
        await async_db_session.refresh(dashboard)

        assert len(dashboard.processing_logs) == 1
        assert dashboard.processing_logs[0].status == "success"

    # Note: Removed low-value string representation tests (__repr__, __str__)
    # These tests have low diagnostic value and are fragile to changes

class TestModelRelationships:
    """Тесты для связей между новыми моделями и существующими."""

    async def test_dashboard_with_all_relationships(self, async_db_session):
        """Тест дашборда со всеми типами связей."""
        dashboard = dashboard_model.Dashboard(
            name="Full Dashboard",
            config={},
        )
        async_db_session.add(dashboard)
        await async_db_session.commit()
        await async_db_session.refresh(dashboard)

        # Добавляем фильтр
        filter_obj = filter_model.Filter(
            name="Test Filter",
            type="select",
            config={},
        )
        async_db_session.add(filter_obj)
        await async_db_session.commit()
        await async_db_session.refresh(filter_obj)

        dashboard.filters.append(filter_obj)

        # Добавляем настройки обработки
        config = processing_config_model.ProcessingConfig(
            dashboard_id=dashboard.id,
            settings={"loader": "test"},
        )
        async_db_session.add(config)

        # Добавляем лог обработки
        log = processing_log_model.ProcessingLog(
            dashboard_id=dashboard.id,
            status="success",
            message="Test",
        )
        async_db_session.add(log)

        await async_db_session.commit()
        await async_db_session.refresh(dashboard)

        # Проверяем все связи
        assert len(dashboard.filters) == 1
        assert dashboard.filters[0].name == "Test Filter"
        assert dashboard.processing_config is not None
        assert dashboard.processing_config.settings == {"loader": "test"}
        assert len(dashboard.processing_logs) == 1
        assert dashboard.processing_logs[0].status == "success"
