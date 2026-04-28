"""Модель логов обработки данных."""

from datetime import datetime
from uuid import uuid4, UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mko_bi.db.base import Base


class ProcessingLog(Base):
    """Модель логов обработки данных дашбордов.

    Хранит историю обработки данных: когда запускалась обработка,
    какой был статус, сообщения об ошибках и т.д.
    """

    __tablename__ = "processing_logs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    dashboard_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dashboards.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    message: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Связь с дашбордом
    dashboard: Mapped["Dashboard"] = relationship(  # type: ignore[name-defined]
        "Dashboard",
        back_populates="processing_logs",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ProcessingLog id={self.id} status={self.status}>"

    def __str__(self) -> str:
        return f"ProcessingLog {self.id} - {self.status}"
