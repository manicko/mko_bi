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

from mko_bi.db.base import Base
from mko_bi.models.user_roles import UserRoleEnum

if TYPE_CHECKING:
    from mko_bi.models.access import DashboardAccess
    from mko_bi.models.dashboard import DashboardConfig


class User(Base):
    """Модель пользователя системы BI Dashboard."""

    __tablename__ = "users"

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

    role: Mapped[UserRoleEnum] = mapped_column(
        Enum(
            UserRoleEnum,
            name="user_role",
        ),
        nullable=False,
        default=UserRoleEnum.viewer,
        server_default=text("'viewer'"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Связь с правами доступа
    accesses: Mapped[list["DashboardAccess"]] = relationship(
        "DashboardAccess",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Связь с дашбордами через таблицу доступа
    dashboards: Mapped[list["DashboardConfig"]] = relationship(
        "Dashboard",
        secondary="dashboard_access",
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role.value}>"

    def __str__(self) -> str:
        return self.email


# Индекс на роль (если часто фильтруешь пользователей по ролям)
Index("ix_users_role", User.role)
