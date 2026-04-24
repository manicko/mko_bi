from typing import Optional
from mko_bi.db.models.user import User as UserModel
from mko_bi.db.repositories.user_repo import UserRepository
from mko_bi.core.security import hash_password
from mko_bi.models.user import UserDB, UserRead
from pydantic import EmailStr, ValidationError


def create_user(email: str, password: str, role: str = "viewer") -> UserRead:
    """Create a new user with hashed password.

    Args:
        email: User email address
        password: Plain text password
        role: User role (admin/editor/viewer)

    Returns:
        Created user model (without password hash)

    Raises:
        ValueError: If email already exists, invalid email format, or invalid role
    """
    # Validate email format
    try:
        EmailStr(email)
    except ValidationError:
        raise ValueError(f"Invalid email format: {email}")

    # Validate role
    if role not in ("admin", "editor", "viewer"):
        raise ValueError(f"Invalid role: {role}. Must be one of: admin, editor, viewer")

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

    user_model = UserRepository.create(user_data)
    # Return user without password hash
    return UserRead(
        id=user_model.id,
        email=user_model.email,
        role=user_model.role,
    )


def get_user_by_email(email: str) -> Optional[UserRead]:
    """Get user by email (without password hash).

    Args:
        email: User email address

    Returns:
        User model without password hash or None
    """
    user = UserRepository.get_by_email(email)
    if user:
        return UserRead(
            id=user.id,
            email=user.email,
            role=user.role,
        )
    return None
