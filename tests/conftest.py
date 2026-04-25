import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Force SQLite for tests BEFORE importing any modules that use config
os.environ["DB_DRIVER"] = "sqlite"
os.environ["DB_HOST"] = ""
os.environ["DB_PORT"] = ""
os.environ["DB_NAME"] = ""
os.environ["DB_USER"] = ""
os.environ["DB_PASSWORD"] = ""

# Remove config and session modules from sys.modules to force reload
# This ensures that the environment variables are read correctly
modules_to_delete = []
for module_name in list(sys.modules.keys()):
    if module_name.startswith("mko_bi.db.") or module_name.startswith("mko_bi.config"):
        modules_to_delete.append(module_name)

for module_name in modules_to_delete:
    del sys.modules[module_name]

# Now import the modules - they will use the environment variables we set
from mko_bi.db.base import Base
from mko_bi.db.models import access, dashboard, user
from mko_bi.db.session import (
    override_engine_for_testing,
    reset_engine,
    engine,
    SessionLocal,
)

TEST_DATABASE_URL = "sqlite:///./test_database.db"


@pytest.fixture(scope="session")
def test_engine():
    """Создаёт engine для тестовой базы данных."""
    engine = create_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False}
        if "sqlite" in TEST_DATABASE_URL
        else {},
    )
    yield engine


@pytest.fixture(autouse=True, scope="session")
def setup_test_engine(test_engine):
    """Настраивает тестовый engine перед всеми тестами."""
    import sys

    print("SETUP_TEST_ENGINE: Starting", file=sys.stderr)
    # Переопределяем engine для тестов
    override_engine_for_testing(test_engine)
    print("SETUP_TEST_ENGINE: Engine overridden", file=sys.stderr)
    # Создаем таблицы
    Base.metadata.create_all(bind=test_engine)
    print("SETUP_TEST_ENGINE: Tables created", file=sys.stderr)
    yield
    # Очищаем таблицы после всех тестов
    Base.metadata.drop_all(bind=test_engine)
    print("SETUP_TEST_ENGINE: Tables dropped", file=sys.stderr)
    # Сбрасываем engine
    reset_engine()
    print("SETUP_TEST_ENGINE: Engine reset", file=sys.stderr)


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Очищает таблицы перед каждым тестом."""
    # Ничего не делаем, так как таблицы уже созданы
    # Таблицы создаются в setup_test_engine и очищаются в нем же
    yield


@pytest.fixture(scope="function")
def test_db():
    """Создаёт новую сессию для каждого теста.

    Yields:
        Session: Сессия SQLAlchemy для тестирования.
    """
    import sys

    print("TEST_DB: Starting", file=sys.stderr)
    from mko_bi.db.session import SessionLocal, engine

    print(f"TEST_DB: SessionLocal bind: {SessionLocal.kw['bind']}", file=sys.stderr)
    print(f"TEST_DB: engine: {engine}", file=sys.stderr)

    db = SessionLocal()
    print(f"TEST_DB: Created session: {db}", file=sys.stderr)

    yield db

    db.close()
    print("TEST_DB: Session closed", file=sys.stderr)


@pytest.fixture(scope="function")
def test_user(test_db):
    """Создаёт тестового пользователя."""
    user_obj = user.User(
        email="test@example.com",
        password_hash="hashed_password",
        role="viewer",
    )
    test_db.add(user_obj)
    test_db.commit()
    test_db.refresh(user_obj)
    return user_obj


@pytest.fixture(scope="function")
def test_dashboard(test_db):
    """Создаёт тестовый дашборд."""
    dashboard_obj = dashboard.Dashboard(
        name="Test Dashboard",
        config='{"graph_types": ["bar"], "charts": []}',
    )
    test_db.add(dashboard_obj)
    test_db.commit()
    test_db.refresh(dashboard_obj)
    return dashboard_obj


@pytest.fixture(scope="function")
def test_access(test_db, test_user, test_dashboard):
    """Создаёт тестовое право доступа."""
    access_obj = access.Access(
        user_id=test_user.id,
        dashboard_id=test_dashboard.id,
        permission_level="read",
    )
    test_db.add(access_obj)
    test_db.commit()
    test_db.refresh(access_obj)
    return access_obj
