from __future__ import annotations

"""Модель определений графиков дашбордов."""

from datetime import datetime
from uuid import uuid4, UUID
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mko_bi.db.base import Base
from mko_bi.models.enums import GraphType

if TYPE_CHECKING:
    from mko_bi.db.models.dashboard import Dashboard
    from mko_bi.db.models.aggregated_data import AggregatedData


class Graph(Base):
    """Модель определений графиков дашбордов.

    Хранит конфигурацию графиков: тип, настройки визуализации,
    измерения и метрики.
    """

    __tablename__ = "graphs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    dashboard_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dashboards.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    type: Mapped[GraphType] = mapped_column(
        Enum(
            GraphType,
            name="graph_type",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )

    config: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    dimensions: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    metrics: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Связь с дашбордом
    dashboard: Mapped[Dashboard] = relationship(
        "Dashboard",
        back_populates="graphs",
        lazy="selectin",
    )

    # Связь с агрегированными данными
    aggregated_data: Mapped[list[AggregatedData]] = relationship(
        "AggregatedData",
        back_populates="graph",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        # Уникальное ограничение: комбинация dashboard_id и name должна быть уникальной
        UniqueConstraint("dashboard_id", "name", name="uq_graph_dashboard_name"),
    )

    def __repr__(self) -> str:
        return f"<Graph id={self.id} name={self.name} type={self.type.value}>"

    def __str__(self) -> str:
        return f"{self.name} ({self.type.value})"
