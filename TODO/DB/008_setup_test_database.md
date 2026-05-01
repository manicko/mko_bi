TASK: Настроить тестовую инфраструктуру (bidb_test)

FILE: conftest.py, pyproject.toml

GOAL: Создать и настроить базу данных для тестирования

IMPLEMENT:

1. Создать базу bidb_test:
   - set "PGPASSWORD=1234" & psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE bidb_test;"
2. Обновить conftest.py:
   - Использовать async engine (asyncpg) для тестов
   - Настроить применение миграций Alembic перед тестами (вместо create_all)
   - Обновить clean_db fixture для очистки всех таблиц
3. Настроить TEST_DB_URL в config.py или через переменные окружения
4. Проверить, что тесты проходят: uv run pytest

LOGIC:

Тестовая база bidb_test не существует - тесты падают
conftest.py использует синхронный engine - нужно исправить на async
clean_db очищает только 3 таблицы - нужно расширить

CONSTRAINTS:

Использовать асинхронный engine для тестов (как в основном приложении после Задачи 002)
Использовать Alembic миграции для создания схемы (а не create_all)
Очищать все таблицы в clean_db

DONE:

 База bidb_test создана
 conftest.py использует async engine
 Миграции применяются перед тестами
 clean_db очищает все таблицы
 Тесты проходят успешно
