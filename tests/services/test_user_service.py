"""Тесты для сервиса управления пользователями."""

from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, patch
import pytest
from mkobi.models.enums import UserRole
from mkobi.models.user import UserRead
from mkobi.services.user_service import UserService
from mkobi.db.models.user import User


@pytest.fixture
def user_service():
    return UserService()


@pytest.fixture
def mock_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        role=UserRole.VIEWER,
        created_at=datetime.now(),
    )


class TestGetUserById:
    async def test_existing_user(self, user_service, mock_user):
        with patch("mkobi.services.user_service.UserRepository.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_user
            result = await user_service.get_user_by_id(mock_user.id)
            assert result is not None
            assert isinstance(result, UserRead)
            assert result.id == mock_user.id
            assert result.email == mock_user.email
            assert result.role == mock_user.role

    async def test_non_existing_user(self, user_service):
        with patch("mkobi.services.user_service.UserRepository.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            result = await user_service.get_user_by_id(uuid4())
            assert result is None


class TestGetUserByEmail:
    async def test_existing_user(self, user_service, mock_user):
        with patch("mkobi.services.user_service.UserRepository.get_by_email", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_user
            result = await user_service.get_user_by_email(mock_user.email)
            assert result is not None
            assert isinstance(result, UserRead)
            assert result.email == mock_user.email

    async def test_non_existing_user(self, user_service):
        with patch("mkobi.services.user_service.UserRepository.get_by_email", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            result = await user_service.get_user_by_email("nonexistent@example.com")
            assert result is None


class TestCreateUser:
    async def test_valid_creation(self, user_service):
        with patch("mkobi.services.user_service.UserRepository.get_by_email", new_callable=AsyncMock) as mock_get_by_email, \
             patch("mkobi.services.user_service.UserRepository.create", new_callable=AsyncMock) as mock_create, \
             patch("mkobi.services.user_service.hash_password", return_value="hashed_pw"):
            
            mock_get_by_email.return_value = None
            mock_user = User(
                id=uuid4(),
                email="new@example.com",
                password_hash="hashed_pw",
                role=UserRole.EDITOR,
                created_at=datetime.now(),
            )
            mock_create.return_value = mock_user
            
            result = await user_service.create_user(
                email="new@example.com",
                password="secure_password",
                role=UserRole.EDITOR,
            )
            assert isinstance(result, UserRead)
            assert result.email == "new@example.com"
            assert result.role == UserRole.EDITOR

    async def test_duplicate_email(self, user_service, mock_user):
        with patch("mkobi.services.user_service.UserRepository.get_by_email", new_callable=AsyncMock) as mock_get_by_email:
            mock_get_by_email.return_value = mock_user
            with pytest.raises(ValueError, match="уже существует"):
                await user_service.create_user(
                    email=mock_user.email,
                    password="password",
                    role=UserRole.VIEWER,
                )


class TestUpdateUserRole:
    async def test_valid_update(self, user_service, mock_user):
        with patch("mkobi.services.user_service.UserRepository.get", new_callable=AsyncMock) as mock_get, \
             patch("mkobi.services.user_service.UserRepository.update", new_callable=AsyncMock) as mock_update:
            
            mock_get.return_value = mock_user
            updated_user = User(
                id=mock_user.id,
                email=mock_user.email,
                password_hash=mock_user.password_hash,
                role=UserRole.EDITOR,
                created_at=datetime.now(),
            )
            mock_update.return_value = updated_user
            
            result = await user_service.update_user_role(mock_user.id, UserRole.EDITOR)
            assert result is not None
            assert isinstance(result, UserRead)
            assert result.role == UserRole.EDITOR

    async def test_non_existing_user(self, user_service):
        with patch("mkobi.services.user_service.UserRepository.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            result = await user_service.update_user_role(uuid4(), UserRole.ADMIN)
            assert result is None


class TestDeleteUser:
    async def test_valid_deletion(self, user_service, mock_user):
        with patch("mkobi.services.user_service.UserRepository.get", new_callable=AsyncMock) as mock_get, \
             patch("mkobi.services.user_service.UserRepository.delete", new_callable=AsyncMock) as mock_delete, \
             patch("mkobi.services.user_service._check_admin_deletion_allowed", new_callable=AsyncMock):
            
            mock_get.return_value = mock_user
            mock_delete.return_value = True
            result = await user_service.delete_user(mock_user.id)
            assert result is True

    async def test_non_existing_user(self, user_service):
        with patch("mkobi.services.user_service.UserRepository.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            result = await user_service.delete_user(uuid4())
            assert result is False


class TestGetAllUsers:
    async def test_returns_list(self, user_service):
        with patch("mkobi.services.user_service.UserRepository.get_all", new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = [
                User(id=uuid4(), email="user1@example.com", password_hash="hash1", role=UserRole.VIEWER, created_at=datetime.now()),
                User(id=uuid4(), email="user2@example.com", password_hash="hash2", role=UserRole.EDITOR, created_at=datetime.now()),
            ]
            result = await user_service.get_all_users()
            assert len(result) == 2
            assert all(isinstance(u, UserRead) for u in result)
