from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    Index,
)
from sqlalchemy.orm import Mapped, relationship

from mko_bi.db.base import Base


class User(Base):
    """Модель пользователя системы BI Dashboard.

    Атрибуты:
        id: Уникальный идентификатор пользователя.
        email: Email пользователя (уникальный).
        password_hash: Хэш пароля (bcrypt).
        role: Роль пользователя (admin/editor/viewer).
        created_at: Дата и время создания записи.
        accesses: Связь с правами доступа к дашбордам.

    Индексы:
        - Уникальный индекс на email
        - Индекс на role для фильтрации по ролям
    """

    __tablename__ = "users"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    email: Mapped[str] = Column(
        String(255),
        nullable=False,
        unique=True,
    )
    password_hash: Mapped[str] = Column(
        String(255),
        nullable=False,
    )
    role: Mapped[str] = Column(
        Enum(
            "admin",
            "editor",
            "viewer",
            name="user_role",
            create_constraint=False,
        ),
        nullable=False,
        default="viewer",
    )
    created_at: Mapped[datetime] = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # Связь с правами доступа
    accesses: Mapped[set["Access"]] = relationship(  # noqa: F821
        "Access",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Связь с дашбордами через права доступа
    dashboards: Mapped[set["Dashboard"]] = relationship(  # noqa: F821
        "Dashboard",
        secondary="accesses",
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    def __str__(self) -> str:
        return self.email


# Индекс на role для быстрого фильтрации
Index("ix_users_role", User.role)
