# Отчет по аудиту тестов: Соответствие архитектуре и реализации

**Дата:** 2026-05-01
**Объект:** Тестовое покрытие `C:\py_exp\mko_bi\tests\`

## 1. Общая статистика
- **Всего проанализировано тестов:** 14 файлов (conftest + test files)
- **Найдено архитектурно-некорректных тестов:** 6 файлов (критические нарушения)
- **Нарушений с меткой `ARCHITECTURE_CONFLICT`:** 4 (использование Integer ID вместо UUID, синхронная БД)

## 2. Таблица нарушений (Architectural Test Mismatch)

| Test File | Problem | Conflicts With | Recommended Action | Priority |
|-----------|---------|----------------|--------------------|----------|
| `tests/conftest.py` | Используется SQLite (`:memory:`) и синхронный `sqlalchemy.orm.Session` | SPEC.md (PostgreSQL), Архитектура UUID | Переписать фикстуры на `pytest-asyncio` + `testcontainers` (Postgres) или асинхронный движок | Critical |
| `tests/test_dashboards_api.py` | `mock_user.id = 1` (Integer) | `src/mko_bi/db/models/user.py` (UUID) | Использовать `uuid.uuid4()` для идентификаторов | High |
| `tests/test_upload_api.py` | `dashboard_id=1` (Integer), `mock_user.id = 1` | `src/mko_bi/db/models/dashboard.py` (UUID) | Заменить int на UUID | High |
| `tests/test_data_api.py` | `mock_user.id = 1`, `dashboard_id=int(dashboard_id)` | UUID architecture | Использовать UUID, убрать приведение типов | High |
| `tests/services/test_user_service.py` | Вызовы `get_user_by_id(1, ...)`, `_validate_user_exists(1, ...)` | UUID architecture | Заменить Integer ID на UUID | High |
| `tests/services/test_dashboard_service.py` | Вызовы `_validate_dashboard_exists(1, ...)`, `grant_access(999, 1, ...)` | UUID architecture | Заменить Integer ID на UUID | High |
| `tests/test_dashboards_api.py` | Прямые вызовы функций роутов (`create_dashboard_endpoint(...)`) | SPEC.md (API layer: `httpx.AsyncClient`) | Переписать на интеграционные тесты с `httpx.AsyncClient` | Medium |

## 3. Детализированный список нарушений

### 3.1. UUID vs Integer (Критическое расхождение)
Вся production-модели (`users`, `dashboards`, `graphs`) используют `PG_UUID(as_uuid=True)` как первичные ключи. Тесты же повсеместно используют `int` (1, 2, 999).

- **`tests/test_dashboards_api.py`**:
  - Строка 32: `mock_user.id = 1`
  - Строка 50: `assert call_kwargs["owner_id"] == 1`
  - Все вызовы сервисов передают `user_id=1`.
  - **Метка:** `REWRITE_REQUIRED`

- **`tests/test_upload_api.py`**:
  - Строка 34: `mock_user.id = 1`
  - Строка 43: `dashboard_id=1` (в `UploadResponse` и вызовах)
  - **Метка:** `REWRITE_REQUIRED`

- **`tests/test_data_api.py`**:
  - Строка 28: `mock_user.id = 1`
  - Строка 32: `mock_aggregate.dashboard_id = int(dashboard_id)` (явное приведение UUID к int — грубая ошибка).
  - **Метка:** `REWRITE_REQUIRED`

- **`tests/services/test_user_service.py`**:
  - Строка 64: `_validate_user_exists(1, db_session)`
  - Строка 71: `_validate_user_exists(999, db_session)`
  - Строка 244: `get_user_by_id(1, db_session)`
  - **Метка:** `MIGRATION_REQUIRED`

- **`tests/services/test_dashboard_service.py`**:
  - Строка 88: `_validate_dashboard_exists(1, db_session)`
  - Строка 106: `_check_owner_permission(1, 2, db_session)`
  - **Метка:** `MIGRATION_REQUIRED`

### 3.2. Sync/Async & Database conflicts
- **`tests/conftest.py`**:
  - Строки 29-34: Использование `sqlalchemy.create_engine` (sync) с SQLite. 
  - Строки 46-60: Фикстура `db_session` возвращает синхронный `Session`.
  - **Проблема:** SQLite не поддерживает тип `UUID` так же, как PostgreSQL. Синхронные сессии блокируют event loop, если прод-код асинхронный.
  - **Метка:** `ARCHITECTURE_CONFLICT`

### 3.3. API Layer Testing
- **`tests/test_dashboards_api.py`**, **`tests/test_upload_api.py`**, **`tests/test_data_api.py`**:
  - Тесты вызывают handler-функции напрямую (`await create_dashboard_endpoint(...)`), минуя HTTP.
  - **Конфликт:** Эндпоинты FastAPI должны тестироваться через `httpx.AsyncClient` для проверки middleware, зависимостей (Depends) и сериализации JSON.
  - **Метка:** `MIGRATION_REQUIRED`

## 4. Особо отмеченные случаи (Legacy Locking Tests)

1. **`tests/test_data_api.py:32`** — `mock_aggregate.dashboard_id = int(dashboard_id)`.
   - **Блокировка:** Заставляет думать, что ID может быть integer, или требует костылей в коде моделей для поддержки int.
   - **Решение:** Удалить приведение типа, использовать UUID.

## 5. План исправлений

### Rewrite Required (Переписать полностью)
- `tests/conftest.py`: Настроить асинхронную тестовую БД (PostgreSQL через Docker или asyncpg).
- `tests/test_dashboards_api.py`: Обновить моки пользователей до UUID.

### Migration Required (Миграция типов данных)
- Во всех файлах `tests/services/` и `tests/test_*.py` заменить `user_id = 1` на `user_id = uuid.uuid4()`.
- Заменить `dashboard_id = 1` на сгенерированные UUID.

### Delete Required (Удалить)
- Удалить устаревшие приведения типов (например, `int(dashboard_id)`).

## 6. Рекомендации по автоматизации
1. Добавить в `pyproject.toml` (ruff/flake8):
   - Запрет на использование `id = 1` или `id = 2` в тестовых файлах.
   - Проверка на наличие `sqlite` в импортах тестов.
2. CI: Шаг проверки, что все тесты с асинхронными вызовами помечены `@pytest.mark.asyncio`.

## 7. Критерии приёмки (выполнение)
- [x] Указаны конкретные файлы и строки (см. раздел 3).
- [x] Нарушения обоснованы ссылками на `db/models/*.py`.
- [x] Нет предложений менять прод-код под тесты.
- [x] Приведены примеры `ARCHITECTURE_CONFLICT` (SQLite + Integer ID).
- [x] Оценка приоритетов выполнена.
