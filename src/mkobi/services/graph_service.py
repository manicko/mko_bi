"""Сервис управления графиками.

Предоставляет бизнес-логику для CRUD операций с графиками.
Все операции выполняются через IGraphRepository с валидацией и логированием.
"""

import logging
from typing import Any
from uuid import UUID

from mkobi.db.session import get_session
from mkobi.interfaces.repository_interfaces import IGraphRepository
from mkobi.interfaces.service_interfaces import IGraphService
from mkobi.models.graph import GraphCreate, GraphRead, GraphUpdate
from mkobi.models.user_roles import GraphTypeEnum

logger = logging.getLogger(__name__)


class GraphService(IGraphService):
    """Сервис для работы с графиками.

    Реализует интерфейс IGraphService и использует IGraphRepository
    для доступа к данным.
    """

    def __init__(self, repository: IGraphRepository):
        """Инициализация сервиса с репозиторием.

        Args:
            repository: Репозиторий графиков.
        """
        self._repository = repository
        logger.info("GraphService инициализирован с репозиторием: %s", type(repository).__name__)

    def create(self, data: GraphCreate) -> GraphRead:
        """Создать новый график.

        Args:
            data: Данные для создания графика.

        Returns:
            GraphRead: Модель созданного графика.

        Raises:
            ValueError: При некорректных данных.
        """
        logger.info("Создание графика: name=%s, dashboard_id=%s", data.name, data.dashboard_id)
        self._validate_graph_data(data)
        
        db = get_session().__enter__()
        try:
            graph_obj = self._repository.create(
                db=db,
                name=data.name,
                type=data.type,
                dashboard_id=data.dashboard_id,
                config=data.config,
                dimensions=data.dimensions,
                metrics=data.metrics,
            )
            db.commit()
            
            logger.info("График создан: id=%s, name=%s", graph_obj.id, graph_obj.name)
            return self._to_read_model(graph_obj)
        except Exception as e:
            db.rollback()
            logger.error("Ошибка при создании графика: %s", e)
            raise
        finally:
            db.close()

    def get(self, graph_id: UUID) -> GraphRead | None:
        """Получить график по ID.

        Args:
            graph_id: Идентификатор графика.

        Returns:
            GraphRead или None, если не найден.
        """
        logger.info("Получение графика: id=%s", graph_id)
        db = get_session().__enter__()
        try:
            graph_obj = self._repository.get(graph_id, db=db)
            if graph_obj is None:
                logger.warning("График не найден: id=%s", graph_id)
                return None
            return self._to_read_model(graph_obj)
        finally:
            db.close()

    def update(self, graph_id: UUID, data: GraphUpdate) -> GraphRead | None:
        """Обновить график.

        Args:
            graph_id: Идентификатор графика.
            data: Данные для обновления.

        Returns:
            GraphRead или None, если не найден.
        """
        logger.info("Обновление графика: id=%s", graph_id)
        
        update_data = {}
        if data.name is not None:
            update_data["name"] = data.name
        if data.type is not None:
            update_data["type"] = data.type
        if data.config is not None:
            update_data["config"] = data.config
        if data.dimensions is not None:
            update_data["dimensions"] = data.dimensions
        if data.metrics is not None:
            update_data["metrics"] = data.metrics
        
        db = get_session().__enter__()
        try:
            graph_obj = self._repository.update(graph_id, db=db, **update_data)
            if graph_obj is None:
                logger.warning("График не найден для обновления: id=%s", graph_id)
                return None
            db.commit()
            logger.info("График обновлен: id=%s", graph_id)
            return self._to_read_model(graph_obj)
        except Exception as e:
            db.rollback()
            logger.error("Ошибка при обновлении графика id=%s: %s", graph_id, e)
            raise
        finally:
            db.close()

    def delete(self, graph_id: UUID) -> bool:
        """Удалить график.

        Args:
            graph_id: Идентификатор графика.

        Returns:
            True, если удаление успешно, False - если не найден.
        """
        logger.info("Удаление графика: id=%s", graph_id)
        db = get_session().__enter__()
        try:
            result: bool = self._repository.delete(graph_id, db=db)
            if result:
                db.commit()
                logger.info("График удален: id=%s", graph_id)
            else:
                logger.warning("График не найден для удаления: id=%s", graph_id)
            return result
        except Exception as e:
            db.rollback()
            logger.error("Ошибка при удалении графика id=%s: %s", graph_id, e)
            raise
        finally:
            db.close()

    def list_by_dashboard(self, dashboard_id: UUID) -> list[GraphRead]:
        """Получить список графиков по ID дашборда.

        Args:
            dashboard_id: Идентификатор дашборда.

        Returns:
            Список графиков дашборда.
        """
        logger.info("Получение графиков для дашборда: dashboard_id=%s", dashboard_id)
        db = get_session().__enter__()
        try:
            graph_objs = self._repository.get_by_dashboard_id(dashboard_id, db=db)
            return [self._to_read_model(g) for g in graph_objs]
        finally:
            db.close()

    def _to_read_model(self, graph_obj) -> GraphRead:
        """Преобразовать объект БД в Pydantic модель.

        Args:
            graph_obj: Объект модели Graph из БД.

        Returns:
            GraphRead модель.
        """
        return GraphRead.model_validate(graph_obj)

    def _validate_graph_data(self, data: GraphCreate) -> None:
        """Валидация данных графика.

        Args:
            data: Данные для валидации.

        Raises:
            ValueError: При некорректных данных.
        """
        if not data.name or not data.name.strip():
            raise ValueError("Имя графика не может быть пустым")
        
        try:
            GraphTypeEnum(data.type)
        except ValueError as e:
            logger.error("Недопустимый тип графика: '%s'", data.type)
            raise ValueError(
                f"Недопустимый тип графика: '{data.type}'. "
                f"Допустимые значения: {', '.join([e.value for e in GraphTypeEnum])}"
            ) from e

    # Реализация методов интерфейса IGraphService
    def create_graph(self, dashboard_id: UUID, name: str, type_: str, config: dict[str, Any], dimensions: list[Any], metrics: list[Any]) -> GraphRead:
        """Создать новый график (метод интерфейса IGraphService)."""
        data = GraphCreate(
            name=name,
            type=type_,
            dashboard_id=dashboard_id,
            config=config,
            dimensions=dimensions,
            metrics=metrics,
        )
        return self.create(data)

    def get_graph_by_id(self, graph_id: UUID) -> GraphRead | None:
        """Получить график по ID (метод интерфейса IGraphService)."""
        return self.get(graph_id)

    def get_graph_by_name_and_dashboard(self, name: str, dashboard_id: UUID) -> GraphRead | None:
        """Получить график по имени и ID дашборда (метод интерфейса IGraphService)."""
        logger.info("Получение графика: name=%s, dashboard_id=%s", name, dashboard_id)
        db = get_session().__enter__()
        try:
            graph_obj = self._repository.get_by_name_and_dashboard(name, dashboard_id, db=db)
            if graph_obj is None:
                logger.warning("График не найден: name=%s, dashboard_id=%s", name, dashboard_id)
                return None
            return self._to_read_model(graph_obj)
        finally:
            db.close()

    def get_graphs_by_dashboard(self, dashboard_id: UUID) -> list[GraphRead]:
        """Получить графики по ID дашборда (метод интерфейса IGraphService)."""
        return self.list_by_dashboard(dashboard_id)

    def update_graph(self, graph_id: UUID, name: str | None, type_: str | None, config: dict[str, Any] | None, dimensions: list[Any] | None, metrics: list[Any] | None) -> GraphRead | None:
        """Обновить график (метод интерфейса IGraphService)."""
        data = GraphUpdate(
            name=name,
            type=type_,
            config=config,
            dimensions=dimensions,
            metrics=metrics,
        )
        return self.update(graph_id, data)

    def delete_graph(self, graph_id: UUID) -> bool:
        """Удалить график (метод интерфейса IGraphService)."""
        return self.delete(graph_id)
