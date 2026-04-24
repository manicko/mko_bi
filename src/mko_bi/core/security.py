import bcrypt
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone
from jose import jwt
from jose.exceptions import JWTError
from mko_bi.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password as string
    """
    password_bytes = password.encode("utf-8")
    # bcrypt has a 72 byte limit for passwords
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hash_value: str) -> bool:
    """Verify a password against a hash.

    Args:
        password: Plain text password to verify
        hash_value: Hashed password to compare against

    Returns:
        True if password matches hash, False otherwise
    """
    password_bytes = password.encode("utf-8")
    # bcrypt has a 72 byte limit for passwords
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return bcrypt.checkpw(password_bytes, hash_value.encode("utf-8"))


def create_access_token(data: Dict) -> str:
    """Create a JWT access token.

    Args:
        data: Dictionary with user data (e.g., {"user_id": 1})

    Returns:
        JWT token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dictionary

    Raises:
        JWTError: If token is invalid or expired
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload
