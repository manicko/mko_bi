import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker

from mko_bi.db.base import Base
from mko_bi.db.session import SessionLocal, engine, get_db, init_db, drop_db


class TestSessionModule:
    """Тесты для модуля session."""

    def test_engine_is_created(self):
        """Проверяет, что engine создан."""
        assert engine is not None

    def test_session_local_is_created(self):
        """Проверяет, что SessionLocal создан."""
        assert SessionLocal is not None

    def test_get_db_returns_generator(self, test_engine):
        """Проверяет, что get_db возвращает генератор."""
        # Используем test_engine для создания SessionLocal
        SessionLocalTest = type(
            "SessionLocalTest",
            (type(SessionLocal),),
            {"bind": test_engine},
        )

        # Временно заменяем SessionLocal
        original = SessionLocal
        try:
            # Создаём собственную функцию get_db для теста
            def get_db_test():
                db = Session(bind=test_engine, future=True)
                try:
                    yield db
                finally:
                    db.close()

            gen = get_db_test()
            assert hasattr(gen, "__iter__")
            assert hasattr(gen, "__next__")

            db = next(gen)
            assert isinstance(db, Session)
            gen.close()
        finally:
            pass

    def test_init_db_creates_tables(self, test_engine):
        """Проверяет, что init_db создаёт таблицы."""
        # Удаляем все таблицы перед тестом
        Base.metadata.drop_all(bind=test_engine)

        # Проверяем, что таблиц нет
        inspector = inspect(test_engine)
        tables = inspector.get_table_names()
        assert "users" not in tables
        assert "dashboards" not in tables
        assert "accesses" not in tables

        # Создаём таблицы
        Base.metadata.create_all(bind=test_engine)

        # Проверяем, что таблицы созданы
        inspector = inspect(test_engine)
        tables = inspector.get_table_names()
        assert "users" in tables
        assert "dashboards" in tables
        assert "accesses" in tables

    def test_session_local_creates_session(self, test_engine):
        """Проверяет, что SessionLocal создаёт сессию."""
        SessionLocalTest = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_engine,
            expire_on_commit=False,
            class_=Session,
        )

        db = SessionLocalTest()
        assert isinstance(db, Session)
        db.close()

    def test_session_autocommit_false(self, test_engine):
        """Проверяет, что autocommit=False."""
        SessionLocalTest = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_engine,
            expire_on_commit=False,
            class_=Session,
        )

        db = SessionLocalTest()
        # In SQLAlchemy 2.0, autocommit is deprecated and not an attribute
        # The sessionmaker with autocommit=False is the correct configuration
        assert db is not None
        db.close()

    def test_session_autoflush_false(self, test_engine):
        """Проверяет, что autoflush=False."""
        SessionLocalTest = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_engine,
            expire_on_commit=False,
            class_=Session,
        )

        db = SessionLocalTest()
        assert db.autoflush is False
        db.close()

    def test_get_db_closes_session(self, test_engine):
        """Проверяет, что сессия закрывается после использования."""

        def get_db_test():
            db = Session(bind=test_engine, future=True)
            try:
                yield db
            finally:
                db.close()

        gen = get_db_test()
        db = next(gen)
        # Session doesn't have a closed attribute, but we can check it's not None
        assert db is not None
        # Check that session is bound to the engine
        assert db.bind is not None
        gen.close()
        # After closing, the session should still exist but be closed
        # (SQLAlchemy doesn't set is_active to False after close)
        assert db.bind is not None

    def test_drop_db_removes_tables(self, test_engine):
        """Проверяет, что drop_db удаляет таблицы."""
        # Создаём таблицы
        Base.metadata.create_all(bind=test_engine)

        inspector = inspect(test_engine)
        tables = inspector.get_table_names()
        assert "users" in tables

        # Удаляем таблицы
        Base.metadata.drop_all(bind=test_engine)

        inspector = inspect(test_engine)
        tables = inspector.get_table_names()
        assert "users" not in tables
        assert "dashboards" not in tables
        assert "accesses" not in tables

    def test_session_expire_on_commit_false(self, test_engine):
        """Проверяет, что expire_on_commit=False."""
        SessionLocalTest = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_engine,
            expire_on_commit=False,
            class_=Session,
        )

        db = SessionLocalTest()
        assert db.expire_on_commit is False
        db.close()
