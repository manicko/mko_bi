"""Модель глобальных фильтров."""

from datetime import datetime
from typing import Any
from uuid import uuid4, UUID

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Table,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mko_bi.db.base import Base


class Filter(Base):
    """Модель глобальных фильтров дашбордов.

    Фильтры не принадлежат конкретному дашборду, они переиспользуются
    между дашбордами через связи многие-ко-многим.
    """

    __tablename__ = "filters"

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

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("(datetime('now'))"),
    )

    # Связь с дашбордами через промежуточную таблицу
    dashboards: Mapped[list["Dashboard"]] = relationship(  # type: ignore[name-defined]
        "Dashboard",
        secondary="dashboard_filters",
        back_populates="filters",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Filter id={self.id} name={self.name} type={self.type}>"

    def __str__(self) -> str:
        return self.name


# Промежуточная таблица для связи многие-ко-многим между дашбордами и фильтрами
dashboard_filters = Table(
    "dashboard_filters",
    Base.metadata,
    Column("dashboard_id", PG_UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"), primary_key=True),
    Column("filter_id", PG_UUID(as_uuid=True), ForeignKey("filters.id", ondelete="CASCADE"), primary_key=True),
    Index("idx_dashboard_filter", "dashboard_id", "filter_id"),
)