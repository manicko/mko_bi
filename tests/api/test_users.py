import pytest
from fastapi.testclient import TestClient
from mko_bi.app import app
from mko_bi.services.user_service import create_user
from mko_bi.db.repositories.user_repo import UserRepository

client = TestClient(app)


@pytest.fixture
def admin_user():
    """Create an admin user for testing."""
    # Clean up any existing user with the same email
    UserRepository.delete_by_email("admin@test.com")
    user = create_user("admin@test.com", "adminpassword", "admin")
    yield user
    # Clean up after test
    UserRepository.delete(user.id)


@pytest.fixture
def non_admin_user():
    """Create a non-admin user for testing."""
    # Clean up any existing user with the same email
    UserRepository.delete_by_email("user@test.com")
    user = create_user("user@test.com", "userpassword", "viewer")
    yield user
    # Clean up after test
    UserRepository.delete(user.id)


@pytest.fixture
def admin_token(admin_user):
    """Get an admin token for testing."""
    from mko_bi.core.security import create_access_token

    return create_access_token({"user_id": admin_user.id})


@pytest.fixture
def non_admin_token(non_admin_user):
    """Get a non-admin token for testing."""
    from mko_bi.core.security import create_access_token

    return create_access_token({"user_id": non_admin_user.id})


def test_list_users_as_admin(admin_token):
    """Test that admin can list users."""
    response = client.get("/users/", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    # Should have at least the admin user
    assert len(users) >= 1
    # Check that the admin user is in the list
    admin_emails = [user["email"] for user in users]
    assert "admin@test.com" in admin_emails


def test_list_users_as_non_admin(non_admin_token):
    """Test that non-admin cannot list users."""
    response = client.get(
        "/users/", headers={"Authorization": f"Bearer {non_admin_token}"}
    )
    assert response.status_code == 403


def test_create_user_as_admin(admin_token):
    """Test that admin can create a user."""
    user_data = {
        "email": "newuser@test.com",
        "password": "newuserpassword",
        "role": "editor",
    }
    response = client.post(
        "/users/", json=user_data, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    created_user = response.json()
    assert created_user["email"] == "newuser@test.com"
    assert created_user["role"] == "editor"
    assert "id" in created_user
    # Clean up
    UserRepository.delete(created_user["id"])


def test_create_user_as_non_admin(non_admin_token):
    """Test that non-admin cannot create a user."""
    user_data = {
        "email": "newuser@test.com",
        "password": "newuserpassword",
        "role": "editor",
    }
    response = client.post(
        "/users/",
        json=user_data,
        headers={"Authorization": f"Bearer {non_admin_token}"},
    )
    assert response.status_code == 403


def test_delete_user_as_admin(admin_token, non_admin_user):
    """Test that admin can delete a user."""
    response = client.delete(
        f"/users/{non_admin_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 204
    # Verify user is deleted
    deleted_user = UserRepository.get(non_admin_user.id)
    assert deleted_user is None


def test_delete_self_as_admin(admin_token, admin_user):
    """Test that admin cannot delete themselves."""
    response = client.delete(
        f"/users/{admin_user.id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 403
    assert "Cannot delete yourself" in response.json()["detail"]


def test_delete_user_as_non_admin(non_admin_token, admin_user):
    """Test that non-admin cannot delete a user."""
    response = client.delete(
        f"/users/{admin_user.id}",
        headers={"Authorization": f"Bearer {non_admin_token}"},
    )
    assert response.status_code == 403


def test_delete_nonexistent_user(admin_token):
    """Test deleting a non-existent user."""
    response = client.delete(
        "/users/99999", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
