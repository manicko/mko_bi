"""User authentication and registration service.

Provides business logic for registration, authentication and authorization
users in the BI Dashboard system. Uses class-based approach.
"""

import re
from typing import Any, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.core.logging_config import get_logger
from mkobi.core.redis_client import get_async_redis_client
from mkobi.core.security import (
    AsyncRateLimiter,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from mkobi.db.repositories.registration_request_repo import (
    RegistrationRequestRepository,
)
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.db.session import get_session
from mkobi.interfaces.service_interfaces import IAuthService
from mkobi.models.enums import UserRole
from mkobi.models.user import UserRead

logger = get_logger(__name__)

# Regular expression for email validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class AuthService(IAuthService):
    """User authentication and registration service.

    Implements IAuthService interface. Uses class-based approach
    for all authentication and registration operations.
    """

    def __init__(self) -> None:
        self._rate_limiter = AsyncRateLimiter(get_async_redis_client())

    def _validate_role(self, role: str) -> None:
        """Validate that role is allowed.

        Args:
            role: User role to validate.

        Raises:
            ValueError: If role is not in allowed list.
        """
        try:
            UserRole(role)
        except ValueError as err:
            logger.error(
                "Invalid role",
                extra={"role": role, "allowed_roles": [e.value for e in UserRole]},
            )
            raise ValueError(
                f"Invalid role: '{role}'. "
                f"Allowed values: {', '.join([e.value for e in UserRole])}"
            ) from err

    def _validate_email_format(self, email: str) -> str:
        """Validate email format using regular expression.

        Args:
            email: Email to validate.

        Returns:
            str: Valid email.

        Raises:
            ValueError: If email has incorrect format.
        """
        if not EMAIL_REGEX.match(email):
            logger.error("Invalid email format", extra={"email": email})
            raise ValueError(f"Invalid email format: '{email}'")
        return email

    async def _check_email_uniqueness(self, email: str, db: AsyncSession) -> None:
        """Check that email is not used by another user.

        Args:
            email: Email to check for uniqueness.
            db: Async database session.

        Raises:
            ValueError: If user with such email already exists.
        """
        repo = UserRepository()
        existing_user = await repo.get_by_email(email=email, db=db)
        if existing_user is not None:
            logger.warning(
                "Registration attempt with existing email", extra={"email": email}
            )
            raise ValueError(f"User with email '{email}' already exists")

    async def register_user(
        self,
        email: str,
        password: str,
        role: str = "viewer",
        db: AsyncSession | None = None,
    ) -> UserRead:
        """Register new user.

        Args:
            email: User email (will be validated).
            password: User password (will be hashed).
            role: User role (admin, editor, viewer).
            db: Optional database session.

        Returns:
            UserRead: Model without password.

        Raises:
            ValueError: If email is invalid, role is invalid,
                or user already exists.
        """
        self._validate_role(role)
        self._validate_email_format(email)
        logger.info("Starting user registration", extra={"email": email, "role": role})

        if db is None:
            async with get_session() as db:
                return await self.register_user(email, password, role, db)

        await self._check_email_uniqueness(email, db)

        try:
            password_hash = hash_password(password)
            logger.info("Password successfully hashed", extra={"email": email})

            repo = UserRepository()
            user = await repo.create(
                db=db,
                email=email,
                password_hash=password_hash,
                role=role,
            )
            if user is None:
                raise ValueError("Error creating user")

            await db.commit()

            logger.info(
                "User successfully registered",
                extra={"id": str(user.id), "email": email, "role": role},
            )
            return UserRead.model_validate(user)
        except Exception as e:
            logger.error(
                "Error during user registration",
                extra={"email": email, "error": str(e)},
            )
            raise

    async def login_user(
        self,
        email: str,
        password: str,
        db: AsyncSession | None = None,
    ) -> dict[str, Any] | None:
        """Authenticate user by email and password.

        Args:
            email: User email.
            password: User password.
            db: Optional database session.

        Returns:
            dict: Token data if authentication successful, None otherwise.
        """
        logger.info("Attempting user authentication", extra={"email": email})

        if db is None:
            async with get_session() as db:
                return await self.login_user(email, password, db)

        repo = UserRepository()
        user_obj = await repo.get_by_email(email=email, db=db)
        if user_obj is None:
            return None
        
        if not verify_password(password, user_obj.password_hash):
            return None
        
        logger.info("User successfully authenticated", extra={"email": email})
        return {
            "access_token": create_access_token({
                "user_id": str(user_obj.id),
                "email": email,
                "role": user_obj.role,
            }),
            "token_type": "bearer",
        }


    async def authenticate_user(
        self, email: str, password: str, db: AsyncSession | None = None
    ) -> UserRead | None:
        """Authenticate user and return user data.

        Args:
            email: User email.
            password: User password.
            db: Optional database session.

        Returns:
            UserRead: User model without password, or None.
        """
        result = await self.login_user(email, password, db)
        if result is None:
            return None
        
        # Get user by email to return UserRead
        repo = UserRepository()
        if db is None:
            async with get_session() as db:
                user_obj = await repo.get_by_email(email=email, db=db)
        else:
            user_obj = await repo.get_by_email(email=email, db=db)
        
        if user_obj is None:
            return None
        return UserRead.model_validate(user_obj)

    def create_access_token(self, user_id: UUID, role: str) -> str:
        """Create access token for user.

        Args:
            user_id: User ID.
            role: User role.

        Returns:
            str: JWT token string.
        """
        return create_access_token({"user_id": str(user_id), "email": "", "role": role})

    async def refresh_token(
        self, user_id: UUID, email: str, role: str
    ) -> dict[str, Any]:
        """Refresh JWT token.

        Args:
            user_id: User ID.
            email: User email.
            role: User role.

        Returns:
            dict: New token data.
        """
        logger.info("Refreshing token", extra={"user_id": user_id})

        token = create_access_token({"user_id": user_id, "email": email, "role": role})

        logger.info("Token refreshed", extra={"user_id": user_id})
        return {
            "access_token": token,
            "token_type": "bearer",
        }

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify JWT token.

        Args:
            token: JWT token to verify.

        Returns:
            dict: Token payload if valid, None otherwise.
        """
        payload = decode_token(token)
        if payload is None:
            logger.warning("Invalid token during verification")
            return None

        logger.info("Token verified", extra={"user_id": payload.get("user_id")})
        return payload

    async def get_user_by_id(
        self, user_id: UUID, db: AsyncSession | None = None
    ) -> UserRead | None:
        """Get user by ID.

        Args:
            user_id: User ID.
            db: Optional database session.

        Returns:
            UserRead: User model without password, or None.
        """
        logger.info("Getting user by id", extra={"user_id": str(user_id)})

        repo = UserRepository()
        if db is None:
            async with get_session() as db:
                return await self.get_user_by_id(user_id, db)

        user_obj = await repo.get(user_id, db)
        if user_obj is None:
            logger.warning("User not found", extra={"user_id": str(user_id)})
            return None

        return cast(UserRead, UserRead.model_validate(user_obj))

    async def get_user_by_email(
        self, email: str, db: AsyncSession | None = None
    ) -> UserRead | None:
        """Get user by email.

        Args:
            email: User email.
            db: Optional database session.

        Returns:
            UserRead: User model without password, or None.
        """
        logger.info("Getting user by email", extra={"email": email})

        repo = UserRepository()
        if db is None:
            async with get_session() as db:
                return await self.get_user_by_email(email, db)

        user_obj = await repo.get_by_email(email=email, db=db)
        if user_obj is None:
            logger.warning("User not found", extra={"email": email})
            return None

        return cast(UserRead, UserRead.model_validate(user_obj))

    async def create_user(
        self,
        email: str,
        password: str,
        role: UserRole,
        db: AsyncSession | None = None,
    ) -> UserRead:
        """Create new user (admin only).

        Args:
            email: User email.
            password: User password.
            role: User role.
            db: Optional database session.

        Returns:
            UserRead: Created user model.
        """
        return await self.register_user(email, password, role, db)

    async def register_request(
        self, email: str, ip: str | None, db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Create registration request.

        Args:
            email: User email.
            ip: Client IP address.
            db: Optional database session.

        Returns:
            dict: Created request data.

        Raises:
            ValueError: If request with this email already exists.
        """
        logger.info("Creating registration request", extra={"email": email, "ip": ip})

        if db is None:
            async with get_session() as db:
                return await self.register_request(email, ip, db)

        # Check if request with this email already exists
        reg_req_repo = RegistrationRequestRepository()
        existing_request = await reg_req_repo.get_by_email(email, db)
        if existing_request is not None:
            logger.warning(
                "Registration request already exists", extra={"email": email}
            )
            raise ValueError(
                f"Registration request with email '{email}' already exists"
            )

        # Check if user with this email already exists
        repo = UserRepository()
        existing_user = await repo.get_by_email(email=email, db=db)
        if existing_user is not None:
            logger.warning("User already exists", extra={"email": email})
            raise ValueError(f"User with email '{email}' already exists")

        try:
            req = await reg_req_repo.create(email, ip, db)
            if req is None:
                raise ValueError("Error creating registration request")

            await db.commit()  # Commit the transaction

            logger.info(
                "Registration request created",
                extra={"id": str(req.id), "email": email},
            )

            return {
                "id": req.id,
                "email": req.email,
                "status": req.status.value,
            }
        except Exception as e:
            logger.error(
                "Error creating registration request",
                extra={"email": email, "error": str(e)},
            )
            raise
