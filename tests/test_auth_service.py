"""Unit tests for AuthService business logic."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from mkobi.core.security import hash_password
from mkobi.models.enums import RegistrationStatus, UserRole
from mkobi.models.user import UserRead
from mkobi.services.auth_service import AuthService


@pytest.mark.asyncio
class TestAuthService:
    """Unit tests for AuthService business logic."""

    @pytest.fixture
    def mock_user_repo(self):
        """Create a mock user repository."""
        mock = AsyncMock()
        mock.get_by_email.return_value = None
        mock.get_by_email_with_hash.return_value = None
        mock.get.return_value = None
        mock.get_all.return_value = []
        return mock

    @pytest.fixture
    def mock_reg_request_repo(self):
        """Create a mock registration request repository."""
        return AsyncMock()

    @pytest.fixture
    def auth_service(self, mock_user_repo, mock_reg_request_repo):
        """Create AuthService with mocked repositories."""
        return AuthService(mock_user_repo, mock_reg_request_repo)

    # --- register_user tests ---

    async def test_register_user_success(self, auth_service, mock_user_repo, mock_db):
        """Test successful user registration."""
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create.return_value = MagicMock(
            id=uuid4(),
            email="test@example.com",
            role="viewer",
            is_active=True,
            password_hash=hash_password("TestPass123!"),
        )

        result = await auth_service.register_user(
                email="test@example.com",
                password="TestPass123!",
                db=mock_db,
                role="viewer",
            )

        assert isinstance(result, UserRead)
        assert result.email == "test@example.com"
        mock_user_repo.create.assert_called_once()

    async def test_register_user_admin_role(self, auth_service, mock_user_repo, mock_db):
        """Test registration with admin role."""
        mock_user_repo.create.return_value = MagicMock(
            id=uuid4(),
            email="admin@example.com",
            role="admin",
            is_active=True,
            password_hash=hash_password("AdminPass123!"),
        )

        result = await auth_service.register_user(
            email="admin@example.com",
            password="AdminPass123!",
            db=mock_db,
            role="admin",
        )

        assert result.role == UserRole.ADMIN

    async def test_register_user_invalid_email(self, auth_service, mock_db):
        """Test registration rejects invalid email format."""
        with pytest.raises(ValueError, match="Invalid email format"):
            await auth_service.register_user(
                email="invalid-email",
                password="TestPass123!",
                db=mock_db,
                role="viewer",
            )

    async def test_register_user_invalid_role(self, auth_service, mock_db):
        """Test registration rejects invalid role."""
        with pytest.raises(ValueError, match="Invalid role"):
            await auth_service.register_user(
                email="test@example.com",
                password="TestPass123!",
                db=mock_db,
                role="invalid_role",
            )

    async def test_register_user_duplicate_email(self, auth_service, mock_user_repo, mock_db):
        """Test registration fails when email already exists."""
        mock_user_repo.get_by_email.return_value = MagicMock(
            id=uuid4(), email="existing@example.com"
        )

        with pytest.raises(ValueError, match="already exists"):
            await auth_service.register_user(
                email="existing@example.com",
                password="TestPass123!",
                db=mock_db,
                role="viewer",
            )

    async def test_register_user_empty_password(self, auth_service, mock_user_repo, mock_db):
        """Test registration rejects empty password.

        Password validation requires non-empty passwords with digits and letters.
        """
        empty_password = ""
        with pytest.raises(ValueError, match="Password is required"):
            await auth_service.register_user(
                email="empty@example.com",
                password=empty_password,
                db=mock_db,
                role="viewer",
            )

    # --- login_user tests ---

    async def test_login_user_success(self, auth_service, mock_user_repo, mock_db):
        """Test successful login."""
        from datetime import datetime

        test_password = "TestPass123!"
        mock_user = MagicMock()
        mock_user.password_hash = hash_password(test_password)
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.role = UserRole.ADMIN
        mock_user.is_active = True
        mock_user.created_at = datetime.now()
        mock_user_repo.get_by_email_with_hash.return_value = mock_user

        result = await auth_service.login_user("test@example.com", test_password, mock_db)

        assert result is not None
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert "user" in result
        assert result["user"].email == "test@example.com"
        assert hasattr(result["user"], "display_name")
        assert result["user"].display_name == "test"

    async def test_login_user_wrong_password(self, auth_service, mock_user_repo, mock_db):
        """Test login with wrong password returns None."""
        mock_user = MagicMock()
        mock_user.password_hash = hash_password("CorrectPassword")
        mock_user_repo.get_by_email_with_hash.return_value = mock_user

        result = await auth_service.login_user("test@example.com", "WrongPassword", db=mock_db)

        assert result is None

    async def test_login_user_not_found(self, auth_service, mock_user_repo, mock_db):
        """Test login with non-existent email returns None."""
        mock_user_repo.get_by_email_with_hash.return_value = None

        result = await auth_service.login_user("nonexistent@example.com", "AnyPassword", db=mock_db)

        assert result is None

    async def test_login_user_empty_password(self, auth_service, mock_user_repo, mock_db):
        """Test login with empty password."""
        mock_user = MagicMock()
        mock_user.password_hash = hash_password("ActualPassword")
        mock_user_repo.get_by_email_with_hash.return_value = mock_user

        result = await auth_service.login_user("test@example.com", "", db=mock_db)

        assert result is None

    # --- authenticate_user tests ---

    async def test_authenticate_user_success(self, auth_service, mock_user_repo, mock_db):
        """Test successful authentication returns user data."""
        test_password = "TestPass123!"
        mock_user = MagicMock()
        mock_user.password_hash = hash_password(test_password)
        mock_user.id = uuid4()
        mock_user.email = "auth@example.com"
        mock_user.role = UserRole.EDITOR
        mock_user.is_active = True
        mock_user_repo.get_by_email_with_hash.return_value = mock_user
        mock_user_repo.get_by_email.return_value = mock_user

        result = await auth_service.authenticate_user("auth@example.com", test_password, db=mock_db)

        assert result is not None
        assert isinstance(result, UserRead)
        assert result.email == "auth@example.com"

    async def test_authenticate_user_wrong_password(self, auth_service, mock_user_repo, mock_db):
        """Test authentication with wrong password returns None."""
        mock_user = MagicMock()
        mock_user.password_hash = hash_password("CorrectPassword")
        mock_user_repo.get_by_email_with_hash.return_value = mock_user

        result = await auth_service.authenticate_user("test@example.com", "WrongPassword", db=mock_db)

        assert result is None

    async def test_authenticate_user_not_found(self, auth_service, mock_user_repo, mock_db):
        """Test authentication with non-existent user returns None."""
        mock_user_repo.get_by_email_with_hash.return_value = None

        result = await auth_service.authenticate_user("nobody@example.com", "AnyPassword", db=mock_db)

        assert result is None

    # --- create_access_token tests ---

    async def test_create_access_token(self, auth_service):
        """Test access token creation."""
        user_id = uuid4()
        role = UserRole.ADMIN

        token = auth_service.create_access_token(user_id, role)

        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT format

    async def test_create_access_token_different_users(self, auth_service):
        """Test different users get different tokens."""
        token1 = auth_service.create_access_token(uuid4(), UserRole.ADMIN)
        token2 = auth_service.create_access_token(uuid4(), UserRole.VIEWER)

        assert token1 != token2

    # --- verify_token tests ---

    async def test_verify_token_valid(self, auth_service):
        """Test verifying a valid token."""
        user_id = uuid4()
        token = auth_service.create_access_token(user_id, UserRole.ADMIN)

        result = auth_service.verify_token(token)

        assert result is not None
        assert result["user_id"] == str(user_id)

    async def test_verify_token_invalid(self, auth_service):
        """Test verifying an invalid token returns None."""
        result = auth_service.verify_token("invalid.token.here")

        assert result is None

    async def test_verify_token_empty(self, auth_service):
        """Test verifying an empty token returns None."""
        result = auth_service.verify_token("")

        assert result is None

    # --- refresh_token tests ---

    async def test_refresh_token_success(self, auth_service):
        """Test successful token refresh."""
        user_id = uuid4()
        original_token = auth_service.create_access_token(user_id, UserRole.ADMIN)
        payload = auth_service.verify_token(original_token)

        result = await auth_service.refresh_token(
            user_id=payload["user_id"],
            email="test@example.com",
            role=UserRole.ADMIN,
        )

        assert "access_token" in result
        assert result["token_type"] == "bearer"

    async def test_refresh_token_new_token_different(self, auth_service):
        """Test refreshed token is different from original."""
        user_id = uuid4()
        original_token = auth_service.create_access_token(user_id, UserRole.ADMIN)
        payload = auth_service.verify_token(original_token)

        result = await auth_service.refresh_token(
            user_id=payload["user_id"],
            email="test@example.com",
            role=UserRole.ADMIN,
        )

        assert result["access_token"] != original_token

    # --- get_user_by_id tests ---

    async def test_get_user_by_id_found(self, auth_service, mock_user_repo, mock_db):
        """Test getting user by ID when user exists."""
        expected_user = MagicMock()
        expected_user.id = uuid4()
        expected_user.email = "found@example.com"
        expected_user.role = UserRole.ADMIN
        expected_user.password_hash = hash_password("password")
        expected_user.is_active = True
        mock_user_repo.get.return_value = expected_user

        result = await auth_service.get_user_by_id(expected_user.id, db=mock_db)

        assert result is not None
        assert isinstance(result, UserRead)
        assert result.id == expected_user.id

    async def test_get_user_by_id_not_found(self, auth_service, mock_user_repo, mock_db):
        """Test getting user by ID when user doesn't exist."""
        mock_user_repo.get.return_value = None

        result = await auth_service.get_user_by_id(uuid4(), db=mock_db)

        assert result is None

    # --- get_user_by_email tests ---

    async def test_get_user_by_email_found(self, auth_service, mock_user_repo, mock_db):
        """Test getting user by email when user exists."""
        expected_user = MagicMock()
        expected_user.id = uuid4()
        expected_user.email = "found@example.com"
        expected_user.role = UserRole.VIEWER
        expected_user.password_hash = hash_password("password")
        expected_user.is_active = True
        mock_user_repo.get_by_email.return_value = expected_user

        result = await auth_service.get_user_by_email("found@example.com", db=mock_db)

        assert result is not None
        assert isinstance(result, UserRead)
        assert result.email == "found@example.com"

    async def test_get_user_by_email_not_found(self, auth_service, mock_user_repo, mock_db):
        """Test getting user by email when user doesn't exist."""
        mock_user_repo.get_by_email.return_value = None

        result = await auth_service.get_user_by_email("nobody@example.com", db=mock_db)

        assert result is None

    # --- create_user tests ---

    async def test_create_user_success(self, auth_service, mock_user_repo, mock_db):
        """Test admin creates user successfully."""
        mock_user_repo.create.return_value = MagicMock(
            id=uuid4(), email="new@example.com", role=UserRole.VIEWER,
            is_active=True,
            password_hash=hash_password("ValidPass123"),
        )

        result = await auth_service.create_user(
            email="new@example.com",
            password="ValidPass123",
            role=UserRole.VIEWER,
            db=mock_db,
        )

        assert isinstance(result, UserRead)
        assert result.email == "new@example.com"

    # --- register_request tests ---

    async def test_register_request_success(self, auth_service, mock_reg_request_repo, mock_db):
        """Test successful registration request."""
        mock_reg_request_repo.get_by_email.return_value = None
        mock_reg_request_repo.create.return_value = MagicMock(
            id=uuid4(), email="request@example.com", status=MagicMock(value="pending")
        )

        result = await auth_service.register_request("request@example.com", db=mock_db, ip="127.0.0.1")

        assert "id" in result
        assert result["email"] == "request@example.com"

    async def test_register_request_invalid_email(self, auth_service, mock_db):
        """Test registration request rejects invalid email."""
        with pytest.raises(ValueError, match="Invalid email format"):
            await auth_service.register_request("invalid-email", db=mock_db, ip="127.0.0.1")

    async def test_register_request_duplicate(self, auth_service, mock_reg_request_repo, mock_db):
        """Test registration request fails for duplicate email (PENDING status)."""
        mock_request = MagicMock()
        mock_request.status = RegistrationStatus.PENDING
        mock_reg_request_repo.get_by_email.return_value = mock_request

        with pytest.raises(ValueError, match="A request for this email already exists"):
            await auth_service.register_request("duplicate@example.com", db=mock_db, ip="127.0.0.1")

    async def test_register_request_duplicate_rejected(self, auth_service, mock_reg_request_repo, mock_db):
        """Test registration request fails with rejected status message."""
        mock_request = MagicMock()
        mock_request.status = RegistrationStatus.REJECTED
        mock_reg_request_repo.get_by_email.return_value = mock_request

        with pytest.raises(ValueError, match="Your request was rejected"):
            await auth_service.register_request("rejected@example.com", db=mock_db, ip="127.0.0.1")

    async def test_register_request_duplicate_approved(self, auth_service, mock_reg_request_repo, mock_db):
        """Test registration request fails with approved status message."""
        mock_request = MagicMock()
        mock_request.status = RegistrationStatus.APPROVED
        mock_reg_request_repo.get_by_email.return_value = mock_request

        with pytest.raises(ValueError, match="A request for this email already exists"):
            await auth_service.register_request("approved@example.com", db=mock_db, ip="127.0.0.1")

    async def test_register_request_blocked_domain(
        self, auth_service, mock_reg_request_repo, mock_db
    ):
        """Test registration request rejects blocked email domains."""
        mock_reg_request_repo.get_by_email.return_value = None

        with pytest.raises(
            ValueError, match="This email domain is not allowed for registration"
        ):
            await auth_service.register_request("user@tempmail.com", db=mock_db, ip="127.0.0.1")