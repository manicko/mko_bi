"""Тесты для менеджера хранения агрегированных данных.

Тестирует класс StorageManager для сохранения агрегированных данных
в PostgreSQL с поддержкой пакетных вставок, транзакций и очистки данных.
"""

import pytest
from uuid import uuid4

from mko_bi.data.storage.manager import StorageManager
from mko_bi.db.models import graphs as graphs_model
from mko_bi.db.models import aggregated_data as aggregated_data_model


class TestStorageManagerInit:
    """Тесты для инициализации StorageManager."""

    def test_init_with_db_session(self, db_session):
        """Тест инициализации с сессией базы данных."""
        manager = StorageManager(db_session)
        assert manager.db == db_session

    def test_init_stores_db_reference(self, db_session):
        """Тест сохранения ссылки на сессию базы данных."""
        manager = StorageManager(db_session)
        assert hasattr(manager, 'db')
        assert manager.db is db_session


class TestSaveAggregates:
    """Тесты для метода save_aggregates."""

    def test_save_single_aggregate(self, db_session):
        """Тест сохранения одного агрегата."""
        # Создаем дашборд и график
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Test Graph",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        db_session.add(graph)
        db_session.commit()
        db_session.refresh(graph)

        # Создаем StorageManager и сохраняем агрегат
        manager = StorageManager(db_session)
        aggregates = [
            {
                "graph_id": graph.id,
                "dims": {"category": "A"},
                "metrics": {"revenue": 1000},
            }
        ]

        saved = manager.save_aggregates(dashboard.id, aggregates, clear_old=True)
        assert saved == 1

    def test_save_multiple_aggregates(self, db_session):
        """Тест сохранения нескольких агрегатов."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Test Graph",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        db_session.add(graph)
        db_session.commit()
        db_session.refresh(graph)

        manager = StorageManager(db_session)
        aggregates = [
            {
                "graph_id": graph.id,
                "dims": {"category": "A"},
                "metrics": {"revenue": 1000},
            },
            {
                "graph_id": graph.id,
                "dims": {"category": "B"},
                "metrics": {"revenue": 2000},
            },
            {
                "graph_id": graph.id,
                "dims": {"category": "C"},
                "metrics": {"revenue": 3000},
            },
        ]

        saved = manager.save_aggregates(dashboard.id, aggregates, clear_old=True)
        assert saved == 3

    def test_save_aggregates_multiple_graphs(self, db_session):
        """Тест сохранения агрегатов для нескольких графиков."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar", "line"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph1 = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Graph 1",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        graph2 = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Graph 2",
            type="line",
            config={},
            dimensions=["year"],
            metrics=["sales"],
        )
        db_session.add_all([graph1, graph2])
        db_session.commit()
        db_session.refresh(graph1)
        db_session.refresh(graph2)

        manager = StorageManager(db_session)
        aggregates = [
            {
                "graph_id": graph1.id,
                "dims": {"category": "A"},
                "metrics": {"revenue": 1000},
            },
            {
                "graph_id": graph2.id,
                "dims": {"year": 2023},
                "metrics": {"sales": 5000},
            },
        ]

        saved = manager.save_aggregates(dashboard.id, aggregates, clear_old=True)
        assert saved == 2

    def test_save_empty_aggregates(self, db_session):
        """Тест сохранения пустого списка агрегатов."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()

        manager = StorageManager(db_session)
        saved = manager.save_aggregates(dashboard.id, [], clear_old=True)
        assert saved == 0

    def test_save_aggregates_with_clear_old(self, db_session):
        """Тест сохранения с очисткой старых данных."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Test Graph",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        db_session.add(graph)
        db_session.commit()
        db_session.refresh(graph)

        manager = StorageManager(db_session)

        # Сохраняем первые данные
        aggregates1 = [
            {
                "graph_id": graph.id,
                "dims": {"category": "A"},
                "metrics": {"revenue": 1000},
            }
        ]
        saved1 = manager.save_aggregates(dashboard.id, aggregates1, clear_old=True)
        assert saved1 == 1

        # Проверяем, что данные сохранены
        query = db_session.query(aggregated_data_model.AggregatedData).filter(
            aggregated_data_model.AggregatedData.dashboard_id == dashboard.id
        )
        assert query.count() == 1

        # Сохраняем новые данные с очисткой старых
        aggregates2 = [
            {
                "graph_id": graph.id,
                "dims": {"category": "B"},
                "metrics": {"revenue": 2000},
            }
        ]
        saved2 = manager.save_aggregates(dashboard.id, aggregates2, clear_old=True)
        assert saved2 == 1

        # Проверяем, что старые данные удалены, а новые добавлены
        assert query.count() == 1
        agg = query.first()
        assert agg.dims == {"category": "B"}
        assert agg.metrics == {"revenue": 2000}

    def test_save_aggregates_without_clear_old(self, db_session):
        """Тест сохранения без очистки старых данных."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Test Graph",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        db_session.add(graph)
        db_session.commit()
        db_session.refresh(graph)

        manager = StorageManager(db_session)

        # Сохраняем первые данные
        aggregates1 = [
            {
                "graph_id": graph.id,
                "dims": {"category": "A"},
                "metrics": {"revenue": 1000},
            }
        ]
        saved1 = manager.save_aggregates(dashboard.id, aggregates1, clear_old=False)
        assert saved1 == 1

        # Сохраняем новые данные без очистки
        aggregates2 = [
            {
                "graph_id": graph.id,
                "dims": {"category": "B"},
                "metrics": {"revenue": 2000},
            }
        ]
        saved2 = manager.save_aggregates(dashboard.id, aggregates2, clear_old=False)
        assert saved2 == 1

        # Проверяем, что обе записи сохранены
        query = db_session.query(aggregated_data_model.AggregatedData).filter(
            aggregated_data_model.AggregatedData.dashboard_id == dashboard.id
        )
        assert query.count() == 2

    def test_save_aggregates_upsert(self, db_session):
        """Тест обновления существующих данных (upsert)."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Test Graph",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        db_session.add(graph)
        db_session.commit()
        db_session.refresh(graph)

        manager = StorageManager(db_session)

        # Сохраняем первые данные
        aggregates1 = [
            {
                "graph_id": graph.id,
                "dims": {"category": "A"},
                "metrics": {"revenue": 1000},
            }
        ]
        saved1 = manager.save_aggregates(dashboard.id, aggregates1, clear_old=True)
        assert saved1 == 1

        # Обновляем те же данные (такие же dims)
        aggregates2 = [
            {
                "graph_id": graph.id,
                "dims": {"category": "A"},
                "metrics": {"revenue": 1500},  # Изменили метрику
            }
        ]
        saved2 = manager.save_aggregates(dashboard.id, aggregates2, clear_old=False)
        assert saved2 == 1

        # Проверяем, что данные обновлены
        query = db_session.query(aggregated_data_model.AggregatedData).filter(
            aggregated_data_model.AggregatedData.dashboard_id == dashboard.id
        )
        assert query.count() == 1
        agg = query.first()
        assert agg.dims == {"category": "A"}
        assert agg.metrics == {"revenue": 1500}

    def test_save_aggregates_invalid_data(self, db_session):
        """Тест сохранения с невалидными данными."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()

        manager = StorageManager(db_session)
        aggregates = [
            {
                "graph_id": uuid4(),
                "dims": "not a dict",  # Неверный тип
                "metrics": {"revenue": 1000},
            }
        ]

        with pytest.raises(ValueError, match="dims должен быть словарем"):
            manager.save_aggregates(dashboard.id, aggregates, clear_old=True)

    def test_save_aggregates_missing_fields(self, db_session):
        """Тест сохранения с отсутствующими обязательными полями."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()

        manager = StorageManager(db_session)
        aggregates = [
            {
                "graph_id": uuid4(),
                # Отсутствует dims
                "metrics": {"revenue": 1000},
            }
        ]

        with pytest.raises(ValueError, match="не содержит обязательное поле"):
            manager.save_aggregates(dashboard.id, aggregates, clear_old=True)

    def test_save_aggregates_nonexistent_graph(self, db_session):
        """Тест сохранения для несуществующего графика."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        manager = StorageManager(db_session)
        aggregates = [
            {
                "graph_id": uuid4(),  # Несуществующий график
                "dims": {"category": "A"},
                "metrics": {"revenue": 1000},
            }
        ]

        with pytest.raises(ValueError, match="Графики не найдены"):
            manager.save_aggregates(dashboard.id, aggregates, clear_old=True)


class TestUpsertAggregate:
    """Тесты для метода upsert_aggregate."""

    def test_upsert_new_aggregate(self, db_session):
        """Тест вставки нового агрегата."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Test Graph",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        db_session.add(graph)
        db_session.commit()
        db_session.refresh(graph)

        manager = StorageManager(db_session)
        manager.upsert_aggregate(
            dashboard_id=dashboard.id,
            graph_id=graph.id,
            dims={"category": "A"},
            metrics={"revenue": 1000},
        )

        # Проверяем, что запись была вставлена
        query = db_session.query(aggregated_data_model.AggregatedData).filter(
            aggregated_data_model.AggregatedData.dashboard_id == dashboard.id
        )
        assert query.count() == 1
        agg = query.first()
        assert agg.dims == {"category": "A"}
        assert agg.metrics == {"revenue": 1000}

    def test_upsert_existing_aggregate(self, db_session):
        """Тест обновления существующего агрегата."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Test Graph",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        db_session.add(graph)
        db_session.commit()
        db_session.refresh(graph)

        manager = StorageManager(db_session)

        # Вставляем первую запись
        manager.upsert_aggregate(
            dashboard_id=dashboard.id,
            graph_id=graph.id,
            dims={"category": "A"},
            metrics={"revenue": 1000},
        )

        # Обновляем ту же запись
        manager.upsert_aggregate(
            dashboard_id=dashboard.id,
            graph_id=graph.id,
            dims={"category": "A"},
            metrics={"revenue": 1500},  # Изменили метрику
        )

        # Проверяем, что данные обновлены
        query = db_session.query(aggregated_data_model.AggregatedData).filter(
            aggregated_data_model.AggregatedData.dashboard_id == dashboard.id
        )
        assert query.count() == 1
        agg = query.first()
        assert agg.metrics == {"revenue": 1500}

    def test_upsert_invalid_data(self, db_session):
        """Тест upsert с невалидными данными."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Test Graph",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        db_session.add(graph)
        db_session.commit()
        db_session.refresh(graph)

        manager = StorageManager(db_session)

        with pytest.raises(ValueError, match="dims и metrics должны быть словарями"):
            manager.upsert_aggregate(
                dashboard_id=dashboard.id,
                graph_id=graph.id,
                dims="not a dict",
                metrics={"revenue": 1000},
            )

    def test_upsert_nonexistent_graph(self, db_session):
        """Тест upsert для несуществующего графика."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        manager = StorageManager(db_session)

        with pytest.raises(ValueError, match="Графики не найдены"):
            manager.upsert_aggregate(
                dashboard_id=dashboard.id,
                graph_id=uuid4(),
                dims={"category": "A"},
                metrics={"revenue": 1000},
            )


class TestClearData:
    """Тесты для методов очистки данных."""

    def test_clear_dashboard_data(self, db_session):
        """Тест очистки всех данных дашборда."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Test Graph",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        db_session.add(graph)
        db_session.commit()
        db_session.refresh(graph)

        manager = StorageManager(db_session)

        # Добавляем данные
        aggregates = [
            {
                "graph_id": graph.id,
                "dims": {"category": "A"},
                "metrics": {"revenue": 1000},
            },
            {
                "graph_id": graph.id,
                "dims": {"category": "B"},
                "metrics": {"revenue": 2000},
            },
        ]
        manager.save_aggregates(dashboard.id, aggregates, clear_old=True)

        # Проверяем, что данные есть
        query = db_session.query(aggregated_data_model.AggregatedData).filter(
            aggregated_data_model.AggregatedData.dashboard_id == dashboard.id
        )
        assert query.count() == 2

        # Очищаем данные
        deleted = manager.clear_dashboard_data(dashboard.id)
        assert deleted == 2

        # Проверяем, что данных больше нет
        assert query.count() == 0

    def test_clear_graph_data(self, db_session):
        """Тест очистки данных конкретного графика."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar", "line"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph1 = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Graph 1",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        graph2 = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Graph 2",
            type="line",
            config={},
            dimensions=["year"],
            metrics=["sales"],
        )
        db_session.add_all([graph1, graph2])
        db_session.commit()
        db_session.refresh(graph1)
        db_session.refresh(graph2)

        manager = StorageManager(db_session)

        # Добавляем данные для обоих графиков
        aggregates = [
            {
                "graph_id": graph1.id,
                "dims": {"category": "A"},
                "metrics": {"revenue": 1000},
            },
            {
                "graph_id": graph2.id,
                "dims": {"year": 2023},
                "metrics": {"sales": 5000},
            },
        ]
        manager.save_aggregates(dashboard.id, aggregates, clear_old=True)

        # Проверяем, что данные есть
        query = db_session.query(aggregated_data_model.AggregatedData).filter(
            aggregated_data_model.AggregatedData.dashboard_id == dashboard.id
        )
        assert query.count() == 2

        # Очищаем данные только для graph1
        deleted = manager.clear_graph_data(dashboard.id, graph1.id)
        assert deleted == 1

        # Проверяем, что остались только данные для graph2
        assert query.count() == 1
        agg = query.first()
        assert agg.graph_id == graph2.id

    def test_clear_nonexistent_data(self, db_session):
        """Тест очистки данных для дашборда без данных."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        manager = StorageManager(db_session)
        deleted = manager.clear_dashboard_data(dashboard.id)
        assert deleted == 0


class TestGetAggregates:
    """Тесты для метода get_aggregates."""

    def test_get_all_aggregates(self, db_session):
        """Тест получения всех агрегатов дашборда."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Test Graph",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        db_session.add(graph)
        db_session.commit()
        db_session.refresh(graph)

        manager = StorageManager(db_session)

        # Добавляем данные
        aggregates = [
            {
                "graph_id": graph.id,
                "dims": {"category": "A"},
                "metrics": {"revenue": 1000},
            },
            {
                "graph_id": graph.id,
                "dims": {"category": "B"},
                "metrics": {"revenue": 2000},
            },
        ]
        manager.save_aggregates(dashboard.id, aggregates, clear_old=True)

        # Получаем агрегаты
        result = manager.get_aggregates(dashboard.id)
        assert len(result) == 2

        # Проверяем данные
        categories = {agg["dims"]["category"] for agg in result}
        assert categories == {"A", "B"}

    def test_get_aggregates_for_graph(self, db_session):
        """Тест получения агрегатов для конкретного графика."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar", "line"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph1 = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Graph 1",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        graph2 = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Graph 2",
            type="line",
            config={},
            dimensions=["year"],
            metrics=["sales"],
        )
        db_session.add_all([graph1, graph2])
        db_session.commit()
        db_session.refresh(graph1)
        db_session.refresh(graph2)

        manager = StorageManager(db_session)

        # Добавляем данные для обоих графиков
        aggregates = [
            {
                "graph_id": graph1.id,
                "dims": {"category": "A"},
                "metrics": {"revenue": 1000},
            },
            {
                "graph_id": graph2.id,
                "dims": {"year": 2023},
                "metrics": {"sales": 5000},
            },
        ]
        manager.save_aggregates(dashboard.id, aggregates, clear_old=True)

        # Получаем агрегаты только для graph1
        result = manager.get_aggregates(dashboard.id, graph1.id)
        assert len(result) == 1
        assert result[0]["graph_id"] == graph1.id
        assert result[0]["dims"] == {"category": "A"}

    def test_get_aggregates_empty(self, db_session):
        """Тест получения агрегатов для пустого дашборда."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        manager = StorageManager(db_session)
        result = manager.get_aggregates(dashboard.id)
        assert result == []


class TestStorageManagerIntegration:
    """Интеграционные тесты для StorageManager."""

    def test_full_save_and_retrieve_flow(self, db_session):
        """Тест полного цикла: сохранение и получение данных."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        # Создаем дашборд и графики
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar", "line"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph1 = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Sales by Category",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        graph2 = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Sales by Year",
            type="line",
            config={},
            dimensions=["year"],
            metrics=["sales"],
        )
        db_session.add_all([graph1, graph2])
        db_session.commit()
        db_session.refresh(graph1)
        db_session.refresh(graph2)

        manager = StorageManager(db_session)

        # Сохраняем агрегированные данные
        aggregates = [
            {
                "graph_id": graph1.id,
                "dims": {"category": "Electronics"},
                "metrics": {"revenue": 100000, "count": 50},
            },
            {
                "graph_id": graph1.id,
                "dims": {"category": "Clothing"},
                "metrics": {"revenue": 75000, "count": 120},
            },
            {
                "graph_id": graph2.id,
                "dims": {"year": 2023},
                "metrics": {"sales": 500000, "growth": 10.5},
            },
            {
                "graph_id": graph2.id,
                "dims": {"year": 2024},
                "metrics": {"sales": 600000, "growth": 20.0},
            },
        ]

        saved = manager.save_aggregates(dashboard.id, aggregates, clear_old=True)
        assert saved == 4

        # Получаем все агрегаты
        all_aggregates = manager.get_aggregates(dashboard.id)
        assert len(all_aggregates) == 4

        # Получаем агрегаты для конкретного графика
        graph1_aggregates = manager.get_aggregates(dashboard.id, graph1.id)
        assert len(graph1_aggregates) == 2

        graph2_aggregates = manager.get_aggregates(dashboard.id, graph2.id)
        assert len(graph2_aggregates) == 2

        # Проверяем данные
        categories = {agg["dims"]["category"] for agg in graph1_aggregates}
        assert categories == {"Electronics", "Clothing"}

        years = {agg["dims"]["year"] for agg in graph2_aggregates}
        assert years == {2023, 2024}

        # Обновляем часть данных
        updated_aggregates = [
            {
                "graph_id": graph1.id,
                "dims": {"category": "Electronics"},
                "metrics": {"revenue": 120000, "count": 60},  # Обновленные данные
            },
        ]

        saved = manager.save_aggregates(
            dashboard.id, updated_aggregates, clear_old=False
        )
        assert saved == 1

        # Проверяем, что данные обновились
        graph1_aggregates = manager.get_aggregates(dashboard.id, graph1.id)
        electronics_agg = next(
            agg for agg in graph1_aggregates if agg["dims"]["category"] == "Electronics"
        )
        assert electronics_agg["metrics"]["revenue"] == 120000
        assert electronics_agg["metrics"]["count"] == 60

        # Очищаем данные и проверяем
        deleted = manager.clear_dashboard_data(dashboard.id)
        assert deleted == 4  # Было 3 записи (2 для graph1 после обновления, 2 для graph2)

        all_aggregates = manager.get_aggregates(dashboard.id)
        assert all_aggregates == []

    def test_batch_insert_performance(self, db_session):
        """Тест пакетной вставки большого количества данных."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Performance Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Performance Test Graph",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["value"],
        )
        db_session.add(graph)
        db_session.commit()
        db_session.refresh(graph)

        manager = StorageManager(db_session)

        # Создаем много записей
        num_records = 100
        aggregates = [
            {
                "graph_id": graph.id,
                "dims": {"category": f"Category_{i}"},
                "metrics": {"value": i * 100},
            }
            for i in range(num_records)
        ]

        # Сохраняем все записи
        saved = manager.save_aggregates(dashboard.id, aggregates, clear_old=True)
        assert saved == num_records

        # Проверяем, что все записи сохранены
        all_aggregates = manager.get_aggregates(dashboard.id)
        assert len(all_aggregates) == num_records

        # Проверяем, что данные корректны
        values = {agg["metrics"]["value"] for agg in all_aggregates}
        expected_values = {i * 100 for i in range(num_records)}
        assert values == expected_values

    def test_transaction_rollback_on_error(self, db_session):
        """Тест отката транзакции при ошибке."""
        from mko_bi.db.models import dashboard as dashboard_model
        
        dashboard = dashboard_model.Dashboard(
            name="Test Dashboard",
            config={"graph_types": ["bar"]},
        )
        db_session.add(dashboard)
        db_session.commit()
        db_session.refresh(dashboard)

        graph = graphs_model.Graph(
            dashboard_id=dashboard.id,
            name="Test Graph",
            type="bar",
            config={},
            dimensions=["category"],
            metrics=["revenue"],
        )
        db_session.add(graph)
        db_session.commit()
        db_session.refresh(graph)

        manager = StorageManager(db_session)

        # Сначала сохраняем валидные данные
        valid_aggregates = [
            {
                "graph_id": graph.id,
                "dims": {"category": "A"},
                "metrics": {"revenue": 1000},
            }
        ]
        saved = manager.save_aggregates(dashboard.id, valid_aggregates, clear_old=True)
        assert saved == 1

        # Пытаемся сохранить данные с несуществующим графиком
        # Это должно вызвать ошибку и откатить транзакцию
        invalid_aggregates = [
            {
                "graph_id": uuid4(),  # Несуществующий график
                "dims": {"category": "B"},
                "metrics": {"revenue": 2000},
            }
        ]

        with pytest.raises(ValueError):
            manager.save_aggregates(dashboard.id, invalid_aggregates, clear_old=False)

        # Проверяем, что валидные данные остались нетронутыми
        all_aggregates = manager.get_aggregates(dashboard.id)
        assert len(all_aggregates) == 1
        assert all_aggregates[0]["dims"] == {"category": "A"}
