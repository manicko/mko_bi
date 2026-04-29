"""Репозиторий для работы с агрегированными данными.

Предоставляет методы для управления агрегированными данными дашбордов.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import delete, insert, select, and_
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import aggregated_data as aggregated_data_model
from mko_bi.db.models import graphs as graphs_model
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AggregatedDataRepository:
    """Репозиторий для операций с агрегированными данными.

    Предоставляет методы для сохранения, чтения и удаления
    агрегированных данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением
    транзакциями.
    """

    @classmethod
    def bulk_insert(
        cls,
        db: Session,
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
            db: Сессия базы данных.
            dashboard_id: Идентификатор дашборда.
            aggregates: Список агрегированных данных для вставки.
                Каждый элемент должен содержать:
                - graph_id: UUID графика
                - dims: dict[str, Any] значения измерений
                - metrics: dict[str, Any] значения метрик
            clear_old: Флаг очистки старых данных перед вставкой.

        Returns:
            Количество успешно вставленных записей.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
            ValueError: Если данные невалидны или графики не найдены.
        """
        if not aggregates:
            logger.info("Пустой список агрегатов для дашборда %s", dashboard_id)
            return 0

        # Проверка существования графиков
        graph_ids = {agg["graph_id"] for agg in aggregates}
        cls._validate_graphs_exist(db, graph_ids, dashboard_id)

        try:
            # Удаляем старые данные если требуется
            if clear_old:
                deleted = cls.delete_by_dashboard(db, dashboard_id)
                logger.info(
                    "Удалено %d старых записей для дашборда %s",
                    deleted,
                    dashboard_id,
                )

            # Пакетная вставка
            inserted_count = 0
            for agg in aggregates:
                result = db.execute(
                    insert(aggregated_data_model.AggregatedData).values(
                        dashboard_id=dashboard_id,
                        graph_id=agg["graph_id"],
                        dims=agg["dims"],
                        metrics=agg["metrics"],
                    )
                )
                if result.rowcount:
                    inserted_count += 1

            db.flush()
            logger.info(
                "Сохранено %d агрегатов для дашборда %s",
                inserted_count,
                dashboard_id,
            )
            return inserted_count

        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при пакетной вставке агрегатов для дашборда %s: %s",
                dashboard_id,
                str(e),
            )
            raise
        except KeyError as e:
            logger.error(
                "Некорректный формат данных для дашборда %s: %s",
                dashboard_id,
                str(e),
            )
            raise ValueError(f"Некорректный формат данных: {e}") from e

    @classmethod
    def delete_by_dashboard(
        cls, db: Session, dashboard_id: int
    ) -> int:
        """Удаляет все агрегированные данные для дашборда.

        Args:
            db: Сессия базы данных.
            dashboard_id: Идентификатор дашборда.

        Returns:
            Количество удалённых записей.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(
                delete(aggregated_data_model.AggregatedData).where(
                    aggregated_data_model.AggregatedData.dashboard_id
                    == dashboard_id
                )
            )
            deleted = result.rowcount if result.rowcount is not None else 0
            logger.info(
                "Удалено %d записей для дашборда %s",
                deleted,
                dashboard_id,
            )
            return deleted
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при удалении агрегатов для дашборда %s: %s",
                dashboard_id,
                str(e),
            )
            raise

    @classmethod
    def delete_by_graph(
        cls, db: Session, graph_id: UUID
    ) -> int:
        """Удаляет агрегированные данные для конкретного графика.

        Args:
            db: Сессия базы данных.
            graph_id: Идентификатор графика (UUID).

        Returns:
            Количество удалённых записей.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(
                delete(aggregated_data_model.AggregatedData).where(
                    aggregated_data_model.AggregatedData.graph_id == graph_id
                )
            )
            deleted = result.rowcount if result.rowcount is not None else 0
            logger.info(
                "Удалено %d записей для графика %s",
                deleted,
                graph_id,
            )
            return deleted
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при удалении агрегатов для графика %s: %s",
                graph_id,
                str(e),
            )
            raise

    @classmethod
    def get_by_graph(
        cls, db: Session, graph_id: UUID
    ) -> list[aggregated_data_model.AggregatedData]:
        """Получает агрегированные данные для конкретного графика.

        Args:
            db: Сессия базы данных.
            graph_id: Идентификатор графика (UUID).

        Returns:
            Список агрегированных данных для графика.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(
                select(aggregated_data_model.AggregatedData).where(
                    aggregated_data_model.AggregatedData.graph_id == graph_id
                )
            )
            aggregates = result.scalars().all()
            logger.info(
                "Получено %d агрегатов для графика %s",
                len(aggregates),
                graph_id,
            )
            return aggregates
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении агрегатов для графика %s: %s",
                graph_id,
                str(e),
            )
            raise

    @classmethod
    def get_by_dashboard(
        cls, db: Session, dashboard_id: int
    ) -> list[aggregated_data_model.AggregatedData]:
        """Получает все агрегированные данные для дашборда.

        Args:
            db: Сессия базы данных.
            dashboard_id: Идентификатор дашборда.

        Returns:
            Список агрегированных данных для дашборда.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(
                select(aggregated_data_model.AggregatedData).where(
                    aggregated_data_model.AggregatedData.dashboard_id
                    == dashboard_id
                )
            )
            aggregates = result.scalars().all()
            logger.info(
                "Получено %d агрегатов для дашборда %s",
                len(aggregates),
                dashboard_id,
            )
            return aggregates
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении агрегатов для дашборда %s: %s",
                dashboard_id,
                str(e),
            )
            raise

    @classmethod
    def _validate_graphs_exist(
        cls,
        db: Session,
        graph_ids: set[UUID],
        dashboard_id: int,
    ) -> None:
        """Проверяет существование графиков и их принадлежность дашборду.

        Args:
            db: Сессия базы данных.
            graph_ids: Множество идентификаторов графиков.
            dashboard_id: Идентификатор дашборда.

        Raises:
            ValueError: Если какие-либо графики не найдены.
        """
        found_graphs = db.execute(
            select(graphs_model.Graph.id).where(
                and_(
                    graphs_model.Graph.id.in_(list(graph_ids)),
                    graphs_model.Graph.dashboard_id == dashboard_id,
                )
            )
        ).scalars().all()

        found_ids = set(found_graphs)
        missing_ids = graph_ids - found_ids

        if missing_ids:
            raise ValueError(
                f"Графики не найдены или не принадлежат дашборду: {missing_ids}"
            )

    @classmethod
    def get_session(cls) -> Session:
        """Создать и вернуть новую сессию базы данных.

        Returns:
            Новая сессия.
        """
        from mko_bi.db.session import get_session
        return get_session()