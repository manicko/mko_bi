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
