"""Репозиторий для работы с агрегированными данными.

Предоставляет методы для управления агрегированными данными дашбордов.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import delete, insert, select
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import aggregated_data as aggregated_data_model
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AggregatedDataRepository:
    """Репозиторий для операций с агрегированными данными.
    
    Предоставляет методы для сохранения, чтения и удаления
    агрегированных данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением
    транзакциями.
    """
    
    @classmethod
    async def bulk_insert(
        cls,
        db: AsyncSession,
        dashboard_id: int,
        aggregates: list[dict[str, Any]],
        clear_old: bool = True,
    ) -> int:
        """Выполняет пакетную вставку агрегированных данных.
        
        Операция выполняется в транзакции:
        1. При clear_old=True удаляются старые данные по dashboard_id
        2. Выполняется пакетная вставка новых данных
        3. При ошибке транзакция откатывается
        
        Args:
            db: Асинхронная сессия базы данных.
            dashboard_id: Идентификатор дашборда.
            aggregates: Список агрегированных данных для вставки.
                Каждый элемент должен содержать:
                - graph_id: UUID графика
                - dims: dict значения измерений (JSON)
                - metrics: dict значения метрик (JSON)
            clear_old: Удалять ли старые данные (по умолчанию True).
        
        Returns:
            Количество вставленных записей.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            if clear_old:
                await db.execute(
                    delete(aggregated_data_model.AggregatedData).where(
                        aggregated_data_model.AggregatedData.dashboard_id == dashboard_id
                    )
                )
            
            if not aggregates:
                logger.info("Нет данных для вставки: dashboard_id=%s", dashboard_id)
                return 0
            
            # Подготавливаем данные для вставки
            insert_data = []
            for item in aggregates:
                insert_data.append({
                    "dashboard_id": dashboard_id,
                    "graph_id": item["graph_id"],
                    "dims": item["dims"],
                    "metrics": item["metrics"],
                })
            
            await db.execute(
                insert(aggregated_data_model.AggregatedData),
                insert_data,
            )
            
            count = len(insert_data)
            logger.info(
                "Данные вставлены: dashboard_id=%s, count=%s",
                dashboard_id,
                count,
            )
            return count
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при вставке данных dashboard_id=%s: %s",
                dashboard_id,
                e,
            )
            raise
    
    @classmethod
    async def get_by_dashboard(
        cls, dashboard_id: int, db: AsyncSession
    ) -> list[aggregated_data_model.AggregatedData]:
        """Получить все агрегированные данные для дашборда.
        
        Args:
            dashboard_id: Идентификатор дашборда.
            db: Асинхронная сессия базы данных.
        
        Returns:
            Список агрегированных данных.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(aggregated_data_model.AggregatedData)
                .where(aggregated_data_model.AggregatedData.dashboard_id == dashboard_id)
            )
            data = list(result.scalars().all())
            logger.info(
                "Получены данные для dashboard_id=%s, count=%s",
                dashboard_id,
                len(data),
            )
            return data
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении данных dashboard_id=%s: %s",
                dashboard_id,
                e,
            )
            raise
    
    @classmethod
    async def get_by_graph(
        cls, graph_id: UUID, db: AsyncSession
    ) -> list[aggregated_data_model.AggregatedData]:
        """Получить агрегированные данные для графика.
        
        Args:
            graph_id: Идентификатор графика (UUID).
            db: Асинхронная сессия базы данных.
        
        Returns:
            Список точек данных для графика.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(aggregated_data_model.AggregatedData)
                .where(aggregated_data_model.AggregatedData.graph_id == graph_id)
            )
            data = list(result.scalars().all())
            logger.info(
                "Получены данные для graph_id=%s, count=%s",
                graph_id,
                len(data),
            )
            return data
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении данных graph_id=%s: %s",
                graph_id,
                e,
            )
            raise
    
    @classmethod
    async def delete_by_dashboard(
        cls, dashboard_id: int, db: AsyncSession
    ) -> int:
        """Удалить все агрегированные данные для дашборда.
        
        Args:
            dashboard_id: Идентификатор дашборда.
            db: Асинхронная сессия базы данных.
        
        Returns:
            Количество удаленных записей.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                delete(aggregated_data_model.AggregatedData)
                .where(aggregated_data_model.AggregatedData.dashboard_id == dashboard_id)
            )
            count = result.rowcount if hasattr(result, 'rowcount') else 0
            logger.info(
                "Данные удалены: dashboard_id=%s, count=%s",
                dashboard_id,
                count,
            )
            return count
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при удалении данных dashboard_id=%s: %s",
                dashboard_id,
                e,
            )
            raise
    
    @classmethod
    async def get_all(cls, db: AsyncSession) -> list[aggregated_data_model.AggregatedData]:
        """Получить все агрегированные данные.
        
        Args:
            db: Асинхронная сессия базы данных.
        
        Returns:
            Список всех агрегированных данных.
        
        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(select(aggregated_data_model.AggregatedData))
            data = list(result.scalars().all())
            logger.info("Получен список данных, количество: %s", len(data))
            return data
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка данных: %s", e)
            raise
