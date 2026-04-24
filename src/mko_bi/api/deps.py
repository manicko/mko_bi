from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from mko_bi.core.security import decode_token
from mko_bi.core.permissions import get_user_by_id
from mko_bi.db.models.user import User as UserModel

reuseable_oauth = HTTPBearer()


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth),
) -> UserModel:
    """Get the current authenticated user from JWT token."""
    try:
        payload = decode_token(token.credentials)
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def get_admin_user(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """Ensure the current user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
