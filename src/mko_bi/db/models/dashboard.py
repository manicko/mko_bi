from datetime import datetime
from typing import Set

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from mko_bi.db.base import Base


class Dashboard(Base):
    """Модель дашборда BI-системы.

    Атрибуты:
        id: Уникальный идентификатор дашборда.
        name: Название дашборда.
        config: JSON-конфигурация дашборда (структура графиков, фильтров и т.д.).
        created_at: Дата и время создания записи.
        accesses: Связь с правами доступа пользователей.

    Индексы:
        - Уникальный индекс на name
    """

    __tablename__ = "dashboards"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    name: Mapped[str] = Column(
        String(255),
        nullable=False,
        unique=True,
    )
    config: Mapped[str] = Column(
        Text,
        nullable=False,
        default="{}",
    )
    created_at: Mapped[datetime] = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # Связь с правами доступа
    accesses: Mapped[Set["Access"]] = relationship(
        "Access",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Связь с пользователями через права доступа
    users: Mapped[Set["User"]] = relationship(
        "User",
        secondary="accesses",
        back_populates="dashboards",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Dashboard(id={self.id}, name='{self.name}')>"

    def __str__(self) -> str:
        return self.name
