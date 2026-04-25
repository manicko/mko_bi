"""Репозиторий для работы с дашбордами.

Предоставляет методы CRUD для модели Dashboard.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.db.session import SessionLocal

logger = logging.getLogger(__name__)


class DashboardRepository:
    """Репозиторий для операций с дашбордами.

    Предоставляет методы для создания, чтения, обновления и удаления
    дашбордов в базе данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением транзакциями.
    """

    @classmethod
    def get(
        cls, dashboard_id: int, db: SessionLocal
    ) -> Optional[dashboard_model.Dashboard]:
        """Получить дашборд по ID.

        Args:
            dashboard_id: Идентификатор дашборда.
            db: Сессия базы данных.

        Returns:
            Модель дашборда или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(
                select(dashboard_model.Dashboard).where(
                    dashboard_model.Dashboard.id == dashboard_id
                )
            ).scalar_one_or_none()
            if result:
                logger.info("Дашборд получен: id=%s", dashboard_id)
            else:
                logger.warning("Дашборд не найден: id=%s", dashboard_id)
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении дашборда id=%s: %s", dashboard_id, e)
            raise

    @classmethod
    def get_by_user(
        cls, user_id: int, db: SessionLocal
    ) -> list[dashboard_model.Dashboard]:
        """Получить все дашборды, доступные пользователю.

        Args:
            user_id: Идентификатор пользователя.
            db: Сессия базы данных.

        Returns:
            Список дашбордов, доступных пользователю.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            from mko_bi.db.models import access as access_model

            result = (
                db.execute(
                    select(dashboard_model.Dashboard)
                    .join(access_model.Access)
                    .where(access_model.Access.user_id == user_id)
                )
                .scalars()
                .all()
            )
            logger.info(
                "Получены дашборды для пользователя id=%s, количество: %s",
                user_id,
                len(result),
            )
            return result
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении дашбордов для пользователя id=%s: %s", user_id, e
            )
            raise

    @classmethod
    def create(cls, db: SessionLocal, **kwargs) -> Optional[dashboard_model.Dashboard]:
        """Создать новый дашборд.

        Args:
            db: Сессия базы данных.
            **kwargs: Параметры дашборда (name, config).

        Returns:
            Модель созданного дашборда с ID или None при ошибке.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            dashboard_obj = dashboard_model.Dashboard(**kwargs)
            db.add(dashboard_obj)
            db.commit()
            db.refresh(dashboard_obj)
            logger.info(
                "Дашборд создан: id=%s, name=%s", dashboard_obj.id, dashboard_obj.name
            )
            return dashboard_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Ошибка при создании дашборда: %s", e)
            raise

    @classmethod
    def update(
        cls, dashboard_id: int, db: SessionLocal, **kwargs
    ) -> Optional[dashboard_model.Dashboard]:
        """Обновить данные дашборда.

        Args:
            dashboard_id: Идентификатор дашборда.
            db: Сессия базы данных.
            **kwargs: Поля для обновления.

        Returns:
            Обновленная модель дашборда или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            dashboard_obj = db.execute(
                select(dashboard_model.Dashboard).where(
                    dashboard_model.Dashboard.id == dashboard_id
                )
            ).scalar_one_or_none()
            if not dashboard_obj:
                logger.warning("Дашборд не найден для обновления: id=%s", dashboard_id)
                return None
            for key, value in kwargs.items():
                if hasattr(dashboard_obj, key):
                    setattr(dashboard_obj, key, value)
            db.commit()
            db.refresh(dashboard_obj)
            logger.info("Дашборд обновлен: id=%s", dashboard_id)
            return dashboard_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Ошибка при обновлении дашборда id=%s: %s", dashboard_id, e)
            raise

    @classmethod
    def delete(cls, dashboard_id: int, db: SessionLocal) -> bool:
        """Удалить дашборд.

        Args:
            dashboard_id: Идентификатор дашборда.
            db: Сессия базы данных.

        Returns:
            True, если удаление успешно, False - если дашборд не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            dashboard_obj = db.execute(
                select(dashboard_model.Dashboard).where(
                    dashboard_model.Dashboard.id == dashboard_id
                )
            ).scalar_one_or_none()
            if not dashboard_obj:
                logger.warning("Дашборд не найден для удаления: id=%s", dashboard_id)
                return False
            db.delete(dashboard_obj)
            db.commit()
            logger.info("Дашборд удален: id=%s", dashboard_id)
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Ошибка при удалении дашборда id=%s: %s", dashboard_id, e)
            raise

    @classmethod
    def get_session(cls) -> SessionLocal:
        """Создать и вернуть новую сессию базы данных.

        Returns:
            Новая сессия SessionLocal.
        """
        return SessionLocal()

    @classmethod
    def get_all(cls, db: SessionLocal) -> list[dashboard_model.Dashboard]:
        """Получить все дашборды.

        Args:
            db: Сессия базы данных.

        Returns:
            Список всех дашбордов.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(select(dashboard_model.Dashboard)).scalars().all()
            logger.info("Получен список дашбордов, количество: %s", len(result))
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка дашбордов: %s", e)
            raise
