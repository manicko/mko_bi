from typing import Optional
from sqlalchemy.orm import Session

from mko_bi.db.models.access import Access as AccessModel
from mko_bi.db.base import SessionLocal


class AccessRepository:
    """Repository for Access model operations."""

    @classmethod
    def get(cls, user_id: int, dashboard_id: int) -> Optional[AccessModel]:
        """Get access record.

        Args:
            user_id: User ID
            dashboard_id: Dashboard ID

        Returns:
            Access model or None
        """
        with SessionLocal() as session:
            return (
                session
                .query(AccessModel)
                .filter(
                    AccessModel.user_id == user_id,
                    AccessModel.dashboard_id == dashboard_id,
                )
                .first()
            )

    @classmethod
    def create(cls, data: dict) -> AccessModel:
        """Create access record.

        Args:
            data: Access data dictionary

        Returns:
            Created access model
        """
        with SessionLocal() as session:
            access = AccessModel(**data)
            session.add(access)
            session.commit()
            session.refresh(access)
            return access

    @classmethod
    def delete(cls, user_id: int, dashboard_id: int) -> bool:
        """Delete access record.

        Args:
            user_id: User ID
            dashboard_id: Dashboard ID

        Returns:
            True if deleted
        """
        with SessionLocal() as session:
            access = (
                session
                .query(AccessModel)
                .filter(
                    AccessModel.user_id == user_id,
                    AccessModel.dashboard_id == dashboard_id,
                )
                .first()
            )
            if access:
                session.delete(access)
                session.commit()
                return True
            return False
