from typing import Optional
from mko_bi.db.models.user import User as UserModel
from mko_bi.db.repositories.user_repo import UserRepository
from mko_bi.core.security import hash_password
from mko_bi.models.user import UserDB


def create_user(email: str, password: str, role: str = "viewer") -> UserModel:
    """Create a new user with hashed password.

    Args:
        email: User email address
        password: Plain text password
        role: User role (admin/editor/viewer)

    Returns:
        Created user model

    Raises:
        ValueError: If email already exists
    """
    # Check if user already exists
    existing_user = UserRepository.get_by_email(email)
    if existing_user:
        raise ValueError(f"User with email {email} already exists")

    # Hash password
    password_hash = hash_password(password)

    # Create user
    user_data = {
        "email": email,
        "password_hash": password_hash,
        "role": role,
    }

    return UserRepository.create(user_data)


def get_user_by_email(email: str) -> Optional[UserDB]:
    """Get user by email.

    Args:
        email: User email address

    Returns:
        User model or None
    """
    user = UserRepository.get_by_email(email)
    if user:
        return UserDB(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role,
        )
    return None
