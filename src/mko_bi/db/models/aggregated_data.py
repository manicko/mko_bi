from __future__ import annotations

"""Модель агрегированных данных дашбордов."""

from typing import Any, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    BigInteger,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from mko_bi.db.base import Base

if TYPE_CHECKING:
    from mko_bi.db.models.dashboard import Dashboard
    from mko_bi.db.models.graphs import Graph


class JSONBType(TypeDecorator[dict[str, Any]]):
    """Тип данных JSONB для PostgreSQL, JSON для других БД."""
    
    impl = JSONB
    cache_ok = True
    
    def load_dialect_impl(self, dialect: Dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            # Для SQLite и других БД используем обычный JSON
            from sqlalchemy import JSON
            return dialect.type_descriptor(JSON())


class AggregatedData(Base):
    """Модель агрегированных данных дашбордов.

    Хранит агрегированные данные для графиков дашбордов.
    Каждая строка представляет одну точку графика.
    """

    __tablename__ = "aggregated_data"

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
