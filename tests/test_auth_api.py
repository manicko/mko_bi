"""Тесты для API аутентификации.

Тестирует эндпоинты аутентификации:
- POST /auth/login
- POST /auth/register  
- POST /auth/refresh
- GET /auth/me
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from jose import jwt

from mko_bi.main import app
from mko_bi.db.session import SessionLocal
from mko_bi.db.models import user as user_model
from mko_bi.core.security import hash_password
from mko_bi.config import config

client = TestClient(app)


class TestAuthAPI:
    """Тесты для API аутентификации."""

    def test_register_user(self, db_session: Session):
        """Тест регистрации нового пользователя."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "secure_password123",
                "role": "viewer",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Проверяем, что пользователь создан в БД
        user = db_session.execute(
            db_session.query(user_model.User).filter(
                user_model.User.email == "test@example.com"
            )
        ).scalar_one_or_none()
        assert user is not None
        assert user.role == "viewer"
        assert user.is_active is True

    def test_register_duplicate_email(self, db_session: Session):
        """Тест регистрации с существующим email."""
        # Создаем пользователя
        hashed_password = hash_password("password123")
        user = user_model.User(
            email="existing@example.com",
            password_hash=hashed_password,
            role="viewer",
        )
        db_session.add(user)
        db_session.commit()

        # Пытаемся зарегистрировать с тем же email
        response = client.post(
            "/auth/register",
            json={
                "email": "existing@example.com",
                "password": "another_password",
                "role": "editor",
            },
        )
        assert response.status_code == 422

    def test_login_success(self, db_session: Session):
        """Тест успешного входа."""
        # Создаем пользователя
        hashed_password = hash_password("correct_password")
        user = user_model.User(
            email="login_test@example.com",
            password_hash=hashed_password,
            role="admin",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Входим
        response = client.post(
            "/auth/login",
            json={
                "email": "login_test@example.com",
                "password": "correct_password",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Проверяем токен
        token = data["access_token"]
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        assert payload["email"] == "login_test@example.com"
        assert payload["role"] == "admin"
        assert "user_id" in payload

    def test_login_wrong_password(self, db_session: Session):
        """Тест входа с неверным паролем."""
        # Создаем пользователя
        hashed_password = hash_password("correct_password")
        user = user_model.User(
            email="wrong_pass@example.com",
            password_hash=hashed_password,
            role="viewer",
        )
        db_session.add(user)
        db_session.commit()

        # Пытаемся войти с неверным паролем
        response = client.post(
            "/auth/login",
            json={
                "email": "wrong_pass@example.com",
                "password": "wrong_password",
            },
        )
        assert response.status_code == 401
        assert "Неверный email или пароль" in response.json()["detail"]

    def test_login_nonexistent_user(self, db_session: Session):
        """Тест входа несуществующим пользователем."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "some_password",
            },
        )
        assert response.status_code == 401
        assert "Неверный email или пароль" in response.json()["detail"]

    def test_login_invalid_email_format(self, db_session: Session):
        """Тест входа с неверным форматом email."""
        response = client.post(
            "/auth/login",
            json={
                "email": "invalid-email",
                "password": "some_password",
            },
        )
        # Валидация Pydantic должна вернуть 422
        assert response.status_code == 422

    def test_login_rate_limiting(self, db_session: Session):
        """Тест ограничения частоты запросов на вход."""
        # Создаем пользователя
        hashed_password = hash_password("password")
        user = user_model.User(
            email="rate_limit@example.com",
            password_hash=hashed_password,
            role="viewer",
        )
        db_session.add(user)
        db_session.commit()

        # Делаем 5 неудачных попыток (лимит 5 в минуту)
        for i in range(5):
            response = client.post(
                "/auth/login",
                json={
                    "email": "rate_limit@example.com",
                    "password": "wrong_password",
                },
            )
            assert response.status_code == 401

        # 6-я попытка должна быть заблокирована
        response = client.post(
            "/auth/login",
            json={
                "email": "rate_limit@example.com",
                "password": "wrong_password",
            },
        )
        assert response.status_code == 429
        assert "лимит" in response.json()["detail"].lower()

    def test_refresh_token(self, db_session: Session):
        """Тест обновления токена."""
        # Создаем пользователя
        hashed_password = hash_password("password")
        user = user_model.User(
            email="refresh_test@example.com",
            password_hash=hashed_password,
            role="editor",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Получаем токен через логин
        response = client.post(
            "/auth/login",
            json={
                "email": "refresh_test@example.com",
                "password": "password",
            },
        )
        assert response.status_code == 200
        old_token = response.json()["access_token"]

        # Обновляем токен
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": old_token,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        new_token = data["access_token"]
        
        # Новый токен должен быть валидным
        payload = jwt.decode(new_token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        assert payload["email"] == "refresh_test@example.com"
        assert payload["role"] == "editor"

    def test_refresh_invalid_token(self, db_session: Session):
        """Тест обновления с неверным токеном."""
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": "invalid.token.here",
            },
        )
        assert response.status_code == 401
        assert "Неверный токен" in response.json()["detail"]

    def test_get_current_user_info(self, db_session: Session):
        """Тест получения информации о текущем пользователе."""
        # Создаем пользователя
        hashed_password = hash_password("password")
        user = user_model.User(
            email="me_test@example.com",
            password_hash=hashed_password,
            role="admin",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Получаем токен
        response = client.post(
            "/auth/login",
            json={
                "email": "me_test@example.com",
                "password": "password",
            },
        )
        token = response.json()["access_token"]

        # Получаем информацию о пользователе
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me_test@example.com"
        assert data["role"] == "admin"
        assert "id" in data
        assert "created_at" in data

    def test_get_current_user_unauthorized(self, db_session: Session):
        """Тест получения информации о пользователе без токена."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_login_form(self, db_session: Session):
        """Тест входа через OAuth2 форму."""
        # Создаем пользователя
        hashed_password = hash_password("form_password")
        user = user_model.User(
            email="form_test@example.com",
            password_hash=hashed_password,
            role="viewer",
        )
        db_session.add(user)
        db_session.commit()

        # Входим через форму
        response = client.post(
            "/auth/login/form",
            data={
                "username": "form_test@example.com",
                "password": "form_password",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_default_role(self, db_session: Session):
        """Тест регистрации с ролью по умолчанию."""
        response = client.post(
            "/auth/register",
            json={
                "email": "default_role@example.com",
                "password": "password123",
                # Не указываем роль, должна быть "viewer"
            },
        )
        assert response.status_code == 201

        # Проверяем роль в БД
        user = db_session.execute(
            db_session.query(user_model.User).filter(
                user_model.User.email == "default_role@example.com"
            )
        ).scalar_one_or_none()
        assert user.role == "viewer"  # Значение по умолчанию


@pytest.fixture
def db_session():
    """Фикстура для сессии БД."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
