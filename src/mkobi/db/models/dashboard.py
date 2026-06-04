from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mkobi.db.base import Base

if TYPE_CHECKING:
    from mkobi.db.models.access import DashboardAccess
    from mkobi.db.models.aggregated_data import AggregatedData
    from mkobi.db.models.dashboard_filter_values import DashboardFilterValue
    from mkobi.db.models.filters import Filter
    from mkobi.db.models.graphs import Graph
    from mkobi.db.models.layout import Layout
    from mkobi.db.models.processing_configs import ProcessingConfig
    from mkobi.db.models.processing_logs import ProcessingLog
    from mkobi.db.models.user import User


class Dashboard(Base):
    __tablename__ = "dashboards"
    __table_args__ = (
        Index("idx_dashboards_name", "name", unique=True),
        Index("idx_dashboards_layout_id", "layout_id"),
        Index("idx_dashboards_created_by", "created_by"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    config: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Relationship with access rights
    accesses: Mapped[list[DashboardAccess]] = relationship(
        "DashboardAccess",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Relationship with users through access table
    users: Mapped[list[User]] = relationship(
        "User",
        secondary="dashboard_access",
        back_populates="dashboards",
        lazy="selectin",
        overlaps="accesses,user",
    )

    # Relationship with layout
    layout: Mapped[Layout | None] = relationship(
        "Layout",
        back_populates="dashboards",
        lazy="selectin",
    )

    # Relationship with charts
    graphs: Mapped[list[Graph]] = relationship(
        "Graph",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Relationship with aggregated data
    aggregated_data: Mapped[list[AggregatedData]] = relationship(
        "AggregatedData",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Relationship with filters
    filters: Mapped[list[Filter]] = relationship(
        "Filter",
        secondary="dashboard_filters",
        back_populates="dashboards",
        lazy="selectin",
    )

    # Relationship with processing settings (one-to-one)
    processing_config: Mapped[ProcessingConfig] = relationship(
        "ProcessingConfig",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )

    # Relationship with processing logs
    processing_logs: Mapped[list[ProcessingLog]] = relationship(
        "ProcessingLog",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Relationship with filter values
    filter_values: Mapped[list[DashboardFilterValue]] = relationship(
        "DashboardFilterValue",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Dashboard id={self.id} name={self.name}>"

    def __str__(self) -> str:
        return self.name
