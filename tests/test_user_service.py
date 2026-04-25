"""Тесты для сервиса управления пользователями (user_service.py).

Тестирует бизнес-логику CRUD операций с пользователями:
- создание пользователей с валидацией
- получение пользователей по ID и email
- обновление ролей с проверкой прав
- удаление пользователей с защитой от удаления администраторов
- обработку ошибок и исключений

Использует изолированную тестовую базу данных SQLite in-memory.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import patch, MagicMock

from mko_bi.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_role,
    delete_user,
    get_all_users,
    register_user,
    _validate_role,
    VALID_ROLES,
)
from mko_bi.db.base import Base
from mko_bi.db.models import user as user_model, access, dashboard
from mko_bi.db.repositories.user_repo import UserRepository
from mko_bi.db.session import SessionLocal
from mko_bi.models.user import UserRead, UserDB


@pytest.fixture(scope="function")
def test_db():
    """Создает новую сессию для каждого теста и очищает данные после."""
    connection = user_service_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, future=True)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# Создаем отдельный engine для тестов user_service
TEST_DATABASE_URL = "sqlite:///:memory:"
user_service_engine = create_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
)
# Создаем таблицы
Base.metadata.create_all(bind=user_service_engine)
user_service_SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=user_service_engine,
    expire_on_commit=False,
    class_=Session,
)


class TestValidateRole:
    """Тесты для функции проверки роли."""

    def test_valid_roles(self):
        """Все допустимые роли должны проходить проверку."""
        for role in VALID_ROLES:
            _validate_role(role)

    def test_invalid_role_raises_error(self):
        """Недопустимая роль должна вызывать ValueError."""
        with pytest.raises(ValueError, match="Недопустимая роль"):
            _validate_role("invalid_role")

    def test_empty_role_raises_error(self):
        """Пустая роль должна вызывать ValueError."""
        with pytest.raises(ValueError, match="Недопустимая роль"):
            _validate_role("")

    def test_none_role_raises_error(self):
        """None как роль должен вызывать ValueError."""
        with pytest.raises(ValueError, match="Недопустимая роль"):
            _validate_role(None)


class TestCreateUser:
    """Тесты для функции создания пользователя."""

    def test_create_user_success(self, test_db):
        """Успешное создание пользователя."""
        user = create_user(
            "newuser@example.com", "secure_password123", "viewer", db=test_db
        )

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.role == "viewer"
        assert user.created_at is not None
        assert isinstance(user, UserRead)
        assert not hasattr(user, "password_hash")

    def test_create_user_all_roles(self, test_db):
        """Создание пользователей со всеми допустимыми ролями."""
        for role in VALID_ROLES:
            email = f"{role}_user@example.com"
            user = create_user(email, "password123", role, db=test_db)
            assert user.role == role
            assert user.email == email

    def test_create_user_duplicate_email(self, test_db, test_user):
        """Создание пользователя с существующим email должно вызывать ошибку."""
        with pytest.raises(ValueError, match="уже существует"):
            create_user(test_user.email, "password123", "viewer", db=test_db)

    def test_create_user_invalid_role(self, test_db):
        """Создание пользователя с недопустимой ролью должно вызывать ошибку."""
        with pytest.raises(ValueError, match="Недопустимая роль"):
            create_user(
                "newuser@example.com", "password123", "invalid_role", db=test_db
            )

    def test_create_user_password_is_hashed(self, test_db):
        """Пароль должен быть захеширован при сохранении."""
        create_user("hashuser@example.com", "plain_password", "viewer", db=test_db)

        user_obj = UserRepository.get_by_email("hashuser@example.com", test_db)
        assert user_obj is not None
        assert user_obj.password_hash.startswith("$2b$")
        assert user_obj.password_hash != "plain_password"

    def test_create_user_empty_password(self, test_db):
        """Создание пользователя с пустым паролем."""
        user = create_user("empty_pass@example.com", "", "viewer", db=test_db)
        assert user.email == "empty_pass@example.com"

    def test_create_user_long_password(self, test_db):
        """Создание пользователя с длинным паролем (более 72 байт)."""
        long_password = "a" * 100
        user = create_user("longpass@example.com", long_password, "viewer", db=test_db)
        assert user.email == "longpass@example.com"

    def test_create_user_special_chars_password(self, test_db):
        """Создание пользователя с паролем со специальными символами."""
        special_password = "p@ssw0rd!#$%^&*()"
        user = create_user(
            "specialchars@example.com", special_password, "editor", db=test_db
        )
        assert user.role == "editor"

    def test_create_user_multiple_users(self, test_db):
        """Создание нескольких пользователей."""
        emails = ["multi1@example.com", "multi2@example.com", "multi3@example.com"]
        for i, email in enumerate(emails):
            user = create_user(email, f"password{i}", "viewer", db=test_db)
            assert user.email == email
            assert user.id > 0

    def test_create_user_returns_correct_type(self, test_db):
        """create_user должна возвращать UserRead."""
        user = create_user("typeduser@example.com", "password", "admin", db=test_db)
        assert isinstance(user, UserRead)

    def test_create_user_db_error(self, test_db):
        """Ошибка базы данных при создании должна пробрасываться."""
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()
        mock_db.close = MagicMock()
        with patch("mko_bi.services.user_service.SessionLocal", return_value=mock_db):
            with patch.object(
                UserRepository, "get_by_email", side_effect=Exception("DB error")
            ):
                with pytest.raises(Exception, match="DB error"):
                    create_user("erroruser@example.com", "password", "viewer")
        mock_db.rollback.assert_called()
        mock_db.close.assert_called()

    def test_create_user_rollback_on_duplicate(self, test_db, test_user):
        """При дублирующемся email изменения не должны сохраняться."""
        initial_count = len(UserRepository.get_all(test_db))
        with patch("mko_bi.services.user_service.SessionLocal", return_value=test_db):
            with pytest.raises(ValueError):
                create_user(test_user.email, "new_password", "admin")
        # Проверяем, что не создалось нового пользователя
        final_count = len(UserRepository.get_all(test_db))
        assert initial_count == final_count


class TestGetUserByEmail:
    """Тесты для функции получения пользователя по email."""

    def test_get_user_by_email_success(self, test_db, test_user):
        """Успешное получение пользователя по email."""
        user = get_user_by_email(test_user.email, db=test_db)
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert user.role == test_user.role

    def test_get_user_by_email_not_found(self, test_db):
        """Получение несуществующего пользователя по email."""
        user = get_user_by_email("nonexistent@example.com", db=test_db)
        assert user is None

    def test_get_user_by_email_db_error(self, test_db):
        """Ошибка базы данных при получении должна пробрасываться."""
        mock_db = MagicMock()
        mock_db.close = MagicMock()
        with patch("mko_bi.services.user_service.SessionLocal", return_value=mock_db):
            with patch.object(
                UserRepository, "get_by_email", side_effect=Exception("DB error")
            ):
                with pytest.raises(Exception, match="DB error"):
                    get_user_by_email("test@example.com")
        mock_db.close.assert_called()


class TestGetUserById:
    """Тесты для функции получения пользователя по ID."""

    def test_get_user_by_id_success(self, test_db, test_user):
        """Успешное получение пользователя по ID."""
        user = get_user_by_id(test_user.id, db=test_db)
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_get_user_by_id_not_found(self, test_db):
        """Получение несуществующего пользователя по ID."""
        user = get_user_by_id(99999, db=test_db)
        assert user is None

    def test_get_user_by_id_db_error(self, test_db):
        """Ошибка базы данных при получении должна пробрасываться."""
        mock_db = MagicMock()
        mock_db.close = MagicMock()
        with patch("mko_bi.services.user_service.SessionLocal", return_value=mock_db):
            with patch.object(UserRepository, "get", side_effect=Exception("DB error")):
                with pytest.raises(Exception, match="DB error"):
                    get_user_by_id(1)
        mock_db.close.assert_called()


class TestUpdateUserRole:
    """Тесты для функции обновления роли пользователя."""

    def test_update_user_role_success(self, test_db, test_user):
        """Успешное обновление роли пользователя."""
        updated = update_user_role(test_user.id, "admin", db=test_db)
        assert updated is not None
        assert updated.id == test_user.id
        assert updated.role == "admin"

    def test_update_user_role_to_all_roles(self, test_db, test_user):
        """Обновление роли пользователя на все допустимые значения."""
        for role in VALID_ROLES:
            updated = update_user_role(test_user.id, role, db=test_db)
            assert updated.role == role

    def test_update_user_role_invalid_role(self, test_db, test_user):
        """Обновление с недопустимой ролью должно вызывать ошибку."""
        with pytest.raises(ValueError, match="Недопустимая роль"):
            update_user_role(test_user.id, "invalid_role", db=test_db)

    def test_update_user_role_nonexistent_user(self, test_db):
        """Обновление несуществующего пользователя должно возвращать None."""
        updated = update_user_role(99999, "admin", db=test_db)
        assert updated is None

    def test_update_user_role_no_change(self, test_db, test_user):
        """Обновление на ту же роль."""
        updated = update_user_role(test_user.id, test_user.role, db=test_db)
        assert updated is not None
        assert updated.role == test_user.role

    def test_update_user_role_db_error(self, test_db, test_user):
        """Ошибка базы данных при обновлении должна пробрасываться."""
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()
        mock_db.close = MagicMock()
        with patch("mko_bi.services.user_service.SessionLocal", return_value=mock_db):
            with patch.object(UserRepository, "get", side_effect=Exception("DB error")):
                with pytest.raises(Exception, match="DB error"):
                    update_user_role(test_user.id, "admin")
        mock_db.rollback.assert_called()
        mock_db.close.assert_called()


class TestDeleteUser:
    """Тесты для функции удаления пользователя."""

    def test_delete_user_success(self, test_db, test_user):
        """Успешное удаление пользователя."""
        result = delete_user(test_user.id, db=test_db)
        assert result is True
        # Проверяем, что пользователь действительно удален
        user = get_user_by_id(test_user.id, db=test_db)
        assert user is None

    def test_delete_nonexistent_user(self, test_db):
        """Удаление несуществующего пользователя должно возвращать False."""
        result = delete_user(99999, db=test_db)
        assert result is False

    def test_delete_user_db_error(self, test_db, test_user):
        """Ошибка базы данных при удалении должна пробрасываться."""
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()
        mock_db.close = MagicMock()
        with patch("mko_bi.services.user_service.SessionLocal", return_value=mock_db):
            with patch.object(UserRepository, "get", side_effect=Exception("DB error")):
                with pytest.raises(Exception, match="DB error"):
                    delete_user(test_user.id)
        mock_db.rollback.assert_called()
        mock_db.close.assert_called()


class TestAdminDeletionProtection:
    """Тесты защиты от удаления администраторов."""

    def test_delete_last_admin_with_other_users(self, test_db):
        """Нельзя удалить последнего администратора при наличии других пользователей."""
        # Создаем администратора
        admin = create_user("admin@example.com", "password", "admin", db=test_db)
        # Создаем обычного пользователя
        create_user("user@example.com", "password", "viewer", db=test_db)
        # Пытаемся удалить администратора - должно выдать ошибку
        with pytest.raises(ValueError, match="Нельзя удалить администратора"):
            delete_user(admin.id, db=test_db)

    def test_delete_admin_when_only_admin(self, test_db):
        """Можно удалить администратора, если он единственный пользователь."""
        # Удаляем всех существующих пользователей
        all_users = get_all_users(db=test_db)
        for u in all_users:
            UserRepository.delete(u.id, test_db)
        # Создаем только администратора
        admin = create_user("solo_admin@example.com", "password", "admin", db=test_db)
        # Удаляем его - должно сработать
        result = delete_user(admin.id, db=test_db)
        assert result is True

    def test_delete_non_admin_with_other_users(self, test_db):
        """Можно удалить не-администратора при наличии других пользователей."""
        # Создаем обычного пользователя
        user = create_user("regular_user@example.com", "password", "viewer", db=test_db)
        # Удаляем его - должно сработать
        result = delete_user(user.id, db=test_db)
        assert result is True


class TestGetAllUsers:
    """Тесты для функции получения всех пользователей."""

    def test_get_all_users(self, test_db, test_user):
        """Получение списка всех пользователей."""
        users = get_all_users(db=test_db)
        assert len(users) >= 1
        emails = [u.email for u in users]
        assert test_user.email in emails

    def test_get_all_users_empty(self, test_db):
        """Получение списка пользователей из пустой базы."""
        # Очищаем базу
        all_users = get_all_users(db=test_db)
        for u in all_users:
            UserRepository.delete(u.id, test_db)
        # Проверяем пустоту
        users = get_all_users(db=test_db)
        assert len(users) == 0

    def test_get_all_users_db_error(self, test_db):
        """Ошибка базы данных при получении списка должна пробрасываться."""
        mock_db = MagicMock()
        mock_db.close = MagicMock()
        with patch("mko_bi.services.user_service.SessionLocal", return_value=mock_db):
            with patch.object(
                UserRepository, "get_all", side_effect=Exception("DB error")
            ):
                with pytest.raises(Exception, match="DB error"):
                    get_all_users()
        mock_db.close.assert_called()


class TestRegisterUser:
    """Тесты для функции регистрации пользователя (алиас)."""

    def test_register_user_is_alias(self, test_db):
        """register_user должна быть алиасом для create_user."""
        user = register_user("aliasuser@example.com", "password", "viewer", db=test_db)
        assert user.email == "aliasuser@example.com"
        assert user.role == "viewer"
        assert isinstance(user, UserRead)


class TestUserServiceIntegration:
    """Интеграционные тесты для user_service."""

    def test_full_user_lifecycle(self, test_db):
        """Полный цикл жизни пользователя: создание -> чтение -> обновление -> удаление."""
        # 1. Создание
        user = create_user("lifecycle@example.com", "password", "viewer", db=test_db)
        assert user.email == "lifecycle@example.com"
        user_id = user.id

        # 2. Чтение по ID
        retrieved = get_user_by_id(user_id, db=test_db)
        assert retrieved is not None
        assert retrieved.email == "lifecycle@example.com"

        # 3. Чтение по email
        retrieved_by_email = get_user_by_email("lifecycle@example.com", db=test_db)
        assert retrieved_by_email is not None
        assert retrieved_by_email.id == user_id

        # 4. Обновление роли
        updated = update_user_role(user_id, "editor", db=test_db)
        assert updated.role == "editor"

        # 5. Удаление
        result = delete_user(user_id, db=test_db)
        assert result is True

        # 6. Проверка удаления
        assert get_user_by_id(user_id, db=test_db) is None

    def test_create_multiple_and_get_all(self, test_db):
        """Создание нескольких пользователей и получение всех."""
        emails = ["user1@test.com", "user2@test.com", "user3@test.com"]
        for email in emails:
            create_user(email, "password", "viewer", db=test_db)

        all_users = get_all_users(db=test_db)
        created_emails = [u.email for u in all_users if u.email in emails]
        assert len(created_emails) == 3

    def test_update_nonexistent_user_returns_none(self, test_db):
        """Обновление несуществующего пользователя возвращает None."""
        result = update_user_role(99999, "admin", db=test_db)
        assert result is None


class TestUserServiceErrorHandling:
    """Тесты обработки ошибок в user_service."""

    def test_create_user_with_invalid_data(self, test_db):
        """Создание пользователя с некорректными данными."""
        with pytest.raises(ValueError):
            create_user("invalid_email", "password", "viewer", db=test_db)

    def test_update_with_invalid_role_format(self, test_db, test_user):
        """Обновление с пустой ролью."""
        with pytest.raises(ValueError):
            update_user_role(test_user.id, "", db=test_db)
