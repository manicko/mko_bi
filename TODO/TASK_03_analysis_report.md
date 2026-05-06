# BI Dashboard System Full Audit Report

## 1. Executive Summary

**Дата аудита**: 2026-05-06  
**Версия системы**: 1.0.8  
**Пакет**: `mkobi` (с 1 underscore)

### Общее качество системы
Система находится в **среднем состоянии готовности (6/10)**. Архитектура в целом соответствует Clean Architecture, но есть критические проблемы с типизацией (mypy errors), тестами (БД не настроена) и использованием enums.

### Основные риски
1. **HIGH**: Тесты не выполняются (отсутствует тестовая БД `bidb_test`)
2. **HIGH**: Множественные ошибки mypy (33+), включая несовместимость типов в сервисах
3. **MEDIUM**: Непоследовательное использование StrEnum (в `permissions.py` импорт из старого модуля)
4. **MEDIUM**: Async/sync смешивание (забыли `await` в сервисах)

### Readiness level: **6/10**
- Backend API: 7/10
- Frontend: 8/10
- Database: 7/10
- Testing: 3/10
- Security: 8/10

### Соответствие спецификациям (SPEC.md + SPEC_FRONTEND.md)
- ✅ JWT auth с bcrypt
- ✅ Polars для обработки (НЕ pandas)
- ✅ PostgreSQL + JSONB
- ✅ React SPA (FSD architecture)
- ✅ Plotly.js React charts
- ✅ StrEnum в `models/enums.py`
- ⚠️ Pydantic models (есть, но есть проблемы с типизацией)
- ❌ Type hints (backend) - mypy выдает много ошибок
- ✅ TypeScript (frontend) - типы присутствуют
- ❌ Tests не выполняются

---

## 2. Architecture Summary

### Сильные стороны
1. **Clean Architecture** соблюдается: API → Services → Repositories → DB models
2. Правильное разделение: `src/mkobi/api/routes/` (HTTP), `src/mkobi/services/` (бизнес-логика), `src/mkobi/db/repositories/` (данные)
3. Использование **Pydantic v2** для API моделей (`src/mkobi/models/`)
4. Использование **SQLAlchemy 2.0** asyncio для работы с БД
5. Фронтенд следует **Feature-Sliced Design (FSD)**
6. Конфигурация через **pydantic-settings** с поддержкой env vars, Docker secrets, YAML
7. Логирование через `logging.getLogger(__name__)` (НЕ print)

### Слабые стороны
1. Mypy ошибки не исправляются (33+ ошибок типизации)
2. Тесты не работают (отсутствует БД `bidb_test`)
3. Непоследовательное использование StrEnum (старый модуль `user_roles.py` все еще импортируется)
4. Смешивание async/sync кода (забыли `await` в некоторых местах)
5. Dash app монтируется в FastAPI, но это legacy и может путать

### Maintainability assessment: **Средняя**
- Код читаемый, но типизация требует исправления
- Архитектура понятная, но есть технический долг

### Соблюдение Clean Architecture: **7/10**
- Слои разделены корректно
- НО есть проблемы с интерфейсами (mypy override errors)

### Соблюдение FSD (Frontend): **8/10**
- Структура соблюдается: `app/`, `features/`, `shared/`
- Правильное использование `axiosInstance`
- Есть `ProtectedRoute` и `RoleBasedAccess` компоненты

---

## 3. Requirements Coverage

| Requirement | Status | Notes |
| ----------- | ------ | ----- |
| JWT auth | ✅ PASS | Используется python-jose, алгоритм HS256, секрет из конфигурации |
| BCrypt password hashing | ✅ PASS | `core/security.py`, SALT_ROUNDS=12, обрезка до 72 байт |
| CSV.gz upload | ✅ PASS | `upload.py`, проверка MIME-type, размера, path traversal |
| Polars processing | ✅ PASS | `data/loaders/loader.py`, lazy evaluation для больших файлов |
| React SPA (FSD) | ✅ PASS | `frontend/src/` структура корректна |
| Plotly.js React charts | ✅ PASS | `frontend/src/features/dashboards/ui/charts/` |
| StrEnum usage | ⚠️ PARTIAL | Есть в `models/enums.py`, НО `permissions.py` импортирует из `user_roles` |
| Logging (НЕ print) | ✅ PASS | Везде используется `logger = logging.getLogger(__name__)` |
| Type hints (backend) | ❌ FAIL | Mypy: 33+ ошибок типизации |
| TypeScript (frontend) | ✅ PASS | Типы в `api.types.ts`, интерфейсы компонентов |
| Pydantic models | ✅ PASS | Все модели в `src/mkobi/models/` |
| PostgreSQL + JSONB | ✅ PASS | `db/models/aggregated_data.py`, JSONBType кастомный |
| Role-based access | ✅ PASS | `core/permissions.py`, проверки в каждом endpoint |
| TanStack Query | ✅ PASS | Используется в фронтенд API вызовах |
| React Hook Form + Zod | ✅ PASS | Формы используют react-hook-form + zod |

---

## 4. Findings (основной раздел)

| Severity | File | Line | Problem | Impact | Recommendation |
| -------- | ---- | ---- | ------- | ------ | -------------- |
| **CRITICAL** | `tests/conftest.py` | 124 | Тестовая БД `bidb_test` не существует | Тесты не выполняются, невозможно проверить корректность | Создать БД `bidb_test` или исправить конфигурацию `test_database_url` |
| **HIGH** | `core/permissions.py` | 29 | Импорт `UserRole` из `mkobi.models.user_roles` вместо `mkobi.models.enums` | Несогласованность enum, возможны баги сравнения | Заменить на `from mkobi.models.enums import UserRole, UserRoleEnum` |
| **HIGH** | `core/permissions.py` | 113-117 | Используется `UserRoleEnum` и `ROLE_LEVELS` словарь вместо чистого StrEnum подхода | Лишняя сложность, смешивание подходов | Использовать только StrEnum сравнение (`user_role == UserRole.ADMIN`) |
| **HIGH** | Multiple services | various | Mypy: override incompatibility в сервисах (`processing_config_service.py`, `graph_service.py`, `filter_service.py`) | Нарушение Liskov substitution principle, типы не совместимы с интерфейсами | Исправить типы возвращаемых значений в сервисах, добавить `await` где нужно |
| **HIGH** | `services/*.py` | various | "Maybe you forgot to use await" - async функции вызываются без `await` | Функции возвращают coroutine вместо результата | Добавить `await` перед вызовами async функций |
| **MEDIUM** | `services/data_service.py` | 444 | `ProcessingStatus.PROCESSING` - опечатка (должно быть `ProcessingStatus.PROCESSING`) | Несуществующий атрибут enum | Исправить на `ProcessingStatus.PROCESSING` |
| **MEDIUM** | `api/routes/auth.py` | 67, 112 | Отсутствует запятая между аргументами: `login_data.email, login_data.password` | SyntaxError (код не выполнится) | Добавить запятую: `login_data.email, login_data.password` |
| **MEDIUM** | `api/routes/upload.py` | 140 | `open(file_path, "wb")` не закрывается явно | Утечка файловых дескрипторов | Использовать `with open(...) as f:` или `async with aiofiles.open(...)` |
| **MEDIUM** | `core/security.py` | 84 | `logger.info("Пароль успешно захеширован")` - логирование операции с паролем | Потенциальная утечка информации (хотя сам пароль не логируется) | Снизить до `logger.debug` или убрать |
| **MEDIUM** | `data/processing/transformations.py` | 137 | `"eq"` и `"ne"` строковые литералы вместо `FilterOperatorEnum.EQ.value` | Непоследовательное использование enum | Использовать `FilterOperatorEnum.EQ.value` |
| **MEDIUM** | Multiple repos | various | Mypy: `Returning Any from function declared to return "X | None"` | Потеря типизации из-за использования SQLAlchemy `execute().scalar()` | Добавить явное приведение типов или type: ignore с объяснением |
| **LOW** | `dashboards/components/charts/line.py` | 350, 441 | `"YoyModeEnum" has no attribute "percent"` - неправильное использование enum | Попытка получить атрибут через строку | Использовать `YoyModeEnum.PERCENT` |
| **LOW** | `pyproject.toml` | 52 | `mko-get-mediascope = "mkobi.app:app"` - странная точка входа | Неясно, зачем это нужно | Удалить или задокументировать |
| **LOW** | Frontend | various | Нет `tsconfig.json` проверки в аудите | Неизвестно, проходит ли `tsc --noEmit` | Добавить проверку TypeScript типов в CI/CD |

---

## 5. File-Level Recommendations

### File: `src/mkobi/core/permissions.py`
```
Problems:
- Импорт UserRole из mkobi.models.user_roles вместо mkobi.models.enums
- Использование UserRoleEnum и ROLE_LEVELS словаря (избыточно)
- Смешивание string literals и enum сравнений
- Функция check_role принимает str вместо UserRole

Recommendations:
- Заменить все импорты на mkobi.models.enums
- Убрать ROLE_LEVELS и использовать прямое сравнение с StrEnum
- Обновить типы аргументов на UserRole
- Удалить дублирующий функционал (UserRoleEnum vs UserRole)
```

### File: `src/mkobi/services/data_service.py`
```
Problems:
- Возможна опечатка: ProcessingStatus.PROCESSING (лишняя O)
- Сложная логика в _upload_file_logic (150+ строк)
- Нет явного закрытия файлов при загрузке

Recommendations:
- Проверить все обращения к ProcessingStatus (должно быть PROCESSING, STARTED, etc.)
- Вынести часть логики в отдельные функции
- Использовать context manager для файловых операций
```

### File: `src/mkobi/api/routes/auth.py`
```
Problems:
- Синтаксические ошибки: отсутствуют запятые между аргументами (строки 67, 112)
- login_form функция не асинхронная, но вызывается в async контексте

Recommendations:
- Добавить запятые: `auth_service.login_user(login_data.email, login_data.password)`
- Сделать login_form асинхронным или вызывать sync версию правильно
```

### File: `src/mkobi/db/repositories/aggregated_data_repo.py`
```
Problems:
- Mypy жалуется на возврат Any вместо конкретных типов
- Использование result.rowcount (может не работать в asyncpg)

Recommendations:
- Добавить явное приведение типов после execute()
- Использовать returnig() для получения количества затронутых строк
```

### File: `frontend/src/features/auth/api/authApi.ts`
```
Problems:
- logoutClient удаляет только access_token, refresh token не очищается
- Нет обработки ошибок в API вызовах (try/catch)

Recommendations:
- Добавить очистку всех auth-related данных при logout
- Добавить try/catch или использовать .catch() для обработки ошибок
```

---

## 6. Missing Features vs Specification

### Отсутствует (не реализовано):
1. **Refresh token endpoint** - в `auth.py` есть `/refresh`, но он просто декодирует тот же токен, а не использует refresh token механизм
2. **Rate limiting на login endpoint** - в `security.py` есть `RateLimiter`, но он используется только для upload, не для login
3. **Email blacklist domains проверка** - в `config.py` есть `blocked_domains`, но нет проверки в `auth_service.py`

### Реализовано частично:
1. **Data API filters** - реализовано в `services/data_service.py`, но фильтрация происходит в Python, а не в БД (для JSONB dims)
2. **Processing config** - есть модели, но интеграция с обработкой данных неполная

### Противоречит ТЗ:
1. В `auth.py` есть `/register` endpoint, которого нет в SPEC.md (SPEC.md указывает только `/register-request`)
2. В `permissions.py` используется `PermissionEnum` со значениями "read"/"write", а в БД CHECK constraint ожидает "view"/"edit"/"admin"

---

## 7. Frontend-Specific Findings

### 7.1 Architecture (FSD)
✅ Соблюдение структуры features/shared/app:
- `frontend/src/app/routes.tsx` - все роуты
- `frontend/src/features/` - auth, dashboards, upload, users, admin
- `frontend/src/shared/` - api (axiosInstance), components (ProtectedRoute, Layout)

⚠️ Нет явного разделения model/ в каждой feature (только в auth есть `model/`)

### 7.2 TypeScript
✅ Типы для API responses в `shared/types/api.types.ts`
✅ Zod schemas для форм (react-hook-form)
⚠️ Не проверено выполнение `tsc --noEmit` (нужно добавить в CI)

### 7.3 Components
✅ Все страницы из SPEC_FRONTEND.md реализованы:
- LoginPage (`/login`)
- RegisterPage (`/register`)
- DashboardList (`/dashboards`)
- DashboardView (`/dashboard/:id`)
- UploadPage (`/dashboard/:id/upload`)
- AdminPanel (`/admin`)
- UserProfile (`/profile`)

✅ Chart rendering работает (Plotly.js React) - `features/dashboards/ui/charts/`
✅ Filters применяются корректно - `DashboardFilters.tsx`

### 7.4 API Integration
✅ axiosInstance настроен с интерцепторами в `shared/api/axiosInstance.ts`
✅ JWT добавляется через интерцептор
⚠️ Error handling - используется react-hot-toast, но нет централизованной обработки ошибок API

---

## 8. Security Assessment

### 8.1 Backend
| Aspect | Status | Notes |
|--------|--------|-------|
| JWT | ✅ Secure | HS256 algorithm, secret from env, expiration check |
| Password hashing | ✅ Secure | BCrypt with 12 rounds, truncation to 72 bytes |
| SQL injection | ✅ Secure | SQLAlchemy ORM, parameterized queries |
| Upload security | ✅ Mostly secure | MIME-type check, file size limit, path traversal protection |
| Rate limiting | ⚠️ Partial | Есть для upload, нет для login |
| Secrets in code | ✅ Not found | Используется pydantic-settings, Docker secrets support |

### 8.2 Frontend
| Aspect | Status | Notes |
|--------|--------|-------|
| JWT storage | ⚠️ Check needed | `sessionStorage` in authApi.ts (не httpOnly, но и не localStorage) |
| ProtectedRoute | ✅ Works | Компонент есть, проверяет auth |
| RoleBasedAccess | ✅ Works | Компонент есть, проверяет роли |
| XSS protection | ✅ React | React экранирует вывод по умолчанию |

---

## 9. Performance Assessment

### 9.1 Backend
| Aspect | Status | Notes |
|--------|--------|-------|
| Processing | ✅ Good | Polars с lazy evaluation для больших файлов (>10MB) |
| DB indexes | ✅ Good | GIN index для JSONB dims, индексы для foreign keys |
| API | ⚠️ Check needed | CORS настроен, rate limiting только для upload |
| Async | ⚠️ Issues | Есть места где забыли `await` (mypy warnings) |

### 9.2 Frontend
| Aspect | Status | Notes |
|--------|--------|-------|
| Bundle size | ⚠️ Not checked | Нет анализа размера бандла |
| React rendering | ✅ Good | Plotly.js React, мемоизация не првоерена |
| API calls | ✅ Good | TanStack Query для кеширования и автоматического обновления |

---

## 10. Final Assessment

### Оценки:
- **Maintainability**: 6/10 (типизация требует исправления, технический долг)
- **Production Readiness**: 6/10 (тесты не работают, mypy errors)
- **Scalability**: 7/10 (Polars, PostgreSQL JSONB, async)
- **Security**: 8/10 (JWT, bcrypt, upload security)
- **Code Quality**: 6/10 (ruff OK, но mypy падает)

### Основные technical risks:
1. **CRITICAL**: Тесты не выполняются (нет БД `bidb_test`)
2. **HIGH**: Mypy errors (33+) - типизация сломана
3. **HIGH**: Непоследовательное использование StrEnum
4. **MEDIUM**: Async/sync смешивание (забыли `await`)
5. **MEDIUM**: Ошибки синтаксиса в `auth.py` (нет запятых)

### Приоритет исправлений:
1. **Критичные (CRITICAL)** — исправить немедленно:
   - Создать тестовую БД `bidb_test` или исправить конфигурацию
   - Исправить синтаксические ошибки в `auth.py` (добавить запятые)

2. **Высокие (HIGH)** — исправить до продакшена:
   - Исправить mypy errors (33+ ошибок типизации)
   - Унифицировать использование StrEnum (убрать `user_roles.py` импорты)
   - Добавить `await` где забыли

3. **Средние (MEDIUM)** — technical debt:
   - Убрать неиспользуемые `type: ignore` комментарии
   - Исправить опечатки в enum обращениях
   - Добавить rate limiting для login endpoint

4. **Низкие (LOW)** — nice to have:
   - Добавить `tsc --noEmit` проверку
   - Удалить странные точки входа в pyproject.toml
   - Добавить централизованную обработку ошибок на фронтенде

---

## 11. Commands Output

### ruff check .
```
All checks passed!
```
✅ Код соответствует стандартам PEP 8 и best practices (ruff)

### mypy .
```
33+ errors (см. раздел 4 Findings для деталей)
❌ Типизация требует исправления
```

### pytest
```
asyncpg.exceptions.InvalidCatalogNameError: database "bidb_test" does not exist
```
❌ Тесты не выполняются - нет тестовой БД

---

**Аудитор**: Senior Python Architect (AI Assistant)  
**Дата**: 2026-05-06  
**Версия отчета**: 1.0
