from typing import Optional
from sqlalchemy.orm import Session

from mko_bi.db.models.dashboard import Dashboard as DashboardModel
from mko_bi.db.base import SessionLocal


class DashboardRepository:
    """Repository for Dashboard model operations."""

    @classmethod
    def get(cls, dashboard_id: int) -> Optional[DashboardModel]:
        """Get dashboard by ID.

        Args:
            dashboard_id: Dashboard ID

        Returns:
            Dashboard model or None
        """
        with SessionLocal() as session:
            return (
                session
                .query(DashboardModel)
                .filter(DashboardModel.id == dashboard_id)
                .first()
            )

    @classmethod
    def get_by_name(cls, name: str) -> Optional[DashboardModel]:
        """Get dashboard by name.

        Args:
            name: Dashboard name

        Returns:
            Dashboard model or None
        """
        with SessionLocal() as session:
            return (
                session
                .query(DashboardModel)
                .filter(DashboardModel.name == name)
                .first()
            )

    @classmethod
    def create(cls, data: dict) -> DashboardModel:
        """Create a new dashboard.

        Args:
            data: Dashboard data dictionary

        Returns:
            Created dashboard model
        """
        with SessionLocal() as session:
            dashboard = DashboardModel(**data)
            session.add(dashboard)
            session.commit()
            session.refresh(dashboard)
            return dashboard

    @classmethod
    def update(cls, dashboard_id: int, data: dict) -> Optional[DashboardModel]:
        """Update dashboard.

        Args:
            dashboard_id: Dashboard ID
            data: Update data

        Returns:
            Updated dashboard model or None
        """
        with SessionLocal() as session:
            dashboard = (
                session
                .query(DashboardModel)
                .filter(DashboardModel.id == dashboard_id)
                .first()
            )
            if dashboard:
                for key, value in data.items():
                    setattr(dashboard, key, value)
                session.commit()
                session.refresh(dashboard)
            return dashboard

    @classmethod
    def delete(cls, dashboard_id: int) -> bool:
        """Delete dashboard.

        Args:
            dashboard_id: Dashboard ID

        Returns:
            True if deleted
        """
        with SessionLocal() as session:
            dashboard = (
                session
                .query(DashboardModel)
                .filter(DashboardModel.id == dashboard_id)
                .first()
            )
            if dashboard:
                session.delete(dashboard)
                session.commit()
                return True
            return False

    @classmethod
    def list_all(cls) -> list:
        """List all dashboards.

        Returns:
            List of dashboard models
        """
        with SessionLocal() as session:
            return session.query(DashboardModel).all()
