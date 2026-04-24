import pytest
from mko_bi.services.user_service import create_user, get_user_by_email
from mko_bi.db.models.user import User as UserModel
from mko_bi.db.repositories.user_repo import UserRepository


def test_create_user_success():
    """Test successful user creation."""
    # Clean up any existing test user
    existing = UserRepository.get_by_email("test@example.com")
    if existing:
        with UserRepository.get_session() as session:
            session.delete(existing)
            session.commit()

    # Create new user
    user = create_user("test@example.com", "password123", "viewer")

    assert user is not None
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.role == "viewer"
    # Password hash should not be in the returned model
    assert not hasattr(user, "password_hash")


def test_create_user_duplicate_email():
    """Test that creating a user with duplicate email raises ValueError."""
    email = "duplicate@example.com"
    password = "password123"

    # Clean up any existing test user
    existing = UserRepository.get_by_email(email)
    if existing:
        with UserRepository.get_session() as session:
            session.delete(existing)
            session.commit()

    # Create first user
    create_user(email, password, "viewer")

    # Try to create user with same email
    with pytest.raises(ValueError, match=f"User with email {email} already exists"):
        create_user(email, password, "editor")


def test_create_user_invalid_email():
    """Test that invalid email format raises ValueError."""
    with pytest.raises(ValueError, match="Invalid email format"):
        create_user("invalid-email", "password123", "viewer")


def test_create_user_invalid_role():
    """Test that invalid role raises ValueError."""
    with pytest.raises(ValueError, match="Invalid role: invalid_role"):
        create_user("test@example.com", "password123", "invalid_role")


def test_get_user_by_email():
    """Test retrieving user by email."""
    email = "getuser@example.com"
    password = "password123"
    role = "editor"

    # Clean up any existing test user
    existing = UserRepository.get_by_email(email)
    if existing:
        with UserRepository.get_session() as session:
            session.delete(existing)
            session.commit()

    # Create user
    created_user = create_user(email, password, role)

    # Retrieve user
    retrieved_user = get_user_by_email(email)

    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == email
    assert retrieved_user.role == role
    # Password hash should not be in the returned model
    assert not hasattr(retrieved_user, "password_hash")


def test_get_user_by_email_not_found():
    """Test retrieving non-existent user returns None."""
    user = get_user_by_email("nonexistent@example.com")
    assert user is None


def test_create_user_default_role():
    """Test that default role is viewer."""
    email = "defaulterole@example.com"

    # Clean up any existing test user
    existing = UserRepository.get_by_email(email)
    if existing:
        with UserRepository.get_session() as session:
            session.delete(existing)
            session.commit()

    # Create user without specifying role
    user = create_user(email, "password123")

    assert user.role == "viewer"
