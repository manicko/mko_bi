from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from mko_bi.db.base import Base


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
