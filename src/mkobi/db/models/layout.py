from __future__ import annotations

from datetime import datetime
from uuid import uuid4, UUID
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mkobi.db.base import Base

if TYPE_CHECKING:
    from mkobi.db.models.dashboard import Dashboard


class Layout(Base):
    """UI layout model.
    
    Stores dashboard UI structure (grid, graphs, filters, bindings)
    in JSON format.
    """
    
    __tablename__ = "layouts"
    __table_args__ = (Index("idx_layouts_name", "name", unique=True),)

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

    definition: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
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

    # Relationship with dashboards
    dashboards: Mapped[list[Dashboard]] = relationship(
        "Dashboard",
        back_populates="layout",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Layout id={self.id} name={self.name}>"

    def __str__(self) -> str:
        return self.name