from datetime import datetime
from uuid import uuid4, UUID
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mkobi.db.base import Base
from mkobi.models.enums import UserRole

if TYPE_CHECKING:
    from mkobi.db.models.access import DashboardAccess
    from mkobi.db.models.dashboard import Dashboard
    from mkobi.db.models.registration_request import RegistrationRequest


class User(Base):
    """User model for BI Dashboard system."""

    __tablename__ = "users"
    __table_args__ = (Index("ix_users_role", "role"),)

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

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
        default=UserRole.VIEWER,
        server_default=text("'viewer'"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    force_password_change: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
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

    # Relationship with access rights
    accesses: Mapped[list["DashboardAccess"]] = relationship(
        "DashboardAccess",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        overlaps="users",
    )

    # Relationship with dashboards through access table
    dashboards: Mapped[list["Dashboard"]] = relationship(
        "Dashboard",
        secondary="dashboard_access",
        back_populates="users",
        lazy="selectin",
        overlaps="accesses,dashboard",
    )

    # Relationship with registration requests reviewed by user
    reviewed_registration_requests: Mapped[list["RegistrationRequest"]] = relationship(
        "RegistrationRequest",
        back_populates="reviewer",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role.value}>"

    def __str__(self) -> str:
        return self.email
