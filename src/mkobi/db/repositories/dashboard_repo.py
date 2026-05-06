"""Репозиторий для работы с дашбордами.

Предоставляет методы CRUD для модели Dashboard.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mkobi.db.models import dashboard as dashboard_model
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DashboardRepository:
    """Репозиторий для операций с дашбордами.

    Предоставляет методы для создания, чтения, обновления и удаления
    дашбордов в базе данных. Все операции выполняются в рамках
    отдельной сессии базы данных с автоматическим управлением транзакциями.
    """

    @classmethod
    async def get(
        cls, dashboard_id: UUID, db: AsyncSession
    ) -> dashboard_model.Dashboard | None:
        """Получить дашборд по ID.

        Args:
            dashboard_id: Идентификатор дашборда (UUID).
            db: Асинхронная сессия базы данных.

        Returns:
            Модель дашборда или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(dashboard_model.Dashboard).where(
                    dashboard_model.Dashboard.id == dashboard_id
                )
            )
            dashboard = result.scalar_one_or_none()
            if dashboard:
                logger.info("Дашборд получен: id=%s", dashboard_id)
            else:
                logger.warning("Дашборд не найден: id=%s", dashboard_id)
            return dashboard
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении дашборда id=%s: %s", dashboard_id, e)
            raise

    @classmethod
    async def get_by_user(
        cls, user_id: UUID, db: AsyncSession
    ) -> list[dashboard_model.Dashboard]:
        """Получить все дашборды, доступные пользователю.

        Args:
            user_id: Идентификатор пользователя (UUID).
            db: Асинхронная сессия базы данных.

        Returns:
            Список дашбордов, доступных пользователю.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            from mkobi.db.models import access as access_model

            result = await db.execute(
                select(dashboard_model.Dashboard)
                .join(access_model.DashboardAccess)
                .where(access_model.DashboardAccess.user_id == user_id)
            )
            dashboards = list(result.scalars().all())
            logger.info(
                "Получены дашборды для пользователя id=%s, количество: %s",
                user_id,
                len(dashboards),
            )
            return dashboards
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении дашбордов для пользователя id=%s: %s", user_id, e
            )
            raise

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs) -> dashboard_model.Dashboard | None:
        """Создать новый дашборд.

        Args:
            db: Асинхронная сессия базы данных.
            **kwargs: Параметры дашборда (name, config).

        Returns:
            Модель созданного дашборда с ID или None при ошибке.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            dashboard_obj = dashboard_model.Dashboard(**kwargs)
            db.add(dashboard_obj)
            await db.flush()
            await db.refresh(dashboard_obj)
            logger.info(
                "Дашборд создан: id=%s, name=%s", dashboard_obj.id, dashboard_obj.name
            )
            return dashboard_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при создании дашборда: %s", e)
            raise

    @classmethod
    async def update(
        cls, dashboard_id: UUID, db: AsyncSession, **kwargs
    ) -> dashboard_model.Dashboard | None:
        """Обновить данные дашборда.

        Args:
            dashboard_id: Идентификатор дашборда (UUID).
            db: Асинхронная сессия базы данных.
            **kwargs: Поля для обновления.

        Returns:
            Обновленная модель дашборда или None, если не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(dashboard_model.Dashboard).where(
                    dashboard_model.Dashboard.id == dashboard_id
                )
            )
            dashboard_obj = result.scalar_one_or_none()
            if not dashboard_obj:
                logger.warning("Дашборд не найден для обновления: id=%s", dashboard_id)
                return None
            for key, value in kwargs.items():
                if hasattr(dashboard_obj, key):
                    setattr(dashboard_obj, key, value)
            await db.flush()
            await db.refresh(dashboard_obj)
            logger.info("Дашборд обновлен: id=%s", dashboard_id)
            return dashboard_obj
        except SQLAlchemyError as e:
            logger.error("Ошибка при обновлении дашборда id=%s: %s", dashboard_id, e)
            raise

    @classmethod
    async def delete(cls, dashboard_id: UUID, db: AsyncSession) -> bool:
        """Удалить дашборд.

        Args:
            dashboard_id: Идентификатор дашборда (UUID).
            db: Асинхронная сессия базы данных.

        Returns:
            True, если удаление успешно, False - если дашборд не найден.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(dashboard_model.Dashboard).where(
                    dashboard_model.Dashboard.id == dashboard_id
                )
            )
            dashboard_obj = result.scalar_one_or_none()
            if not dashboard_obj:
                logger.warning("Дашборд не найден для удаления: id=%s", dashboard_id)
                return False
            await db.delete(dashboard_obj)
            await db.flush()
            logger.info("Дашборд удален: id=%s", dashboard_id)
            return True
        except SQLAlchemyError as e:
            logger.error("Ошибка при удалении дашборда id=%s: %s", dashboard_id, e)
            raise

    @classmethod
    async def get_all(cls, db: AsyncSession) -> list[dashboard_model.Dashboard]:
        """Получить все дашборды.

        Args:
            db: Асинхронная сессия базы данных.

        Returns:
            Список всех дашбордов.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(select(dashboard_model.Dashboard))
            dashboards = list(result.scalars().all())
            logger.info("Получен список дашбордов, количество: %s", len(dashboards))
            return dashboards
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка дашбордов: %s", e)
            raise
