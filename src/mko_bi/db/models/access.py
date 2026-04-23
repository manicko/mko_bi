from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from mko_bi.db.base import Base


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
