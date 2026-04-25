from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy.

    Наследование от DeclarativeBase обеспечивает поддержку
    декларативного стиля определения моделей.
    """
