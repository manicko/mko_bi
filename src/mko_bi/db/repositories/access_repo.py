"""Репозиторий для работы с правами доступа.

Предоставляет методы для управления правами доступа пользователей к дашбордам.
Все методы используют контекстный менеджер сессий и обрабатывают ошибки.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mko_bi.db.models import access as access_model
from mko_bi.db.models import dashboard as dashboard_model
from mko_bi.db.session import SessionLocal

logger = logging.getLogger(__name__)


class AccessRepository:
    """Репозиторий для операций с правами доступа.

    Предоставляет методы для управления правами доступа пользователей
    к дашбордам. Все операции выполняются в рамках отдельной сессии
    базы данных с автоматическим управлением транзакциями.
    """

    @classmethod
    def grant_access(
        cls,
        db: SessionLocal,
        user_id: UUID,
        dashboard_id: UUID,
        permission: str = "view",
    ) -> access_model.DashboardAccess | None:
        """Предоставить пользователю доступ к дашборду.

        Args:
            user_id: Идентификатор пользователя (UUID).
            dashboard_id: Идентификатор дашборда (UUID).
            permission: Уровень доступа (view/edit/admin).
            db: Сессия базы данных.

        Returns:
            Модель права доступа или None при ошибке.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            # Проверяем, не существует ли уже такое право доступа
            existing = db.execute(
                select(access_model.DashboardAccess).where(
                    access_model.DashboardAccess.user_id == user_id,
                    access_model.DashboardAccess.dashboard_id == dashboard_id,
                )
            ).scalar_one_or_none()
            if existing:
                logger.warning(
                    "Право доступа уже существует: user_id=%s, dashboard_id=%s",
                    user_id,
                    dashboard_id,
                )
                return existing

            access_obj = access_model.DashboardAccess(
                user_id=user_id,
                dashboard_id=dashboard_id,
                permission=permission,
            )
            db.add(access_obj)
            db.commit()
            db.refresh(access_obj)
            logger.info(
                "Право доступа предоставлено: user_id=%s, dashboard_id=%s, permission=%s",
                user_id,
                dashboard_id,
                permission,
            )
            return access_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "Ошибка при предоставлении доступа user_id=%s, dashboard_id=%s: %s",
                user_id,
                dashboard_id,
                e,
            )
            raise

    @classmethod
    def revoke_access(cls, user_id: UUID, dashboard_id: UUID, db: SessionLocal) -> bool:
        """Отозвать доступ пользователя к дашборду.

        Args:
            user_id: Идентификатор пользователя (UUID).
            dashboard_id: Идентификатор дашборда (UUID).
            db: Сессия базы данных.

        Returns:
            True, если доступ успешно отозван, False - если право доступа не найдено.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            access_obj = db.execute(
                select(access_model.DashboardAccess).where(
                    access_model.DashboardAccess.user_id == user_id,
                    access_model.DashboardAccess.dashboard_id == dashboard_id,
                )
            ).scalar_one_or_none()
            if not access_obj:
                logger.warning(
                    "Право доступа не найдено для отзыва: user_id=%s, dashboard_id=%s",
                    user_id,
                    dashboard_id,
                )
                return False
            db.delete(access_obj)
            db.commit()
            logger.info(
                "Право доступа отозвано: user_id=%s, dashboard_id=%s",
                user_id,
                dashboard_id,
            )
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "Ошибка при отзыве доступа user_id=%s, dashboard_id=%s: %s",
                user_id,
                dashboard_id,
                e,
            )
            raise

    @classmethod
    def check_access(
        cls, user_id: UUID, dashboard_id: UUID, db: SessionLocal
    ) -> str | None:
        """Проверить уровень доступа пользователя к дашборду.

        Args:
            user_id: Идентификатор пользователя (UUID).
            dashboard_id: Идентификатор дашборда (UUID).
            db: Сессия базы данных.

        Returns:
            Уровень доступа (view/edit/admin) или None, если доступа нет.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            access_obj = db.execute(
                select(access_model.DashboardAccess).where(
                    access_model.DashboardAccess.user_id == user_id,
                    access_model.DashboardAccess.dashboard_id == dashboard_id,
                )
            ).scalar_one_or_none()
            if access_obj:
                logger.info(
                    "Проверка доступа: user_id=%s, dashboard_id=%s, permission=%s",
                    user_id,
                    dashboard_id,
                    access_obj.permission,
                )
                return access_obj.permission
            logger.warning(
                "Доступ отсутствует: user_id=%s, dashboard_id=%s",
                user_id,
                dashboard_id,
            )
            return None
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при проверке доступа user_id=%s, dashboard_id=%s: %s",
                user_id,
                dashboard_id,
                e,
            )
            raise

    @classmethod
    def get_user_dashboards(
        cls, user_id: UUID, db: SessionLocal
    ) -> list[dashboard_model.Dashboard]:
        """Получить все дашборды, доступные пользователю.

        Args:
            user_id: Идентификатор пользователя (UUID).
            db: Сессия базы данных.

        Returns:
            Список дашбордов, доступных пользователю.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = (
                db
                .execute(
                    select(dashboard_model.Dashboard)
                    .join(access_model.DashboardAccess)
                    .where(access_model.DashboardAccess.user_id == user_id)
                )
                .scalars()
                .all()
            )
            logger.info(
                "Получены дашборды пользователя id=%s, количество: %s",
                user_id,
                len(result),
            )
            return result
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении дашбордов пользователя id=%s: %s", user_id, e
            )
            raise

    @classmethod
    def get_session(cls) -> SessionLocal:
        """Создать и вернуть новую сессию базы данных.

        Returns:
            Новая сессия SessionLocal.
        """
        return SessionLocal()

    @classmethod
    def get_all(cls, db: SessionLocal) -> list[access_model.DashboardAccess]:
        """Получить все права доступа.

        Args:
            db: Сессия базы данных.

        Returns:
            Список всех прав доступа.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = db.execute(select(access_model.DashboardAccess)).scalars().all()
            logger.info("Получен список прав доступа, количество: %s", len(result))
            return result
        except SQLAlchemyError as e:
            logger.error("Ошибка при получении списка прав доступа: %s", e)
            raise