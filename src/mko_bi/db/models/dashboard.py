from datetime import datetime
from uuid import uuid4, UUID
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mko_bi.db.base import Base

if TYPE_CHECKING:
    from mko_bi.models.access import DashboardAccess
    from mko_bi.models.user import UserBase


class Dashboard(Base):
    __tablename__ = "dashboards"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    layout_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("layouts.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )

    # Связь с правами доступа
    accesses: Mapped[list["DashboardAccess"]] = relationship(
        "DashboardAccess",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Связь с пользователями через таблицу доступа
    users: Mapped[list["UserBase"]] = relationship(
        "User",
        secondary="dashboard_access",
        back_populates="dashboards",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Dashboard id={self.id} name={self.name}>"

    def __str__(self) -> str:
        return self.name
