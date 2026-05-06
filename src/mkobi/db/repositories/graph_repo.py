"""Репозиторий для работы с графиками.

Предоставляет методы CRUD для модели Graph.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mkobi.db.models import graphs as graph_model
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class GraphRepository:
    """Репозиторий для операций с графиками.
    
    Предоставляет методы для создания, чтения, обновления и удаления
    графиков в базе данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением
    транзакциями.
    """
    
    @classmethod
    async def get(
        cls, graph_id: UUID, db: AsyncSession
    ) -> graph_model.Graph | None:
        """Получить график по ID.
        
        Args:
            graph_id: Идентификатор графика (UUID).
            db: Асинхронная сессия базы данных.
        
        Returns:
            Модель графика или None, если не найден.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(graph_model.Graph).where(
                    graph_model.Graph.id == graph_id
                )
            )
            graph = result.scalar_one_or_none()
            if graph:
                logger.info("График получен: id=%s", graph_id)
            else:
                logger.warning("График не найден: id=%s", graph_id)
            return graph
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении графика id=%s: %s", graph_id, e)
            raise

    @classmethod
    async def get_by_dashboard(
        cls, dashboard_id: UUID, db: AsyncSession
    ) -> list[graph_model.Graph]:
        """Получить все графики дашборда.
        
        Args:
            dashboard_id: Идентификатор дашборда (UUID).
            db: Асинхронная сессия базы данных.
        
        Returns:
            Список графиков дашборда.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(graph_model.Graph)
                .where(graph_model.Graph.dashboard_id == dashboard_id)
            )
            graphs = list(result.scalars().all())
            logger.info(
                "Получены графики для dashboard_id=%s, количество: %s",
                dashboard_id,
                len(graphs),
            )
            return graphs
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении графиков dashboard_id=%s: %s", dashboard_id, e
            )
            raise

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> graph_model.Graph | None:
        """Создать новый график.
        
        Args:
            db: Асинхронная сессия базы данных.
            **kwargs: Параметры графика (name, type, config, etc.).
        
        Returns:
            Модель созданного графика с ID или None при ошибке.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            graph_obj = graph_model.Graph(**kwargs)
            db.add(graph_obj)
            await db.flush()
            await db.refresh(graph_obj)
            logger.info(
                "График создан: id=%s, name=%s", graph_obj.id, graph_obj.name
            )
            return graph_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при создании графика: %s", e)
            raise

    @classmethod
    async def update(
        cls, graph_id: UUID, db: AsyncSession, **kwargs
    ) -> graph_model.Graph | None:
        """Обновить данные графика.
        
        Args:
            graph_id: Идентификатор графика (UUID).
            db: Асинхронная сессия базы данных.
            **kwargs: Поля для обновления.
        
        Returns:
            Обновленная модель графика или None, если не найден.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(graph_model.Graph).where(
                    graph_model.Graph.id == graph_id
                )
            )
            graph_obj = result.scalar_one_or_none()
            if not graph_obj:
                logger.warning("График не найден для обновления: id=%s", graph_id)
                return None
            for key, value in kwargs.items():
                if hasattr(graph_obj, key):
                    setattr(graph_obj, key, value)
            await db.flush()
            await db.refresh(graph_obj)
            logger.info("График обновлен: id=%s", graph_id)
            return graph_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при обновлении графика id=%s: %s", graph_id, e)
            raise

    @classmethod
    async def delete(cls, graph_id: UUID, db: AsyncSession) -> bool:
        """Удалить график.
        
        Args:
            graph_id: Идентификатор графика (UUID).
            db: Асинхронная сессия базы данных.
        
        Returns:
            True, если удаление успешно, False - если график не найден.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(graph_model.Graph).where(
                    graph_model.Graph.id == graph_id
                )
            )
            graph_obj = result.scalar_one_or_none()
            if not graph_obj:
                logger.warning("График не найден для удаления: id=%s", graph_id)
                return False
            await db.delete(graph_obj)
            await db.flush()
            logger.info("График удален: id=%s", graph_id)
            return True
        except SQLAlchemyError as e:
            logger.error("Ошибка при удалении графика id=%s: %s", graph_id, e)
            raise

    @classmethod
    async def get_all(cls, db: AsyncSession) -> list[graph_model.Graph]:
        """Получить все графики.
        
        Args:
            db: Асинхронная сессия базы данных.
        
        Returns:
            Список всех графиков.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(select(graph_model.Graph))
            graphs = list(result.scalars().all())
            logger.info("Получен список графиков, количество: %s", len(graphs))
            return graphs
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка графиков: %s", e)
            raise
