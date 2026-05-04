"""Менеджер хранения агрегированных данных.

Реализует операции сохранения, обновления и удаления агрегированных данных
для дашбордов в PostgreSQL с использованием SQLAlchemy Core для пакетных операций.
"""

import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import delete, insert, select, update, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Result


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class StorageManager:
    """Менеджер для работы с агрегированными данными дашбордов.

    Обеспечивает сохранение, обновление, удаление и получение
    агрегированных данных через единую таблицу aggregated_data.
    Использует SQLAlchemy Core для пакетных операций (batch insert)
    и работает в рамках транзакций.

    Attributes:
        db: Асинхронная сессия SQLAlchemy для работы с базой данных.
    """

    CHUNK_SIZE: int = 1000
    """Размер чанка для пакетных операций."""

    def __init__(self, db: "AsyncSession") -> None:
        """Инициализация менеджера хранения.

        Args:
            db: Асинхронная сессия SQLAlchemy для выполнения операций с БД.
        """
        self.db = db
        logger.debug("StorageManager инициализирован с асинхронной сессией БД")

    async def save_aggregates(
        self,
        dashboard_id: UUID,
        aggregates: list[dict[str, Any]],
        clear_old: bool = True,
    ) -> int:
        """Сохраняет агрегированные данные для дашборда.

        Операция выполняется в транзакции:
        1. При clear_old=True удаляются старые данные по dashboard_id
        2. Выполняется пакетная вставка новых данных через SQLAlchemy Core
        3. При ошибке транзакция откатывается

        Формат данных в aggregates:
            [
                {
                    "graph_id": UUID,
                    "dims": {...},
                    "metrics": {...}
                }
            ]

        Args:
            dashboard_id: Идентификатор дашборда.
            aggregates: Список агрегированных данных для сохранения.
            clear_old: Флаг очистки старых данных перед вставкой.

        Returns:
            Количество успешно сохранённых записей.

        Raises:
            ValueError: Если данные невалидны или графики не найдены.
            SQLAlchemyError: При ошибках работы с базой данных.
        """
        if not aggregates:
            logger.info("Пустой список агрегатов для дашборда %s", dashboard_id)
            return 0

        # Валидация данных
        self._validate_aggregates(aggregates)

        # Проверка существования графиков
        graph_ids = {agg["graph_id"] for agg in aggregates}
        await self._validate_graphs_exist(graph_ids, dashboard_id)

        try:
            # Удаляем старые данные если требуется
            if clear_old:
                deleted = await self._clear_dashboard_data_internal(dashboard_id)
                logger.info(
                    "Удалено %d старых записей для дашборда %s",
                    deleted,
                    dashboard_id,
                )

            # Пакетная вставка через SQLAlchemy Core
            from mko_bi.db.models.aggregated_data import AggregatedData

            if clear_old:
                # Простая вставка, если старые данные удалены
                inserted_count = await self._batch_insert_aggregates(
                    dashboard_id,
                    aggregates,
                    AggregatedData,
                )
            else:
                # Upsert: обновляем существующие, вставляем новые
                inserted_count = await self._upsert_aggregates_batch(
                    dashboard_id,
                    aggregates,
                    AggregatedData,
                )

            logger.info(
                "Сохранено %d агрегатов для дашборда %s",
                inserted_count,
                dashboard_id,
            )
            return inserted_count

        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при сохранении агрегатов для дашборда %s: %s",
                dashboard_id,
                str(e),
            )
            await self.db.rollback()
            raise

    async def upsert_aggregate(
        self,
        dashboard_id: UUID,
        graph_id: UUID,
        dims: dict[str, Any],
        metrics: dict[str, Any],
    ) -> bool:
        """Выполняет upsert (вставка или обновление) одного агрегата.

        Проверяет наличие записи с таким же dashboard_id, graph_id и dims.
        Если запись существует — обновляет metrics, иначе вставляет новую.

        Args:
            dashboard_id: Идентификатор дашборда.
            graph_id: Идентификатор графика.
            dims: Словарь значений измерений.
            metrics: Словарь значений метрик.

        Returns:
            True если была вставлена новая запись, False если обновлена существующая.

        Raises:
            ValueError: Если данные невалидны или график не найден.
            SQLAlchemyError: При ошибках работы с базой данных.
        """
        # Валидация
        if not isinstance(dims, dict) or not isinstance(metrics, dict):
            raise ValueError("dims и metrics должны быть словарями")

        from mko_bi.db.models import graphs as graphs_model

        graph = await self.db.get(graphs_model.Graph, graph_id)
        if not graph:
            raise ValueError("Графики не найдены")

        if graph.dashboard_id != dashboard_id:
            raise ValueError("График не принадлежит указанному дашборду")

        try:
            from mko_bi.db.models.aggregated_data import AggregatedData

            # Ищем существующую запись
            result = await self.db.execute(
                select(AggregatedData).where(
                    and_(
                        AggregatedData.dashboard_id == dashboard_id,
                        AggregatedData.graph_id == graph_id,
                        AggregatedData.dims == dims,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Обновляем существующую запись
                await self.db.execute(
                    update(AggregatedData)
                    .where(AggregatedData.id == existing.id)
                    .values(metrics=metrics)
                )
                logger.debug(
                    "Обновлён агрегат %s для дашборда %s",
                    existing.id,
                    dashboard_id,
                )
                return False

            # Вставляем новую запись
            await self.db.execute(
                insert(AggregatedData).values(
                    dashboard_id=dashboard_id,
                    graph_id=graph_id,
                    dims=dims,
                    metrics=metrics,
                )
            )
            logger.debug(
                "Вставлен новый агрегат для дашборда %s",
                dashboard_id,
            )
            return True

        except SQLAlchemyError as e:
            logger.error(
                "Ошибка upsert для дашборда %s, графика %s: %s",
                dashboard_id,
                graph_id,
                str(e),
            )
            await self.db.rollback()
            raise

    async def clear_dashboard_data(self, dashboard_id: UUID) -> int:
        """Удаляет все агрегированные данные для дашборда.

        Args:
            dashboard_id: Идентификатор дашборда.

        Returns:
            Количество удалённых записей.

        Raises:
            SQLAlchemyError: При ошибках работы с базой данных.
        """
        try:
            deleted = await self._clear_dashboard_data_internal(dashboard_id)
            logger.info(
                "Удалено %d записей для дашборда %s",
                deleted,
                dashboard_id,
            )
            return deleted
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при очистке данных дашборда %s: %s",
                dashboard_id,
                str(e),
            )
            await self.db.rollback()
            raise

    async def clear_graph_data(self, dashboard_id: UUID, graph_id: UUID) -> int:
        """Удаляет агрегированные данные для конкретного графика дашборда.

        Args:
            dashboard_id: Идентификатор дашборда.
            graph_id: Идентификатор графика.

        Returns:
            Количество удалённых записей.

        Raises:
            SQLAlchemyError: При ошибках работы с базой данных.
        """
        try:
            from mko_bi.db.models.aggregated_data import AggregatedData

            result: Result[Any] = await self.db.execute(
                delete(AggregatedData).where(
                    and_(
                        AggregatedData.dashboard_id == dashboard_id,
                        AggregatedData.graph_id == graph_id,
                    )
                )
            )
            # В SQLAlchemy 2.0 rowcount может быть None для некоторых операций
            deleted = result.rowcount if result.rowcount is not None else 0  # type: ignore[attr-defined]
            logger.debug(
                "Удалено %d записей для графика %s дашборда %s",
                deleted,
                graph_id,
                dashboard_id,
            )
            return deleted
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при очистке данных графика %s дашборда %s: %s",
                graph_id,
                dashboard_id,
                str(e),
            )
            await self.db.rollback()
            raise

    async def get_aggregates(
        self,
        dashboard_id: UUID,
        graph_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        """Возвращает агрегированные данные для дашборда.

        Args:
            dashboard_id: Идентификатор дашборда.
            graph_id: Опциональный идентификатор графика для фильтрации.

        Returns:
            Список словарей с агрегированными данными.
            Каждый словарь содержит: id, graph_id, dims, metrics.

        Raises:
            SQLAlchemyError: При ошибках работы с базой данных.
        """
        try:
            from mko_bi.db.models.aggregated_data import AggregatedData

            query = select(
                AggregatedData.id,
                AggregatedData.graph_id,
                AggregatedData.dims,
                AggregatedData.metrics,
            ).where(AggregatedData.dashboard_id == dashboard_id)

            if graph_id:
                query = query.where(AggregatedData.graph_id == graph_id)

            result = await self.db.execute(query)
            aggregates = [
                {
                    "id": row.id,
                    "graph_id": row.graph_id,
                    "dims": row.dims,
                    "metrics": row.metrics,
                }
                for row in result
            ]
            return aggregates
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении агрегатов для дашборда %s: %s",
                dashboard_id,
                str(e),
            )
            raise

    async def _clear_dashboard_data_internal(self, dashboard_id: UUID) -> int:
        """Внутренний метод удаления данных дашборда.
        
        Args:
            dashboard_id: Идентификатор дашборда.
        
        Returns:
            Количество удалённых записей.
        """
        from mko_bi.db.models.aggregated_data import AggregatedData
        
        result: Result[Any] = await self.db.execute(
            delete(AggregatedData).where(
                AggregatedData.dashboard_id == dashboard_id
            )
        )
        # В SQLAlchemy 2.0 rowcount может быть None для некоторых операций
        return result.rowcount if result.rowcount is not None else 0  # type: ignore[attr-defined]

    async def _batch_insert_aggregates(
        self,
        dashboard_id: UUID,
        aggregates: list[dict[str, Any]],
        table_model: Any,
    ) -> int:
        """Выполняет пакетную вставку агрегированных данных.

        Использует ORM для вставки данных. Для SQLite это более надежно,
        так как корректно обрабатывает autoincrement.
        Данные разбиваются на чанки для оптимизации памяти.

        Args:
            dashboard_id: Идентификатор дашборда.
            aggregates: Список агрегированных данных.
            table_model: Модель таблицы SQLAlchemy.

        Returns:
            Количество вставленных записей.
        """
        total_inserted = 0

        # Разбиваем на чанки
        for i in range(0, len(aggregates), self.CHUNK_SIZE):
            chunk = aggregates[i : i + self.CHUNK_SIZE]

            # Создаем объекты для вставки
            objects = [
                table_model(
                    dashboard_id=dashboard_id,
                    graph_id=agg["graph_id"],
                    dims=agg["dims"],
                    metrics=agg["metrics"],
                )
                for agg in chunk
            ]

            # Добавляем объекты в сессию
            self.db.add_all(objects)
            await self.db.flush()
            total_inserted += len(objects)

        return total_inserted

    async def _upsert_aggregates_batch(
        self,
        dashboard_id: UUID,
        aggregates: list[dict[str, Any]],
        table_model: Any,
    ) -> int:
        """Выполняет пакетный upsert агрегированных данных.

        Для каждой записи проверяет наличие существующей с таким же
        dashboard_id, graph_id и dims. Если запись существует — обновляет
        metrics, иначе вставляет новую.

        Args:
            dashboard_id: Идентификатор дашборда.
            aggregates: Список агрегированных данных.
            table_model: Модель таблицы SQLAlchemy.

        Returns:
            Количество обработанных записей.
        """
        from mko_bi.db.models.aggregated_data import AggregatedData

        total_processed = 0

        for agg in aggregates:
            # Ищем существующую запись
            result = await self.db.execute(
                select(AggregatedData).where(
                    and_(
                        AggregatedData.dashboard_id == dashboard_id,
                        AggregatedData.graph_id == agg["graph_id"],
                        AggregatedData.dims == agg["dims"],
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Обновляем существующую запись
                await self.db.execute(
                    update(AggregatedData)
                    .where(AggregatedData.id == existing.id)
                    .values(metrics=agg["metrics"])
                )
            else:
                # Вставляем новую запись
                await self.db.execute(
                    insert(AggregatedData).values(
                        dashboard_id=dashboard_id,
                        graph_id=agg["graph_id"],
                        dims=agg["dims"],
                        metrics=agg["metrics"],
                    )
                )
            total_processed += 1

        return total_processed

    def _validate_aggregates(self, aggregates: list[dict[str, Any]]) -> None:
        """Валидирует список агрегированных данных.

        Проверяет наличие обязательных полей и корректность типов.

        Args:
            aggregates: Список агрегированных данных.

        Raises:
            ValueError: Если данные невалидны.
        """
        required_fields = {"graph_id", "dims", "metrics"}

        for idx, agg in enumerate(aggregates):
            # Проверка обязательных полей
            missing = required_fields - set(agg.keys())
            if missing:
                raise ValueError(
                    f"Агрегат {idx} не содержит обязательное поле: {missing}"
                )

            # Проверка типов
            if not isinstance(agg["dims"], dict):
                raise ValueError("dims должен быть словарем")
            if not isinstance(agg["metrics"], dict):
                raise ValueError("metrics должен быть словарем")

    async def _validate_graphs_exist(
        self,
        graph_ids: set[UUID],
        dashboard_id: UUID,
    ) -> None:
        """Проверяет существование графиков и их принадлежность дашборду.

        Args:
            graph_ids: Множество идентификаторов графиков.
            dashboard_id: Идентификатор дашборда.

        Raises:
            ValueError: Если какие-либо графики не найдены.
        """
        from mko_bi.db.models import graphs as graphs_model

        result = await self.db.execute(
            select(graphs_model.Graph.id).where(
                and_(
                    graphs_model.Graph.id.in_(list(graph_ids)),
                    graphs_model.Graph.dashboard_id == dashboard_id,
                )
            )
        )
        found_graphs = result.scalars().all()

        found_ids = set(found_graphs)
        missing_ids = graph_ids - found_ids

        if missing_ids:
            raise ValueError(
                f"Графики не найдены или не принадлежат дашборду: {missing_ids}"
            )
