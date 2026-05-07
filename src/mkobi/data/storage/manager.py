"""Менеджер хранения агрегированных данных.

Реализует операции сохранения, обновления, удаления и получения
агрегированных данных для дашбордов в PostgreSQL.

Особенности:
- Использует PostgreSQL UPSERT (ON CONFLICT DO UPDATE)
- Поддерживает batch insert/upsert
- Не управляет транзакциями (commit/rollback снаружи)
- Использует SQLAlchemy Core
- Без race condition
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.dialects.postgresql import insert

from mkobi.db.models.aggregated_data import AggregatedData
from mkobi.models.enums import UploadMode

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class StorageManager:
    """Менеджер хранения агрегированных данных."""

    CHUNK_SIZE: int = 1000

    def __init__(self, db: AsyncSession) -> None:
        """Инициализация менеджера.

        Args:
            db: Async SQLAlchemy session.
        """
        self.db = db

    # =========================================================================
    # Public API
    # =========================================================================

    async def save_aggregates(
        self,
        dashboard_id: UUID,
        aggregates: list[dict[str, Any]],
        clear_old: bool = False,
    ) -> int:
        """Сохраняет агрегированные данные.

        При clear_old=True:
        - удаляются старые данные dashboard
        - выполняется bulk insert

        При clear_old=False:
        - выполняется bulk upsert

        Args:
            dashboard_id: ID дашборда.
            aggregates: Агрегированные данные.
            clear_old: Удалить старые данные.

        Returns:
            Количество обработанных записей.

        Raises:
            ValueError: Ошибка валидации.
            SQLAlchemyError: Ошибка БД.
        """
        if not aggregates:
            logger.info(
                "Пустой список агрегатов для dashboard_id=%s",
                dashboard_id,
            )
            return 0

        self._validate_aggregates(aggregates)

        graph_ids = {agg["graph_id"] for agg in aggregates}

        await self._validate_graphs_exist(
            graph_ids=graph_ids,
            dashboard_id=dashboard_id,
        )

        if clear_old:
            deleted = await self.delete_by_dashboard(dashboard_id)

            logger.info(
                "Удалено %d старых записей dashboard_id=%s",
                deleted,
                dashboard_id,
            )

            inserted = await self._bulk_insert(
                dashboard_id=dashboard_id,
                aggregates=aggregates,
                table_model=AggregatedData,
            )

            logger.info(
                "Вставлено %d агрегатов dashboard_id=%s",
                inserted,
                dashboard_id,
            )

            return inserted

        processed = await self._bulk_upsert(
            dashboard_id=dashboard_id,
            aggregates=aggregates,
            table_model=AggregatedData,
        )

        logger.info(
            "Upsert %d агрегатов dashboard_id=%s",
            processed,
            dashboard_id,
        )

        return processed

    async def upsert_aggregate(
        self,
        dashboard_id: UUID,
        graph_id: UUID,
        dims: dict[str, Any],
        metrics: dict[str, Any],
    ) -> bool:
        """Выполняет UPSERT одного агрегата.

        Returns:
            True если вставлена новая запись.
            False если обновлена существующая.
        """
        self._validate_single_aggregate(dims, metrics)

        await self._validate_graphs_exist(
            graph_ids={graph_id},
            dashboard_id=dashboard_id,
        )

        stmt = insert(AggregatedData).values(
            dashboard_id=dashboard_id,
            graph_id=graph_id,
            dims=dims,
            metrics=metrics,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=[
                AggregatedData.dashboard_id,
                AggregatedData.graph_id,
                AggregatedData.dims,
            ],
            set_={
                "metrics": stmt.excluded.metrics,
            },
        ).returning(AggregatedData.id)

        result = await self.db.execute(stmt)

        inserted = result.scalar_one_or_none() is not None

        logger.debug(
            "UPSERT aggregate dashboard_id=%s graph_id=%s",
            dashboard_id,
            graph_id,
        )

        return inserted

    async def get_aggregates(
        self,
        dashboard_id: UUID,
        graph_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        """Получает агрегированные данные."""
        query = select(
            AggregatedData.id,
            AggregatedData.graph_id,
            AggregatedData.dims,
            AggregatedData.metrics,
        ).where(
            AggregatedData.dashboard_id == dashboard_id,
        )

        if graph_id:
            query = query.where(
                AggregatedData.graph_id == graph_id,
            )

        result = await self.db.execute(query)

        return [
            {
                "id": row.id,
                "graph_id": row.graph_id,
                "dims": row.dims,
                "metrics": row.metrics,
            }
            for row in result
        ]

    async def delete_by_graph(
        self,
        graph_id: UUID,
    ) -> int:
        """Удаляет данные графика."""
        result = await self.db.execute(
            delete(AggregatedData).where(
                AggregatedData.graph_id == graph_id,
            )
        )

        deleted = result.rowcount or 0

        logger.info(
            "Удалено %d записей graph_id=%s",
            deleted,
            graph_id,
        )

        return deleted

    async def delete_by_dashboard(
        self,
        dashboard_id: UUID,
    ) -> int:
        """Удаляет данные дашборда."""
        result = await self.db.execute(
            delete(AggregatedData).where(
                AggregatedData.dashboard_id == dashboard_id,
            )
        )

        deleted = result.rowcount or 0

        logger.info(
            "Удалено %d записей dashboard_id=%s",
            deleted,
            dashboard_id,
        )

        return deleted

    # =========================================================================
    # Internal methods
    # =========================================================================

    async def _bulk_insert(
        self,
        dashboard_id: UUID,
        aggregates: list[dict[str, Any]],
        table_model: Any,
    ) -> int:
        """Выполняет bulk insert."""
        total_inserted = 0

        for i in range(0, len(aggregates), self.CHUNK_SIZE):
            chunk = aggregates[i : i + self.CHUNK_SIZE]

            insert_data = [
                {
                    "dashboard_id": dashboard_id,
                    "graph_id": agg["graph_id"],
                    "dims": agg["dims"],
                    "metrics": agg["metrics"],
                }
                for agg in chunk
            ]

            await self.db.execute(
                insert(table_model),
                insert_data,
            )

            total_inserted += len(insert_data)

        return total_inserted

    async def _bulk_upsert(
        self,
        dashboard_id: UUID,
        aggregates: list[dict[str, Any]],
        table_model: Any,
    ) -> int:
        """Выполняет bulk upsert."""
        total_processed = 0

        for i in range(0, len(aggregates), self.CHUNK_SIZE):
            chunk = aggregates[i : i + self.CHUNK_SIZE]

            insert_data = [
                {
                    "dashboard_id": dashboard_id,
                    "graph_id": agg["graph_id"],
                    "dims": agg["dims"],
                    "metrics": agg["metrics"],
                }
                for agg in chunk
            ]

            stmt = insert(table_model).values(insert_data)

            stmt = stmt.on_conflict_do_update(
                index_elements=[
                    table_model.dashboard_id,
                    table_model.graph_id,
                    table_model.dims,
                ],
                set_={
                    "metrics": stmt.excluded.metrics,
                },
            )

            await self.db.execute(stmt)

            total_processed += len(insert_data)

        return total_processed

    async def _validate_graphs_exist(
        self,
        graph_ids: set[UUID],
        dashboard_id: UUID,
    ) -> None:
        """Проверяет существование графиков."""
        from mkobi.db.models import graphs as graphs_model

        result = await self.db.execute(
            select(graphs_model.Graph.id).where(
                and_(
                    graphs_model.Graph.id.in_(list(graph_ids)),
                    graphs_model.Graph.dashboard_id == dashboard_id,
                )
            )
        )

        found_ids = set(result.scalars().all())

        missing = graph_ids - found_ids

        if missing:
            raise ValueError(
                f"Графики не найдены или не принадлежат dashboard: {missing}"
            )

    def _validate_aggregates(
        self,
        aggregates: list[dict[str, Any]],
    ) -> None:
        """Валидирует список агрегатов."""
        required_fields = {
            "graph_id",
            "dims",
            "metrics",
        }

        for idx, agg in enumerate(aggregates):
            missing = required_fields - set(agg.keys())

            if missing:
                raise ValueError(f"Агрегат {idx} не содержит поля: {missing}")

            self._validate_single_aggregate(
                dims=agg["dims"],
                metrics=agg["metrics"],
            )

    @staticmethod
    def _validate_single_aggregate(
        dims: dict[str, Any],
        metrics: dict[str, Any],
    ) -> None:
        """Валидирует один агрегат."""
        if not isinstance(dims, dict):
            raise ValueError("dims должен быть dict")

        if not isinstance(metrics, dict):
            raise ValueError("metrics должен быть dict")

    # =========================================================================
    # Compatibility API
    # =========================================================================

    @classmethod
    async def save_aggregated_data(
        cls,
        dashboard_id: UUID,
        graph_id: UUID,
        aggregated_results: list[dict[str, Any]],
        mode: UploadMode,
        db: AsyncSession,
    ) -> None:
        """Compatibility wrapper."""
        manager = cls(db)

        aggregates = [
            {
                "graph_id": graph_id,
                "dims": item.get("dims", {}),
                "metrics": item.get("metrics", {}),
            }
            for item in aggregated_results
        ]

        await manager.save_aggregates(
            dashboard_id=dashboard_id,
            aggregates=aggregates,
            clear_old=(mode == UploadMode.OVERWRITE),
        )
