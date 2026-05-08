"""Processing logs model for data processing."""

from datetime import datetime
from uuid import uuid4, UUID

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mkobi.db.base import Base
from mkobi.models.enums import ProcessingStatus


class ProcessingLog(Base):
    """Processing logs model for dashboards.

    Stores data processing history: when processing was started,
    what status it had, error messages, etc.
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

    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(
            ProcessingStatus,
            name="processing_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
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

    __table_args__ = (
        Index("idx_processing_logs_dashboard_id", "dashboard_id"),
    )

    # Relationship with dashboard
    dashboard: Mapped["Dashboard"] = relationship(
        "Dashboard",
        back_populates="processing_logs",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ProcessingLog id={self.id} status={self.status.value}>"

    def __str__(self) -> str:
        return f"ProcessingLog {self.id} - {self.status.value}"
