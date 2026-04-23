import bcrypt
from typing import Optional


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password as string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hash_value: str) -> bool:
    """Verify a password against a hash.

    Args:
        password: Plain text password to verify
        hash_value: Hashed password to compare against

    Returns:
        True if password matches hash, False otherwise
    """
    return bcrypt.checkpw(password.encode("utf-8"), hash_value.encode("utf-8"))
