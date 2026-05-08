# BI Dashboard System Full Audit Task

## Цель

Провести полный comprehensive audit BI Dashboard System (`mkobi`) на соответствие спецификациям SPEC.md и SPEC_FRONTEND.md.

Фокус аудита:

* **Backend (FastAPI)**: архитектура, безопасность, корректность обработки данных, типизация
* **Frontend (React SPA)**: архитектура FSD, type safety, интеграция с API, UI компоненты
* **Data Layer**: PostgreSQL schema, миграции, JSONB usage, индексы
* **DevOps**: Docker, deployment readiness, конфигурация

Критерии качества:

* Clean Architecture (разделение слоев)
* Separation of Concerns (предметные области)
* Строгая модульность
* Отсутствие overengineering
* Полная типизация (Python type hints + Pydantic, TypeScript)
* Соблюдение стандартов кода (PEP 8, ruff, mypy)
* Корректное логирование (logging, НЕ print)
* Использование StrEnum вместо dict/list
* Пакет `mkobi` (с 1 underscore)

ИЗБЕГАТЬ:

* enterprise overengineering
* unnecessary abstractions
* сложных паттернов без необходимости

---

# Правила аудита

## Основные принципы

При проверке:

1. Сначала проверять соответствие ТЗ (SPEC.md + SPEC_FRONTEND.md)
2. Затем корректность реализации
3. Затем качество кода

Не считать проблемой:

* Простую архитектуру, если она:
  * последовательна
  * читаема
  * тестируема
  * расширяема

Критичными считать:

* Нарушения безопасности
* Нарушения access control
* Потерю данных
* Смешивание ответственности
* Нестабильную обработку данных
* Async/blocking issues
* Hardcoded behavior
* Отсутствие validation
* Использование print() вместо logging
* Отсутствие StrEnum там, где используются dict/list для констант

---

# BLOCK 1 — Project Structure & Architecture

## 1.1 Backend Structure (src/mkobi/)

Проверить соблюдение Clean Architecture:

### Слои приложения

* **API Layer** (`src/mkobi/api/routes/`): только HTTP, валидация входных данных, вызов сервисов
* **Service Layer** (`src/mkobi/services/`): бизнес-логика, оркестрация
* **Repository Layer** (`src/mkobi/db/repositories/`): доступ к данным, SQL queries
* **Model Layer** (`src/mkobi/models/`): Pydantic модели для API, `src/mkobi/db/models/` для ORM
* **Interfaces** (`src/mkobi/interfaces/`): абстракции для DI
* **Core** (`src/mkobi/core/`): инфраструктурный код (security, permissions, logging)
* **Data Processing** (`src/mkobi/data/`): loaders, processing, storage
* **Config** (`src/mkobi/config.py`, `src/mkobi/settings/`): централизованная конфигурация

### Проверить отсутствие

* Business logic inside routes
* SQL inside controllers/routes
* Global mutable state
* Cyclic imports
* Hidden side effects
* Смешивания ответственности между слоями

### Проверить наличие

* Dependency Injection (через `src/mkobi/api/deps.py`)
* Config centralization (pydantic-settings, env vars, Docker secrets)
* Logging centralization (`src/mkobi/core/logging_config.py`)
* Enum usage (StrEnum в `src/mkobi/models/enums.py`)

## 1.2 Frontend Structure (frontend/src/)

Проверить соответствие Feature-Sliced Design (FSD):

### Структура

```
frontend/src/
├── app/                    # Инициализация, провайдеры
│   ├── providers.tsx       # QueryClient, Router, Theme
│   └── routes.tsx          # Все роуты
├── features/               # Фичи (основные бизнес-возможности)
│   ├── auth/
│   ├── dashboards/
│   ├── upload/
│   ├── users/
│   └── admin/
├── shared/                 # Переиспользуемый код
│   ├── api/               # axiosInstance, errorHandling
│   ├── components/         # ProtectedRoute, Layout, RoleBasedAccess
│   ├── config/            # constants
│   └── types/             # api.types.ts
└── main.tsx
```

### Проверить для каждой feature

* **ui/**: React компоненты (только UI логика)
* **api/**: API вызовы (axios, TanStack Query)
* **model/**: состояние, хуки (useAuth, useDashboards)
* **types/**: TypeScript типы

### Проверить отсутствие

* Бизнес-логики в компонентах
* Дублирования API вызовов
* Хардкода URL (использовать axiosInstance)
* Смешивания ответственности

## 1.3 Processing Pipeline

Проверить `src/mkobi/data/processing/`:

Pipeline должен быть:

* Явным (читаемые этапы)
* Разбитым по шагам: upload → parse → transform → aggregate → save
* Использовать Polars (НЕ pandas)
* Иметь корректную обработку ошибок
* Очищать временные файлы (platformdirs)

Проверить файлы:

* `loaders/loader.py`: загрузка и валидация CSV/CSV.gz
* `processing/transformations.py`: трансформации, агрегации
* `processing/registry.py`: реестр обработчиков
* `storage/manager.py`: сохранение в PostgreSQL (JSONB)

---

# BLOCK 2 — Backend API Layer (FastAPI)

## 2.1 Auth Endpoints

Проверить `src/mkobi/api/routes/auth.py`:

### Функционал

* `POST /api/v1/auth/login` → `{access_token, user}`
* `POST /api/v1/auth/register-request` → `{message}`
* `GET /api/v1/auth/me` → `UserProfile`

### Проверить

* JWT generation (correct algorithm, expiration)
* JWT validation (dependencies в deps.py)
* Password hashing (bcrypt, НЕ plaintext)
* Email validation (pydantic EmailStr или regex)
* Rate limiting на login endpoint
* Нет print(), только logger

## 2.2 Dashboard Endpoints

Проверить `src/mkobi/api/routes/dashboards.py`:

### Функционал

* `GET /api/v1/dashboards/my` → `DashboardSummary[]`
* `GET /api/v1/dashboards/:id` → `DashboardDetail`
* `POST /api/v1/dashboards` (admin only)
* `PUT /api/v1/dashboards/:id` (admin only)
* `DELETE /api/v1/dashboards/:id` (admin only)

### Проверить

* Access validation (user ↔ dashboard via dashboard_access)
* Role-based permissions (admin/editor/viewer)
* Correct Pydantic models (src/mkobi/models/dashboard.py)
* Layout связь (layout_id → layouts table)
* Ошибки возвращаются через HTTPException (НЕ print)

## 2.3 Data Endpoints

Проверить `src/mkobi/api/routes/data.py` и `src/mkobi/api/routes/upload.py`:

### Функционал

* `GET /api/v1/data/aggregated?dashboard_id=:id&filters=...` → графики данные
* `POST /api/v1/upload/:dashboard_id?mode=overwrite|append` (multipart file)

### Проверить upload

* File type validation (MIME-type: `text/csv`, `application/gzip`)
* UTF-8 validation
* Max file size limit
* Temp file cleanup (platformdirs, finally block)
* CSV.gz handling (gzip decompression)
* Path traversal protection
* Unsafe filenames handling
* Rate limiting

### Проверить data API

* Filters применяются на backend (SQL/Polars)
* JSONB dims фильтрация (GIN index usage)
* Dashboard access validation
* Pagination/limits if needed

## 2.4 Admin Endpoints

Проверить `src/mkobi/api/routes/admin.py`:

### Функционал

* `GET /api/v1/admin/users` → `User[]`
* `PATCH /api/v1/admin/users/:id/role`
* `GET /api/v1/admin/registration-requests` → `Request[]`
* `POST /api/v1/admin/registration-requests/:id/approve`
* `GET /api/v1/admin/logs` → `ProcessingLog[]`

### Проверить

* Только admin может выполнять
* Корректная работа с registration_requests
* Логи возвращаются корректно
* Нет утечки чувствительных данных (password_hash)

## 2.5 Other Endpoints

Проверить:

* `src/mkobi/api/routes/users.py`: user CRUD, profile
* `src/mkobi/api/routes/filters.py`: filters management
* `src/mkobi/api/routes/graphs.py`: graph definitions
* `src/mkobi/api/routes/layouts.py`: layout management
* `src/mkobi/api/routes/processing_configs.py`: processing settings
* `src/mkobi/api/routes/processing_logs.py`: processing logs

---

# BLOCK 3 — Access Control & Security

## 3.1 Access Control

Проверить `src/mkobi/core/permissions.py`:

### Dashboard Access

* Проверка dashboard_access на каждом запросе к дашборду
* Editor/viewer/admin restrictions
* Direct object access vulnerabilities (user может получить чужой дашборд?)
* Admin имеет полный доступ

### User Roles

Проверить использование `UserRole` StrEnum:

* ADMIN = "admin"
* EDITOR = "editor"
* VIEWER = "viewer"

Все проверки ролей должны использовать StrEnum, НЕ строки.

## 3.2 JWT Security

Проверить `src/mkobi/core/security.py`:

* Token expiration validation
* Invalid token handling (401 Unauthorized)
* Missing token handling (401 Unauthorized)
* Secret key хранится в env (JWT__SECRET_KEY)
* Algorithm указан явно (НЕ default)

## 3.3 Password Security

Проверить:

* bcrypt usage (НЕ md5, SHA, plaintext)
* Password hash хранится в БД (НЕ plaintext)
* Нет password logging
* Password strength validation (опционально)

## 3.4 Upload Security

Проверить `src/mkobi/api/routes/upload.py`:

* Path traversal (../../file.csv)
* Unsafe filenames (использовать secure filename)
* Oversized files handling (limit через config)
* MIME-type validation (client + server side)
* Rate limiting (защита от spam upload)

## 3.5 SQL Safety

Проверить repositories (`src/mkobi/db/repositories/`):

* Отсутствие raw unsafe SQL
* Parameterized queries (SQLAlchemy ORM/Core)
* Запрещено формирование SQL через string interpolation (f-strings, +)
* Использование ORM для всех операций

## 3.6 Secrets & Config

Проверить `src/mkobi/config.py`:

* Отсутствие hardcoded secrets
* Env-based configuration (pydantic-settings)
* Docker secrets support (_FILE suffix)
* Nested env vars (DATABASE__HOST, DATABASE__PORT)
* `.env` файл только для development

---

# BLOCK 4 — Data Processing (Polars)

## 4.1 Data Loaders

Проверить `src/mkobi/data/loaders/loader.py`:

* Используется Polars (import polars as pl)
* НЕ используется pandas (import pandas as pd)
* Чтение CSV (read_csv)
* Чтение CSV.gz (read_csv с decompression)
* Валидация схемы (validator.py)
* Обработка ошибок (corrupted CSV, invalid schema, missing columns, empty files)

## 4.2 Transformations

Проверить `src/mkobi/data/processing/transformations.py`:

### Aggregations

Проверить наличие:

* Groupby (Polars group_by)
* YoY (year-over-year calculations)
* Shares (доли)
* Custom metrics (настраиваемые метрики)

### Pipeline Correctness

* Parsing (CSV → Polars DataFrame)
* Transformations (по конфигу dashboard)
* Aggregations (группировки, метрики)
* Full recalculation logic (перезапись данных)

## 4.3 Storage

Проверить `src/mkobi/data/storage/manager.py`:

* Save to PostgreSQL (aggregated_data table)
* JSONB usage для dims и metrics
* Корректная сериализация
* DB transaction handling (atomic processing, rollback on failure)

## 4.4 Resource Handling

Проверить:

* Temp files cleanup (platformdirs, удаление после обработки)
* DB transaction handling (commit/rollback)
* Memory-heavy operations (streaming для больших файлов?)
* Ошибки обрабатываются и логируются

---

# BLOCK 5 — PostgreSQL Layer

## 5.1 Schema Compliance

Проверить соответствие SPEC.md (раздел 16):

### Core Tables

* `users`: id, email, password_hash, role (UserRole StrEnum), is_active, created_at, updated_at
* `layouts`: id, name, definition (JSONB), created_at, updated_at
* `dashboards`: id, name, description, layout_id, created_by, created_at, updated_at
* `graphs`: id, dashboard_id, name, type (GraphType StrEnum), config, dimensions, metrics, created_at
* `filters`: id, name, type (FilterType StrEnum), config, created_at
* `dashboard_access`: user_id, dashboard_id, permission (DashboardPermission StrEnum)
* `dashboard_filters`: dashboard_id, filter_id (many-to-many)
* `processing_configs`: dashboard_id, settings (JSONB), updated_at
* `aggregated_data`: id, dashboard_id, graph_id, dims (JSONB), metrics (JSONB)
* `processing_logs`: id, dashboard_id, status (ProcessingStatus StrEnum), message, timestamps
* `registration_requests`: id, email, status (RegistrationStatus StrEnum), ip, reviewed_by, timestamps

### Проверить

* Foreign keys присутствуют
* CASCADE behavior корректен
* CHECK constraints для enums (используют StrEnum значения)
* UNIQUE constraints где нужно

## 5.2 Indexes

Проверить наличие индексов (SPEC.md раздел 16.2):

```sql
CREATE INDEX idx_aggregated_data_graph_id ON aggregated_data(graph_id);
CREATE INDEX idx_aggregated_data_dashboard_id ON aggregated_data(dashboard_id);
CREATE INDEX idx_aggregated_data_dashboard_graph ON aggregated_data(dashboard_id, graph_id);
CREATE INDEX idx_aggregated_data_dims_gin ON aggregated_data USING GIN (dims);
CREATE INDEX idx_dashboard_access_user ON dashboard_access(user_id);
CREATE INDEX idx_dashboard_access_dashboard ON dashboard_access(dashboard_id);
CREATE INDEX idx_graphs_dashboard ON graphs(dashboard_id);
CREATE INDEX idx_dashboard_filters_dashboard_filter ON dashboard_filters(dashboard_id, filter_id);
```

## 5.3 Aggregated Data Model

Проверить `src/mkobi/db/models/aggregated_data.py`:

* Корректность JSONB usage (dims, metrics)
* Фильтрация через dims (GIN index)
* Metrics consistency
* 1 строка = 1 точка графика

## 5.4 Queries (Repositories)

Проверить `src/mkobi/db/repositories/`:

* Отсутствие N+1 проблем
* Корректность joins (если используются)
* Index usage (GIN для JSONB)
* Prepared statements (SQLAlchemy)

## 5.5 Migrations (Alembic)

Проверить `alembic/versions/`:

* Все миграции применяются корректно
* Downgrade не нарушает данные (или запрещен)
* Имена миграций описательные
* Порядок миграций корректен

---

# BLOCK 6 — Frontend (React SPA)

## 6.1 Architecture (FSD)

Проверить соответствие Feature-Sliced Design:

### App Layer

* `app/providers.tsx`: QueryClient, Router, Theme провайдеры
* `app/routes.tsx`: все роуты приложения

### Features Layer

Для каждой feature проверить:

* **auth**: LoginForm, RegisterForm, useAuth, authApi, authToken
* **dashboards**: DashboardList, DashboardView, DashboardFilters, useDashboards, dashboardApi
* **upload**: FileDropzone, UploadPage, uploadApi
* **users**: UserProfile, userApi
* **admin**: AdminPanel, UserManagement, LogViewer, RegistrationRequests, DashboardManagement, adminApi

### Shared Layer

* **api**: axiosInstance с интерцепторами для JWT
* **components**: ProtectedRoute, RoleBasedAccess, Layout (AppLayout, Header, Sidebar)
* **types**: api.types.ts (общие типы User, Dashboard, etc.), enums.ts (TypeScript enums)

## 6.2 Type Safety

Проверить:

* TypeScript используется (НЕ any)
* Типы для API responses (AuthResponse, DashboardSummary, etc.)
* Типы для компонентов (props interfaces)
* Zod schemas для форм (React Hook Form)
* Отсутствие type errors (tsc --noEmit)

## 6.3 API Integration

Проверить `frontend/src/features/*/api/`:

* Используется axiosInstance (НЕ прямой axios)
* JWT добавляется через интерцептор
* Error handling (react-hot-toast)
* TanStack Query для серверного состояния
* Polling для long operations (processing status)

## 6.4 UI Components

Проверить рендеринг:

### Login Page (`/login`)

* Поля: email, password
* Валидация формата email
* Кнопка "Войти"
* Ссылка "Зарегистрироваться"
* Сообщение об ошибке

### Registration Page (`/register`)

* Поле email (Zod validation)
* Кнопка "Отправить заявку"
* Проверка по blacklist доменов

### Dashboard List Page (`/dashboards`)

* Список доступных дашбордов
* Карточки: название, описание, ссылка
* GET `/api/v1/dashboards/my`

### Dashboard View Page (`/dashboard/:id`)

* Заголовок дашборда
* Filters Panel (динамически по конфигу)
* Charts Grid (Plotly.js React)
* Upload Button (для editor+)
* GET `/api/v1/data/aggregated?dashboard_id=:id&filters=...`

### Data Upload Page (`/dashboard/:id/upload`)

* Mode Toggle: "Перезаписать" / "Добавить"
* Dropzone (react-dropzone)
* Progress Bar
* POST `/api/v1/upload/:dashboard_id?mode=overwrite|append`

### Admin Panel (`/admin`)

* User Management (таблица, изменение ролей)
* Registration Requests (одобрение/отклонение)
* Dashboard Management (CRUD)
* Log Viewer (просмотр логов)

### User Profile Page (`/profile`)

* Email (read-only), роль (read-only)
* Кнопка "Удалить аккаунт" (только для НЕ-админов)

## 6.5 State Management

Проверить:

* TanStack Query для серверного состояния (НЕ Redux/Zustand)
* React Hook Form для форм
* Zod для валидации форм
* Local state через useState/useReducer где уместно
* Отсутствие избыточного глобального состояния

## 6.6 Chart Rendering

Проверить `frontend/src/features/dashboards/ui/charts/`:

* BarChart (Plotly.js React)
* LineChart (Plotly.js React)
* PieChart (Plotly.js React)
* TableChart
* PlotlyChart (обертка)
* Поддерживаемые типы: bar, line, pie, table
* Config-driven rendering (из graph.config)
* Invalid config handling
* Missing data handling

## 6.7 Security (Frontend)

Проверить:

* JWT хранится в memory или secure httpOnly cookie (НЕ localStorage для продакшена)
* Axios интерцепторы добавляют токен
* ProtectedRoute компонент работает
* RoleBasedAccess компонент работает
* Email validation (Zod regex + blacklist domains)

---

# BLOCK 7 — Code Quality (Backend)

## 7.1 Typing

Проверить `src/mkobi/`:

* Type hints во всех функциях (параметры и возвращаемое значение)
* Pydantic модели для API (src/mkobi/models/)
* SQLAlchemy модели для ORM (src/mkobi/db/models/)
* Отсутствие `Any` типов (кроме обоснованных случаев)
* mypy проходит без ошибок

## 7.2 Pydantic Models

Проверить `src/mkobi/models/`:

* Все модели наследуются от BaseModel
* Используются типы: EmailStr, UUID, datetime
* Валидаторы где нужно (validator, field_validator)
* Config class (или model_config) настроена
* Отсутствие дублирования логики

Проверить файлы:

* `auth.py`: LoginRequest, AuthResponse, UserResponse
* `dashboard.py`: DashboardCreate, DashboardUpdate, DashboardResponse
* `user.py`: UserCreate, UserUpdate, UserResponse
* `enums.py`: ВСЕ StrEnum (UserRole, DashboardPermission, GraphType, FilterType, RegistrationStatus, UploadMode, ProcessingStatus)

## 7.3 Enum Usage (StrEnum)

Проверить `src/mkobi/models/enums.py`:

Все константы должны быть StrEnum, НЕ dict или list:

```python
from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class GraphType(StrEnum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    TABLE = "table"
```

Проверить использование enum в коде (НЕ строковые литералы):

* Bad: `if user.role == "admin":`
* Good: `if user.role == UserRole.ADMIN:`

## 7.4 Readability

Проверить:

* Oversized functions (разбивать на меньшие)
* Duplicated logic (выносить в helpers)
* Unclear naming (переименовывать)
* Magic constants (выносить в константы или config)
* Комментарии там, где сложная логика (НО не избыточные)
* Comments MUST be in English (НЕ на русском)

## 7.5 Logging Language

Проверить:

* Log messages are in English (НЕ на русском)
* Exception messages are in English
* Comments are in English
* Example: `logger.info("User logged in")` (GOOD), `logger.info("Пользователь вошел")` (BAD)

## 7.5 Error Handling

Проверить:

* Отсутствие broad except (except Exception:)
* Отсутствие swallowed exceptions (пустые except)
* Consistent errors (всегда возвращать HTTPException с кодом)
* Логирование ошибок (logger.error с контекстом)
* Отсутствие print()

## 7.6 Async Correctness

Проверить:

* Blocking IO в async endpoints (НЕ делать)
* Sync DB calls в async endpoints (использовать async SQLAlchemy)
* time.sleep() в async (использовать asyncio.sleep)
* Proper await usage

## 7.7 Logging

Проверить использование logging:

```python
import logging

logger = logging.getLogger(__name__)
```

Проверить наличие логирования:

* Upload events (start, complete, failure)
* Processing events (start, steps, complete, failure)
* Auth events (login success/failure)
* Errors (с stack trace)
* Уровни: INFO, WARNING, ERROR (НЕ DEBUG в продакшене)

Проверить отсутствие:

* print() statements
* logger.info() для ошибок (использовать logger.error())

---

# BLOCK 8 — Code Quality (Frontend)

## 8.1 TypeScript

Проверить:

* Type hints (интерфейсы, типы)
* Отсутствие `any` (использовать конкретные типы)
* Zod schemas для runtime validation
* Корректные props types для компонентов
* tsc --noEmit проходит без ошибок

## 8.2 React Best Practices

Проверить:

* Функциональные компоненты (НЕ class components)
* Hooks usage (useState, useEffect, custom hooks)
* Key props в списках
* Memoization где нужно (useMemo, useCallback)
* Отсутствие бизнес-логики в компонентах (выносить в hooks/services)

## 8.3 Code Style

Проверить:

* ESLint проходит без ошибок
* Prettier (если настроен)
* Именование: PascalCase для компонентов, camelCase для переменных
* Отсутствие закомментированного кода
* Отсутствие console.log() в продакшене
* Comments MUST be in English (НЕ на русском)

---

# BLOCK 9 — Testing

## 9.1 pytest Usage

Проверить `tests/`:

* Используется pytest (НЕ unittest)
* Фикстуры в conftest.py
* Mocking где нужно (unittest.mock)

## 9.2 Coverage

Проверить наличие тестов для:

* **Auth**: login, register-request, me endpoint
* **API**: все endpoints (успех и ошибки)
* **Processing**: loaders, transformations, aggregations
* **Access Control**: permissions, roles
* **Repositories**: DB operations
* **Config**: loading, validation

Проверить файлы:

* `test_auth.py`
* `test_dashboards_api.py`
* `test_users_api.py`
* `test_upload_api.py`
* `test_data_processing.py`
* `test_data_loader.py`
* `test_models.py`
* `test_repositories.py`
* `test_security.py`
* `test_filters.py`
* `test_graphs.py`
* `test_layouts.py`
* `test_processing_logs.py`
* `test_config.py`
* `test_pydantic_models.py`
* `test_storage_manager.py`
* `test_yoy_calculation.py`
* `test_share_calculation.py`

## 9.3 Test Quality

Проверить:

* Edge cases (пустые данные, некорректный ввод)
* Invalid input tests (wrong types, missing fields)
* Permission tests (разные роли)
* Error handling tests
* Mocking внешних зависимостей

---

# BLOCK 10 — Performance & Stability

## 10.1 Processing Scalability

Проверить:

* Memory-heavy operations (чтение всего файла в память?)
* Full file loading issues (streaming для больших файлов?)
* Polars lazy evaluation где применимо
* Chunked processing для больших datasets

## 10.2 API Stability

Проверить:

* Error isolation (один endpoint не падает → другие работают)
* Long-running requests (timeout handling)
* Rate limiting (защита от abuse)
* CORS настроен корректно (FastAPI CORSMiddleware)

## 10.3 Database

Проверить:

* Heavy JSONB scans (используется GIN index?)
* Missing indexes usage (проверить query plans)
* Connection pooling (asyncpg pool)
* Deadlocks (транзакции короткие)
* N+1 problems (используется eager loading где нужно)

---

# BLOCK 11 — Configuration & Deployment

## 11.1 Configuration

Проверить `src/mkobi/config.py` и `src/mkobi/settings/`:

* Pydantic-settings для загрузки конфигурации
* Приоритет: env vars > Docker secrets > .env > YAML > defaults
* Secrets через env vars (DATABASE__PASSWORD, JWT__SECRET_KEY)
* Docker secrets support (_FILE suffix)
* `.env` файл только для development
* `app.yaml` только для нечувствительных настроек

## 11.2 Database Initialization

Проверить `src/mkobi/db/starter.py` и lifespan в `src/mkobi/app.py`:

* Автоматическая проверка схемы БД при старте
* Миграции применяются согласно окружению (ENV)
* Production ограничения соблюдаются

## 11.3 Docker

Проверить `Dockerfile` и `docker-compose.yml`:

* Многостадийная сборка (multi-stage build)
* Только необходимые зависимости в продакшене
* Переменные окружения передаются корректно
* Volumes для данных (если нужно)
* Healthcheck (опционально)

## 11.4 Deployment Options

Проверить SPEC.md раздел 24:

**Development**:

* React dev server (port 3000) + FastAPI (port 8000) с CORS
* Hot reload для обоих серверов
* Environment variables через `.env` файлы

**Production (Вариант А)**:

* FastAPI раздает собранные статические файлы React (`frontend/dist`)
* Статические файлы через StaticFiles

**Production (Вариант Б)**:

* Nginx проксирует `/api` → FastAPI, остальное → React SPA

---

# BLOCK 12 — No Overengineering Check

Проверить отсутствие:

* Redux/Zustand (TanStack Query достаточно для серверного состояния)
* Лишних слоев абстракции (axiosInstance → прямые вызовы API)
* Дублирования Pydantic моделей
* Сложных паттернов без необходимости (если простое решение работает)
* Enterprise patterns где не требуется

---

# Формат отчета (ОБЯЗАТЕЛЬНО)
 
Создать новый файл `TODO/TASK_<number>_analysis_report.md`
вместо <number> - подставить номер, убедившись, что файл с таким номером не существует

## 1. Executive Summary

Кратко:

* Общее качество системы
* Основные риски
* Readiness level (1-10)
* Соответствие спецификациям (SPEC.md + SPEC_FRONTEND.md)

---

## 2. Architecture Summary

Кратко:

* Сильные стороны
* Слабые стороны
* Maintainability assessment
* Соблюдение Clean Architecture
* Соблюдение FSD (Frontend)

---

## 3. Requirements Coverage

Таблица (на основе SPEC.md и SPEC_FRONTEND.md):

| Requirement | Status | Notes |
| ----------- | ------ | ----- |
| JWT auth | PASS/FAIL | ... |
| CSV.gz upload | PASS/FAIL | ... |
| Polars processing | PASS/FAIL | ... |
| React SPA (FSD) | PASS/FAIL | ... |
| Plotly.js React charts | PASS/FAIL | ... |
| StrEnum usage | PASS/FAIL | ... |
| Logging (НЕ print) | PASS/FAIL | ... |
| Type hints (backend) | PASS/FAIL | ... |
| TypeScript (frontend) | PASS/FAIL | ... |
| Pydantic models | PASS/FAIL | ... |
| PostgreSQL + JSONB | PASS/FAIL | ... |
| Role-based access | PASS/FAIL | ... |
| TanStack Query | PASS/FAIL | ... |
| React Hook Form + Zod | PASS/FAIL | ... |

---

## 4. Findings (основной раздел)

Для каждой проблемы ОБЯЗАТЕЛЬНО:

| Severity | File | Line | Problem | Impact | Recommendation |
| -------- | ---- | ---- | ------- | ------ | -------------- |
| CRITICAL | api/upload.py | 84 | temp files not deleted | disk leaks | add finally cleanup |
| HIGH | models/enums.py | 12 | dict used instead of StrEnum | maintainability | refactor to StrEnum |
| MEDIUM | services/processing.py | 156 | print() instead of logger | logging standards | use logger.error() |
| LOW | frontend/src/features/auth/ui/LoginForm.tsx | 23 | any type used | type safety | add interface |

Severity:

* **CRITICAL**: блокирует работу, security vulnerability, data loss
* **HIGH**: серьезная проблема, влияет на стабильность или безопасность
* **MEDIUM**: проблема качества, technical debt
* **LOW**: style, naming, minor improvements

---

## 5. File-Level Recommendations

Для каждого проблемного файла:

```text
File: src/mkobi/data/processing/transformations.py

Problems:
- oversized function (process_data: 200+ lines)
- mixed responsibilities (parse + transform + aggregate)
- transaction handling unclear
- print() statements for debug

Recommendations:
- split into parse/transform/aggregate functions
- isolate DB writes in storage/manager.py
- add typed intermediate models
- replace print() with logger
- add docstrings (Google style)
```

---

## 6. Missing Features vs Specification

Отдельно перечислить:

**Отсутствует (не реализовано)**:

* Feature X из SPEC.md раздел Y
* Endpoint Z из SPEC_FRONTEND.md

**Реализовано частично**:

* Feature A (не хватает B, C)
* ...

**Противоречит ТЗ**:

* В коде X, в ТЗ Y
* ...

---

## 7. Frontend-Specific Findings

Отдельный раздел для React SPA:

### 7.1 Architecture (FSD)

* Соблюдение структуры features/shared/app
* Отсутствие бизнес-логики в компонентах
* Корректное использование TanStack Query

### 7.2 TypeScript

* Отсутствие `any`
* Корректные типы для API
* Zod schemas для форм

### 7.3 Components

* Все страницы из SPEC_FRONTEND.md реализованы
* Chart rendering работает (Plotly.js React)
* Filters применяются корректно

### 7.4 API Integration

* axiosInstance настроен
* JWT interceptors работают
* Error handling (react-hot-toast)

---

## 8. Security Assessment

### 8.1 Backend

* JWT: корректно
* Password hashing: bcrypt
* SQL injection: защита через ORM
* Upload: защита от path traversal, oversized files
* Rate limiting: настроен/отсутствует

### 8.2 Frontend

* JWT storage: memory/httpOnly cookie (НЕ localStorage)
* ProtectedRoute: работает
* RoleBasedAccess: работает

---

## 9. Performance Assessment

### 9.1 Backend

* Processing: Polars используется, memory-efficient
* DB: индексы настроены, GIN для JSONB
* API: CORS, rate limiting

### 9.2 Frontend

* Bundle size: оптимизирован (или нет)
* React rendering: optimizations (memoization)
* API calls: TanStack Query caching

---

## 10. Final Assessment

Кратко оценить:

* **Maintainability**: легко поддерживать? (1-10)
* **Production Readiness**: готово к продакшену? (1-10)
* **Scalability**: масштабируемость (1-10)
* **Security**: уровень безопасности (1-10)
* **Code Quality**: качество кода (1-10)

### Основные technical risks

1. Risk 1 (CRITICAL/HIGH/MEDIUM/LOW)
2. Risk 2
3. ...

### Приоритет исправлений

1. Критичные (CRITICAL) — исправить немедленно
2. Высокие (HIGH) — исправить до продакшена
3. Средние (MEDIUM) — technical debt
4. Низкие (LOW) — nice to have

---

# Важные ограничения для аудитора (LLM)

## НЕ считать проблемой

* Простую архитектуру
* Небольшое количество abstraction layers
* Отсутствие enterprise patterns
* Использование "простых" решений, если они работают и читаемы

## Считать проблемой

* Сложность поддержки (hard to understand, modify)
* Неявную логику (hidden behavior, side effects)
* Небезопасность (security vulnerabilities)
* Смешивание ответственности (business logic in routes)
* Нестабильный processing (data loss, corruption)
* Слабый access control (unauthorized access)
* Плохую обработку ошибок (swallowed exceptions)
* Использование print() вместо logging
* Отсутствие StrEnum там, где уместно
* Hardcoded strings вместо enum values
* Отсутствие type hints
* Прямой SQL через string interpolation

## Основной критерий

Система должна быть:

* Понятной (читаемый код, clear intent)
* Устойчивой (error handling, transactions, cleanup)
* Безопасной (auth, access control, validation)
* Легко поддерживаемой (modular, tested, typed)
* Соответствующей спецификации (SPEC.md + SPEC_FRONTEND.md)

## Специфичные требования к mkobi

* Package name: `mkobi`
* StrEnum вместо dict/list для всех констант
* Pydantic models в `src/mkobi/models/`
* Logging через `logger = logging.getLogger(__name__)`
* Type hints во всех функциях
* Clean Architecture (разделение слоев)
* FSD для frontend
* Polars (НЕ pandas)
* PostgreSQL + JSONB для агрегированных данных
* Comments and logs MUST be in English (НЕ на русском)
