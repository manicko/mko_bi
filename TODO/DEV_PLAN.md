# DEV_PLAN.md - План разработки mkobi

**Автор**: Senior Python Architect (Kilo)
**Дата**: 2026-05-05
**Версия**: 1.0

---

## Обзор проекта

BI Dashboard System - веб-приложение для загрузки CSV данных, их обработки, хранения агрегатов и отображения в дашбордах с системой управления доступом.

**Stack**: FastAPI + React 18+ (TypeScript) + PostgreSQL + Polars + Pydantic + JWT

---

## Соответствие файлов структуры блокам ТЗ

| Блок ТЗ | Файлы в структуре |
|---------|-------------------|
| Database & Models | `src/mkobi/db/models/*.py`, `alembic/versions/*.py` |
| Configuration | `src/mkobi/config.py`, `src/mkobi/settings/app.yaml` |
| Authentication | `src/mkobi/api/routes/auth.py`, `src/mkobi/services/auth_service.py`, `src/mkobi/models/auth.py` |
| Core Infrastructure | `src/mkobi/core/*.py`, `src/mkobi/utils/*.py` |
| Data Upload | `src/mkobi/api/routes/upload.py`, `src/mkobi/data/loaders/*.py` |
| Data Processing | `src/mkobi/data/processing/*.py` |
| Data Storage | `src/mkobi/data/storage/manager.py`, `src/mkobi/db/repositories/aggregated_data_repo.py` |
| Dashboard Management | `src/mkobi/api/routes/dashboards.py`, `src/mkobi/services/dashboard_service.py`, `src/mkobi/dashboards/*` |
| Data API | `src/mkobi/api/routes/data.py`, `src/mkobi/services/data_service.py` |
| User Management | `src/mkobi/api/routes/users.py`, `src/mkobi/services/user_service.py` |
| Processing Logs | `src/mkobi/api/routes/processing_logs.py`, `src/mkobi/services/processing_log_service.py` |
| Frontend | `frontend/` (создать с нуля) |
| Testing | `tests/*.py` |

---

## Блоки разработки (изолированные модули)

### Блок 1: Database & Models (БД и модели)
**Файл**: `001_database_models.md`
- Настройка SQLAlchemy models
- Enum definitions (StrEnum)
- Alembic миграции
- Таблицы: users, layouts, dashboards, graphs, filters, dashboard_access, dashboard_filters, processing_configs, aggregated_data, processing_logs, registration_requests

### Блок 2: Configuration & Settings (Конфигурация)
**Файл**: `002_configuration.md`
- Pydantic Settings
- app.yaml (нечувствительные настройки)
- Env vars, Docker secrets support
- Секреты (DB password, JWT key)

### Блок 3: Authentication & Authorization (Аутентификация)
**Файл**: `003_authentication.md`
- JWT токены
- bcrypt хеширование
- Login endpoint
- Register-request endpoint
- Role-based access control
- Permissions (view, edit, admin)

### Блок 4: Core Infrastructure (Базовая инфраструктура)
**Файл**: `004_core_infrastructure.md`
- Logging config
- Base repository (async)
- Permissions utils
- Security utils
- Task queue (для обработки данных)
- File utils (platformdirs)

### Блок 5: Data Upload (Загрузка данных)
**Файл**: `005_data_upload.md`
- Upload endpoint (multipart)
- File validation (MIME-type, extension, size)
- Rate limiting
- Temp files (platformdirs)
- Upload modes (overwrite, append)

### Блок 6: Data Processing (Обработка данных)
**Файл**: `006_data_processing.md`
- Polars data loading
- Transformations (filters, computed fields)
- Aggregations (groupby, YoY, shares, custom metrics)
- Data pipeline orchestration
- Processing configs

### Блок 7: Data Storage (Хранение данных)
**Файл**: `007_data_storage.md`
- Storage manager
- Aggregated data repository
- JSONB operations
- Full recalculation logic

### Блок 8: Dashboard Management (Управление дашбордами)
**Файл**: `008_dashboard_management.md`
- Layouts CRUD (JSONB definition)
- Dashboards CRUD
- Graphs CRUD (bar, line, pie, table)
- Filters CRUD (select, multiselect, range, date)
- Dashboard filters binding (many-to-many)
- Access management (user ↔ dashboard)

### Блок 9: Data API (API данных)
**Файл**: `009_data_api.md`
- Aggregated data endpoint
- Filters application (backend SQL/Polars)
- JSON response для React
- Graph data formatting

### Блок 10: User Management Admin (Админка пользователей)
**Файл**: `010_user_management.md`
- Users CRUD (admin)
- Registration requests management
- Role changes
- User deletion (non-admin)
- User profile endpoint

### Блок 11: Processing Logs (Логи обработки)
**Файл**: `011_processing_logs.md`
- Processing logs repository
- Log endpoints (admin)
- Log levels (INFO, WARNING, ERROR)
- Upload/processing/errors logging

### Блок 12: Frontend Foundation (Основа фронтенда)
**Файл**: `012_frontend_foundation.md`
- Vite + React 18 + TypeScript setup
- Project structure (FSD architecture)
- Routing (React Router v6)
- Providers (QueryClient, Theme, Router)
- Shared components (Layout, ProtectedRoute, RoleBasedAccess)
- Axios instance with JWT interceptors
- Constants and types

### Блок 13: Frontend Auth (Фронтенд аутентификация)
**Файл**: `013_frontend_auth.md`
- Login page (/login)
- Registration page (/register)
- Auth hooks (useAuth)
- JWT token management
- Protected routes
- Role-based access components

### Блок 14: Frontend Dashboards (Фронтенд дашборды)
**Файл**: `014_frontend_dashboards.md`
- Dashboard list page (/dashboards)
- Dashboard view page (/dashboard/:id)
- Filters panel (dynamic)
- Charts grid (Plotly.js React)
- Graph rendering (bar, line, pie, table)
- Multi-axis, combined charts, YoY

### Блок 15: Frontend Upload (Фронтенд загрузка)
**Файл**: `015_frontend_upload.md`
- Data upload page (/dashboard/:id/upload)
- Mode toggle (overwrite/append)
- File dropzone (react-dropzone)
- Progress bar
- File validation (extension, MIME-type)
- Upload API integration

### Блок 16: Frontend Admin (Фронтенд админка)
**Файл**: `016_frontend_admin.md`
- Admin panel (/admin)
- User management tab
- Registration requests tab
- Dashboard management tab
- Log viewer tab
- DataGrid (MUI) for tables
- Modal forms

### Блок 17: Frontend Profile (Фронтенд профиль)
**Файл**: `017_frontend_profile.md`
- User profile page (/profile)
- Email/role display (read-only)
- Account deletion (non-admin)
- Confirmation modal

### Блок 18: Testing (Тестирование)
**Файл**: `018_testing.md`
- pytest configuration
- API tests
- Service tests
- Auth tests
- Data processing tests
- Repository tests
- Coverage setup

### Блок 19: Deployment (Деплой)
**Файл**: `019_deployment.md`
- Docker setup
- Nginx configuration
- CORS setup
- Static files serving (FastAPI)
- Environment configs
- Production checks

---

## Порядок разработки (зависимости)

```
Блок 1 (DB) → Блок 2 (Config) → Блок 3 (Auth) → Блок 4 (Core)
                                              ↓
                    Блок 5 (Upload) ← Блок 6 (Processing) ← Блок 7 (Storage)
                              ↓
                    Блок 8 (Dashboards) → Блок 9 (Data API)
                              ↓
                    Блок 10 (Users) + Блок 11 (Logs)
                              ↓
                    Блок 12 (Frontend Foundation)
                              ↓
        ┌─────────────────────┴─────────────────────┐
        ↓                     ↓                     ↓
   Блок 13 (Auth)      Блок 14 (Dashboards)   Блок 15 (Upload)
        ↓                     ↓                     ↓
                          Блок 16 (Admin)
                              ↓
                          Блок 17 (Profile)
                              ↓
                          Блок 18 (Testing)
                              ↓
                          Блок 19 (Deployment)
```

---

## Критерии готовности (Definition of Done)

Каждый блок считается завершенным когда:
1. Код написан согласно стандартам (ruff, mypy clean)
2. Типизация покрывает все публичные методы
3. Тесты написаны и проходят (pytest)
4. Логирование настроено (INFO/WARNING/ERROR)
5. Enum использованы вместо dict/list где применимо
6. Clean Architecture соблюдена (разделение слоев)
7. Docstrings на публичные методы (кратко)

---

## Заметки по реализации

- Использовать `StrEnum` для всех перечислений
- Pydantic models в `src/mkobi/models/`
- Async SQLAlchemy с asyncpg драйвером
- Polars (не pandas) для обработки данных
- JSONB для гибких структур (dims, metrics, configs)
- JWT токены без сессий (stateless)
- platformdirs для временных файлов
- TanStack Query (не Redux) на фронтенде
- Plotly.js React для графиков
- No overengineering - минимум абстракций
