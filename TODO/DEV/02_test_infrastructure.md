---
## TEST INFRASTRUCTURE SETUP
---

### TASK: Создание тестовой базы данных

FILE: `tests/conftest.py`, `pyproject.toml`

GOAL: Настроить тестовую среду для запуска pytest

FINDINGS (TASK_03):
- Тестовая БД `bidb_test` не существует (conftest.py строка 18)
- pytest падает с INTERNALERROR из-за проблем с логированием

IMPLEMENT:

* Создать БД `bidb_test` в PostgreSQL
* Настроить `test_database_url` в конфигурации
* Применить миграции Alembic к тестовой БД
* Исправить настройку логирования в conftest.py

SQL:
```sql
CREATE DATABASE bidb_test;
```

DONE:

* [ ] БД `bidb_test` создана
* [ ] Миграции применены к тестовой БД
* [ ] `uv run pytest tests/` выполняется без INTERNALERROR
* [ ] Базовые тесты проходят

---

### TASK: Исправление конфигурации тестов

FILE: `tests/conftest.py`

GOAL: Настроить корректную инициализацию тестовой среды

IMPLEMENT:

* Проверить настройки логирования (избегать конфликтов с pytest)
* Настроить fixtures для сессии БД
* Добавить fixture для создания тестового пользователя
* Настроить очистку после тестов

DONE:

* [ ] conftest.py не вызывает ошибок при запуске
* [ ] Fixtures работают корректно
* [ ] Тесты могут использовать тестовую БД

---
