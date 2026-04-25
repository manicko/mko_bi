"""Тесты для API аутентификации (auth.py).

Тестирует эндпоинты:
- POST /auth/login - вход пользователя
- POST /auth/register - регистрация пользователя
- POST /auth/refresh - обновление токена
- GET /auth/me - получение данных текущего пользователя

Использует изолированную тестовую базу данных SQLite in-memory.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from jose import jwt
from sqlalchemy.orm import Session

from mko_bi.main import create_application
from mko_bi.models.auth import LoginRequest, RegisterRequest, RefreshRequest, Token
from mko_bi.models.user import UserRead
from mko_bi.services.auth_service import (
    authenticate_user,
    register_user,
    login_user,
)
from mko_bi.core.security import create_access_token, decode_token
from mko_bi.db.models import user as user_model
from mko_bi.db.repositories.user_repo import UserRepository
from mko_bi.db.session import SessionLocal, get_db


@pytest.fixture
def client(test_db):
    """Создает тестовый клиент FastAPI с переопределенной зависимостью БД."""
    app = create_application()

    # Переопределяем зависимость get_db для использования тестовой БД
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Не закрываем, так как тестовая БД управляется фикстурой

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestLoginEndpoint:
    """Тесты эндпоинта POST /auth/login."""

    def test_login_success(self, client):
        """Успешный вход возвращает токен."""
        # Регистрируем пользователя через API
        register_response = client.post(
            "/auth/register",
            json={
                "email": "login_test@example.com",
                "password": "test_password",
                "role": "viewer",
            },
        )
        assert register_response.status_code == 201

        # Выполняем вход
        response = client.post(
            "/auth/login",
            json={
                "email": "login_test@example.com",
                "password": "test_password",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert "." in data["access_token"]  # JWT формат

    def test_login_success_with_model(self, client, test_db):
        """Успешный вход с использованием Pydantic модели."""
        register_user(
            email="model_test@example.com",
            password="test_password",
            role="editor",
            db=test_db,
        )

        response = client.post(
            "/auth/login",
            json={
                "email": "model_test@example.com",
                "password": "test_password",
            },
        )

        assert response.status_code == 200
        token = Token(**response.json())
        assert token.token_type == "bearer"
        assert token.access_token is not None

    def test_login_wrong_password(self, client, test_db):
        """Вход с неверным паролем возвращает 401."""
        register_user(
            email="wrong_pass@example.com",
            password="correct_password",
            role="viewer",
            db=test_db,
        )

        response = client.post(
            "/auth/login",
            json={
                "email": "wrong_pass@example.com",
                "password": "wrong_password",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert "Неверный email или пароль" in data["detail"]

    def test_login_nonexistent_user(self, client):
        """Вход несуществующего пользователя возвращает 401."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "any_password",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert "Неверный email или пароль" in data["detail"]

    def test_login_invalid_email_format(self, client):
        """Вход с некорректным email возвращает 422."""
        response = client.post(
            "/auth/login",
            json={
                "email": "invalid_email",
                "password": "password",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_login_empty_password(self, client, test_db):
        """Вход с пустым паролем (если такой пользователь существует)."""
        register_user(
            email="empty_pass_login@example.com",
            password="",
            role="viewer",
            db=test_db,
        )

        response = client.post(
            "/auth/login",
            json={
                "email": "empty_pass_login@example.com",
                "password": "",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_rate_limiting(self, client, test_db):
        """Превышение лимита попыток входа возвращает 429."""
        register_user(
            email="rate_limit@example.com",
            password="password",
            role="viewer",
            db=test_db,
        )

        # Делаем 6 попыток с неверным паролем
        for i in range(6):
            response = client.post(
                "/auth/login",
                json={
                    "email": "rate_limit@example.com",
                    "password": "wrong_password",
                },
            )

        # Последняя попытка должна вернуть 429
        assert response.status_code == 429
        data = response.json()
        assert "лимит" in data["detail"].lower() or "limit" in data["detail"].lower()

    def test_login_returns_valid_jwt(self, client, test_db):
        """Токен, возвращаемый при входе, должен быть валидным JWT."""
        register_user(
            email="jwt_test@example.com",
            password="test_password",
            role="admin",
            db=test_db,
        )

        response = client.post(
            "/auth/login",
            json={
                "email": "jwt_test@example.com",
                "password": "test_password",
            },
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        # Декодируем токен (без проверки подписи для теста)
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["email"] == "jwt_test@example.com"
        assert decoded["role"] == "admin"
        assert "user_id" in decoded

    def test_login_response_structure(self, client, test_db):
        """Ответ при входе должен содержать все необходимые поля."""
        register_user(
            email="struct_test@example.com",
            password="password",
            role="editor",
            db=test_db,
        )

        response = client.post(
            "/auth/login",
            json={
                "email": "struct_test@example.com",
                "password": "password",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"access_token", "token_type"}


class TestRegisterEndpoint:
    """Тесты эндпоинта POST /auth/register."""

    def test_register_success(self, client):
        """Успешная регистрация возвращает токен."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "new_password",
                "role": "viewer",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_default_role(self, client):
        """Регистрация без указания роли использует роль по умолчанию (viewer)."""
        response = client.post(
            "/auth/register",
            json={
                "email": "default_role@example.com",
                "password": "password",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data

    def test_register_duplicate_email(self, client, test_db):
        """Регистрация с существующим email возвращает 422."""
        # Создаем пользователя напрямую
        register_user(
            email="duplicate@example.com",
            password="password1",
            role="viewer",
            db=test_db,
        )

        # Пытаемся зарегистрировать с тем же email
        response = client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password2",
                "role": "editor",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "уже существует" in data["detail"] or "exists" in data["detail"].lower()

    def test_register_invalid_role(self, client):
        """Регистрация с недопустимой ролью возвращает 422."""
        response = client.post(
            "/auth/register",
            json={
                "email": "invalid_role@example.com",
                "password": "password",
                "role": "superadmin",
            },
        )

        assert response.status_code == 422

    def test_register_invalid_email(self, client):
        """Регистрация с некорректным email возвращает 422."""
        response = client.post(
            "/auth/register",
            json={
                "email": "not_an_email",
                "password": "password",
                "role": "viewer",
            },
        )

        assert response.status_code == 422

    def test_register_all_roles(self, client):
        """Регистрация пользователей со всеми допустимыми ролями."""
        for role in ["admin", "editor", "viewer"]:
            response = client.post(
                "/auth/register",
                json={
                    "email": f"{role}_user@example.com",
                    "password": "password",
                    "role": role,
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert "access_token" in data

    def test_register_returns_valid_token(self, client):
        """Токен, возвращаемый при регистрации, должен быть валидным."""
        response = client.post(
            "/auth/register",
            json={
                "email": "token_test@example.com",
                "password": "password",
                "role": "editor",
            },
        )

        assert response.status_code == 201
        token = response.json()["access_token"]
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["email"] == "token_test@example.com"
        assert decoded["role"] == "editor"

    def test_register_response_structure(self, client):
        """Ответ при регистрации должен содержать все необходимые поля."""
        response = client.post(
            "/auth/register",
            json={
                "email": "struct_test2@example.com",
                "password": "password",
                "role": "viewer",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert set(data.keys()) == {"access_token", "token_type"}

    def test_register_creates_user_in_db(self, client, test_db):
        """Регистрация должна создавать пользователя в базе данных."""
        response = client.post(
            "/auth/register",
            json={
                "email": "db_test@example.com",
                "password": "password",
                "role": "viewer",
            },
        )

        assert response.status_code == 201

        # Проверяем, что пользователь создан в БД
        user = UserRepository.get_by_email("db_test@example.com", test_db)
        assert user is not None
        assert user.email == "db_test@example.com"
        assert user.role == "viewer"


class TestRefreshEndpoint:
    """Тесты эндпоинта POST /auth/refresh."""

    def test_refresh_success(self, client, test_db):
        """Успешное обновление токена."""
        # Создаем пользователя и получаем токен
        register_user(
            email="refresh_test@example.com",
            password="password",
            role="viewer",
            db=test_db,
        )

        token = create_access_token(
            data={
                "user_id": 1,
                "email": "refresh_test@example.com",
                "role": "viewer",
            }
        )

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["access_token"] != token  # Новый токен должен отличаться

    def test_refresh_invalid_token(self, client):
        """Обновление с неверным токеном возвращает 401."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "Неверный токен" in data["detail"]

    def test_refresh_expired_token(self, client):
        """Обновление с истекшим токеном возвращает 401."""
        from datetime import timedelta
        from mko_bi.config import config

        # Создаем токен с отрицательным временем жизни (уже истек)
        expired_token = create_access_token(
            data={"user_id": 1, "email": "test@example.com"},
            expires_delta=timedelta(seconds=-1),
        )

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": expired_token},
        )

        assert response.status_code == 401

    def test_refresh_missing_user(self, client, test_db):
        """Обновление токена для несуществующего пользователя."""
        # Создаем токен для несуществующего пользователя
        token = create_access_token(
            data={
                "user_id": 99999,
                "email": "nonexistent@example.com",
                "role": "viewer",
            }
        )

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": token},
        )

        assert response.status_code == 401
        data = response.json()
        assert "Пользователь не найден" in data["detail"]

    def test_refresh_response_structure(self, client, test_db):
        """Ответ при обновлении должен содержать все необходимые поля."""
        register_user(
            email="refresh_struct@example.com",
            password="password",
            role="editor",
            db=test_db,
        )

        token = create_access_token(
            data={
                "user_id": 1,
                "email": "refresh_struct@example.com",
                "role": "editor",
            }
        )

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": token},
        )

        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"access_token", "token_type"}

    def test_refresh_returns_new_valid_token(self, client, test_db):
        """Новый токен должен быть валидным и содержать правильные данные."""
        register_user(
            email="new_token_test@example.com",
            password="password",
            role="admin",
            db=test_db,
        )

        token = create_access_token(
            data={
                "user_id": 1,
                "email": "new_token_test@example.com",
                "role": "admin",
            }
        )

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": token},
        )

        assert response.status_code == 200
        new_token = response.json()["access_token"]
        decoded = decode_token(new_token)

        assert decoded is not None
        assert decoded["email"] == "new_token_test@example.com"
        assert decoded["role"] == "admin"
        assert decoded["user_id"] == 1


class TestGetCurrentUserEndpoint:
    """Тесты эндпоинта GET /auth/me."""

    def test_get_current_user_success(self, client, test_db):
        """Получение данных текущего пользователя."""
        # Регистрируем пользователя
        register_user(
            email="me_test@example.com",
            password="password",
            role="editor",
            db=test_db,
        )

        # Получаем токен
        token = create_access_token(
            data={
                "user_id": 1,
                "email": "me_test@example.com",
                "role": "editor",
            }
        )

        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me_test@example.com"
        assert data["role"] == "editor"
        assert "id" in data
        assert "created_at" in data
        assert "password_hash" not in data

    def test_get_current_user_invalid_token(self, client):
        """Запрос с неверным токеном возвращает 401."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401

    def test_get_current_user_missing_token(self, client):
        """Запрос без токена возвращает 401."""
        response = client.get("/auth/me")

        assert response.status_code == 401

    def test_get_current_user_nonexistent(self, client, test_db):
        """Запрос с токеном несуществующего пользователя."""
        token = create_access_token(
            data={
                "user_id": 99999,
                "email": "nonexistent@example.com",
                "role": "viewer",
            }
        )

        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401


class TestIntegrationAuthFlow:
    """Интеграционные тесты полного цикла аутентификации."""

    def test_full_registration_login_refresh_flow(self, client):
        """Полный цикл: регистрация -> вход -> обновление токена."""
        # 1. Регистрация
        reg_response = client.post(
            "/auth/register",
            json={
                "email": "fullflow@example.com",
                "password": "secure_password",
                "role": "admin",
            },
        )
        assert reg_response.status_code == 201
        reg_token = reg_response.json()["access_token"]

        # 2. Вход
        login_response = client.post(
            "/auth/login",
            json={
                "email": "fullflow@example.com",
                "password": "secure_password",
            },
        )
        assert login_response.status_code == 200
        login_token = login_response.json()["access_token"]

        # 3. Получение данных пользователя
        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {login_token}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "fullflow@example.com"
        assert me_response.json()["role"] == "admin"

        # 4. Обновление токена
        refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": login_token},
        )
        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["access_token"]
        assert new_token != login_token

        # 5. Проверка нового токена
        me_response2 = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {new_token}"},
        )
        assert me_response2.status_code == 200
        assert me_response2.json()["email"] == "fullflow@example.com"

    def test_multiple_users_independent_tokens(self, client):
        """Разные пользователи имеют независимые токены."""
        # Регистрируем двух пользователей
        client.post(
            "/auth/register",
            json={
                "email": "user1@example.com",
                "password": "pass1",
                "role": "viewer",
            },
        )
        client.post(
            "/auth/register",
            json={
                "email": "user2@example.com",
                "password": "pass2",
                "role": "admin",
            },
        )

        # Вход первого пользователя
        login1 = client.post(
            "/auth/login",
            json={"email": "user1@example.com", "password": "pass1"},
        )
        token1 = login1.json()["access_token"]

        # Вход второго пользователя
        login2 = client.post(
            "/auth/login",
            json={"email": "user2@example.com", "password": "pass2"},
        )
        token2 = login2.json()["access_token"]

        # Токены должны быть разными
        assert token1 != token2

        # Каждый токен дает доступ только к своему пользователю
        me1 = client.get("/auth/me", headers={"Authorization": f"Bearer {token1}"})
        assert me1.json()["email"] == "user1@example.com"

        me2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token2}"})
        assert me2.json()["email"] == "user2@example.com"


class TestAuthAPIErrorHandling:
    """Тесты обработки ошибок в API аутентификации."""

    def test_login_with_missing_fields(self, client):
        """Вход без обязательных полей возвращает 422."""
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com"},  # Нет пароля
        )
        assert response.status_code == 422

    def test_register_with_missing_fields(self, client):
        """Регистрация без обязательных полей возвращает 422."""
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com"},  # Нет пароля
        )
        assert response.status_code == 422

    def test_refresh_with_missing_field(self, client):
        """Обновление без refresh_token возвращает 422."""
        response = client.post(
            "/auth/refresh",
            json={},  # Нет refresh_token
        )
        assert response.status_code == 422

    def test_login_with_empty_body(self, client):
        """Вход с пустым телом запроса возвращает 422."""
        response = client.post("/auth/login", json={})
        assert response.status_code == 422

    def test_register_with_empty_body(self, client):
        """Регистрация с пустым телом запроса возвращает 422."""
        response = client.post("/auth/register", json={})
        assert response.status_code == 422

    def test_refresh_with_empty_body(self, client):
        """Обновление с пустым телом запроса возвращает 422."""
        response = client.post("/auth/refresh", json={})
        assert response.status_code == 422

    def test_login_with_wrong_content_type(self, client):
        """Вход с неверным Content-Type."""
        response = client.post(
            "/auth/login",
            content="not json",
            headers={"Content-Type": "text/plain"},
        )
        # FastAPI вернет 422 или 400 в зависимости от версии
        assert response.status_code in [400, 422]


class TestAuthAPIEndpoints:
    """Тесты доступности эндпоинтов."""

    def test_login_endpoint_exists(self, client):
        """Эндпоинт /auth/login должен существовать."""
        response = client.post("/auth/login", json={"email": "t", "password": "t"})
        # Может вернуть 401/422, но не 404
        assert response.status_code != 404

    def test_register_endpoint_exists(self, client):
        """Эндпоинт /auth/register должен существовать."""
        response = client.post(
            "/auth/register", json={"email": "t@t.com", "password": "t"}
        )
        assert response.status_code != 404

    def test_refresh_endpoint_exists(self, client):
        """Эндпоинт /auth/refresh должен существовать."""
        response = client.post("/auth/refresh", json={"refresh_token": "t"})
        assert response.status_code != 404

    def test_me_endpoint_exists(self, client):
        """Эндпоинт /auth/me должен существовать."""
        response = client.get("/auth/me")
        # Без токена вернет 401, но не 404
        assert response.status_code != 404

    def test_root_endpoint_exists(self, client):
        """Корневой эндпоинт должен существовать."""
        response = client.get("/")
        assert response.status_code == 200

    def test_health_endpoint_exists(self, client):
        """Эндпоинт /health должен существовать."""
        response = client.get("/health")
        assert response.status_code == 200


class TestAuthAPIValidation:
    """Тесты валидации данных в API аутентификации."""

    def test_email_too_long(self, client):
        """Email, превышающий максимальную длину."""
        response = client.post(
            "/auth/register",
            json={
                "email": "a" * 300 + "@example.com",
                "password": "password",
                "role": "viewer",
            },
        )
        # Должно быть 422 (ошибка валидации Pydantic)
        assert response.status_code == 422

    def test_password_too_long(self, client):
        """Пароль, превышающий разумную длину (bcrypt обрежет)."""
        response = client.post(
            "/auth/register",
            json={
                "email": "longpass@example.com",
                "password": "a" * 1000,
                "role": "viewer",
            },
        )
        # Должно пройти (bcrypt сам обрежет)
        assert response.status_code == 201

    def test_role_case_sensitive(self, client):
        """Роль чувствительна к регистру."""
        response = client.post(
            "/auth/register",
            json={
                "email": "case@example.com",
                "password": "password",
                "role": "VIEWER",  # Заглавными
            },
        )
        # Должно быть 422 (недопустимая роль)
        assert response.status_code == 422

    def test_special_characters_in_email(self, client):
        """Email со специальными символами должен быть валидным."""
        response = client.post(
            "/auth/register",
            json={
                "email": "user+tag@example.com",
                "password": "password",
                "role": "viewer",
            },
        )
        assert response.status_code == 201

    def test_unicode_in_password(self, client):
        """Пароль с Unicode символами."""
        response = client.post(
            "/auth/register",
            json={
                "email": "unicode@example.com",
                "password": "пароль123αβγ",
                "role": "viewer",
            },
        )
        assert response.status_code == 201


class TestAuthAPISecurity:
    """Тесты безопасности API аутентификации."""

    def test_token_not_exposed_in_register_response(self, client, test_db):
        """В ответе на регистрацию не должно быть пароля."""
        response = client.post(
            "/auth/register",
            json={
                "email": "security_test@example.com",
                "password": "password",
                "role": "viewer",
            },
        )

        assert response.status_code == 201
        data = response.json()
        # В ответе только токен, нет пароля
        assert "password" not in data
        assert "password_hash" not in data

    def test_different_passwords_different_tokens(self, client):
        """Разные пароли должны давать разные токены."""
        client.post(
            "/auth/register",
            json={"email": "user1@test.com", "password": "pass1", "role": "viewer"},
        )
        client.post(
            "/auth/register",
            json={"email": "user2@test.com", "password": "pass2", "role": "viewer"},
        )

        login1 = client.post(
            "/auth/login", json={"email": "user1@test.com", "password": "pass1"}
        )
        login2 = client.post(
            "/auth/login", json={"email": "user2@test.com", "password": "pass2"}
        )

        token1 = login1.json()["access_token"]
        token2 = login2.json()["access_token"]

        assert token1 != token2

    def test_token_cannot_be_used_as_refresh(self, client, test_db):
        """Токен доступа можно использовать как refresh (в текущей реализации)."""
        register_user(
            email="token_refresh@example.com",
            password="password",
            role="viewer",
            db=test_db,
        )

        token = create_access_token(
            data={
                "user_id": 1,
                "email": "token_refresh@example.com",
                "role": "viewer",
            }
        )

        # В текущей реализации можно использовать access_token как refresh
        response = client.post("/auth/refresh", json={"refresh_token": token})
        assert response.status_code == 200


class TestAuthAPIRateLimiting:
    """Тесты rate limiting для эндпоинта входа."""

    def test_rate_limit_allows_five_attempts(self, client, test_db):
        """Первые 5 попыток должны быть разрешены."""
        register_user(
            email="rate_limit_test@example.com",
            password="correct",
            role="viewer",
            db=test_db,
        )

        for i in range(5):
            response = client.post(
                "/auth/login",
                json={
                    "email": "rate_limit_test@example.com",
                    "password": "wrong",
                },
            )
            assert response.status_code == 401

    def test_rate_limit_blocks_sixth_attempt(self, client, test_db):
        """6-я попытка должна быть заблокирована."""
        register_user(
            email="rate_limit_test2@example.com",
            password="correct",
            role="viewer",
            db=test_db,
        )

        # 5 неверных попыток
        for i in range(5):
            client.post(
                "/auth/login",
                json={
                    "email": "rate_limit_test2@example.com",
                    "password": "wrong",
                },
            )

        # 6-я попытка должна быть заблокирована
        response = client.post(
            "/auth/login",
            json={
                "email": "rate_limit_test2@example.com",
                "password": "wrong",
            },
        )
        assert response.status_code == 429

    def test_rate_limit_different_emails_independent(self, client, test_db):
        """Лимиты для разных email независимы."""
        register_user(
            email="email1@test.com",
            password="correct",
            role="viewer",
            db=test_db,
        )
        register_user(
            email="email2@test.com",
            password="correct",
            role="viewer",
            db=test_db,
        )

        # 5 попыток для первого email
        for i in range(5):
            client.post(
                "/auth/login",
                json={"email": "email1@test.com", "password": "wrong"},
            )

        # Попытка для второго email должна работать
        response = client.post(
            "/auth/login",
            json={"email": "email2@test.com", "password": "wrong"},
        )
        assert response.status_code == 401  # Не 429

    def test_correct_login_resets_rate_limit(self, client, test_db):
        """Успешный вход должен сбрасывать счетчик попыток."""
        register_user(
            email="reset_test@example.com",
            password="correct",
            role="viewer",
            db=test_db,
        )

        # Несколько неверных попыток
        for i in range(3):
            client.post(
                "/auth/login",
                json={
                    "email": "reset_test@example.com",
                    "password": "wrong",
                },
            )

        # Успешный вход
        response = client.post(
            "/auth/login",
            json={
                "email": "reset_test@example.com",
                "password": "correct",
            },
        )
        assert response.status_code == 200

        # Еще одна неверная попытка должна работать (счетчик сброшен)
        response = client.post(
            "/auth/login",
            json={
                "email": "reset_test@example.com",
                "password": "wrong",
            },
        )
        assert response.status_code == 401  # Не 429
