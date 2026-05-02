from __future__ import annotations

from datetime import datetime
from uuid import uuid4, UUID
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    String,
    JSON,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mko_bi.db.base import Base

if TYPE_CHECKING:
    from mko_bi.db.models.dashboard import Dashboard


class Layout(Base):
    """Модель UI компоновки дашборда.
    
    Хранит структуру UI дашборда (grid, graphs, filters, bindings)
    в формате JSON.
    """
    
    __tablename__ = "layouts"
    
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
    
    definition: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    
    # Связь с дашбордами
    dashboards: Mapped[list[Dashboard]] = relationship(
        "Dashboard",
        back_populates="layout",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Layout id={self.id} name={self.name}>"
    
    def __str__(self) -> str:
        return self.name