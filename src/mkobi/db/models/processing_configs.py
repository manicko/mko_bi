"""Модель настроек обработки для дашбордов."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mkobi.db.base import Base


class ProcessingConfig(Base):
    """Модель настроек обработки данных для дашборда.

    Хранит конфигурацию обработки данных, специфичную для каждого дашборда.
    Связана с дашбордом отношением один-к-одному.
    """

    __tablename__ = "processing_configs"

    dashboard_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dashboards.id", ondelete="CASCADE"),
        primary_key=True,
    )

    settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now(),
    )

    # Связь с дашбордом
    dashboard: Mapped["Dashboard"] = relationship(  # type: ignore[name-defined]
        "Dashboard",
        back_populates="processing_config",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ProcessingConfig dashboard_id={self.dashboard_id}>"

    def __str__(self) -> str:
        return f"ProcessingConfig for dashboard {self.dashboard_id}"
