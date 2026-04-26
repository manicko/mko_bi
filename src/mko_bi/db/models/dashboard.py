from datetime import datetime
from uuid import uuid4, UUID
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    JSON,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mko_bi.db.base import Base

if TYPE_CHECKING:
    from mko_bi.models.access import DashboardAccess
    from mko_bi.models.layout import Layout
    from mko_bi.models.graphs import Graph
    from mko_bi.models.aggregated_data import AggregatedData


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
        JSON,
        nullable=False,
        default=dict,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("(datetime('now'))"),
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("(datetime('now'))"),
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
    
    # Связь с layout
    layout: Mapped["Layout"] = relationship(
        "Layout",
        back_populates="dashboards",
        lazy="selectin",
    )

    # Связь с графиками
    graphs: Mapped[list["Graph"]] = relationship(
        "Graph",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Связь с агрегированными данными
    aggregated_data: Mapped[list["AggregatedData"]] = relationship(
        "AggregatedData",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Dashboard id={self.id} name={self.name}>"
    
    def __str__(self) -> str:
        return self.name
