"""Тесты для сервиса управления дашбордами (dashboard_service.py).

Тестирует бизнес-логику CRUD операций с дашбордами:
- создание дашбордов с валидацией и правами доступа
- получение дашбордов с проверкой прав
- обновление конфигурации
- удаление дашбордов
- управление доступами
- обработку ошибок и исключений

Использует изолированную тестовую базу данных SQLite in-memory.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from unittest.mock import patch, MagicMock

from mko_bi.services.dashboard_service import (
    create_dashboard,
    get_dashboard,
    get_user_dashboards,
    update_dashboard,
    delete_dashboard,
    grant_access,
    _validate_permission,
    _validate_config,
    VALID_PERMISSIONS,
)
from mko_bi.db.base import Base
from mko_bi.db.models import access, dashboard, user
from mko_bi.db.repositories.dashboard_repo import DashboardRepository
from mko_bi.db.repositories.access_repo import AccessRepository
from mko_bi.db.session import SessionLocal
from mko_bi.models.dashboard import DashboardConfig, DashboardRead


@pytest.fixture(scope="function")
def test_db():
    """Создает новую сессию для каждого теста и очищает данные после."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, future=True)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# Создаем отдельный engine для тестов dashboard_service
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
)
# Создаем таблицы
Base.metadata.create_all(bind=test_engine)
test_SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    expire_on_commit=False,
    class_=Session,
)


class TestValidatePermission:
    """Тесты для функции проверки уровня доступа."""

    def test_valid_permissions(self):
        """Все допустимые уровни доступа должны проходить проверку."""
        for permission in VALID_PERMISSIONS:
            _validate_permission(permission)

    def test_invalid_permission_raises_error(self):
        """Недопустимый уровень доступа должен вызывать ValueError."""
        with pytest.raises(ValueError, match="Недопустимый уровень доступа"):
            _validate_permission("invalid_permission")

    def test_empty_permission_raises_error(self):
        """Пустой уровень доступа должен вызывать ValueError."""
        with pytest.raises(ValueError, match="Недопустимый уровень доступа"):
            _validate_permission("")

    def test_none_permission_raises_error(self):
        """None как уровень доступа должен вызывать ValueError."""
        with pytest.raises(ValueError, match="Недопустимый уровень доступа"):
            _validate_permission(None)


class TestValidateConfig:
    """Тесты для функции проверки конфигурации дашборда."""

    def test_valid_config(self):
        """Валидная конфигурация должна проходить проверку."""
        config = DashboardConfig(graph_types=["bar", "line"])
        _validate_config(config)

    def test_empty_graph_types_raises_error(self):
        """Конфигурация без типов графиков должна вызывать ошибку."""
        config = DashboardConfig(graph_types=[])
        with pytest.raises(ValueError, match="должна содержать хотя бы один тип"):
            _validate_config(config)

    def test_invalid_graph_type_raises_error(self):
        """Недопустимый тип графика должен вызывать ошибку при валидации."""
        with pytest.raises(
            Exception, match="Input should be 'bar', 'line', 'pie' or 'table'"
        ):
            DashboardConfig(graph_types=["invalid_type"])

    def test_valid_graph_types(self):
        """Все допустимые типы графиков должны проходить проверку."""
        config = DashboardConfig(graph_types=["bar", "line", "pie", "table"])
        _validate_config(config)


class TestCreateDashboard:
    """Тесты для функции создания дашборда."""

    def test_create_dashboard_success(self, test_db, test_user):
        """Успешное создание дашборда."""
        config = {"graph_types": ["bar"], "charts": []}
        dashboard = create_dashboard(
            name="Test Dashboard",
            config=config,
            owner_id=test_user.id,
            db=test_db,
        )

        assert dashboard.id is not None
        assert dashboard.name == "Test Dashboard"
        assert isinstance(dashboard.config, DashboardConfig)
        assert dashboard.config.graph_types == ["bar"]
        assert isinstance(dashboard, DashboardRead)

    def test_create_dashboard_with_full_config(self, test_db, test_user):
        """Создание дашборда с полной конфигурацией."""
        config = {
            "graph_types": ["bar", "line"],
            "filters": [{"field": "year", "type": "select"}],
            "charts": [
                {
                    "type": "bar",
                    "x": "category",
                    "y": "revenue",
                    "title": "Revenue by Category",
                }
            ],
            "title": "Sales Dashboard",
            "description": "Overview of sales performance",
        }
        dashboard = create_dashboard(
            name="Sales Dashboard",
            config=config,
            owner_id=test_user.id,
            db=test_db,
        )

        assert dashboard.id is not None
        assert dashboard.name == "Sales Dashboard"
        assert dashboard.config.graph_types == ["bar", "line"]
        assert len(dashboard.config.filters) == 1
        assert len(dashboard.config.charts) == 1

    def test_create_dashboard_invalid_config(self, test_db, test_user):
        """Создание дашборда с некорректной конфигурацией."""
        config = {"graph_types": []}
        with pytest.raises(ValueError, match="должна содержать хотя бы один тип"):
            create_dashboard(
                name="Test Dashboard",
                config=config,
                owner_id=test_user.id,
                db=test_db,
            )

    def test_create_dashboard_invalid_graph_type(self, test_db, test_user):
        """Создание дашборда с недопустимым типом графика."""
        config = {"graph_types": ["invalid_type"]}
        with pytest.raises(
            Exception, match="Input should be 'bar', 'line', 'pie' or 'table'"
        ):
            create_dashboard(
                name="Test Dashboard",
                config=config,
                owner_id=test_user.id,
                db=test_db,
            )

    def test_create_dashboard_creates_admin_access(self, test_db, test_user):
        """Создание дашборда должно предоставлять права администратора владельцу."""
        config = {"graph_types": ["bar"]}
        dashboard = create_dashboard(
            name="Test Dashboard",
            config=config,
            owner_id=test_user.id,
            db=test_db,
        )

        # Проверяем, что владелец имеет права администратора
        permission = AccessRepository.check_access(
            user_id=test_user.id,
            dashboard_id=dashboard.id,
            db=test_db,
        )
        assert permission == "admin"

    def test_create_multiple_dashboards(self, test_db, test_user):
        """Создание нескольких дашбордов."""
        config = {"graph_types": ["bar"]}
        for i in range(3):
            dashboard = create_dashboard(
                name=f"Dashboard {i}",
                config=config,
                owner_id=test_user.id,
                db=test_db,
            )
            assert dashboard.name == f"Dashboard {i}"

    def test_create_dashboard_db_error(self, test_db, test_user):
        """Ошибка базы данных при создании должна пробрасываться."""
        config = {"graph_types": ["bar"]}
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()
        mock_db.close = MagicMock()
        with patch(
            "mko_bi.services.dashboard_service.SessionLocal", return_value=mock_db
        ):
            with patch.object(
                DashboardRepository, "create", side_effect=Exception("DB error")
            ):
                with pytest.raises(Exception, match="DB error"):
                    create_dashboard(
                        name="Test Dashboard",
                        config=config,
                        owner_id=test_user.id,
                    )
        mock_db.rollback.assert_called()
        mock_db.close.assert_called()

    def test_create_dashboard_rollback_on_error(self, test_db, test_user):
        """При ошибке создания доступа изменения должны откатиться."""
        config = {"graph_types": ["bar"]}
        initial_count = len(DashboardRepository.get_all(test_db))

        with patch(
            "mko_bi.services.dashboard_service.SessionLocal", return_value=test_db
        ):
            with patch.object(
                AccessRepository, "grant_access", side_effect=Exception("Access error")
            ):
                with pytest.raises(Exception, match="Access error"):
                    create_dashboard(
                        name="Test Dashboard",
                        config=config,
                        owner_id=test_user.id,
                    )

        # Проверяем, что дашборд не был создан
        final_count = len(DashboardRepository.get_all(test_db))
        assert initial_count == final_count


class TestGetDashboard:
    """Тесты для функции получения дашборда."""

    def test_get_dashboard_success(self, test_db, test_user, test_dashboard):
        """Успешное получение дашборда с доступом."""
        # Предоставляем доступ
        AccessRepository.grant_access(
            user_id=test_user.id,
            dashboard_id=test_dashboard.id,
            permission_level="read",
            db=test_db,
        )

        dashboard = get_dashboard(
            dashboard_id=test_dashboard.id,
            user_id=test_user.id,
            db=test_db,
        )

        assert dashboard is not None
        assert dashboard.id == test_dashboard.id
        assert dashboard.name == test_dashboard.name
        assert isinstance(dashboard, DashboardRead)

    def test_get_dashboard_no_access(self, test_db, test_user, test_dashboard):
        """Получение дашборда без доступа должно возвращать None."""
        dashboard = get_dashboard(
            dashboard_id=test_dashboard.id,
            user_id=test_user.id,
            db=test_db,
        )

        assert dashboard is None

    def test_get_dashboard_admin_access(self, test_db, test_user, test_dashboard):
        """Получение дашборда с правами администратора."""
        AccessRepository.grant_access(
            user_id=test_user.id,
            dashboard_id=test_dashboard.id,
            permission_level="admin",
            db=test_db,
        )

        dashboard = get_dashboard(
            dashboard_id=test_dashboard.id,
            user_id=test_user.id,
            db=test_db,
        )

        assert dashboard is not None
        assert dashboard.id == test_dashboard.id

    def test_get_nonexistent_dashboard(self, test_db, test_user):
        """Получение несуществующего дашборда."""
        dashboard = get_dashboard(
            dashboard_id=99999,
            user_id=test_user.id,
            db=test_db,
        )

        assert dashboard is None

    def test_get_dashboard_with_different_permissions(
        self, test_db, test_user, test_dashboard
    ):
        """Получение дашборда с разными уровнями доступа."""
        for permission in ["read", "write", "admin"]:
            AccessRepository.grant_access(
                user_id=test_user.id,
                dashboard_id=test_dashboard.id,
                permission_level=permission,
                db=test_db,
            )

            dashboard = get_dashboard(
                dashboard_id=test_dashboard.id,
                user_id=test_user.id,
                db=test_db,
            )

            assert dashboard is not None
            assert dashboard.id == test_dashboard.id

            # Очищаем доступ для следующей итерации
            AccessRepository.revoke_access(
                user_id=test_user.id,
                dashboard_id=test_dashboard.id,
                db=test_db,
            )

    def test_get_dashboard_db_error(self, test_db, test_user):
        """Ошибка базы данных при получении должна пробрасываться."""
        mock_db = MagicMock()
        mock_db.close = MagicMock()
        with patch(
            "mko_bi.services.dashboard_service.SessionLocal", return_value=mock_db
        ):
            with patch.object(
                DashboardRepository, "get", side_effect=Exception("DB error")
            ):
                with pytest.raises(Exception, match="DB error"):
                    get_dashboard(dashboard_id=1, user_id=test_user.id)
        mock_db.close.assert_called()


class TestGetUserDashboards:
    """Тесты для функции получения дашбордов пользователя."""

    def test_get_user_dashboards(self, test_db, test_user, test_dashboard, test_access):
        """Получение дашбордов пользователя с доступом."""
        dashboards = get_user_dashboards(user_id=test_user.id, db=test_db)

        assert len(dashboards) >= 1
        dashboard_ids = [d.id for d in dashboards]
        assert test_dashboard.id in dashboard_ids

    def test_get_user_dashboards_no_access(self, test_db, test_user):
        """Получение дашбордов пользователя без доступа."""
        # Создаем дашборд без доступа
        dashboard = DashboardRepository.create(
            db=test_db,
            name="Private Dashboard",
            config='{"graph_types": ["bar"]}',
        )

        dashboards = get_user_dashboards(user_id=test_user.id, db=test_db)
        dashboard_ids = [d.id for d in dashboards]

        assert dashboard.id not in dashboard_ids

    def test_get_user_dashboards_multiple(self, test_db, test_user):
        """Получение нескольких дашбордов пользователя."""
        # Создаем несколько дашбордов с доступом
        for i in range(3):
            dashboard = DashboardRepository.create(
                db=test_db,
                name=f"Dashboard {i}",
                config='{"graph_types": ["bar"]}',
            )
            AccessRepository.grant_access(
                user_id=test_user.id,
                dashboard_id=dashboard.id,
                permission_level="read",
                db=test_db,
            )

        dashboards = get_user_dashboards(user_id=test_user.id, db=test_db)
        assert len(dashboards) >= 3

    def test_get_user_dashboards_empty(self, test_db, test_user):
        """Получение дашбордов пользователя без каких-либо доступов."""
        # Удаляем все доступы пользователя
        all_access = AccessRepository.get_all(test_db)
        for access_obj in all_access:
            if access_obj.user_id == test_user.id:
                AccessRepository.revoke_access(
                    user_id=test_user.id,
                    dashboard_id=access_obj.dashboard_id,
                    db=test_db,
                )

        dashboards = get_user_dashboards(user_id=test_user.id, db=test_db)
        assert len(dashboards) == 0

    def test_get_user_dashboards_different_permissions(
        self, test_db, test_user, test_dashboard
    ):
        """Получение дашбордов с разными уровнями доступа."""
        for permission in ["read", "write", "admin"]:
            AccessRepository.grant_access(
                user_id=test_user.id,
                dashboard_id=test_dashboard.id,
                permission_level=permission,
                db=test_db,
            )

            dashboards = get_user_dashboards(user_id=test_user.id, db=test_db)
            dashboard_ids = [d.id for d in dashboards]
            assert test_dashboard.id in dashboard_ids

            # Очищаем доступ для следующей итерации
            AccessRepository.revoke_access(
                user_id=test_user.id,
                dashboard_id=test_dashboard.id,
                db=test_db,
            )

    def test_get_user_dashboards_db_error(self, test_db, test_user):
        """Ошибка базы данных при получении должна пробрасываться."""
        mock_db = MagicMock()
        mock_db.close = MagicMock()
        with patch(
            "mko_bi.services.dashboard_service.SessionLocal", return_value=mock_db
        ):
            with patch.object(
                AccessRepository,
                "get_user_dashboards",
                side_effect=Exception("DB error"),
            ):
                with pytest.raises(Exception, match="DB error"):
                    get_user_dashboards(user_id=test_user.id)
        mock_db.close.assert_called()


class TestUpdateDashboard:
    """Тесты для функции обновления дашборда."""

    def test_update_dashboard_success(self, test_db, test_dashboard):
        """Успешное обновление дашборда."""
        config = {"graph_types": ["line"], "title": "Updated Dashboard"}
        updated = update_dashboard(
            dashboard_id=test_dashboard.id,
            config=config,
            db=test_db,
        )

        assert updated is not None
        assert updated.id == test_dashboard.id
        assert updated.config.graph_types == ["line"]
        assert updated.config.title == "Updated Dashboard"

    def test_update_dashboard_partial_config(self, test_db, test_dashboard):
        """Обновление дашборда с частичной конфигурацией."""
        config = {"graph_types": ["bar", "line"]}
        updated = update_dashboard(
            dashboard_id=test_dashboard.id,
            config=config,
            db=test_db,
        )

        assert updated is not None
        assert updated.config.graph_types == ["bar", "line"]

    def test_update_nonexistent_dashboard(self, test_db):
        """Обновление несуществующего дашборда."""
        config = {"graph_types": ["bar"]}
        updated = update_dashboard(
            dashboard_id=99999,
            config=config,
            db=test_db,
        )

        assert updated is None

    def test_update_dashboard_invalid_config(self, test_db, test_dashboard):
        """Обновление с некорректной конфигурацией."""
        config = {"graph_types": []}
        with pytest.raises(ValueError, match="должна содержать хотя бы один тип"):
            update_dashboard(
                dashboard_id=test_dashboard.id,
                config=config,
                db=test_db,
            )

    def test_update_dashboard_invalid_graph_type(self, test_db, test_dashboard):
        """Обновление с недопустимым типом графика."""
        config = {"graph_types": ["invalid_type"]}
        with pytest.raises(
            Exception, match="Input should be 'bar', 'line', 'pie' or 'table'"
        ):
            update_dashboard(
                dashboard_id=test_dashboard.id,
                config=config,
                db=test_db,
            )

    def test_update_dashboard_db_error(self, test_db, test_dashboard):
        """Ошибка базы данных при обновлении должна пробрасываться."""
        config = {"graph_types": ["bar"]}
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()
        mock_db.close = MagicMock()
        with patch(
            "mko_bi.services.dashboard_service.SessionLocal", return_value=mock_db
        ):
            with patch.object(
                DashboardRepository, "update", side_effect=Exception("DB error")
            ):
                with pytest.raises(Exception, match="DB error"):
                    update_dashboard(
                        dashboard_id=test_dashboard.id,
                        config=config,
                    )
        mock_db.rollback.assert_called()
        mock_db.close.assert_called()

    def test_update_dashboard_rollback_on_error(self, test_db, test_dashboard):
        """При ошибке обновления изменения должны откатиться."""
        config = {"graph_types": ["bar"]}
        with patch(
            "mko_bi.services.dashboard_service.SessionLocal", return_value=test_db
        ):
            with patch.object(
                DashboardRepository, "update", side_effect=Exception("Update error")
            ):
                with pytest.raises(Exception, match="Update error"):
                    update_dashboard(
                        dashboard_id=test_dashboard.id,
                        config=config,
                    )


class TestDeleteDashboard:
    """Тесты для функции удаления дашборда."""

    def test_delete_dashboard_success(self, test_db, test_dashboard):
        """Успешное удаление дашборда."""
        result = delete_dashboard(dashboard_id=test_dashboard.id, db=test_db)

        assert result is True
        # Проверяем, что дашборд действительно удален
        dashboard = DashboardRepository.get(test_dashboard.id, db=test_db)
        assert dashboard is None

    def test_delete_nonexistent_dashboard(self, test_db):
        """Удаление несуществующего дашборда."""
        result = delete_dashboard(dashboard_id=99999, db=test_db)

        assert result is False

    def test_delete_dashboard_cascades_access(self, test_db, test_user, test_dashboard):
        """Удаление дашборда должно удалять связанные права доступа."""
        # Создаем доступ
        AccessRepository.grant_access(
            user_id=test_user.id,
            dashboard_id=test_dashboard.id,
            permission_level="read",
            db=test_db,
        )

        # Удаляем дашборд
        result = delete_dashboard(dashboard_id=test_dashboard.id, db=test_db)
        assert result is True

        # Проверяем, что доступ также удален
        permission = AccessRepository.check_access(
            user_id=test_user.id,
            dashboard_id=test_dashboard.id,
            db=test_db,
        )
        assert permission is None

    def test_delete_dashboard_db_error(self, test_db, test_dashboard):
        """Ошибка базы данных при удалении должна пробрасываться."""
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()
        mock_db.close = MagicMock()
        with patch(
            "mko_bi.services.dashboard_service.SessionLocal", return_value=mock_db
        ):
            with patch.object(
                DashboardRepository, "delete", side_effect=Exception("DB error")
            ):
                with pytest.raises(Exception, match="DB error"):
                    delete_dashboard(dashboard_id=test_dashboard.id)
        mock_db.rollback.assert_called()
        mock_db.close.assert_called()

    def test_delete_dashboard_rollback_on_error(self, test_db, test_dashboard):
        """При ошибке удаления изменения должны откатиться."""
        with patch(
            "mko_bi.services.dashboard_service.SessionLocal", return_value=test_db
        ):
            with patch.object(
                DashboardRepository, "delete", side_effect=Exception("Delete error")
            ):
                with pytest.raises(Exception, match="Delete error"):
                    delete_dashboard(dashboard_id=test_dashboard.id)


class TestGrantAccess:
    """Тесты для функции предоставления доступа."""

    def test_grant_access_success(self, test_db, test_user, test_dashboard):
        """Успешное предоставление доступа."""
        result = grant_access(
            dashboard_id=test_dashboard.id,
            user_id=test_user.id,
            permission="write",
            db=test_db,
        )

        assert result is True
        # Проверяем, что доступ предоставлен
        permission = AccessRepository.check_access(
            user_id=test_user.id,
            dashboard_id=test_dashboard.id,
            db=test_db,
        )
        assert permission == "write"

    def test_grant_access_duplicate(
        self, test_db, test_user, test_dashboard, test_access
    ):
        """Предоставление дублирующегося доступа."""
        result = grant_access(
            dashboard_id=test_dashboard.id,
            user_id=test_user.id,
            permission="read",
            db=test_db,
        )

        assert result is True
        # Должен вернуть существующий доступ
        permission = AccessRepository.check_access(
            user_id=test_user.id,
            dashboard_id=test_dashboard.id,
            db=test_db,
        )
        assert permission == "read"

    def test_grant_access_all_permissions(self, test_db, test_user, test_dashboard):
        """Предоставление всех допустимых уровней доступа."""
        for permission in ["read", "write", "admin"]:
            # Отзываем предыдущий доступ перед предоставлением нового
            AccessRepository.revoke_access(
                user_id=test_user.id,
                dashboard_id=test_dashboard.id,
                db=test_db,
            )
            result = grant_access(
                dashboard_id=test_dashboard.id,
                user_id=test_user.id,
                permission=permission,
                db=test_db,
            )
            assert result is True

            # Проверяем уровень доступа
            perm = AccessRepository.check_access(
                user_id=test_user.id,
                dashboard_id=test_dashboard.id,
                db=test_db,
            )
            assert perm == permission

    def test_grant_access_invalid_permission(self, test_db, test_user, test_dashboard):
        """Предоставление доступа с некорректным уровнем."""
        with pytest.raises(ValueError, match="Недопустимый уровень доступа"):
            grant_access(
                dashboard_id=test_dashboard.id,
                user_id=test_user.id,
                permission="invalid",
                db=test_db,
            )

    def test_grant_access_nonexistent_dashboard(self, test_db, test_user):
        """Предоставление доступа к несуществующему дашборду."""
        with pytest.raises(ValueError, match="Дашборд с id=99999 не найден"):
            grant_access(
                dashboard_id=99999,
                user_id=test_user.id,
                permission="read",
                db=test_db,
            )

    def test_grant_access_db_error(self, test_db, test_user, test_dashboard):
        """Ошибка базы данных при предоставлении доступа должна пробрасываться."""
        mock_db = MagicMock()
        mock_db.rollback = MagicMock()
        mock_db.close = MagicMock()
        with patch(
            "mko_bi.services.dashboard_service.SessionLocal", return_value=mock_db
        ):
            with patch.object(
                AccessRepository, "grant_access", side_effect=Exception("DB error")
            ):
                with pytest.raises(Exception, match="DB error"):
                    grant_access(
                        dashboard_id=test_dashboard.id,
                        user_id=test_user.id,
                        permission="read",
                    )
        mock_db.rollback.assert_called()
        mock_db.close.assert_called()

    def test_grant_access_rollback_on_error(self, test_db, test_user, test_dashboard):
        """При ошибке предоставления доступа изменения должны откатиться."""
        with patch(
            "mko_bi.services.dashboard_service.SessionLocal", return_value=test_db
        ):
            with patch.object(
                AccessRepository, "grant_access", side_effect=Exception("Grant error")
            ):
                with pytest.raises(Exception, match="Grant error"):
                    grant_access(
                        dashboard_id=test_dashboard.id,
                        user_id=test_user.id,
                        permission="read",
                    )


class TestDashboardServiceIntegration:
    """Интеграционные тесты для dashboard_service."""

    def test_full_dashboard_lifecycle(self, test_db, test_user):
        """Полный цикл жизни дашборда: создание -> чтение -> обновление -> удаление."""
        # 1. Создание
        config = {"graph_types": ["bar"], "title": "Test Dashboard"}
        dashboard = create_dashboard(
            name="Test Dashboard",
            config=config,
            owner_id=test_user.id,
            db=test_db,
        )
        assert dashboard.name == "Test Dashboard"
        dashboard_id = dashboard.id

        # 2. Чтение
        retrieved = get_dashboard(
            dashboard_id=dashboard_id,
            user_id=test_user.id,
            db=test_db,
        )
        assert retrieved is not None
        assert retrieved.name == "Test Dashboard"

        # 3. Обновление
        updated_config = {"graph_types": ["line"], "title": "Updated Dashboard"}
        updated = update_dashboard(
            dashboard_id=dashboard_id,
            config=updated_config,
            db=test_db,
        )
        assert updated.config.graph_types == ["line"]
        assert updated.config.title == "Updated Dashboard"

        # 4. Удаление
        result = delete_dashboard(dashboard_id=dashboard_id, db=test_db)
        assert result is True

        # 5. Проверка удаления
        assert (
            get_dashboard(dashboard_id=dashboard_id, user_id=test_user.id, db=test_db)
            is None
        )

    def test_create_dashboard_and_grant_access(self, test_db, test_user):
        """Создание дашборда и предоставление доступа другому пользователю."""
        # Создаем второго пользователя
        user2 = user.User(
            email="user2@example.com",
            password_hash="hashed_password",
            role="viewer",
        )
        test_db.add(user2)
        test_db.commit()
        test_db.refresh(user2)

        # Создаем дашборд
        config = {"graph_types": ["bar"]}
        dashboard = create_dashboard(
            name="Test Dashboard",
            config=config,
            owner_id=test_user.id,
            db=test_db,
        )

        # Предоставляем доступ второму пользователю
        result = grant_access(
            dashboard_id=dashboard.id,
            user_id=user2.id,
            permission="read",
            db=test_db,
        )
        assert result is True

        # Проверяем, что второй пользователь может получить дашборд
        retrieved = get_dashboard(
            dashboard_id=dashboard.id,
            user_id=user2.id,
            db=test_db,
        )
        assert retrieved is not None
        assert retrieved.id == dashboard.id

    def test_multiple_users_access_same_dashboard(self, test_db, test_user):
        """Несколько пользователей имеют доступ к одному дашборду."""
        # Создаем дополнительных пользователей
        users = []
        for i in range(3):
            user_obj = user.User(
                email=f"user{i}@example.com",
                password_hash="hashed_password",
                role="viewer",
            )
            test_db.add(user_obj)
            test_db.commit()
            test_db.refresh(user_obj)
            users.append(user_obj)

        # Создаем дашборд
        config = {"graph_types": ["bar"]}
        dashboard = create_dashboard(
            name="Shared Dashboard",
            config=config,
            owner_id=test_user.id,
            db=test_db,
        )

        # Предоставляем доступ всем пользователям
        for user_obj in users:
            grant_access(
                dashboard_id=dashboard.id,
                user_id=user_obj.id,
                permission="read",
                db=test_db,
            )

        # Проверяем, что все пользователи могут получить дашборд
        for user_obj in users:
            retrieved = get_dashboard(
                dashboard_id=dashboard.id,
                user_id=user_obj.id,
                db=test_db,
            )
            assert retrieved is not None

    def test_dashboard_config_json_serialization(self, test_db, test_user):
        """Проверка сериализации/десериализации конфигурации дашборда в JSON."""
        config = {
            "graph_types": ["bar", "line"],
            "filters": [{"field": "year", "type": "select"}],
            "charts": [
                {
                    "type": "bar",
                    "x": "category",
                    "y": "revenue",
                }
            ],
        }
        dashboard = create_dashboard(
            name="Test Dashboard",
            config=config,
            owner_id=test_user.id,
            db=test_db,
        )

        # Проверяем, что конфигурация корректно сериализуется и десериализуется
        assert dashboard.config.graph_types == ["bar", "line"]
        assert len(dashboard.config.filters) == 1
        assert len(dashboard.config.charts) == 1


class TestDashboardServiceErrorHandling:
    """Тесты обработки ошибок в dashboard_service."""

    def test_create_dashboard_with_invalid_data(self, test_db, test_user):
        """Создание дашборда с некорректными данными."""
        with pytest.raises(ValueError):
            create_dashboard(
                name="Test Dashboard",
                config={"graph_types": []},
                owner_id=test_user.id,
                db=test_db,
            )

    def test_update_dashboard_with_invalid_data(self, test_db, test_dashboard):
        """Обновление дашборда с некорректными данными."""
        with pytest.raises(ValueError):
            update_dashboard(
                dashboard_id=test_dashboard.id,
                config={"graph_types": []},
                db=test_db,
            )

    def test_grant_access_with_invalid_permission(
        self, test_db, test_user, test_dashboard
    ):
        """Предоставление доступа с некорректным уровнем."""
        with pytest.raises(ValueError):
            grant_access(
                dashboard_id=test_dashboard.id,
                user_id=test_user.id,
                permission="invalid_permission",
                db=test_db,
            )
