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
