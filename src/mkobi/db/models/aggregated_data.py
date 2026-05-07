from __future__ import annotations

"""Aggregated data model for dashboards."""

from typing import Any, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    BigInteger,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from mkobi.db.base import Base

if TYPE_CHECKING:
    from mkobi.db.models.dashboard import Dashboard
    from mkobi.db.models.graphs import Graph


class JSONBType(TypeDecorator[dict[str, Any]]):
    """JSONB type for PostgreSQL, JSON for other databases."""
    
    impl = JSONB
    cache_ok = True
    
    def load_dialect_impl(self, dialect: Dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            # For SQLite and other databases, use regular JSON
            from sqlalchemy import JSON
            return dialect.type_descriptor(JSON())


class AggregatedData(Base):
    """Aggregated data model for dashboards.

    Stores aggregated data for dashboard graphs.
    Each row represents one chart data point.
    """

    __tablename__ = "aggregated_data"
    __table_args__ = (
        Index("idx_aggregated_data_graph_id", "graph_id"),
        Index("idx_aggregated_data_dashboard_id", "dashboard_id"),
        Index("idx_aggregated_data_dashboard_graph", "dashboard_id", "graph_id"),
        Index("idx_aggregated_data_dims_gin", "dims", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )

    dashboard_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dashboards.id", ondelete="CASCADE"),
        nullable=False,
    )

    graph_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("graphs.id", ondelete="CASCADE"),
        nullable=False,
    )

    dims: Mapped[dict[str, Any]] = mapped_column(
        JSONBType,
        nullable=False,
        default=dict,
    )

    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONBType,
        nullable=False,
        default=dict,
    )

    # Связь с дашбордом
    dashboard: Mapped[Dashboard] = relationship(
        "Dashboard",
        back_populates="aggregated_data",
        lazy="selectin",
    )

    # Связь с графиком
    graph: Mapped[Graph] = relationship(
        "Graph",
        back_populates="aggregated_data",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<AggregatedData id={self.id} "
            f"dashboard_id={self.dashboard_id} "
            f"graph_id={self.graph_id}>"
        )

    def __str__(self) -> str:
        return f"AggregatedData {self.id}"
