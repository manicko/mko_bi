from sqlalchemy import (
    Column,
    Enum,
    ForeignKey,
    Integer,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, relationship

from mko_bi.db.base import Base


class Access(Base):
    """Модель прав доступа пользователя к дашборду.

    Атрибуты:
        id: Уникальный идентификатор права доступа.
        user_id: ID пользователя (внешний ключ).
        dashboard_id: ID дашборда (внешний ключ).
        permission_level: Уровень доступа (read/write/admin).
        user: Связь с моделью пользователя.
        dashboard: Связь с моделью дашборда.

    Индексы:
        - Уникальный индекс на комбинацию user_id и dashboard_id
        - Индекс на user_id
        - Индекс на dashboard_id
    """

    __tablename__ = "accesses"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    dashboard_id: Mapped[int] = Column(
        Integer,
        ForeignKey("dashboards.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_level: Mapped[str] = Column(
        Enum(
            "read",
            "write",
            "admin",
            name="access_permission_level",
            create_constraint=False,
        ),
        nullable=False,
        default="read",
    )

    # Связи
    user: Mapped["User"] = relationship(
        "User",
        back_populates="accesses",
    )
    dashboard: Mapped["Dashboard"] = relationship(
        "Dashboard",
        back_populates="accesses",
    )

    def __repr__(self) -> str:
        return (
            f"<Access(id={self.id}, user_id={self.user_id}, "
            f"dashboard_id={self.dashboard_id}, "
            f"permission='{self.permission_level}')>"
        )


# Индексы для быстрого поиска
Index("ix_accesses_user_id", Access.user_id)
Index("ix_accesses_dashboard_id", Access.dashboard_id)
Index("ix_accesses_permission_level", Access.permission_level)
