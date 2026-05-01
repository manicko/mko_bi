TASK: настроить асинхронную тестовую БД PostgreSQL в conftest.py

FILE: tests/conftest.py

GOAL: заменить синхронный SQLite на асинхронный PostgreSQL через testcontainers

IMPLEMENT:

func: async_db_session()
func: async_client()
func: test_db_engine()

LOGIC:

убалить sqlalchemy.create_engine (sync) и SQLite :memory:
добавить testcontainers[postgres] для запуска PostgreSQL в Docker
настроить асинхронный движок через sqlalchemy.ext.asyncio.AsyncEngine
использовать asyncpg в качестве драйвера
создать фикстуру async_db_session с async session maker
создать фикстуру async_client для httpx.AsyncClient
все фикстуры пометить @pytest.fixture и @pytest.mark.asyncio

CONSTRAINTS:

использовать PostgreSQL (не SQLite)
использовать асинхронные сессии (AsyncSession)
testcontainers должен поднимать БД автоматически
фикстура БД должна создавать таблицы через metadata.create_all

DONE:

conftest.py использует PostgreSQL через testcontainers
все фикстуры асинхронные
тесты запускаются: uv run pytest tests/conftest.py
