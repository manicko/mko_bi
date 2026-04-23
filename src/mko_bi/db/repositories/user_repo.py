from typing import Optional
from sqlalchemy.orm import Session

from mko_bi.db.models.user import User as UserModel
from mko_bi.db.base import SessionLocal


class UserRepository:
    """Repository for User model operations."""

    @classmethod
    def get(cls, user_id: int) -> Optional[UserModel]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User model or None
        """
        with SessionLocal() as session:
            return session.query(UserModel).filter(UserModel.id == user_id).first()

    @classmethod
    def get_by_email(cls, email: str) -> Optional[UserModel]:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User model or None
        """
        with SessionLocal() as session:
            return session.query(UserModel).filter(UserModel.email == email).first()

    @classmethod
    def create(cls, data: dict) -> UserModel:
        """Create a new user.

        Args:
            data: User data dictionary

        Returns:
            Created user model
        """
        with SessionLocal() as session:
            user = UserModel(**data)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    @classmethod
    def update(cls, user_id: int, data: dict) -> Optional[UserModel]:
        """Update user.

        Args:
            user_id: User ID
            data: Update data

        Returns:
            Updated user model or None
        """
        with SessionLocal() as session:
            user = session.query(UserModel).filter(UserModel.id == user_id).first()
            if user:
                for key, value in data.items():
                    setattr(user, key, value)
                session.commit()
                session.refresh(user)
            return user

    @classmethod
    def delete(cls, user_id: int) -> bool:
        """Delete user.

        Args:
            user_id: User ID

        Returns:
            True if deleted
        """
        with SessionLocal() as session:
            user = session.query(UserModel).filter(UserModel.id == user_id).first()
            if user:
                session.delete(user)
                session.commit()
                return True
            return False
