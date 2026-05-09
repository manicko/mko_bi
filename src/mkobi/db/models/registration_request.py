"""Registration request model."""

from __future__ import annotations

from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import TYPE_CHECKING
from uuid import uuid4, UUID

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import INET, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mkobi.db.base import Base
from mkobi.models.enums import RegistrationStatus

if TYPE_CHECKING:
    from mkobi.db.models.user import User


class RegistrationRequest(Base):
    """Registration request model for user signups.

    Requests are created via /api/v1/auth/register-request
    and processed by administrators.
    """

    __tablename__ = "registration_requests"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(
            RegistrationStatus,
            name="registration_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
        default=RegistrationStatus.PENDING,
        server_default=text("'pending'"),
    )

    requested_by_ip: Mapped[IPv4Address | IPv6Address | None] = mapped_column(
        INET,
        nullable=True,
    )

    reviewed_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Relationship with user who reviewed the request
    reviewer: Mapped[User | None] = relationship(
        "User",
        back_populates="reviewed_registration_requests",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<RegistrationRequest id={self.id} email={self.email} status={self.status.value}>"

    def __str__(self) -> str:
        return f"{self.email} ({self.status.value})"
