"""Репозиторий для работы с заявками на регистрацию.

Предоставляет методы для создания и чтения заявок на регистрацию.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mkobi.db.models.registration_request import RegistrationRequest
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RegistrationRequestRepository:
    """Репозиторий для операций с заявками на регистрацию."""

    @classmethod
    async def create(
        cls, email: str, ip: str | None, db: AsyncSession
    ) -> RegistrationRequest | None:
        """Создать новую заявку на регистрацию.

        Args:
            email: Email заявителя.
            ip: IP-адрес заявителя.
            db: Асинхронная сессия базы данных.

        Returns:
            Модель созданной заявки или None при ошибке.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            req = RegistrationRequest(email=email, requested_by_ip=ip)
            db.add(req)
            await db.flush()
            await db.refresh(req)
            logger.info("Заявка на регистрацию создана: id=%s, email=%s", req.id, email)
            return req
        except SQLAlchemyError as e:
            logger.error("Ошибка при создании заявки на регистрацию %s: %s", email, e)
            raise

    @classmethod
    async def get_by_email(cls, email: str, db: AsyncSession) -> RegistrationRequest | None:
        """Получить заявку по email.

        Args:
            email: Email для поиска.
            db: Асинхронная сессия базы данных.

        Returns:
            Модель заявки или None, если не найдена.
        """
        try:
            result = await db.execute(
                select(RegistrationRequest).where(RegistrationRequest.email == email)
            )
            req = result.scalar_one_or_none()
            if req:
                logger.info("Заявка найдена: email=%s, status=%s", email, req.status)
            else:
                logger.info("Заявка не найдена: email=%s", email)
            return req
        except SQLAlchemyError as e:
            logger.error("Ошибка при поиске заявки %s: %s", email, e)
            raise

    @classmethod
    async def delete(cls, request_id: UUID, db: AsyncSession) -> bool:
        """Удалить заявку по ID.

        Args:
            request_id: ID заявки.
            db: Асинхронная сессия базы данных.

        Returns:
            True, если удаление успешно, False - если заявка не найдена.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            result = await db.execute(
                select(RegistrationRequest).where(RegistrationRequest.id == request_id)
            )
            req = result.scalar_one_or_none()
            if not req:
                logger.warning("Заявка не найдена для удаления: id=%s", request_id)
                return False
            await db.delete(req)
            await db.flush()
            logger.info("Заявка удалена: id=%s", request_id)
            return True
        except SQLAlchemyError as e:
            logger.error("Ошибка при удалении заявки id=%s: %s", request_id, e)
            raise
