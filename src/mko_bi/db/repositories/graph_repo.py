"""Репозиторий для работы с графиками.

Предоставляет методы CRUD для модели Graph.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import graphs as graph_model
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class GraphRepository:
    """Репозиторий для операций с графиками.

    Предоставляет методы для создания, чтения, обновления и удаления
    графиков в базе данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением транзакциями.
    """

    @classmethod
    def get(
        cls, graph_id: UUID, db: Session
    ) -> graph_model.Graph | None:
        """Получить график по ID.

        Args:
            graph_id: Идентификатор графика (UUID).
            db: Сессия базы данных.

        Returns:
            Модель графика или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(
                select(graph_model.Graph).where(
                    graph_model.Graph.id == graph_id
                )
            ).scalar_one_or_none()
            if result:
                logger.info("График получен: id=%s", graph_id)
            else:
                logger.warning("График не найден: id=%s", graph_id)
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении графика id=%s: %s", graph_id, e)
            raise

    @classmethod
    def get_by_dashboard_id(
        cls, dashboard_id: UUID, db: Session
    ) -> list[graph_model.Graph]:
        """Получить графики по ID дашборда.

        Args:
            dashboard_id: Идентификатор дашборда (UUID).
            db: Сессия базы данных.

        Returns:
            Список графиков дашборда.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = (
                db.execute(
                    select(graph_model.Graph).where(
                        graph_model.Graph.dashboard_id == dashboard_id
                    )
                )
                .scalars()
                .all()
            )
            logger.info(
                "Получены графики для дашборда id=%s, количество: %s",
                dashboard_id,
                len(result),
            )
            return list(result)
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении графиков для дашборда id=%s: %s",
                dashboard_id,
                e,
            )
            raise

    @classmethod
    def get_by_name_and_dashboard(
        cls, name: str, dashboard_id: UUID, db: Session
    ) -> graph_model.Graph | None:
        """Получить график по имени и ID дашборда.

        Args:
            name: Имя графика.
            dashboard_id: Идентификатор дашборда (UUID).
            db: Сессия базы данных.

        Returns:
            Модель графика или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = (
                db.execute(
                    select(graph_model.Graph)
                    .where(graph_model.Graph.name == name)
                    .where(graph_model.Graph.dashboard_id == dashboard_id)
                )
                .scalar_one_or_none()
            )
            if result:
                logger.info(
                    "График получен: name=%s, dashboard_id=%s",
                    name,
                    dashboard_id,
                )
            else:
                logger.warning(
                    "График не найден: name=%s, dashboard_id=%s",
                    name,
                    dashboard_id,
                )
            return result
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении графика name=%s, dashboard_id=%s: %s",
                name,
                dashboard_id,
                e,
            )
            raise

    @classmethod
    def create(cls, db: Session, **kwargs) -> graph_model.Graph | None:
        """Создать новый график.

        Args:
            db: Сессия базы данных.
            **kwargs: Параметры графика (name, type, dashboard_id, config, dimensions, metrics).

        Returns:
            Модель созданного графика с ID или None при ошибке.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            graph_obj = graph_model.Graph(**kwargs)
            db.add(graph_obj)
            db.flush()
            db.refresh(graph_obj)
            logger.info(
                "График создан: id=%s, name=%s", graph_obj.id, graph_obj.name
            )
            return graph_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при создании графика: %s", e)
            raise

    @classmethod
    def update(
        cls, graph_id: UUID, db: Session, **kwargs
    ) -> graph_model.Graph | None:
        """Обновить данные графика.

        Args:
            graph_id: Идентификатор графика (UUID).
            db: Сессия базы данных.
            **kwargs: Поля для обновления.

        Returns:
            Обновленная модель графика или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            graph_obj = db.execute(
                select(graph_model.Graph).where(
                    graph_model.Graph.id == graph_id
                )
            ).scalar_one_or_none()
            if not graph_obj:
                logger.warning("График не найден для обновления: id=%s", graph_id)
                return None
            for key, value in kwargs.items():
                if hasattr(graph_obj, key):
                    setattr(graph_obj, key, value)
            db.flush()
            db.refresh(graph_obj)
            logger.info("График обновлен: id=%s", graph_id)
            return graph_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при обновлении графика id=%s: %s", graph_id, e)
            raise

    @classmethod
    def delete(cls, graph_id: UUID, db: Session) -> bool:
        """Удалить график.

        Args:
            graph_id: Идентификатор графика (UUID).
            db: Сессия базы данных.

        Returns:
            True, если удаление успешно, False - если график не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            graph_obj = db.execute(
                select(graph_model.Graph).where(
                    graph_model.Graph.id == graph_id
                )
            ).scalar_one_or_none()
            if not graph_obj:
                logger.warning("График не найден для удаления: id=%s", graph_id)
                return False
            db.delete(graph_obj)
            db.flush()
            logger.info("График удален: id=%s", graph_id)
            return True
        except SQLAlchemyError as e:
            logger.error("Ошибка при удалении графика id=%s: %s", graph_id, e)
            raise

    @classmethod
    def get_all(cls, db: Session) -> list[graph_model.Graph]:
        """Получить все графики.

        Args:
            db: Сессия базы данных.

        Returns:
            Список всех графиков.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(select(graph_model.Graph)).scalars().all()
            logger.info("Получен список графиков, количество: %s", len(result))
            return list(result)
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка графиков: %s", e)
            raise

    @classmethod
    def get_session(cls) -> Session:
        """Создать и вернуть новую сессию базы данных.

        Returns:
            Новая сессия.
        """
        from mko_bi.db.session import _get_SessionLocal
        SessionLocal = _get_SessionLocal()
        return SessionLocal()  # type: ignore[no-any-return]
