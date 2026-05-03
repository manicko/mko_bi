import pytest
from pydantic import ValidationError

from mko_bi.models.user import (
    UserBase,
    UserCreate,
    UserRead,
    UserDB,
    UserUpdate,
)
from mko_bi.models.dashboard import (
    DashboardConfig,
    DashboardCreate,
    DashboardRead,
    DashboardUpdate,
)
from mko_bi.models.data import (
    DataUpload,
    ProcessingConfig,
    ProcessingResult,
    AggregatedData,
)
from mko_bi.models.auth import (
    LoginRequest,
    Token,
    TokenData,
)
from mko_bi.models.access import (
    AccessCheck,
    AccessGrant,
)


class TestUserModels:
    """Тесты для Pydantic моделей пользователя."""

    def test_user_create_valid(self):
        """Проверяет создание валидного пользователя."""
        user = UserCreate(
            email="test@example.com",
            password="secure_password123",
            role="viewer",
        )
        assert user.email == "test@example.com"
        assert user.password == "secure_password123"
        assert user.role == "viewer"

    def test_user_create_invalid_email(self):
        """Проверяет валидацию неверного email."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                password="secure_password123",
                role="viewer",
            )

    def test_user_create_invalid_role(self):
        """Проверяет валидацию неверной роли."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="secure_password123",
                role="invalid_role",
            )

    def test_user_create_missing_password(self):
        """Проверяет обязательность пароля."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                role="viewer",
            )

    def test_user_read_valid(self):
        """Проверка создания модели чтения пользователя."""
        user = UserRead(
            id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            role="admin",
            created_at="2026-04-24T16:02:46+03:00",
        )
        assert str(user.id) == "550e8400-e29b-41d4-a716-446655440000"
        assert user.email == "test@example.com"
        assert user.role == "admin"

    def test_user_db_valid(self):
        """Проверка создания модели пользователя БД."""
        user = UserDB(
            id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            password_hash="$2b$12$examplehash",
            role="editor",
            created_at="2026-04-24T16:02:46+03:00",
        )
        assert str(user.id) == "550e8400-e29b-41d4-a716-446655440000"
        assert user.password_hash == "$2b$12$examplehash"
        assert user.role == "editor"

    def test_user_update_partial(self):
        """Проверяет частичное обновление пользователя."""
        user = UserUpdate(email="new@example.com")
        assert user.email == "new@example.com"
        assert user.role is None
        assert user.password is None

    def test_user_update_all_fields(self):
        """Проверяет обновление всех полей пользователя."""
        user = UserUpdate(
            email="new@example.com",
            role="admin",
            password="new_password",
        )
        assert user.email == "new@example.com"
        assert user.role == "admin"
        assert user.password == "new_password"

    def test_user_base_config(self):
        """Проверяет конфигурацию базовой модели."""
        user = UserBase(email="test@example.com", role="viewer")
        config = user.model_config
        assert config.get("from_attributes") is True

    def test_user_create_from_attributes(self):
        """Проверяет создание модели из атрибутов."""
        data = {
            "email": "test@example.com",
            "password": "pass",
            "role": "admin",
        }
        user = UserCreate.model_validate(data)
        assert user.email == "test@example.com"
        assert user.role == "admin"


class TestDashboardModels:
    """Тесты для Pydantic моделей дашборда."""

    def test_dashboard_config_valid(self):
        """Проверяет создание валидной конфигурации дашборда."""
        config = DashboardConfig(
            graph_types=["bar", "line"],
            filters=[{"field": "year", "type": "select"}],
            aggregations=[{"type": "sum", "field": "revenue"}],
        )
        assert config.graph_types == ["bar", "line"]
        assert len(config.filters) == 1
        assert len(config.aggregations) == 1

    def test_dashboard_config_minimal(self):
        """Проверяет создание минимальной конфигурации."""
        config = DashboardConfig(graph_types=["bar"])
        assert config.graph_types == ["bar"]
        assert config.filters is None
        assert config.aggregations is None

    def test_dashboard_config_invalid_graph_type(self):
        """Проверяет валидацию неверного типа графика."""
        with pytest.raises(ValidationError):
            DashboardConfig(graph_types=["invalid_type"])

    def test_dashboard_create_valid(self):
        """Проверяет создание валидного дашборда."""
        dashboard = DashboardCreate(
            name="Sales Dashboard",
            config=DashboardConfig(
                graph_types=["bar", "line"],
                filters=[{"field": "year", "type": "select"}],
            ),
        )
        assert dashboard.name == "Sales Dashboard"
        assert dashboard.config.graph_types == ["bar", "line"]

    def test_dashboard_read_valid(self):
        """Проверка создания модели чтения дашборда."""
        dashboard = DashboardRead(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Sales Dashboard",
            description="Test description",
            config=DashboardConfig(graph_types=["bar"]),
            created_at="2026-04-24T16:02:46+03:00",
            updated_at="2026-04-24T16:02:46+03:00",
        )
        assert str(dashboard.id) == "550e8400-e29b-41d4-a716-446655440000"
        assert dashboard.name == "Sales Dashboard"
        assert dashboard.description == "Test description"
        assert dashboard.config.graph_types == ["bar"]

    def test_dashboard_update_partial(self):
        """Проверяет частичное обновление дашборда."""
        update = DashboardUpdate(name="New Name")
        assert update.name == "New Name"
        assert update.config is None

    def test_dashboard_config_with_charts(self):
        """Проверяет конфигурацию с графиками."""
        config = DashboardConfig(
            graph_types=["bar", "line", "pie"],
            charts=[
                {
                    "type": "bar",
                    "x": "category",
                    "y": "revenue",
                    "title": "Revenue by Category",
                }
            ],
        )
        assert len(config.charts) == 1
        assert config.charts[0]["type"] == "bar"


class TestDataModels:
    """Тесты для Pydantic моделей данных."""

    def test_data_upload_valid(self):
        """Проверяет создание валидной загрузки данных."""
        upload = DataUpload(
            file=b"test,data\n1,2",
            filename="data.csv.gz",
            dashboard_id="550e8400-e29b-41d4-a716-446655440000",
        )
        assert upload.filename == "data.csv.gz"
        assert str(upload.dashboard_id) == "550e8400-e29b-41d4-a716-446655440000"
        assert upload.file == b"test,data\n1,2"

    def test_processing_config_valid(self):
        """Проверяет создание валидной конфигурации обработки."""
        config = ProcessingConfig(
            transformations=[{"type": "filter", "condition": {"year": {"$gte": 2020}}}],
            aggregations=[{"type": "sum", "field": "revenue", "groupby": "category"}],
            groupby=["category", "region"],
            filters=[{"field": "year", "operator": ">=", "value": 2020}],
            metrics=[
                {"name": "total_revenue", "type": "sum", "field": "revenue"},
                {"name": "avg_sales", "type": "avg", "field": "sales"},
            ],
        )
        assert len(config.transformations) == 1
        assert len(config.aggregations) == 1
        assert config.groupby == ["category", "region"]

    def test_processing_config_minimal(self):
        """Проверяет создание минимальной конфигурации обработки."""
        config = ProcessingConfig()
        assert config.transformations is None
        assert config.aggregations is None

    def test_processing_result_valid(self):
        """Проверяет создание валидного результата обработки."""
        result = ProcessingResult(
            success=True,
            task_id="550e8400-e29b-41d4-a716-446655440000",
            dashboard_id="550e8400-e29b-41d4-a716-446655440000",
            rows_processed=1000,
            message="Data processed successfully",
            data={"columns": ["category", "revenue"], "rows": 50},
        )
        assert result.success is True
        assert str(result.task_id) == "550e8400-e29b-41d4-a716-446655440000"
        assert str(result.dashboard_id) == "550e8400-e29b-41d4-a716-446655440000"
        assert result.rows_processed == 1000
        assert result.message == "Data processed successfully"
        assert result.data == {"columns": ["category", "revenue"], "rows": 50}

    def test_processing_result_without_data(self):
        """Проверяет результат обработки без дополнительных данных."""
        result = ProcessingResult(
            success=True,
            task_id="550e8400-e29b-41d4-a716-446655440000",
            dashboard_id="550e8400-e29b-41d4-a716-446655440000",
            rows_processed=0,
            message="No data to process",
        )
        assert result.success is True
        assert str(result.task_id) == "550e8400-e29b-41d4-a716-446655440000"
        assert str(result.dashboard_id) == "550e8400-e29b-41d4-a716-446655440000"
        assert result.rows_processed == 0
        assert result.message == "No data to process"
        assert result.data is None

    def test_aggregated_data_valid(self):
        """Проверяет создание валидных агрегированных данных."""
        data = AggregatedData(
            dashboard_id="550e8400-e29b-41d4-a716-446655440000",
            chart_type="bar",
            data=[
                {"dims": {"category": "A"}, "metrics": {"revenue": 1000}},
                {"dims": {"category": "B"}, "metrics": {"revenue": 2000}},
            ],
            metadata={"total": 3000, "count": 2},
        )
        assert str(data.dashboard_id) == "550e8400-e29b-41d4-a716-446655440000"
        assert data.chart_type == "bar"
        assert len(data.data) == 2

    def test_aggregated_data_invalid_chart_type(self):
        """Проверяет валидацию неверного типа графика."""
        with pytest.raises(ValidationError):
            AggregatedData(
                dashboard_id=1,
                chart_type="invalid",
                data=[],
            )


class TestAuthModels:
    """Тесты для Pydantic моделей аутентификации."""

    def test_login_request_valid(self):
        """Проверяет создание валидного запроса на вход."""
        login = LoginRequest(
            email="user@example.com",
            password="secure_password123",
        )
        assert login.email == "user@example.com"
        assert login.password == "secure_password123"

    def test_login_request_invalid_email(self):
        """Проверяет валидацию неверного email в запросе на вход."""
        with pytest.raises(ValidationError):
            LoginRequest(
                email="not-an-email",
                password="secure_password123",
            )

    def test_token_valid(self):
        """Проверяет создание валидного токена."""
        token = Token(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            token_type="bearer",
        )
        assert token.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert token.token_type == "bearer"

    def test_token_data_valid(self):
        """Проверка создания валидных данных токена."""
        token_data = TokenData(
            email="user@example.com",
            user_id="550e8400-e29b-41d4-a716-446655440000",
        )
        assert token_data.email == "user@example.com"
        assert str(token_data.user_id) == "550e8400-e29b-41d4-a716-446655440000"

    def test_token_data_partial(self):
        """Проверяет создание данных токена с частичными данными."""
        token_data = TokenData(email="user@example.com")
        assert token_data.email == "user@example.com"
        assert token_data.user_id is None

    def test_access_check_valid(self):
        """Проверка создания валидной проверки доступа."""
        check = AccessCheck(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            dashboard_id="550e8400-e29b-41d4-a716-446655440001",
            required_permission="view",
        )
        assert str(check.user_id) == "550e8400-e29b-41d4-a716-446655440000"
        assert str(check.dashboard_id) == "550e8400-e29b-41d4-a716-446655440001"
        assert check.required_permission == "view"

    def test_access_check_default_permission(self):
        """Проверка значения разрешения по умолчанию."""
        check = AccessCheck(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            dashboard_id="550e8400-e29b-41d4-a716-446655440001",
        )
        assert str(check.user_id) == "550e8400-e29b-41d4-a716-446655440000"
        assert str(check.dashboard_id) == "550e8400-e29b-41d4-a716-446655440001"
        assert check.required_permission == "view"

    def test_access_grant_valid(self):
        """Проверка создания валидного предоставления доступа."""
        grant = AccessGrant(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            dashboard_id="550e8400-e29b-41d4-a716-446655440001",
            permission_level="edit",
        )
        assert str(grant.user_id) == "550e8400-e29b-41d4-a716-446655440000"
        assert str(grant.dashboard_id) == "550e8400-e29b-41d4-a716-446655440001"
        assert grant.permission_level == "edit"

    def test_access_grant_default_permission(self):
        """Проверка значения уровня доступа по умолчанию."""
        grant = AccessGrant(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            dashboard_id="550e8400-e29b-41d4-a716-446655440001",
        )
        assert str(grant.user_id) == "550e8400-e29b-41d4-a716-446655440000"
        assert str(grant.dashboard_id) == "550e8400-e29b-41d4-a716-446655440001"
        assert grant.permission_level == "view"