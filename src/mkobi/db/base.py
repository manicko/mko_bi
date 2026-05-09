from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Inheritance from DeclarativeBase provides support for
    declarative style model definition.
    """
