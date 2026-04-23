from typing import Optional
from mko_bi.db.models.access import Access as AccessModel
from mko_bi.db.models.user import User as UserModel
from mko_bi.db.models.dashboard import Dashboard as DashboardModel
from mko_bi.db.repositories.access_repo import AccessRepository


def check_access(user_id: int, dashboard_id: int) -> bool:
    """Check if a user has access to a dashboard.

    Args:
        user_id: User ID to check
        dashboard_id: Dashboard ID to check access for

    Returns:
        True if user has access, False otherwise
    """
    # Admin users have access to all dashboards
    user = get_user_by_id(user_id)
    if user and user.role == "admin":
        return True

    # Check specific access record
    access = AccessRepository.get(user_id, dashboard_id)
    return access is not None


def grant_access(user_id: int, dashboard_id: int) -> bool:
    """Grant access to a dashboard for a user.

    Args:
        user_id: User ID to grant access to
        dashboard_id: Dashboard ID to grant access to

    Returns:
        True if granted successfully
    """
    access_data = {
        "user_id": user_id,
        "dashboard_id": dashboard_id,
    }
    AccessRepository.create(access_data)
    return True


def revoke_access(user_id: int, dashboard_id: int) -> bool:
    """Revoke access to a dashboard for a user.

    Args:
        user_id: User ID to revoke access from
        dashboard_id: Dashboard ID to revoke access from

    Returns:
        True if revoked successfully
    """
    return AccessRepository.delete(user_id, dashboard_id)


def get_user_by_id(user_id: int) -> Optional[UserModel]:
    """Get user by ID.

    Args:
        user_id: User ID to look up

    Returns:
        User model or None if not found
    """
    return UserRepository.get(user_id)


def get_user_by_email(email: str) -> Optional[UserModel]:
    """Get user by email.

    Args:
        email: Email to look up

    Returns:
        User model or None if not found
    """
    return UserRepository.get_by_email(email)
