from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Enum,
    ForeignKey,
    Index,
    PrimaryKeyConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mko_bi.db.base import Base
from mko_bi.models.user_roles import PermissionEnum

if TYPE_CHECKING:
    from mko_bi.models.dashboard import DashboardConfig
    from mko_bi.models.user import UserBase


class DashboardAccess(Base):
    """Модель прав доступа пользователя к дашборду."""

    __tablename__ = "dashboard_access"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    dashboard_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dashboards.id", ondelete="CASCADE"),
        nullable=False,
    )

    permission: Mapped[PermissionEnum] = mapped_column(
        Enum(
            PermissionEnum,
            name="dashboard_permission_level",
        ),
        nullable=False,
        default=PermissionEnum.view,
        server_default=text("'view'"),
    )

    # Связи
    user: Mapped["UserBase"] = relationship(
        "User",
        back_populates="accesses",
    )

    dashboard: Mapped["DashboardConfig"] = relationship(
        "Dashboard",
        back_populates="accesses",
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "user_id",
            "dashboard_id",
            name="dashboard_access_pkey",
        ),
        Index("idx_access_dashboard", "dashboard_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<DashboardAccess "
            f"user_id={self.user_id} "
            f"dashboard_id={self.dashboard_id} "
            f"permission={self.permission.value}>"
        )
