from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from mko_bi.db.base import Base


class User(Base):
    """User model.

    Represents a system user with role-based access control.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="viewer")

    # Relationships
    accesses = relationship("Access", back_populates="user")


class Dashboard(Base):
    """Dashboard model.

    Represents a dashboard with its configuration.
    """

    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    config = Column(String, nullable=False)  # JSON string
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user = relationship("User")
    accesses = relationship("Access", back_populates="dashboard")


class Access(Base):
    """Access model.

    Represents user access to dashboards.
    """

    __tablename__ = "access"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"))

    # Relationships
    user = relationship("User", back_populates="accesses")
    dashboard = relationship("Dashboard", back_populates="accesses")
