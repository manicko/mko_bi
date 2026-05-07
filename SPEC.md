# BI Dashboard System 

## 1. Purpose

Веб-приложение для:

* загрузки CSV и CSV.gz данных во временную папку пользователя
* их обработки
* хранения агрегатов
* отображения в дашбордах
* управления доступом пользователей

---

## 2. Stack 

* Backend: **FastAPI**
* Frontend: **React 18+ (TypeScript) + Vite**
* UI Kit: **Material UI v5** or **Ant Design**
* State Management: **TanStack Query** (React Query)
* Forms: **React Hook Form + Zod**
* Charts: **Plotly.js React**
* File Upload: **react-dropzone**
* HTTP Client: **Axios** (with JWT interceptors)
* Notifications: **react-hot-toast**
* Data processing: **Polars** (запрещено использовать pandas)
* Storage: **PostgreSQL**
* Validation: **Pydantic**
* Auth: **JWT + bcrypt**
* Testing: **pytest**
* Logging: **Python logging**
* Env/deps: **uv**
* temp files - platformdirs
* SQLAlchemy (async)
* alembic для миграций
* asyncpg драйвер
---

## 3. Core Entities

### User

* id
* email
* password_hash
* role: `admin | editor | viewer`

### Dashboard

* id
* name
* config (описание структуры и графиков)

### Access

* user_id
* dashboard_id

### Data (aggregated)

* dashboard_id
* агрегированные значения (таблицы в PostgreSQL)

---

## 4. Roles & Permissions

### Admin

* CRUD dashboards
* задаёт:

  * схему данных
  * логику обработки
  * графики
* управляет пользователями
* выдаёт доступы

### Editor

* загружает CSV
* инициирует пересчёт данных

### Viewer

* только просмотр

---

## 5. Authentication

* login: email + password
* password → bcrypt hash
* auth → JWT
* все API защищены

---
## 6. Security & ограничения

* Для upload endpoints должен использоваться rate limiting
* Необходимо ограничение максимального размера загружаемых CSV-файлов
* Обязательна проверка MIME-type загружаемых файлов (`text/csv`, `application/gzip`)
* Все SQL-запросы должны выполняться через parameterized queries (SQLAlchemy ORM/Core)
* Запрещено формирование SQL через string interpolation
* Временные файлы должны удаляться после обработки
---
## 6.1 Configuration & Secrets Management

* Конфигурация загружается из нескольких источников (приоритет: env vars > Docker secrets > .env > YAML > defaults)
* Секреты (DB password, JWT key) хранятся в переменных окружения: `DATABASE__PASSWORD`, `JWT__SECRET_KEY`
* Поддержка Docker secrets через `_FILE` суффикс: `DATABASE__PASSWORD_FILE=/run/secrets/db_password`
* Поддержка `.env` файла для разработки (pydantic-settings)
* `app.yaml` содержит только нечувствительные настройки (хосты, порты, пути)
* Формат вложенных переменных: `DATABASE__HOST`, `DATABASE__PORT` (double underscore)

---
## 7. Data Flow

1. Upload CSV / CSV.gz во временную папку пользователя platformdirs
2. Parse (Polars)
3. Transform (LoaderConfig)
4. Aggregate
5. Save to PostgreSQL
6. React SPA запрашивает данные через API
7. Plotly.js React строит графики

---

## 8. Data Upload

* формат: `.csv`, `.csv.gz`
* кодировка `UTF-8`
* файл:

  * загружается
  * обрабатывается
  * удаляется
* история не хранится

---

## 9. Data Processing

* триггер: upload файла
* pipeline:
  * чтение (Polars)
  * трансформация (по конфигу dashboard)
  * агрегации:
    * groupby
    * YoY
    * доли
    * кастомные метрики
* результат:
  * **полный пересчёт**
  * запись в PostgreSQL

---

## 10. Data Storage

* хранится только агрегированное
* структура:
   единая таблица с данными графиков всех дашбордов с ипользованием JSONB 
* данные общие (не зависят от пользователя)

---

---

## 12. Dashboards

* задаются админом (config-driven)
* каждый дашборд:
  * набор графиков
  * отдельная страница

### Graph types (фиксировано)

* bar
* line
* pie
* table

### Features

* multi-axis
* комбинированные графики
* YoY

---

## 13. Filters

* глобальные:
  * year
  * category
  * brand
* применяются ко всем графикам
* реализуются через backend (SQL/Polars)

---

## 14. API Responsibilities (FastAPI)

* auth (login, register-request)
* users CRUD (admin only)
* dashboards CRUD (admin only)
* upload endpoint (React SPA → FastAPI)
* trigger processing
* get aggregated data (JSON для React)
* access validation (user ↔ dashboard)
* registration requests management (admin)

### 14.1 Auth Endpoints
- `POST /api/v1/auth/login` → `{access_token, user}`
- `POST /api/v1/auth/register-request` → `{message}`
- `GET /api/v1/auth/me` → `UserProfile`

### 14.2 Dashboard Endpoints
- `GET /api/v1/dashboards/my` → `DashboardSummary[]`
- `GET /api/v1/dashboards/:id` → `DashboardDetail`
- `POST /api/v1/dashboards` (admin)
- `PUT /api/v1/dashboards/:id` (admin)
- `DELETE /api/v1/dashboards/:id` (admin)

### 14.3 Data Endpoints
- `GET /api/v1/data/aggregated?dashboard_id=:id&filters=...` → графики данные
- `POST /api/v1/upload/:dashboard_id?mode=overwrite|append` (multipart file)

### 14.4 Admin Endpoints
- `GET /api/v1/admin/users` → `User[]`
- `PATCH /api/v1/admin/users/:id/role`
- `GET /api/v1/admin/registration-requests` → `Request[]`
- `POST /api/v1/admin/registration-requests/:id/approve`
- `GET /api/v1/admin/logs` → `ProcessingLog[]`

---

## 15. Access Control

* проверка на каждом запросе
* пользователь видит только свои dashboards

---

## 16. Database Schema (PostgreSQL)

### 16.1 Core Tables

#### `users` - Пользователи системы
```sql
users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);
```
- **role**: `admin` | `editor` | `viewer`
- Пароли хранятся как bcrypt hash

#### `layouts` - UI композиция (без привязки к данным)
```sql
layouts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT UNIQUE NOT NULL,
    definition      JSONB NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);
```
- `definition` JSONB структура:
  ```json
  {
    "grid": [...],
    "graphs": [...],
    "filters": [...],
    "bindings": [
      { "filter": "year", "graphs": ["g1", "g2"] }
    ]
  }
  ```

#### `dashboards` - Дашборды
```sql
dashboards (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT UNIQUE NOT NULL,
    description     TEXT,
    layout_id       UUID REFERENCES layouts(id),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

#### `graphs` - Определения графиков
```sql
graphs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dashboard_id    UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL CHECK (type IN ('bar', 'line', 'pie', 'table')),
    config          JSONB NOT NULL,  -- оси, цвета, настройки визуализации
    dimensions      JSONB NOT NULL,  -- список измерений
    metrics         JSONB NOT NULL,  -- список метрик
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE (dashboard_id, name)
);
```
- **type**: `bar` | `line` | `pie` | `table`
- `config` содержит: axis config, colors, display options
- `dimensions`: список полей для группировки
- `metrics`: список агрегируемых полей

#### `filters` - Глобальные фильтры
```sql
filters (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT UNIQUE NOT NULL,
    type            TEXT NOT NULL,  -- 'select' | 'multiselect' | 'range' | 'date'
    config          JSONB NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);
```
- Пример `config`: `{"field": "year", "source": "dims", "multi": false}`
- Фильтры не принадлежат конкретному дашборду (переиспользуемые)

#### `dashboard_access` - Управление доступом
```sql
dashboard_access (
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    dashboard_id    UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    permission      TEXT NOT NULL CHECK (permission IN ('view', 'edit', 'admin')),
    PRIMARY KEY (user_id, dashboard_id)
);
```
- **permission**: `view` | `edit` | `admin`

#### `dashboard_filters` - Связь дашбордов с фильтрами (many-to-many)
```sql
dashboard_filters (
    dashboard_id    UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    filter_id       UUID NOT NULL REFERENCES filters(id) ON DELETE CASCADE,
    PRIMARY KEY (dashboard_id, filter_id)
);
```
- Связь многие-ко-многим между дашбордами и фильтрами
- При удалении дашборда или фильтра связь удаляется (CASCADE)

#### `processing_configs` - Настройки обработки
```sql
processing_configs (
    dashboard_id    UUID PRIMARY KEY REFERENCES dashboards(id) ON DELETE CASCADE,
    settings        JSONB NOT NULL,
    updated_at      TIMESTAMP DEFAULT NOW()
);
```
- Пример: `{"loader": "sales_loader", "date_column": "event_date", "timezone": "UTC"}`
- Только настройки, без бизнес-логики

#### `aggregated_data` - Агрегированные данные (CORE)
```sql
aggregated_data (
    id              BIGSERIAL PRIMARY KEY,
    dashboard_id    UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    graph_id        UUID NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,
    dims            JSONB NOT NULL,  -- значения измерений
    metrics         JSONB NOT NULL   -- значения метрик
);
```

- 1 строка = 1 точка графика
- `dims`: ключ-значение для фильтров и осей
- `metrics`: ключ-значение для отображения

#### `processing_logs` - Логи обработки
```sql
processing_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dashboard_id    UUID REFERENCES dashboards(id) ON DELETE SET NULL,
    status          TEXT NOT NULL CHECK (status IN ('started', 'uploaded', 'processing', 'success', 'failed', 'completed')),
    message         TEXT,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ
);
```

#### `registration_requests` - Заявки на регистрацию
```sql
registration_requests (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT UNIQUE NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
    requested_by_ip INET,
    reviewed_by     UUID REFERENCES users(id),
    reviewed_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);
```
- **status**: `pending` | `approved` | `rejected`
- Заявки создаются через `/api/v1/auth/register-request`

### 16.2 Indexes
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

### 16.3 Data Principles
- **Гибкость**: JSONB для dims/metrics — поддержка любых данных без миграций
- **Производительность**: GIN индекс для фильтрации по dims
- **Безопасность**: ON DELETE CASCADE для связанных данных
- **Масштабируемость**: Отдельные таблицы под каждый дашборд не нужны — гибкая схема

---

## 11. Frontend Architecture (React SPA)

### 11.1 Общая концепция
Архитектурный паттерн: **Clean Architecture + Feature-Sliced Design (FSD)**

```
Browser (React SPA)
       ↓ HTTPS/JSON
FastAPI (REST API)
       ↓
Service Layer (существующий)
       ↓
PostgreSQL
```

### 11.2 Ключевые принципы
- **Separation of Concerns**: React отвечает только за UI, FastAPI — за бизнес-логику и данные
- **Stateless Backend**: JWT токены, сессии не хранятся на бэкенде
- **Type Safety**: TypeScript на фронтенде, Pydantic на бэкенде
- **No Overengineering**: Используем проверенные библиотеки, избегаем избыточной абстракции

### 11.3 Project Structure (Frontend)
```
frontend/
├── public/
├── src/
│   ├── app/
│   │   ├── providers.tsx
│   │   └── routes.tsx
│   ├── features/
│   │   ├── auth/
│   │   │   ├── ui/LoginForm.tsx
│   │   │   ├── api/authApi.ts
│   │   │   └── model/useAuth.ts
│   │   ├── dashboards/
│   │   │   ├── ui/DashboardList.tsx
│   │   │   └── api/dashboardApi.ts
│   │   ├── upload/
│   │   │   └── ui/FileDropzone.tsx
│   │   ├── users/
│   │   │   └── ui/UserList.tsx
│   │   └── admin/
│   │       └── ui/AdminPanel.tsx
│   ├── shared/
│   │   ├── api/axiosInstance.ts
│   │   ├── components/ProtectedRoute.tsx
│   │   └── types/api.types.ts
│   └── main.tsx
├── package.json
└── vite.config.ts
```

---

## 18. UI Pages (React SPA)

### 18.1 Login Page (`/login`)
- Поле email (валидация формата)
- Поле password (type="password")
- Кнопка "Войти"
- Ссылка "Зарегистрироваться" → `/register`

### 18.2 Registration Page (`/register`)
- Поле email (валидация через Zod)
- Кнопка "Отправить заявку"
- Заявка сохраняется в БД (`registration_requests`)

### 18.3 Dashboard List Page (`/dashboards`)
- Список доступных пользователю дашбордов
- Каждая карточка: название, описание, ссылка "Открыть"
- GET `/api/v1/dashboards/my`

### 18.4 Dashboard View Page (`/dashboard/:id`)
- Заголовок дашборда
- **Filters Panel**: Select/Range/Date фильтры (динамически по конфигу)
- **Charts Grid**: Графики (Plotly.js React), таблицы
- **Upload Button** (видна для роли `editor` и выше)
- GET `/api/v1/data/aggregated?dashboard_id=:id&filters=...`

### 18.5 User Profile Page (`/profile`)
- Email (read-only), роль (read-only)
- Кнопка "Удалить аккаунт" (только для НЕ-админов)

### 18.6 Admin Panel (`/admin`)
- **User Management**: таблица пользователей, изменение ролей
- **Registration Requests**: одобрение/отклонение заявок
- **Dashboard Management**: CRUD дашбордов
- **Log Viewer**: просмотр логов обработки

### 18.7 Data Upload Page (`/dashboard/:id/upload`)
- Mode Toggle: "Перезаписать" / "Добавить данные"
- Dropzone для drag-and-drop файлов (.csv, .csv.gz)
- Progress Bar для каждого файла
- POST `/api/v1/upload/:dashboard_id?mode=overwrite|append`

---
## 19. Architecture (React + FastAPI)

React SPA интегрирован с FastAPI backend через REST API.

### 19.1 Общая архитектура

```
Browser (React SPA)
       ↓ HTTPS/JSON
FastAPI (REST API)
       ↓
Service Layer
       ↓
PostgreSQL
```

### 19.2 Ключевые принципы

1. Вся бизнес-логика находится в FastAPI/service layer
2. React отвечает только за UI и визуализацию (Plotly.js React)
3. Проверка прав доступа выполняется на бэкенде (каждый API запрос)
4. React не содержит бизнес-логики, только UI state
5. Все запросы к данным проходят через FastAPI REST API

### 19.3 Поток работы

```
Browser (React SPA)
    ↓ HTTPS/JSON
FastAPI
    ├── REST API (JSON)
    ├── Auth / JWT
    ├── Upload API
    ├── Data API
    └── Service Layer
            ↓
       PostgreSQL
```

### 19.4 Stateless Architecture

* FastAPI не хранит сессии (JWT токены)
* React SPA хранит JWT в memory или secure cookie
* Каждый запрос к API включает JWT токен в заголовке

### Database Initialization

При старте приложения FastAPI выполняется автоматическая проверка и инициализация схемы БД через модуль `DatabaseStarter` (lifespan). Миграции применяются согласно окружению (`ENV`) с соблюдением production-ограничений.

**Поведение при первом запуске в Docker:**

1. **Основная БД** (`bidb`):
   - Проверка существования БД
   - Применение миграций Alembic (если `AUTO_MIGRATE=true`)

2. **Тестовая БД** (`bidb_test`):
   - Автоматическое создание при `RECREATE_TEST_DB=true`
   - Применение миграций Alembic к тестовой БД
   - Необходимо для запуска `uv run pytest tests/` в Docker

**Конфигурация через переменные окружения:**

```yaml
# docker-compose.yml (app service environment)
ENV: development|test|production
DATABASE__DBNAME: bidb
DATABASE__TEST_DBNAME: bidb_test  # опционально
AUTO_MIGRATE: "true"
RECREATE_TEST_DB: "true"  # для test env
```

**Реализация:** `src/mkobi/db/starter.py`
- `DatabaseStarter.startup()` - инициализация основной БД
- `DatabaseStarter.recreate_test_database()` - создание и миграция тестовой БД

---

## 20. Logging

логируются:

* upload
* processing
* errors
* access events

уровни:

* INFO
* WARNING
* ERROR

---

## 21. Testing

* pytest
* покрытие:

  * API
  * processing
  * auth

---

## 22. Enums (StrEnum)

Все типы сущностей определяются через `StrEnum` в `src/mkobi/models/enums.py`:

```python
from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class DashboardPermission(StrEnum):
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"


class GraphType(StrEnum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    TABLE = "table"


class FilterType(StrEnum):
    SELECT = "select"
    MULTISELECT = "multiselect"
    RANGE = "range"
    DATE = "date"


class RegistrationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UploadMode(StrEnum):
    OVERWRITE = "overwrite"
    APPEND = "append"


class ProcessingStatus(StrEnum):
    STARTED = "started"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    COMPLETED = "completed"
```

---

## 23. Frontend Security

### 23.1 JWT Handling
- Access token хранится в memory или secure httpOnly cookie (не в localStorage для продакшена)
- Refresh token (опционально) для продления сессии
- Интерцепторы Axios для добавления токена к каждому запросу

### 23.2 File Upload
- Rate limiting на `/api/v1/upload/*`
- Максимальный размер файла (проверка на бэкенде)
- MIME-type validation (.csv, .csv.gz) на фронтенде и бэкенде

### 23.3 Role-Based Access
- Frontend: `ProtectedRoute` + `RoleBasedAccess` компоненты
- Backend: существующие permissions (обновленные для новых эндпоинтов)

### 23.4 Email Validation (Registration)
- Regex паттерн (на фронтенде через Zod и на бэкенде через Pydantic)
- Blacklist доменов (configurable через `app.yaml`)

### 23.5 CORS Configuration (FastAPI)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 24. Deployment

### 24.1 Development
- React dev server (port 3000) + FastAPI (port 8000) с CORS
- Hot reload для обоих серверов
- Environment variables через `.env` файлы

### 24.2 Production

**Вариант А**: FastAPI раздает собранные статические файлы React
```
frontend/ (после npm run build)
  └── dist/  →  раздается через FastAPI StaticFiles
```

**Вариант Б**: Nginx проксирует `/api` → FastAPI, остальное → React SPA
```
Nginx:
  /api/*  → FastAPI (port 8000)
  /*      → React SPA static files (port 3000 или static build)
```

### 24.3 No Overengineering
- Не использовать Redux/Zustand (TanStack Query достаточно для серверного состояния)
- Не создавать лишние слои абстракции (axiosInstance → прямые вызовы API)
- Использовать существующие Pydantic модели (не дублировать логику)

### 24.4 Миграция с Dash
- Dash можно оставить как fallback для сложных графиков (iframe)
- Или полностью заменить на Plotly.js React (предпочтительно)

---

**Автор**: Senior Python Architect  
**Дата**: 2026-05-05  
**Версия**: 2.0 (React + FastAPI Architecture)

