---
## BLOCK 1: DATABASE & MODELS
---

### TASK: Enum definitions (StrEnum)

FILE: `src/mko_bi/models/enums.py`

GOAL: Определить все перечисления через StrEnum согласно SPEC.md п.22

IMPLEMENT:

* `UserRole(StrEnum)`: ADMIN, EDITOR, VIEWER
* `DashboardPermission(StrEnum)`: VIEW, EDIT, ADMIN
* `GraphType(StrEnum)`: BAR, LINE, PIE, TABLE
* `FilterType(StrEnum)`: SELECT, MULTISELECT, RANGE, DATE
* `RegistrationStatus(StrEnum)`: PENDING, APPROVED, REJECTED
* `UploadMode(StrEnum)`: OVERWRITE, APPEND
* `ProcessingStatus(StrEnum)`: STARTED, UPLOADED, PROCESSING, SUCCESS, FAILED, COMPLETED
* `EnvironmentEnum(StrEnum)`: PRODUCTION, STAGING, DEVELOPMENT, TEST
* `MimeTypeEnum(StrEnum)`: TEXT_CSV, APPLICATION_GZIP, APPLICATION_X_GZIP
* `FileExtensionEnum(StrEnum)`: CSV, CSV_GZ

LOGIC:

1. Импорт `from enum import StrEnum`
2. Каждый enum наследуется от StrEnum
3. Значения строго соответствуют SPEC.md
4. Добавить `allowed_values()` методы где требуется

DONE:

* [ ] Все enums определены
* [ ] Экспортированы из `__init__.py`
* [ ] Тест на корректные значения

---

### TASK: SQLAlchemy base models

FILE: `src/mko_bi/db/models/*.py`

GOAL: Создать SQLAlchemy async models согласно SPEC.md п.16

IMPLEMENT:

* `user.py`: User model (id UUID, email, password_hash, role, is_active, created_at)
* `layout.py`: Layout model (id UUID, name, definition JSONB, created_at)
* `dashboard.py`: Dashboard model (id UUID, name, description, layout_id FK, created_by FK, created_at, updated_at)
* `graph.py`: Graph model (id UUID, dashboard_id FK, name, type, config JSONB, dimensions JSONB, metrics JSONB, created_at)
* `filter.py`: Filter model (id UUID, name, type, config JSONB, created_at)
* `access.py`: DashboardAccess model (user_id FK, dashboard_id FK, permission, PK(user_id, dashboard_id))
* `dashboard_filter.py`: DashboardFilter model (dashboard_id FK, filter_id FK, PK(dashboard_id, filter_id))
* `processing_config.py`: ProcessingConfig model (dashboard_id PK FK, settings JSONB, updated_at)
* `aggregated_data.py`: AggregatedData model (id BIGSERIAL, dashboard_id FK, graph_id FK, dims JSONB, metrics JSONB)
* `processing_log.py`: ProcessingLog model (id UUID, dashboard_id FK, status, message, started_at, finished_at)
* `registration_request.py`: RegistrationRequest model (id UUID, email, status, requested_by_ip, reviewed_by, reviewed_at, created_at)

LOGIC:

1. Все модели наследуются от `Base` (src/mko_bi/db/base.py)
2. Использовать `UUID` с `uuid_generate_v4()` как default
3. JSONB для гибких полей (definition, config, dims, metrics, settings)
4. ForeignKey с `ondelete="CASCADE"` где применимо
5. Check constraints для enum полей
6. Индексы согласно SPEC.md п.16.2

DONE:

* [ ] Все models созданы
* [ ] Связи (relationships) настроены
* [ ] Индексы добавлены
* [ ] Alembic migration сгенерирована

---

### TASK: Pydantic API models

FILE: `src/mko_bi/models/*.py`

GOAL: Создать Pydantic models для валидации API запросов/ответов

IMPLEMENT:

* `user.py`: UserCreate, UserResponse, UserUpdate, UserProfile
* `auth.py`: LoginRequest, AuthResponse, RegisterRequestCreate, RegisterRequestResponse
* `dashboard.py`: DashboardCreate, DashboardUpdate, DashboardResponse, DashboardSummary
* `graph.py`: GraphCreate, GraphUpdate, GraphResponse
* `filter.py`: FilterCreate, FilterUpdate, FilterResponse
* `layout.py`: LayoutCreate, LayoutUpdate, LayoutResponse
* `processing_configs.py`: ProcessingConfigCreate, ProcessingConfigUpdate, ProcessingConfigResponse
* `processing_logs.py`: ProcessingLogResponse, ProcessingLogFilter
* `data.py`: AggregatedDataResponse, DataRequest
* `access.py`: AccessGrant, AccessRevoke

LOGIC:

1. Наследование от `BaseModel` (pydantic)
2. Использовать `EmailStr` для email полей
3. Использовать StrEnum для типизированных полей
4. `ConfigDict(from_attributes=True)` для ORM compatibility
5. Валидаторы где необходимо

DONE:

* [ ] Все Pydantic models созданы
* [ ] Экспортированы из `src/mko_bi/models/__init__.py`
* [ ] Тесты на валидацию

---

### TASK: Alembic migrations

FILE: `alembic/versions/*.py`

GOAL: Создать миграции для всех таблиц согласно SPEC.md п.16

IMPLEMENT:

* Initial migration (все таблицы)
* Индексы (GIN для JSONB, обычные для FK)
* Check constraints для enum полей
* UUID generation defaults

LOGIC:

1. `alembic revision --autogenerate -m "initial_schema"`
2. Проверить и применить миграции
3. Добавить composite indexes согласно SPEC.md п.16.2

DONE:

* [ ] Миграции применяются без ошибок
* [ ] `uv run alembic upgrade head` успешно
* [ ] Проверка структуры БД через `\dt` в psql

---
