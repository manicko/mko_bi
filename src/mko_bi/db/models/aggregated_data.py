"""Модель агрегированных данных дашбордов."""

from uuid import UUID

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mko_bi.db.base import Base


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

    dims: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    metrics: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Связь с дашбордом
    dashboard: Mapped["Dashboard"] = relationship(
        "Dashboard",
        back_populates="aggregated_data",
        lazy="selectin",
    )

    # Связь с графиком
    graph: Mapped["Graph"] = relationship(
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
