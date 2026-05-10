---
name: audit implementation general
description: audit implementation general
agent: audit
alwaysApply: false
---

# Full Audit Task

## Цель

Провести полный аудит проекта **mkobi** (Backend + Frontend + Data Layer + DevOps) на соответствие:
- Спецификациям (`SPEC.md` + `SPEC_FRONTEND.md`)
- Принципам Clean Architecture и Feature-Sliced Design
- Стандартам качества и безопасности

**Основной принцип:** Production-код должен быть понятным, безопасным, поддерживаемым и соответствующим ТЗ. Простота предпочтительнее избыточной сложности.

---

## Правила аудита

**Порядок проверки:**
1. Соответствие ТЗ
2. Архитектура и Separation of Concerns
3. Безопасность и надёжность
4. Качество кода и типизация
5. Производительность и maintainability

**Не считать проблемой:**
- Простые и понятные решения
- Минималистичную архитектуру (если она последовательна и расширяема)

**Критичные нарушения:**
- Уязвимости безопасности
- Смешивание слоёв / бизнес-логика в роутах
- Потеря данных / отсутствие cleanup
- Использование `print()` вместо logging
- Отсутствие `StrEnum` (где нужны фиксированные значения)
- Отсутствие type hints / `any` в TypeScript
- Нарушения access control

---

## BLOCK 1 — Architecture & Project Structure

### 1.1 Backend (Clean Architecture)
Проверить структуру `src/mkobi/`:

- **API Layer** — только routing, валидация, вызов сервисов
- **Service Layer** — бизнес-логика
- **Repository Layer** — доступ к данным
- **Models** — Pydantic + SQLAlchemy модели
- **Core** — security, permissions, logging, config
- **Data** — loaders, processing, storage

**Запрещено:**
- Бизнес-логика в роутах
- SQL в API-слое
- Циклические импорты
- Global mutable state

### 1.2 Frontend (Feature-Sliced Design)
Проверить соответствие FSD:
- `app/`, `features/`, `shared/`, `entities/` (если есть)
- Разделение: `ui/`, `api/`, `model/`, `lib/`

### 1.3 Data Processing Pipeline
- Использование **Polars** (НЕ pandas)
- Чёткий pipeline: upload → parse → transform → aggregate → save
- Корректная обработка ошибок и очистка временных файлов

---

## BLOCK 2 — Security & Access Control (КРИТИЧНО)

- JWT security (algorithm, expiration, secret management)
- Password hashing (bcrypt)
- Role & Permission system (`StrEnum`)
- Dashboard access control (`dashboard_access`)
- Upload security (path traversal, size limit, MIME-type, cleanup)
- SQL injection protection (ORM / parameterized queries)
- Secrets management (env + Docker secrets)

---

## BLOCK 3 — Backend API & Business Logic

Проверить все ключевые роуты:
- Auth (`login`, `register-request`, `me`)
- Dashboards (CRUD + access)
- Upload + Processing
- Data endpoints (aggregated)
- Admin endpoints

Особое внимание:
- Корректность Pydantic моделей
- Обработка ошибок (`HTTPException`)
- Rate limiting
- Access validation на каждом защищённом endpoint

---

## BLOCK 4 — Data Layer (PostgreSQL)

- Соответствие схемы БД спецификации
- Правильное использование **JSONB** + GIN-индексы
- Наличие необходимых индексов
- Alembic-миграции (качество, порядок, downgrade)
- Отсутствие N+1 и неэффективных запросов

---

## BLOCK 5 — Code Quality

### Backend
- Полная типизация (type hints + mypy)
- `StrEnum` вместо строк/dict/list
- Logging (английский, `getLogger(__name__)`, без `print()`)
- Error handling (не глотать исключения)
- Async correctness

### Frontend
- TypeScript (без `any`)
- ESLint + Prettier
- TanStack Query + React Hook Form + Zod
- Отсутствие `console.log()` в продакшен-коде
- Комментарии и логи на английском

---

## BLOCK 6 — Performance & Stability

- Обработка больших файлов (memory, streaming)
- Эффективность Polars
- Индексы и query performance
- Connection pooling
- Rate limiting и защита от abuse

---

## BLOCK 7 — Configuration & Deployment

- Pydantic-settings + nested env vars
- Docker / docker-compose
- Multi-stage build
- Production-ready конфигурация (static files, CORS и т.д.)

---

## Формат отчёта (ОБЯЗАТЕЛЬНО)

Создать файл: `TODO/AUDIT/PROJECT/audit_report_<number>.md` (свободный следующий номер)

### Структура отчёта:

1. **Executive Summary** (качество 1–10 по основным направлениям + Readiness)
2. **Architecture Compliance**
3. **Security Assessment**
4. **Requirements Coverage** (таблица PASS/FAIL по SPEC)
5. **Critical Findings** (таблица)
6. **Findings & Recommendations** (с severity)
7. **Missing / Partially Implemented Features**
8. **Final Assessment & Risks**

**Таблица проблем (пример):**

| Severity | Component | File | Problem | Recommendation |
|----------|---------|------|-------|--------------|
| CRITICAL | Security | upload.py | No temp file cleanup | Добавить `finally` + `platformdirs` |

---

### Правило аудитора: Лучше простое и надёжное решение, чем сложное и «правильное». Главный критерий — **maintainability** и **безопасность**.

---
